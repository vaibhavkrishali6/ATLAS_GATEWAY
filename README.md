# Atlas

Atlas is a gateway that discovers downstream services deployed independently.
This starter includes two service boundaries:

| Component | Responsibility | Default address |
| --- | --- | --- |
| `main:app` | Gateway health and service discovery | `:8000` |
| `services.accounts.app:app` | Account lifecycle and account schemas | `:8001` |
| `services.catalog.app:app` | Product catalog and product schemas | `:8002` |

Copy `.env.example` to `.env` and replace the service URLs with the addresses
of the actual remote servers. The gateway reads them using the `ATLAS_` prefix.

```powershell
uv run uvicorn main:app --port 8000
uv run uvicorn services.accounts.app:app --port 8001
uv run uvicorn services.catalog.app:app --port 8002
```

Each service owns its request/response contracts in its `schemas.py` file.
Replace the `NotImplementedError` route bodies with that service's database or
domain layer; do not put service persistence in the gateway.
