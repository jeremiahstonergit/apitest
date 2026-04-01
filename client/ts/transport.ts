// SpaceWeb JSON-RPC transport adapter (RC draft)
// Minimal TypeScript client for Codex-generated integrations.

export type JsonRpcEnvelope<T = unknown> = {
  jsonrpc: '2.0' | string;
  id?: string;
  version?: string;
  result?: T;
  error?: { code: number; message: string; data?: unknown };
};

export type OperationMeta = {
  operationId: string;
  upstreamPath: string;
  upstreamMethod: string;
};

export class SwebApiError extends Error {
  code: number;
  data: unknown;

  constructor(code: number, message: string, data?: unknown) {
    super(`Sweb API error ${code}: ${message}`);
    this.code = code;
    this.data = data;
  }
}

export class SwebTransportClient {
  private server: string;
  private token?: string;
  private operations: Record<string, OperationMeta>;

  constructor(args: {
    server?: string;
    token?: string;
    operations: Record<string, OperationMeta>;
  }) {
    this.server = (args.server ?? 'https://api.sweb.ru').replace(/\/$/, '');
    this.token = args.token;
    this.operations = args.operations;
  }

  setToken(token: string) {
    this.token = token;
  }

  async getToken(login: string, password: string, id?: string): Promise<string> {
    const payload = await this.post<{ result: string }>('/notAuthorized/', {
      jsonrpc: '2.0',
      method: 'getToken',
      params: { login, password },
      ...(id ? { id } : {}),
    }, false);

    const token = payload.result;
    if (!token || typeof token !== 'string') {
      throw new Error('Token was not returned in result');
    }
    this.token = token;
    return token;
  }

  async callByOperation<T = unknown>(
    operationId: string,
    params: Record<string, unknown>,
    id?: string,
    user?: string,
  ): Promise<JsonRpcEnvelope<T>> {
    const op = this.operations[operationId];
    if (!op) throw new Error(`Unknown operationId: ${operationId}`);

    const body: Record<string, unknown> = {
      jsonrpc: '2.0',
      method: op.upstreamMethod,
      params: params ?? {},
    };
    if (id) body.id = id;
    if (user) body.user = user;

    const withAuth = !(op.upstreamPath === '/notAuthorized/' && op.upstreamMethod === 'getToken');
    return this.post<T>(op.upstreamPath, body, withAuth);
  }

  private async post<T = unknown>(
    path: string,
    body: Record<string, unknown>,
    withAuth: boolean,
  ): Promise<JsonRpcEnvelope<T>> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json; charset=utf-8',
      'Accept': 'application/json',
    };

    if (withAuth) {
      if (!this.token) throw new Error('Auth token is required but not set');
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    const res = await fetch(`${this.server}${path}`, {
      method: 'POST',
      headers,
      body: JSON.stringify(body),
    });

    if (!res.ok) throw new Error(`HTTP ${res.status}`);

    const payload = (await res.json()) as JsonRpcEnvelope<T>;
    if (payload.error) {
      throw new SwebApiError(payload.error.code, payload.error.message, payload.error.data);
    }
    return payload;
  }
}
