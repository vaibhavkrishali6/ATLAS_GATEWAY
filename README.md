# Atlas — API Gateway for Microservices

Atlas is a **FastAPI-based API Gateway** designed to provide a single entry point for independently deployable healthcare microservices.

Instead of exposing every backend service directly to clients, requests are sent through Atlas, which handles **authentication, authorization, rate limiting, request tracing, routing, and structured logging** before forwarding traffic to the appropriate downstream service.

```text
                         ┌─────────────────┐
                         │     Client      │
                         └────────┬────────┘
                                  │
                                  ▼
                         ┌─────────────────┐
                         │  Atlas Gateway  │
                         │     :8000       │
                         ├─────────────────┤
                         │ JWT Auth        │
                         │ Authorization   │
                         │ Rate Limiting   │
                         │ Request ID      │
                         │ Routing         │
                         │ Logging         │
                         └────────┬────────┘
                                  │
                ┌─────────────────┼─────────────────┐
                │                 │                 │
                ▼                 ▼                 ▼
        ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
        │   Patient    │  │    Doctor    │  │   Medicine   │
        │    :8001     │  │    :8002     │  │    :8003     │
        └──────────────┘  └──────────────┘  └──────────────┘
                │                 │                 │
                └─────────────────┼─────────────────┘
                                  │
                         ┌────────▼────────┐
                         │   PostgreSQL    │
                         │ Route Registry  │
                         └─────────────────┘

                         ┌─────────────────┐
                         │      Redis      │
                         │  Rate Limiter   │
                         └─────────────────┘
```

## Why Atlas?

In a microservice architecture, exposing every service directly to clients creates several problems:

* Clients need to know where individual services are deployed.
* Authentication and authorization logic can become duplicated across services.
* Rate limiting has to be implemented repeatedly.
* Request tracing becomes harder across multiple services.
* Changes to service locations can require client-side changes.

Atlas introduces a **single gateway layer** between clients and backend services.

```text
Without Atlas

Client ──────► Patient Service
     ├───────► Doctor Service
     └───────► Medicine Service


With Atlas

Client ──────► Atlas ──────► Patient Service
                  ├────────► Doctor Service
                  └────────► Medicine Service
```

The client only needs to know about Atlas.

---

# Core Features

### 🔐 JWT Authentication

Atlas validates RS256-signed JWT access tokens issued by the authentication service.

Validation includes:

* JWT signature
* Token expiration
* Issuer
* Subject
* Required claims
* Bearer authentication

The gateway uses the **public RSA key** for verification. The private signing key remains within the authentication service.

```text
Auth Service
     │
     │ Private RSA Key
     ▼
   JWT Token
     │
     ▼
   Client
     │
     │ Authorization: Bearer <token>
     ▼
 Atlas Gateway
     │
     │ Public RSA Key
     ▼
 Verify Token
```

---

# Role-Based Authorization

Atlas currently enforces gateway-level role authorization for protected proxy routes.

For example:

| Role          | Gateway access |
| ------------- | -------------- |
| `doctor`      | ✅ Allowed      |
| `patient`     | ❌ Forbidden    |
| Missing token | ❌ Unauthorized |
| Invalid token | ❌ Unauthorized |
| Expired token | ❌ Unauthorized |

A valid token therefore does not automatically mean a request is authorized.

```text
Request
   │
   ▼
JWT validation
   │
   ├── Invalid ──────► 401
   │
   ▼
Role validation
   │
   ├── Insufficient ─► 403
   │
   ▼
Forward request
```

> Gateway authorization is intentionally separate from downstream business/data authorization. Services remain responsible for enforcing permissions specific to their own resources.

---

# 🚦 Redis-Backed Rate Limiting

Atlas implements distributed request rate limiting using **Redis and a Token Bucket algorithm**.

Each client receives a token bucket with a configured capacity and refill rate.

```text
                  ┌───────────────┐
Request ─────────►│ Redis Bucket  │
                  └───────┬───────┘
                          │
                    Tokens available?
                     /            \
                   Yes             No
                   │                │
                   ▼                ▼
              Forward request      429
```

The bucket state is stored in Redis so that multiple Atlas instances can share rate-limit state.

The token calculation and update are performed atomically using a Redis Lua script.

When the limit is exceeded, Atlas returns:

```http
HTTP/1.1 429 Too Many Requests
Retry-After: <seconds>
```

This allows clients to determine when they should retry.

---

# 🔀 Reverse Proxy & Service Routing

Clients communicate only with Atlas.

Routes follow the pattern:

```text
/api/{service}/{path}
```

Examples:

```text
GET  /api/patients/1
GET  /api/doctors/1
GET  /api/medicines
POST /api/patients
```

Atlas resolves the service and forwards the request to the appropriate downstream application.

For example:

```text
GET /api/doctors/1
        │
        ▼
Atlas :8000
        │
        ▼
Doctor Service :8002
        │
        ▼
GET /1
```

Atlas forwards the relevant:

* HTTP method
* request body
* query parameters
* request headers

and returns the downstream response to the client.

---

# 🗂️ Persistent Route Registry

Atlas maintains service route definitions in PostgreSQL.

The `routes` table stores information such as:

```text
service_name
base_url
path_prefix
active
created_at
updated_at
```

Example:

```text
patients   → http://localhost:8001   → /api/patients
doctors    → http://localhost:8002   → /api/doctors
medicines  → http://localhost:8003   → /api/medicines
```

At startup, Atlas initializes the registry and inserts missing service definitions without duplicating existing records.

### Current implementation

The database currently acts as **persistent route configuration**. Request-time proxy resolution still uses the gateway's in-memory routing configuration.

Database-backed request lookup and dynamic service management are planned as future improvements.

---

# 🔎 Request Correlation & Structured Logging

Atlas generates or propagates an `X-Request-ID` for every request.

The same identifier is forwarded to downstream services.

```text
Client
  │
  │ X-Request-ID: abc123
  ▼
Atlas
  │
  │ X-Request-ID: abc123
  ▼
Doctor Service
```

This allows a request to be traced across the gateway and downstream services.

Atlas also produces structured JSON logs containing information such as:

```json
{
  "request_id": "abc123",
  "method": "GET",
  "path": "/api/doctors/1",
  "status_code": 200,
  "duration_ms": 24
}
```

Logs use rotating file handlers to prevent individual log files from growing indefinitely.

---

# 🧩 Architecture

The project is organized around independently deployable services:

| Component                            | Responsibility                | Default Address |
| ------------------------------------ | ----------------------------- | --------------- |
| `atlas.main:app`                     | API Gateway / Reverse Proxy   | `:8000`         |
| `services.auth_service.main:app`     | Authentication & JWT issuance | `:8004`         |
| `services.patient_service.main:app`  | Patient API                   | `:8001`         |
| `services.doctor_service.main:app`   | Doctor API                    | `:8002`         |
| `services.medicine_service.main:app` | Medicine API                  | `:8003`         |
| PostgreSQL                           | Route registry                | `:5433`         |
| Redis                                | Distributed rate-limit state  | `:6379`         |

---

# Development Setup

## 1. Start the Authentication Service

The authentication service generates the development RSA key pair when required and issues RS256 access tokens.

```bash
uv run uvicorn services.auth_service.main:app --port 8004
```

Development credentials:

```text
doctor  / doctor123
patient / patient123
```

Obtain a token:

### PowerShell

```powershell
$token = (Invoke-RestMethod `
  -Method Post `
  http://localhost:8004/auth/login `
  -ContentType application/json `
  -Body '{"username":"doctor","password":"doctor123"}'
).access_token
```

Use the token with Atlas:

```powershell
Invoke-RestMethod `
  http://localhost:8000/api/doctors `
  -Headers @{ Authorization = "Bearer $token" }
```

---

# 2. Start the Backend Services

```bash
uv run uvicorn services.patient_service.main:app --port 8001
uv run uvicorn services.doctor_service.main:app --port 8002
uv run uvicorn services.medicine_service.main:app --port 8003
```

---

# 3. Start Atlas

```bash
uv run uvicorn atlas.main:app --port 8000
```

Atlas is now available at:

```text
http://localhost:8000
```

---

# 4. PostgreSQL Route Registry

Configure:

```text
ATLAS_DATABASE_URL
```

in `.env`.

For the local development setup, PostgreSQL is available through port `5433`.

Create the database if required:

```bash
psql -h localhost -p 5433 -U postgres -c "CREATE DATABASE atlas_db"
```

After Atlas starts, verify the seeded routes:

```bash
psql -h localhost -p 5433 \
  -U postgres \
  -d atlas_db \
  -c "SELECT id, service_name, base_url, path_prefix, active FROM routes ORDER BY id;"
```

---

# 🖥️ Streamlit Test Client

Atlas includes a small Streamlit client for manually testing gateway behavior.

The client communicates **only with Atlas**, not with the downstream services.

```text
Streamlit :8501
      │
      ▼
Atlas :8000
      │
      ├────► Patient :8001
      ├────► Doctor  :8002
      └────► Medicine:8003
```

Start it with:

```bash
uv run streamlit run client/app.py
```

Example requests:

```text
GET  /api/patients/1
GET  /api/doctors/1
GET  /api/medicines
POST /api/patients
```

For example:

```text
GET
/api/doctors/1
```

is sent to:

```text
Atlas :8000
      ↓
Doctor Service :8002
```

---

# 🧪 Testing

Atlas includes automated tests for authentication and gateway behavior.

The authentication test suite covers scenarios including:

* Valid JWT
* Missing JWT
* Invalid JWT
* Expired JWT
* Invalid signature
* Insufficient role
* Request ID propagation
* Request logging

Run the tests with:

```bash
uv run pytest
```

---

# 📊 Load Testing

Atlas includes a Locust-based load-testing setup for evaluating gateway behavior under concurrent traffic.

The goal is to measure:

* Request throughput
* Latency
* Error rate
* Rate-limit behavior
* Gateway overhead
* Downstream connection handling

Start Locust with:

```bash
uv run locust -f locust/locustfile.py
```

Then open the Locust interface and configure the target Atlas gateway.

> Benchmark results should be interpreted together with the test environment, concurrency, request mix, and downstream service configuration. Local development numbers should not be treated as production capacity.

---

# 🐳 Docker

Atlas and its supporting services can be run using Docker Compose.

The containerized architecture consists of:

```text
                    Atlas
                     │
       ┌─────────────┼─────────────┐
       ▼             ▼             ▼
   Patient        Doctor        Medicine
       │             │             │
       └─────────────┼─────────────┘
                     │
                PostgreSQL
                     │
                   Redis
```

Start the stack with:

```bash
docker compose up --build
```

---

# 🛡️ Security Notes

This repository contains **development-only credentials and configuration** intended for local testing.

Before production deployment, the system should be extended with:

* Secure password hashing
* Secret management
* Restricted administrative endpoints
* Production key rotation
* HTTPS/TLS
* Stronger role/permission policies
* Service-to-service authentication
* Redis failure handling
* Production-grade health checks

Development credentials and private signing keys should never be reused in production.

---

# 🚧 Current Limitations & Roadmap

Atlas is intentionally being developed incrementally.

Current limitations include:

* Route lookup still uses in-memory configuration at request time.
* Dynamic service registration is not yet implemented.
* Authentication uses development-oriented user management.
* Rate limiting currently focuses on the Token Bucket implementation.
* Load-testing results depend on the local development environment.
* Production secret/key management is not implemented.

Planned improvements:

```text
✓ Reverse proxy
✓ JWT authentication
✓ Role authorization
✓ Redis rate limiting
✓ Request correlation
✓ Structured logging
✓ Persistent route registry
✓ Dockerized deployment
✓ Load-testing infrastructure

→ Dynamic service discovery
→ Async Redis integration
→ Health-aware routing
→ Service health checks
→ Circuit breaking
→ Metrics / Prometheus
→ Distributed tracing
→ Production secret management
```

---

# Tech Stack

**Backend**

* Python
* FastAPI
* Pydantic
* SQLAlchemy
* HTTPX

**Infrastructure**

* PostgreSQL
* Redis
* Docker
* Docker Compose

**Authentication**

* JWT
* RSA / RS256

**Testing & Performance**

* Pytest
* Locust

**Client**

* Streamlit

---

# Project Goal

Atlas is primarily a **backend infrastructure project** focused on understanding how an API gateway operates in a distributed system.

The project explores the problems that appear when multiple independently deployable services need a common layer for:

```text
Authentication
      +
Authorization
      +
Rate Limiting
      +
Routing
      +
Request Tracing
      +
Logging
      +
Service Configuration
```

The long-term goal is to evolve Atlas from a basic reverse proxy into a more complete, production-oriented gateway capable of handling dynamic service discovery, health-aware routing, observability, and resilient distributed traffic management.


