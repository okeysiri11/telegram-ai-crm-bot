# REST API

Base URL: `http://localhost:8080`

Auth: `Authorization: Bearer <jwt>`

Issue token:

```http
POST /api/auth/token
Content-Type: application/json

{"api_key": "<JWT_SECRET>", "telegram_id": 123}
```

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/auth/token` | JWT issue |
| GET | `/api/leads` | List leads |
| GET | `/api/leads/{request_number}` | Lead detail |
| GET | `/api/clients` | Unique clients from leads |
| GET | `/api/managers` | Configured managers |
| GET | `/api/inventory` | Search inventory (filters below) |
| POST | `/api/inventory` | Create inventory item |
| GET | `/api/recommendations` | Similar / alternatives |
| GET | `/api/analytics` | Owner analytics |
| GET | `/api/openapi.json` | OpenAPI 3 schema |
| GET | `/api/docs` or `/swagger` | Swagger UI |

## Inventory filters

Query params: `brand`, `model`, `year_from`, `year_to`, `price_from`, `price_to`,
`fuel`, `transmission`, `mileage_max`, `city`, `limit`.

## Example

```bash
TOKEN=$(curl -s -X POST localhost:8080/api/auth/token \
  -H 'Content-Type: application/json' \
  -d '{"api_key":"change-me-in-production"}' | jq -r .access_token)

curl -s localhost:8080/api/inventory?brand=BMW \
  -H "Authorization: Bearer $TOKEN"
```

Legacy gateway endpoints remain under `/v1/*`.
