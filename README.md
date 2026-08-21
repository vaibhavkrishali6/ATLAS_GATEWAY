# Atlas

Atlas is a basic FastAPI reverse proxy for independently deployable healthcare services.

| Component | Responsibility | Default address |
| --- | --- | --- |
| `main:app` | Atlas reverse proxy | `:8000` |
| `services.patient_service.main:app` | Patient service | `:8001` |
| `services.doctor_service.main:app` | Doctor service | `:8002` |
| `services.medicine_service.main:app` | Medicine service | `:8003` |

Atlas receives API requests under `/api` and forwards them to the appropriate
service. Clients do not need to know the downstream service addresses.

## Development authentication

Start the auth service once to generate the ignored development RSA key pair
and issue RS256 access tokens. The private key stays under `auth_service`; ATLAS
uses only the configured public-key file.

```powershell
uv run uvicorn services.auth_service.main:app --port 8004
```

Development users are `doctor` / `doctor123` and `patient` / `patient123`.
Obtain a token, then include it in all `/api` requests:

```powershell
$token = (Invoke-RestMethod -Method Post http://localhost:8004/auth/login -ContentType application/json -Body '{"username":"doctor","password":"doctor123"}').access_token
Invoke-RestMethod http://localhost:8000/api/doctors -Headers @{ Authorization = "Bearer $token" }
```

At the current gateway authorization level, proxy routes require the `doctor`
role. A valid `patient` token is authenticated but receives `403 Forbidden`;
missing or invalid tokens receive `401 Unauthorized`. This rule applies only at
ATLAS and does not replace downstream business/data authorization.

## Persistent route registry

Atlas stores its route definitions in PostgreSQL table `routes`. Configure its
database with `ATLAS_DATABASE_URL` in `.env`; the included local configuration
uses the existing PostgreSQL instance on port `5433` and database `atlas_db`.
Create that database once if it does not exist:

```powershell
psql -h localhost -p 5433 -U postgres -c "CREATE DATABASE atlas_db"
```

At gateway startup, Atlas creates the `routes` table and inserts any missing
`patients`, `doctors`, and `medicines` routes. Existing rows are not duplicated.
The gateway still uses its current in-memory routing lookup for proxy requests;
database-backed request lookup is intentionally a later step.

```powershell
uv run uvicorn atlas.main:app --port 8000
uv run uvicorn services.patient_service.main:app --port 8001
uv run uvicorn services.doctor_service.main:app --port 8002
uv run uvicorn services.medicine_service.main:app --port 8003
```

To verify the seeded records after Atlas has started:

```powershell
psql -h localhost -p 5433 -U postgres -d atlas_db -c "SELECT id, service_name, base_url, path_prefix, active FROM routes ORDER BY id;"
```

## Streamlit proxy test client

`client/app.py` is a small manual test client for the Atlas reverse proxy. It
communicates only with Atlas at `http://localhost:8000`; it never calls the
Patient, Doctor, or Medicine services directly.

```text
Streamlit :8501
      ↓
Atlas :8000
      ↓
Patient :8001
Doctor :8002
Medicine :8003
```

Run the client after starting Atlas and the required downstream services:

```powershell
uv run streamlit run client/app.py
```

Example requests to enter in the UI:

- `GET` Patients with path `/1` → `http://localhost:8000/api/patients/1`
- `GET` Doctors with path `/1` → `http://localhost:8000/api/doctors/1`
- `GET` Medicines with an empty path → `http://localhost:8000/api/medicines`
- `POST` Patients with an empty path and a JSON body containing `name`, `age`,
  `gender`, `phone`, and `email`.
