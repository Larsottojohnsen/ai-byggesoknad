# AI Byggesøknad – Prosjekt TODO & Fremdrift

> Sist oppdatert: 2026-04-21
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
- [x] ✅ GitHub Actions workflow for automatisk deploy til Pages (`.github/workflows/pages.yml`)

### Database
- [x] ✅ Docker Compose: PostgreSQL 15 + PostGIS 3.4 + Redis 7
- [x] ✅ `001_initial_schema.sql` – alle tabeller med PostGIS-indekser
- [x] ✅ `002_seed_rules.sql` – 11 regler seeded

### Backend (FastAPI)
- [x] ✅ `main.py`, `core/config.py`, `core/database.py`, `core/cache.py`
- [x] ✅ `models/schemas.py` – alle Pydantic-modeller
- [x] ✅ `models/orm.py` – SQLAlchemy ORM-modeller (Fase 2)
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
  - Risikonivå-badge på kartet
  - Eiendomsgrense-sirkel som fallback

---

## FASE 3 – Innsending & Integrasjoner (Neste)

### Altinn-integrasjon
- [ ] ⬜ OAuth mot Altinn
- [ ] ⬜ Prefill søknadsskjema (blankett 5174)
- [ ] ⬜ Innsending via Altinn API

### Kommuneintegrasjon
- [ ] ⬜ eByggesak-integrasjon
- [ ] ⬜ Kommunespesifikke regler (YAML per kommune)
- [ ] ⬜ Automatisk kommuneidentifikasjon fra koordinat

### Auth & Multi-tenancy
- [ ] ⬜ Brukerregistrering/innlogging
- [ ] ⬜ Prosjekthistorikk per bruker
- [ ] ⬜ Deling av prosjekter

---

## Teknisk gjeld

- [ ] ⬜ Pytest-tester for regelmotor
- [ ] ⬜ Rate limiting på API
- [ ] ⬜ Sentry error tracking
- [ ] ⬜ OpenTelemetry tracing
- [ ] ⬜ Alembic for DB-migrasjoner
- [ ] ⬜ Frontend build-optimalisering (pnpm build)
- [ ] ⬜ E2E-tester (Playwright)

---

## Kjente begrensninger (v1)

| Begrensning | Årsak | Plan |
|---|---|---|
| Eiendomsdata returnerer fallback | WFS utilgjengelig i sandbox | Fungerer i prod |
| Plandata returnerer ukjent | Geonorge WFS begrensning | Fungerer i prod |
| NVE faredata returnerer ukjent | ArcGIS begrensning i sandbox | Fungerer i prod |
| In-memory prosjektlagring (dev) | Ingen Docker i dev | Start Docker Compose |
| Ingen auth | Bevisst v1-valg | Fase 3 |

---

## API-endepunkter (komplett)

```
GET  /health
GET  /address/search?q={tekst}
POST /project/create
POST /project/{id}/analyze
GET  /project/{id}
GET  /project/{id}/results
POST /classify
POST /documents/generate          → PDF-rapport
POST /documents/tiltaksbeskrivelse → AI Agent 3
POST /documents/nabovarsel         → AI Agent 4
POST /documents/soknadsutkast      → AI Agent 5
GET  /documents/download/{filename}
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

---

*Dette dokumentet oppdateres løpende. Sjekk commit-historikk for fremdrift.*
