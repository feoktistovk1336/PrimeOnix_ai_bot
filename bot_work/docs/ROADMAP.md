# Roadmap

## Stage 1 — Stabilization
- Keep FSM flows predictable and reset states on menu switching.
- Split large handlers into smaller modules over time.
- Add better queue statuses: `queued`, `processing`, `done`, `failed`.
- Add safer retry and timeout handling for AI/image providers.

## Stage 2 — SaaS Features
- AI Week Machine for regular users.
- Channel connection wizard.
- Scheduled content calendar UI.
- Advanced analytics: conversion, feature usage, paid/free split.
- Referral System 2.0 with bonus history.

## Stage 3 — Production
- PostgreSQL instead of SQLite for deployment.
- Redis/RQ/Celery queue for heavy generation tasks.
- Web dashboard for admin analytics.
- Dockerfile and CI/CD deployment.
- Error monitoring and structured logging.
