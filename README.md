# LDAP via HTTP (FastAPI)

Minimal FastAPI service that authenticates a user against LDAP and returns all available user attributes.

## Endpoints

- POST /auth/ldap
  - Body: { "login": "<user>", "password": "<pass>" }
  - 200: { ok: true, user: { dn: string, attributes: { ... } } }
  - 401: { ok: false, detail: "Invalid credentials" }
- GET /healthz

## Environment

Copy `.env.example` to `.env` and set:

- LDAP_SERVER
- LDAP_PORT (default 389)
- LDAP_BIND_DN (e.g., example.com to form login@example.com)
- LDAP_BASE_DN (e.g., DC=example,DC=com)
- PORT (default 8000)
 - ROOT_PATH (optional, e.g., "/api" when served behind a reverse proxy under a subpath)

## Local run

- Python 3.11+
- Install deps and run:

```
python -m venv .venv
. .venv/Scripts/Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open http://localhost:8000/docs

## Docker

Build and run with docker-compose:

```
docker compose up --build
```

Or plain Docker:

```
docker build -t ztueduua-ldap-via-http .
docker run --rm -p 8000:8000 --env-file .env ztueduua-ldap-via-http
```

## Notes

- The service binds using "<login>@<LDAP_BIND_DN>" and searches by sAMAccountName under LDAP_BASE_DN.
- Returned attributes are provided as-is from LDAP (json-decoded).
- Do not expose this service publicly without proper rate limiting and TLS.
 - If you run the service behind a reverse proxy at a subpath (e.g., `/api`), set `ROOT_PATH=/api`. Then the docs will be available at `/api/docs` and Swagger will correctly fetch `/api/openapi.json`.
 - When running behind a proxy, you may also want Uvicorn to respect proxy headers: add `--proxy-headers` (and configure allowed IPs as needed) to ensure correct scheme/host in generated OpenAPI.
