# Sales CRM (External)

Aplicación externa para el ciclo completo de ventas (lead → actividades → cotización → cierre → facturación → cobro). Incluye roles, pipeline, reportes, automatizaciones y generación de PDF de cotizaciones.

## Stack
- Backend: FastAPI + SQLAlchemy + Alembic
- DB: PostgreSQL
- Frontend: React + Vite + Tailwind
- Auth: JWT access + refresh
- PDF: WeasyPrint (HTML → PDF)
- Scheduler: APScheduler

## Requisitos
- Docker + Docker Compose

## Inicio rápido
1. Levantar servicios
   - `docker compose up --build`
2. Migraciones
   - `docker compose exec api alembic upgrade head`
3. Seed demo
   - `docker compose exec api python -m app.seed`
4. Sincronizar usuarios de producción (no borra datos)
   - `docker compose exec api python -m app.sync_users`

### URLs
- API: http://localhost:8000/docs
- Web: http://localhost:5173

### Usuarios demo
- Gerente: `manager@example.com` / `manager123`
- Supervisor Agras: `supervisor.agras@example.com` / `supervisor123`
- Supervisor Enterprise: `supervisor.enterprise@example.com` / `supervisor123`
- Vendedor Agras 1: `seller.agras1@example.com` / `seller123`
- Vendedor Agras 2: `seller.agras2@example.com` / `seller123`
- Vendedor Enterprise 1: `seller.enterprise1@example.com` / `seller123`
- Vendedor Enterprise 2: `seller.enterprise2@example.com` / `seller123`

## Deploy gratis (Netlify + Render + Supabase)
Configuración recomendada para producción gratuita con límites:

### 1) Base de datos (Supabase)
- Crear proyecto en Supabase.
- Copiar `DATABASE_URL` (Postgres).

### 2) API en Render (gratis)
- Conecta el repo a Render y usa `render.yaml`.
- Variables obligatorias:
  - `DATABASE_URL`
  - `JWT_SECRET`
  - `JWT_REFRESH_SECRET`
- `CORS_ORIGINS` ya está configurado para:
  - `https://latitude-ventas.com`
  - `https://www.latitude-ventas.com`
  - `https://app.latitude-ventas.com`

### 3) Migraciones + usuarios
Ejecutar contra la DB de Supabase:
- `DATABASE_URL="postgresql+psycopg2://..." alembic upgrade head`
- `DATABASE_URL="postgresql+psycopg2://..." python -m app.sync_users`

### 4) Frontend en Netlify (gratis)
- Usa `netlify.toml` en la raíz.
- Define `VITE_API_URL=https://api.latitude-ventas.com`.

### 5) Dominio Latitude-Ventas.com
Configurar DNS:
- `app.latitude-ventas.com` → CNAME a Netlify
- `api.latitude-ventas.com` → CNAME al dominio de Render
- `latitude-ventas.com` (apex) → apunta a Netlify (A/ALIAS según tu DNS)

## Comandos útiles
- `make up` / `make down`
- `make db-migrate`
- `make db-seed`
- `make test`

## Arquitectura
- `api/app/models`: entidades (Users, Opportunities, Activities, Quotes, Orders, Invoices, Payments, Tasks, Alerts)
- `api/app/api/routes`: endpoints REST
- `api/app/scheduler`: jobs de SLA, oportunidades estancadas y recordatorios de pago
- `web/src/pages`: UI en español

## Reglas de negocio clave
- No se puede mover a `Oferta Enviada` sin cotización.
- Descuento > umbral requiere aprobación para enviar.
- No se puede mover a `Ganado` sin cotización enviada/aprobada.
- No se puede cerrar como `Pagado/Cerrado` si la factura no está pagada (salvo permiso de manager).

## PDF de cotizaciones
- Endpoint: `POST /api/quotes/{id}/pdf`
- Se guarda en `api/app/storage/quotes`

## Reportes (CSV)
- `GET /api/reports/seller-performance`
- `GET /api/reports/pipeline-snapshot`
- `GET /api/reports/aging`

## Tests
- Unit tests de permisos y reglas de negocio
- Integración: flujo completo de venta

Ejecutar:
- `docker compose exec api pytest`

## Capturas (opcional)
- Abrir la Web y usar los módulos: Pipeline, Oportunidades, Cotizaciones, Facturas y Dashboard.
