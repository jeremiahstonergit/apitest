from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parent.parent
RAW_SCHEMA_DIR = ROOT / 'notes' / 'raw' / 'schema'
RAW_MISC_DIR = ROOT / 'notes' / 'raw'
MANIFEST_PATH = ROOT / 'sources' / 'manifest.json'
SUMMARY_JSON = ROOT / 'notes' / 'update-summary.latest.json'
SUMMARY_MD = ROOT / 'notes' / 'update-summary.latest.md'
PROJECTION_SPEC = ROOT / 'spec' / 'openapi.llm-projection.yaml'
TRANSPORT_SPEC = ROOT / 'spec' / 'openapi.transport.yaml'


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return yaml.safe_load(path.read_text(encoding='utf-8')) or {}


def collect_projection_ops(path: Path) -> dict[str, dict[str, Any]]:
    spec = load_yaml(path)
    out: dict[str, dict[str, Any]] = {}
    for route, item in (spec.get('paths') or {}).items():
        post = (item or {}).get('post') or {}
        op_id = post.get('operationId')
        if op_id:
            out[op_id] = {'path': route, 'post': post}
    return out


def copy_snapshot_files(source_root: Path) -> list[Path]:
    source_root = source_root.resolve()
    schema_candidates = sorted(source_root.rglob('openrpc*.json'))
    if not schema_candidates:
        raise FileNotFoundError(f'No openrpc*.json files found in {source_root}')

    RAW_SCHEMA_DIR.mkdir(parents=True, exist_ok=True)
    copied: list[Path] = []
    for src in schema_candidates:
        dst = RAW_SCHEMA_DIR / src.name
        shutil.copy2(src, dst)
        copied.append(dst)

    for name in [
        'CallingTheApi.js',
        'GettingATokenApi.js',
        'constants.text.js',
        'instructions.auth.snippets.txt',
    ]:
        src = next(iter(source_root.rglob(name)), None)
        if src and src.is_file():
            shutil.copy2(src, RAW_MISC_DIR / name)
            copied.append(RAW_MISC_DIR / name)
    return copied


def run_step(*cmd: str) -> None:
    subprocess.run([sys.executable, *cmd], cwd=ROOT, check=True)


def build_manifest(snapshot_source: str | None) -> dict[str, Any]:
    schema_files = sorted(RAW_SCHEMA_DIR.glob('openrpc*.json'))
    projection_ops = collect_projection_ops(PROJECTION_SPEC)
    transport = load_yaml(TRANSPORT_SPEC)
    transport_paths = sorted((transport.get('paths') or {}).keys())
    return {
        'updated_at': datetime.now(timezone.utc).isoformat(),
        'snapshot_source': snapshot_source,
        'raw_schema_dir': str(RAW_SCHEMA_DIR.relative_to(ROOT)),
        'raw_schema_files': [
            {
                'name': p.name,
                'sha256': sha256_file(p),
                'bytes': p.stat().st_size,
            }
            for p in schema_files
        ],
        'artifacts': {
            'projection_spec': str(PROJECTION_SPEC.relative_to(ROOT)),
            'transport_spec': str(TRANSPORT_SPEC.relative_to(ROOT)),
            'operation_count': len(projection_ops),
            'transport_path_count': len(transport_paths),
            'examples': 'examples/examples.jsonl',
            'python_operations_map': 'client/python/operations.generated.json',
            'ts_operations_map': 'client/ts/operations.generated.json',
        },
    }


def compare_ops(before: dict[str, dict[str, Any]], after: dict[str, dict[str, Any]]) -> dict[str, Any]:
    before_ids = set(before)
    after_ids = set(after)
    added = sorted(after_ids - before_ids)
    removed = sorted(before_ids - after_ids)
    changed = []
    for op_id in sorted(before_ids & after_ids):
        left = json.dumps(before[op_id], sort_keys=True, ensure_ascii=False)
        right = json.dumps(after[op_id], sort_keys=True, ensure_ascii=False)
        if left != right:
            changed.append(op_id)
    return {
        'before_count': len(before_ids),
        'after_count': len(after_ids),
        'added_count': len(added),
        'removed_count': len(removed),
        'changed_count': len(changed),
        'added': added,
        'removed': removed,
        'changed': changed,
    }


def write_summary(summary: dict[str, Any]) -> None:
    SUMMARY_JSON.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')

    lines = [
        '# Latest update summary',
        '',
        f"Generated at: {summary['generated_at']}",
        '',
        '## Operation diff',
        '',
        f"- Before: **{summary['operation_diff']['before_count']}**",
        f"- After: **{summary['operation_diff']['after_count']}**",
        f"- Added: **{summary['operation_diff']['added_count']}**",
        f"- Removed: **{summary['operation_diff']['removed_count']}**",
        f"- Changed: **{summary['operation_diff']['changed_count']}**",
        '',
    ]
    for key in ('added', 'removed', 'changed'):
        values = summary['operation_diff'][key]
        lines.append(f'## {key.capitalize()} operations')
        lines.append('')
        if not values:
            lines.append('- none')
        else:
            for op_id in values[:100]:
                lines.append(f'- `{op_id}`')
            if len(values) > 100:
                lines.append(f'- ... and {len(values) - 100} more')
        lines.append('')

    if summary.get('snapshot_source'):
        lines.extend([
            '## Snapshot source',
            '',
            f"- `{summary['snapshot_source']}`",
            '',
        ])

    SUMMARY_MD.write_text('\n'.join(lines), encoding='utf-8')


def resolve_snapshot_root(source_dir: str | None, source_archive: str | None) -> tuple[Path | None, tempfile.TemporaryDirectory[str] | None, str | None]:
    if not source_dir and not source_archive:
        return None, None, None
    if source_dir and source_archive:
        raise ValueError('Use either --source-dir or --source-archive, not both')
    if source_dir:
        p = Path(source_dir).expanduser().resolve()
        if not p.exists():
            raise FileNotFoundError(p)
        return p, None, str(p)

    archive = Path(source_archive).expanduser().resolve()
    if not archive.exists():
        raise FileNotFoundError(archive)
    tmp = tempfile.TemporaryDirectory(prefix='sweb-api-snapshot-')
    target = Path(tmp.name)
    with tarfile.open(archive, 'r:*') as tf:
        tf.extractall(target)
    return target, tmp, str(archive)


def main() -> None:
    parser = argparse.ArgumentParser(description='Update repository artifacts from raw SpaceWeb API snapshot.')
    parser.add_argument('--root', help='Project root (default: parent of scripts/)')
    parser.add_argument('--source-dir', help='Directory with upstream snapshot files (openrpc*.json, optional auth snippets)')
    parser.add_argument('--source-archive', help='Archive with upstream snapshot files')
    parser.add_argument('--limit', type=int, default=None, help='Optional method limit for partial builds; omit for all methods')
    parser.add_argument('--rebuild-only', action='store_true', help='Do not import a new snapshot; only rebuild current raw files')
    args = parser.parse_args()

    global ROOT, RAW_SCHEMA_DIR, RAW_MISC_DIR, MANIFEST_PATH, SUMMARY_JSON, SUMMARY_MD, PROJECTION_SPEC, TRANSPORT_SPEC
    if args.root:
        ROOT = Path(args.root).resolve()
        RAW_SCHEMA_DIR = ROOT / 'notes' / 'raw' / 'schema'
        RAW_MISC_DIR = ROOT / 'notes' / 'raw'
        MANIFEST_PATH = ROOT / 'sources' / 'manifest.json'
        SUMMARY_JSON = ROOT / 'notes' / 'update-summary.latest.json'
        SUMMARY_MD = ROOT / 'notes' / 'update-summary.latest.md'
        PROJECTION_SPEC = ROOT / 'spec' / 'openapi.llm-projection.yaml'
        TRANSPORT_SPEC = ROOT / 'spec' / 'openapi.transport.yaml'

    before = collect_projection_ops(PROJECTION_SPEC)
    snapshot_root = None
    temp_dir = None
    snapshot_source = None
    try:
        if not args.rebuild_only:
            snapshot_root, temp_dir, snapshot_source = resolve_snapshot_root(args.source_dir, args.source_archive)
            if snapshot_root is not None:
                copied = copy_snapshot_files(snapshot_root)
                print(f'Imported {len(copied)} snapshot files into repository raw sources.')

        build_cmd = ['scripts/build_mvp.py']
        if args.limit is not None:
            build_cmd.extend(['--limit', str(args.limit)])
        run_step(*build_cmd)
        run_step('scripts/tighten_results_from_examples.py')
        run_step('scripts/validate_mvp.py')

        after = collect_projection_ops(PROJECTION_SPEC)
        diff = compare_ops(before, after)

        manifest = build_manifest(snapshot_source)
        MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
        MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')

        summary = {
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'snapshot_source': snapshot_source,
            'operation_diff': diff,
            'manifest_path': str(MANIFEST_PATH.relative_to(ROOT)),
        }
        write_summary(summary)

        print('Repository update completed successfully.')
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    finally:
        if temp_dir is not None:
            temp_dir.cleanup()


if __name__ == '__main__':
    main()
