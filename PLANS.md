# Plan - Sales CRM

Milestones (in order)
1) Scaffold repository structure (api/, web/, docker-compose, Makefile, basic configs)
2) Data model + migrations (SQLAlchemy models, Alembic setup, seed script)
3) Auth + RBAC (JWT access/refresh, password hashing, permission guards)
4) Core CRM CRUD + pipeline rules (leads/opps, activities, quotes, orders, invoices, payments)
5) Automations (SLA, stale opps, payment reminders) via scheduler
6) Frontend UI (auth, pipeline, detail views, quotes, invoices, dashboards)
7) Reporting + exports (CSV endpoints + UI triggers)
8) Tests (unit for rules/permissions, integration flow), docs, CI

Checks
- Migrations run clean on empty DB
- Permissions enforced on every endpoint
- Business rules validated server-side
- PDF generation works end-to-end
- Dashboards and reports match filters
- Containerized local run works (api, web, db)
