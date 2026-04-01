# SpaceWeb API Authorization (from apidoc.sweb.ru/instructions)

## Summary
SpaceWeb API uses token-based auth over HTTP POST + JSON-RPC payloads.

- Token endpoint: `POST https://api.sweb.ru/notAuthorized/`
- Token method: `getToken`
- Main API endpoints require: `Authorization: Bearer <token>`

## 1) Get token
Request:

```http
POST /notAuthorized/ HTTP/1.1
Host: api.sweb.ru
Content-Type: application/json; charset=utf-8
Accept: application/json

{
  "jsonrpc": "2.0",
  "method": "getToken",
  "params": {
    "login": "<LOGIN>",
    "password": "<PASSWORD>"
  }
}
```

Response (example):

```json
{
  "jsonrpc": "2.0",
  "id": "20220505104244.40FxsQ16Ff",
  "result": "<TOKEN>"
}
```

## 2) Call authorized methods
Request headers for protected objects:

- `Content-Type: application/json; charset=utf-8`
- `Accept: application/json`
- `Authorization: Bearer <TOKEN>`

Example:

```http
POST /domains/ HTTP/1.1
Host: api.sweb.ru
Authorization: Bearer <TOKEN>
Content-Type: application/json; charset=utf-8
Accept: application/json

{
  "jsonrpc": "2.0",
  "method": "move",
  "params": {
    "domain": "mysite.ru",
    "prolongType": "no"
  }
}
```

## 3) Error behavior observed
- Missing/expired auth token for protected object may return JSON-RPC error `code: -32603` with message similar to `Время сеанса истекло.`
- Unknown method returns JSON-RPC error `code: -32601`.

## Notes
- API transport: JSON-RPC 2.0 over HTTP POST.
- Endpoint path identifies object/class (`/domains/`, `/sites/`, `/vps/`, ...).
- Request body identifies method and params.
