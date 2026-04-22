# AI Byggesøknad – Prosjekt TODO & Fremdrift

> Sist oppdatert: 2026-04-22
> Repo: https://github.com/Larsottojohnsen/ai-byggesoknad
> Live: https://larsottojohnsen.github.io/ai-byggesoknad/
> Status-nøkkel: ✅ Ferdig | 🔄 Pågår | ⬜ Ikke startet | ❌ Blokkert

---

## FASE 1 – Forhåndsvurdering ✅ FERDIG

### Infrastruktur & Repo
- [x] ✅ GitHub-repo: `Larsottojohnsen/ai-byggesoknad`
- [x] ✅ Monorepo: `apps/web`, `apps/api`, `infra/`, `scripts/`, `docs/`
- [x] ✅ `.gitignore`, `README.md`, `pnpm-workspace.yaml`, `.env.example`
- [x] ✅ `scripts/dev.sh` – lokal oppstart
- [x] ✅ GitHub Pages landingsside (`docs/index.html`) – profesjonell HTML/CSS
- [x] ✅ GitHub Pages deployet fra `/docs`-mappen

### Database
- [x] ✅ Docker Compose: PostgreSQL 15 + PostGIS 3.4 + Redis 7
- [x] ✅ `001_initial_schema.sql` – alle tabeller med PostGIS-indekser
- [x] ✅ `002_seed_rules.sql` – 11 regler seeded

### Backend (FastAPI)
- [x] ✅ `main.py`, `core/config.py`, `core/database.py`, `core/cache.py`
- [x] ✅ `models/schemas.py` – alle Pydantic-modeller
- [x] ✅ `models/orm.py` – SQLAlchemy ORM-modeller
- [x] ✅ `providers/address_provider.py` – Kartverket **TESTET**
- [x] ✅ `providers/property_provider.py` – graceful fallback
- [x] ✅ `providers/plan_provider.py` – graceful fallback
- [x] ✅ `providers/hazard_provider.py` – graceful fallback
- [x] ✅ `rules/engine.py` – 12 regler (SØKP, PLAN, FARE, DOK, DISP)
- [x] ✅ `services/ai_orchestrator.py` – Agent 1 (klassifisering) + Agent 2 (oppsummering)
- [x] ✅ `services/analysis_service.py` – full pipeline **TESTET END-TO-END**
- [x] ✅ `services/document_service.py` – PDF-rapport (WeasyPrint)
- [x] ✅ `templates/report_template.html`

### Frontend (Next.js 14)
- [x] ✅ Landingsside, analyseside, resultatside
- [x] ✅ `AddressSearch` – autocomplete mot Kartverket
- [x] ✅ `MapView` – MapLibre GL JS med WMS-lag
- [x] ✅ `RiskBadge`, `RuleCard`
- [x] ✅ Zustand + TanStack Query

---

## FASE 2 – Søknadsforberedelse ✅ FERDIG

### PostgreSQL-integrasjon
- [x] ✅ `models/orm.py` – SQLAlchemy ORM for alle tabeller
- [x] ✅ `services/project_repository.py` – PostgreSQL + in-memory fallback
- [x] ✅ `services/analysis_service.py` – refaktorert til å bruke repository
- [x] ✅ `routers/project.py` – async get_project/get_analysis_result

### Dokumentmodul (AI Agenter 3–5)
- [x] ✅ `services/document_generator.py`
  - Agent 3: Tiltaksbeskrivelse (formell SAK10-kompatibel)
  - Agent 4: Nabovarsel (PBL § 21-3 kompatibel)
  - Agent 5: Søknadsveiledning (strukturert med alle seksjoner)
  - Fallback-maler for alle dokumenttyper
- [x] ✅ `routers/documents.py` – nye endepunkter:
  - `POST /documents/tiltaksbeskrivelse`
  - `POST /documents/nabovarsel`
  - `POST /documents/soknadsutkast`
- [x] ✅ `components/documents/DocumentPanel.tsx` – UI for dokumentgenerering

### Kartforbedringer
- [x] ✅ `MapView.tsx` – WMS-overlay fra Kartverket og NVE:
  - Eiendomsgrenser (Kartverket Matrikkel WMS)
  - Reguleringsplan (Kartverket arealplaner WMS)
  - Flomsoner (NVE ArcGIS WMS)
  - Skredfareområder (NVE ArcGIS WMS)
  - Lag-toggle med fargekoding

---

## FASE 3 – Kommuneintegrasjon & Kvalitet ✅ FERDIG

### Kommuneintegrasjon
- [x] ✅ `providers/municipality_provider.py` – identifiserer kommune fra koordinat (Kartverket API)
- [x] ✅ `rules/kommuner/0301_oslo.yaml` – Oslo-spesifikke regler, gebyrer, kontakt
- [x] ✅ `rules/kommuner/4601_bergen.yaml` – Bergen-spesifikke regler
- [x] ✅ `rules/kommuner/5001_trondheim.yaml` – Trondheim-spesifikke regler
- [x] ✅ `routers/municipality.py` – endepunkter:
  - `GET /municipality/identify?lat=&lng=`
  - `GET /municipality/rules/{kommunenr}`
  - `GET /municipality/supported`
- [x] ✅ `analysis_service.py` – integrert kommuneidentifikasjon og ekstra dokumentkrav

### Rate Limiting & Middleware
- [x] ✅ In-memory token bucket rate limiter (60 req/min generelt, 10 req/min for AI-endepunkter)
- [x] ✅ `X-RateLimit-Limit` og `X-RateLimit-Remaining` headers
- [x] ✅ Request timing middleware (`X-Response-Time` header)
- [x] ✅ `Retry-After` header ved 429-respons

### SSE Fremdriftsindikator
- [x] ✅ `GET /project/{id}/progress` – Server-Sent Events stream
- [x] ✅ `emit_progress()` funksjon i analysis_service
- [x] ✅ `components/analysis/AnalysisProgress.tsx` – animert steg-for-steg UI
- [x] ✅ `analyze/page.tsx` – oppdatert med modal progress overlay

### Alembic Migrasjoner
- [x] ✅ `alembic.ini` + `alembic/env.py` (async SQLAlchemy)
- [x] ✅ `alembic/versions/001_initial_schema.py` – alle tabeller
- [x] ✅ `alembic/versions/002_add_municipality_fields.py` – kommunenr, fylke, rate_limit_log

### Tester (pytest)
- [x] ✅ `tests/test_rule_engine.py` – 33 tester for regelmotor
- [x] ✅ `tests/test_municipality_provider.py` – 13 tester for kommuneintegrasjon
- [x] ✅ `tests/conftest.py` + `pytest.ini`
- [x] ✅ **46/46 tester passerer** ✅

---

## FASE 4 – Altinn & Innsending (Neste)

### Altinn-integrasjon
- [ ] ⬜ OAuth mot Altinn (Maskinporten)
- [ ] ⬜ Prefill søknadsskjema (blankett 5174)
- [ ] ⬜ Innsending via Altinn API v3

### eByggesak-integrasjon
- [ ] ⬜ Kommunespesifikk eByggesak-kobling
- [ ] ⬜ Automatisk saksnummer-oppslag

### Brukerautentisering (Fase 5)
- [ ] ⬜ NextAuth.js / Clerk
- [ ] ⬜ Prosjekthistorikk per bruker
- [ ] ⬜ Deling av prosjekter

---

## Teknisk gjeld

- [ ] ⬜ E2E-tester (Playwright)
- [ ] ⬜ Sentry error tracking
- [ ] ⬜ OpenTelemetry tracing
- [ ] ⬜ Frontend build-optimalisering (pnpm build)
- [ ] ⬜ Flere kommuner i YAML (Stavanger, Kristiansand, Tromsø, ++)
- [ ] ⬜ Persistent rate limiting (Redis-backed)

---

## API-endepunkter (komplett)

```
GET  /health
GET  /address/search?q={tekst}
POST /project/create
POST /project/{id}/analyze
GET  /project/{id}
GET  /project/{id}/results
GET  /project/{id}/progress          ← SSE (Fase 3)
POST /classify
POST /documents/generate             → PDF-rapport
POST /documents/tiltaksbeskrivelse   → AI Agent 3
POST /documents/nabovarsel           → AI Agent 4
POST /documents/soknadsutkast        → AI Agent 5
GET  /documents/download/{filename}
GET  /municipality/identify?lat=&lng= ← Fase 3
GET  /municipality/rules/{kommunenr}  ← Fase 3
GET  /municipality/supported          ← Fase 3
```

---

## Slik starter du lokalt

```bash
git clone https://github.com/Larsottojohnsen/ai-byggesoknad
cd ai-byggesoknad
cp .env.example .env
# Legg inn OPENAI_API_KEY i .env
./scripts/dev.sh
```

Frontend: http://localhost:3000 · Backend: http://localhost:8000 · API-docs: http://localhost:8000/docs

### Kjør tester

```bash
cd apps/api
pytest tests/ -v
# → 46/46 passed
```

### Kjør Alembic-migrasjoner

```bash
cd apps/api
alembic upgrade head
```

---

*Dette dokumentet oppdateres løpende. Sjekk commit-historikk for fremdrift.*
