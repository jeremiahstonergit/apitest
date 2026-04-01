PYTHON ?= python3

.PHONY: rebuild validate import-dir import-archive package

rebuild:
	$(PYTHON) scripts/update_repo.py --rebuild-only

validate:
	$(PYTHON) scripts/update_repo.py --rebuild-only

import-dir:
	@test -n "$(SRC)" || (echo "Usage: make import-dir SRC=/path/to/snapshot" && exit 1)
	$(PYTHON) scripts/update_repo.py --source-dir "$(SRC)"

import-archive:
	@test -n "$(SRC)" || (echo "Usage: make import-archive SRC=/path/to/snapshot.tar.gz" && exit 1)
	$(PYTHON) scripts/update_repo.py --source-archive "$(SRC)"

package:
	tar -czf sweb-api-llm-spec-local.tar.gz \
		AGENTS.md CLAUDE.md README.md CHANGELOG.md CONTRIBUTING.md \
		auth client docs examples llm mcp notes scripts sources spec .github .cursor .windsurf .claude
