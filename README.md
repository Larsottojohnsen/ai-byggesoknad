# AI Byggesøknad

Norsk AI-plattform som tar en bruker fra idé til byggesøknad – med automatisk geodatainnhenting, regelmotor og AI-assistert dokumentgenerering.

## Arkitektur

```
ai-byggesoknad/
├── apps/
│   ├── web/          # Next.js 14 frontend (TypeScript, Tailwind, MapLibre)
│   └── api/          # Python FastAPI backend (geodata, regelmotor, AI)
├── packages/
│   ├── rule-engine/  # Deklarativ regelmotor (YAML/JSON-regler)
│   ├── ai-orchestrator/ # AI-agenter (klassifisering, oppsummering, dokumenter)
│   └── shared-types/ # Delte TypeScript/Python-typer
├── infra/
│   ├── docker/       # Docker Compose (PostgreSQL+PostGIS, Redis)
│   └── migrations/   # SQL-migrasjoner
├── docs/             # Arkitekturdokumentasjon
└── scripts/          # Hjelpeskript
```

## Teknologistack

| Lag | Teknologi |
|-----|-----------|
| Frontend | Next.js 14, TypeScript, Tailwind CSS, shadcn/ui |
| Kart | MapLibre GL JS, Turf.js |
| Backend | Python 3.11, FastAPI, asyncpg |
| Database | PostgreSQL 15 + PostGIS |
| Cache | Redis 7 |
| AI | OpenAI GPT-4.1 |
| Containerisering | Docker Compose |

## Datakilder

- **Kartverket** – adresse-autocomplete og eiendomsdata
- **Geonorge OGC API** – reguleringsplaner og arealformål
- **NVE Atlas** – flom- og skredfare

## Kom i gang

```bash
# Klon repo
git clone https://github.com/Larsottojohnsen/ai-byggesoknad.git
cd ai-byggesoknad

# Start infrastruktur
docker-compose -f infra/docker/docker-compose.yml up -d

# Start backend
cd apps/api && pip install -r requirements.txt && uvicorn main:app --reload

# Start frontend
cd apps/web && pnpm install && pnpm dev
```

## Fremdrift

Se [TODO.md](./TODO.md) for detaljert prosjektstatus.

## Fase 1 – Forhåndsvurdering (nåværende)

- Adressebasert start med autocomplete
- Automatisk eiendomsoppslag
- Reguleringsplan- og faredata-analyse
- AI-klassifisering av tiltak
- Deklarativ regelmotor
- Resultatside med kart, risikobadge og neste steg
- PDF-rapport
