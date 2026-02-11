# Billing API (Django + DRF + PostgreSQL + Docker)

This project implements the **Provider / Barrel / Invoice / InvoiceLine** model and exposes read-only endpoints.

## Stack
- Django + Django REST Framework
- PostgreSQL
- drf-spectacular (OpenAPI + Swagger UI)
- django-filter (enabled globally)

## Endpoints
Base: `http://localhost:8000/api/`

- `GET /api/invoices/` (includes `lines`, **without barrel objects**; only `barrel_id`)
- `GET /api/providers/` (basic provider data + `has_barrels_to_bill`)
- `GET /api/barrels/` (lists all barrels; no billed/unbilled filter configured)

Docs:
- Swagger UI: `GET /api/schema/swagger-ui/`
- OpenAPI JSON: `GET /api/schema/`

## Quick start (Docker)
1) Create `.env` (you can copy from `.env.example`):


```bash
cp .env.example .env
```

2) Build & run:

```bash
docker-compose build
docker-compose up
```

3) Apply migrations and (optionally) load sample data:

```bash
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py seed_demo
```

4) Create superuser to access to admin
```bash
docker-compose exec web sh -c "python manage.py createsuperuser"
```

## Notes about domain behavior
- `Provider.has_barrels_to_bill()` returns `True` if any related barrel is not billed.
- `Invoice.add_line_for_barrel(...)` enforces:
  - liters > 0
  - unit_price_per_liter > 0
  - only allows billing when `liters == barrel.liters`
  - marks the barrel as billed when the line is added
