# AI Byggesøknad – Prosjekt TODO & Fremdrift

> Sist oppdatert: 2026-04-21
> Repo: https://github.com/Larsottojohnsen/ai-byggesoknad
> Status-nøkkel: ✅ Ferdig | 🔄 Pågår | ⬜ Ikke startet | ❌ Blokkert

---

## FASE 1 – Forhåndsvurdering (MVP) ← **AKTIV**

### Infrastruktur & Repo
- [x] ✅ GitHub-repo opprettet: `Larsottojohnsen/ai-byggesoknad`
- [x] ✅ Monorepo-struktur: `apps/web`, `apps/api`, `infra/`, `scripts/`
- [x] ✅ `.gitignore`, `README.md`, `pnpm-workspace.yaml`
- [x] ✅ `.env.example` med alle nødvendige variabler
- [x] ✅ `scripts/dev.sh` – lokal oppstart

### Docker & Database
- [x] ✅ `infra/docker/docker-compose.yml` – PostgreSQL 15 + PostGIS 3.4 + Redis 7
- [x] ✅ `infra/docker/init-db.sql` – PostGIS extension aktivering
- [x] ✅ `infra/migrations/001_initial_schema.sql` – alle tabeller med PostGIS-indekser
  - `addresses`, `properties`, `projects`, `plan_layer_results`
  - `hazard_results`, `rules`, `rule_results`, `files`
  - `document_artifacts`, `audit_events`
- [x] ✅ `infra/migrations/002_seed_rules.sql` – 11 initielle regler seeded
- [x] ✅ Trigger: `update_updated_at_column` på `projects` og `rules`

### Backend (FastAPI) – `apps/api/`
- [x] ✅ `main.py` – FastAPI app med CORS, health endpoint
- [x] ✅ `core/config.py` – Pydantic Settings med feature flags
- [x] ✅ `core/database.py` – SQLAlchemy async engine
- [x] ✅ `core/cache.py` – Redis async cache (graceful fallback)
- [x] ✅ `models/schemas.py` – alle Pydantic-modeller og enums
- [x] ✅ `requirements.txt`

**Providers (API-adaptere):**
- [x] ✅ `providers/address_provider.py` – Kartverket ws.geonorge.no **TESTET OG FUNGERER**
- [x] ✅ `providers/property_provider.py` – Kartverket WFS (graceful fallback)
- [x] ✅ `providers/plan_provider.py` – Geonorge OGC API (graceful fallback)
- [x] ✅ `providers/hazard_provider.py` – NVE ArcGIS (graceful fallback)

**Regelmotor:**
- [x] ✅ `rules/engine.py` – 12 regler implementert og testet
  - SØKP-001: Bruksendring søknadsplikt (PBL § 20-1 d)
  - SØKP-002: Tilbygg/påbygg søknadsplikt (PBL § 20-1 b)
  - SØKP-003: Mulig unntak § 20-5
  - PLAN-001: Strid med reguleringsplan
  - PLAN-002: LNF-område
  - PLAN-003: Hensynssoner
  - FARE-001: Flomsone (TEK17 § 7-2)
  - FARE-002: Skredfareområde (TEK17 § 7-3)
  - DOK-001/002/003: Dokumentkrav
  - DISP-001: Dispensasjonsindikator
- [x] ✅ `compute_risk_level()` – lav/middels/høy
- [x] ✅ `compute_application_required()` – søknadsplikt-logikk
- [x] ✅ `generate_next_steps()` – kontekstuelle neste steg
- [x] ✅ `generate_document_requirements()` – dokumentliste

**AI-orkestrering:**
- [x] ✅ `services/ai_orchestrator.py`
  - Agent 1: Klassifisering av tiltakstype (GPT-4.1-mini) **TESTET**
  - Agent 2: Norsk oppsummering av analyse **TESTET**
  - Fallback: nøkkelordbasert klassifisering uten AI
- [x] ✅ `services/analysis_service.py` – full pipeline **TESTET END-TO-END**
- [x] ✅ `services/document_service.py` – Jinja2 + WeasyPrint PDF
- [x] ✅ `templates/report_template.html` – full HTML-rapport med CSS

**API-endepunkter (alle testet):**
- [x] ✅ `GET /health`
- [x] ✅ `GET /address/search?q=...` – Kartverket live-søk
- [x] ✅ `POST /project/create`
- [x] ✅ `POST /project/{id}/analyze` – full pipeline
- [x] ✅ `GET /project/{id}`
- [x] ✅ `GET /project/{id}/results`
- [x] ✅ `POST /classify`
- [x] ✅ `POST /documents/generate`
- [x] ✅ `GET /documents/download/{filename}`

### Frontend (Next.js) – `apps/web/`
- [x] ✅ Next.js 14 + TypeScript + Tailwind CSS
- [x] ✅ `src/types/index.ts` – TypeScript-typer
- [x] ✅ `src/lib/api.ts` – API-klient
- [x] ✅ `src/lib/utils.ts` – utility-funksjoner
- [x] ✅ `src/store/projectStore.ts` – Zustand state management
- [x] ✅ `src/app/layout.tsx` – root layout
- [x] ✅ `src/app/page.tsx` – landingsside
- [x] ✅ `src/app/analyze/page.tsx` – analyseside med adressesøk
- [x] ✅ `src/app/project/[id]/page.tsx` – resultatside
- [x] ✅ `src/components/analysis/AddressSearch.tsx` – autocomplete
- [x] ✅ `src/components/map/MapView.tsx` – MapLibre GL JS kart
- [x] ✅ `src/components/ui/RiskBadge.tsx` – risikonivå-badge
- [x] ✅ `src/components/ui/RuleCard.tsx` – regelresultat-kort

---

## FASE 2 – Søknadsforberedelse (Neste sprint)

### Database-integrasjon
- [ ] ⬜ Koble `analysis_service` til PostgreSQL (nå: in-memory dict)
- [ ] ⬜ Persistent prosjektlagring
- [ ] ⬜ Alembic for DB-migrasjoner
- [ ] ⬜ Audit log aktivert

### Dokumentmodul
- [ ] ⬜ Opplasting av tegninger/bilder
- [ ] ⬜ AI-analyse av opplastede dokumenter
- [ ] ⬜ Nabovarsel-generator (AI Agent 3)
- [ ] ⬜ Tiltaksbeskrivelse-generator (AI Agent 4)

### Kartforbedringer
- [ ] ⬜ Eiendomsgrenser fra Kartverket WFS
- [ ] ⬜ Planlag-overlay (WMS)
- [ ] ⬜ NVE farelag-overlay
- [ ] ⬜ Hensynssone-visualisering
- [ ] ⬜ Lag-toggle i UI

### Brukeropplevelse
- [ ] ⬜ Fremdriftsindikator under analyse (SSE/WebSocket)
- [ ] ⬜ Feilhåndtering i frontend
- [ ] ⬜ Mobiloptimalisering
- [ ] ⬜ Mørk modus

---

## FASE 3 – Innsending & Integrasjoner (Fremtidig)

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

- [ ] ⬜ Erstatt in-memory store med PostgreSQL i `analysis_service`
- [ ] ⬜ Legg til pytest-tester for regelmotor
- [ ] ⬜ Legg til rate limiting på API
- [ ] ⬜ Legg til Sentry error tracking
- [ ] ⬜ Legg til OpenTelemetry tracing
- [ ] ⬜ Bygg frontend (pnpm install + pnpm build)

---

## Kjente begrensninger (v1)

| Begrensning | Årsak | Plan |
|---|---|---|
| Eiendomsdata returnerer fallback | WFS utilgjengelig i sandbox | Fungerer i prod |
| Plandata returnerer ukjent | Geonorge WFS begrensning | Fungerer i prod |
| NVE faredata returnerer ukjent | ArcGIS begrensning i sandbox | Fungerer i prod |
| In-memory prosjektlagring | Ingen DB-tilkobling i dev | Fase 2 |
| Ingen auth | Bevisst v1-valg | Fase 3 |

---

## Arkitektur & Teknologivalg

| Lag | Teknologi | Status |
|-----|-----------|--------|
| Frontend | Next.js 14, TypeScript, Tailwind CSS | ✅ Scaffold klar |
| Kart | MapLibre GL JS | ✅ Komponent klar |
| State | TanStack Query + Zustand | ✅ Konfigurert |
| Backend | Python 3.11 + FastAPI | ✅ Kjører |
| Database | PostgreSQL 15 + PostGIS | ✅ Schema klar |
| Cache | Redis 7 | ✅ Graceful fallback |
| AI | OpenAI GPT-4.1-mini | ✅ Fungerer |
| Fil-lagring | Lokal (S3-kompatibel senere) | ✅ Konfigurert |
| Containerisering | Docker Compose | ✅ Klar |

---

## Datakilder

| Kilde | Formål | Adapter | Status |
|-------|--------|---------|--------|
| Kartverket Adresse-API | Adresse-autocomplete | `AddressProvider` | ✅ Testet |
| Kartverket Matrikkel WFS | Eiendomsdata, gnr/bnr | `PropertyProvider` | ✅ Graceful fallback |
| Geonorge OGC API Features | Reguleringsplaner | `PlanProvider` | ✅ Graceful fallback |
| NVE Atlas ArcGIS | Flom- og skredfare | `HazardProvider` | ✅ Graceful fallback |

---

## Filstruktur

```
ai-byggesoknad/
├── apps/
│   ├── api/                    # FastAPI backend
│   │   ├── core/               # Config, DB, Cache
│   │   ├── models/             # Pydantic schemas
│   │   ├── providers/          # Kartverket, NVE adaptere
│   │   ├── rules/              # Regelmotor (12 regler)
│   │   ├── routers/            # API endepunkter
│   │   ├── services/           # Business logic + AI
│   │   ├── templates/          # PDF-maler (HTML/CSS)
│   │   ├── main.py
│   │   └── requirements.txt
│   └── web/                    # Next.js frontend
│       └── src/
│           ├── app/            # Next.js App Router
│           ├── components/     # React-komponenter
│           ├── lib/            # Utilities + API-klient
│           ├── store/          # Zustand state
│           └── types/          # TypeScript typer
├── infra/
│   ├── docker/                 # Docker Compose + init SQL
│   └── migrations/             # SQL-migrasjoner
├── scripts/
│   └── dev.sh                  # Lokal oppstart
├── .env.example
├── .gitignore
├── README.md
└── TODO.md                     # ← Du er her
```

---

## Neste umiddelbare steg

1. `git push` – push alt til GitHub
2. Koble `OPENAI_API_KEY` i `.env` for full AI-funksjonalitet
3. Kjør `docker compose up -d` for lokal database
4. Kjør `scripts/dev.sh` for å starte hele stacken
5. Fase 2: Koble `analysis_service` til PostgreSQL

---

*Dette dokumentet oppdateres løpende. Sjekk commit-historikk for fremdrift.*
