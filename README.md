# DBCBackend

Django REST Framework backend for the Digital Business Card SaaS platform. Full spec: [backend.md](backend.md).

## Stack

Python 3.12, Django, DRF, MySQL, Redis, Celery, JWT auth (SimpleJWT), S3-compatible storage, Stripe / M-Pesa / SasaPay.

## Local setup

```bash
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env   # then fill in DATABASE_URL etc.

mysql -u root -e "CREATE DATABASE dbc_backend CHARACTER SET utf8mb4;"   # or: docker compose up -d db redis

python manage.py migrate
python manage.py seed_initial_data   # plans + card templates
python manage.py createsuperuser

python manage.py runserver
```

`mysqlclient` (the Python driver) needs MySQL's client dev headers to build — on macOS: `brew install mysql-client && export PKG_CONFIG_PATH="$(brew --prefix mysql-client)/lib/pkgconfig"` before `pip install`.

In separate terminals for background jobs:

```bash
celery -A config worker -l info
celery -A config beat -l info
```

Or run everything (MySQL, Redis, web, worker, beat) via:

```bash
docker compose up --build
```

## Project layout

- `config/` — settings (`base`/`development`/`production`), root URLConf, Celery app.
- `apps/` — one Django app per domain area (`accounts`, `organizations`, `cards`, `profile_blocks`,
  `templates`, `appointments`, `analytics`, `billing`, `directory`, `orders`, `nfc_qr`, `enquiries`,
  `notifications`, `core`). See `backend.md` §6 for what lives where.
- Authenticated API: `/api/v1/...`. Public, unauthenticated surfaces (card renderer, `.vcf`, QR,
  directory search, webhooks, health checks) are mounted outside `/api/v1/` — see `config/urls.py`.
- API schema: `/api/v1/schema/`, Swagger UI: `/api/v1/docs/`.
- Postman collection + environment: `docs/postman/` (see `docs/postman/README.md` to import or regenerate).

## Status

This is the initial backend scaffold: full data model, JWT auth, tenant-scoped CRUD for every
resource in the spec, the server-rendered public card page (SEO/OG/JSON-LD, `.vcf`, QR), booking/
enquiry flows, analytics event capture + hourly rollups, and a provider-abstracted billing layer
(Stripe/M-Pesa/SasaPay) with idempotent webhook handling.

Not yet wired to live provider credentials or production infra — see the `TODO` comments in
`apps/billing/services.py` (storage-usage accounting) and the payment provider modules before
processing real payments.
