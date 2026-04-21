#!/bin/bash
# AI Byggesøknad – Local development startup script

set -e

echo "🏗️  AI Byggesøknad – Starting development environment"
echo ""

# Check for .env
if [ ! -f ".env" ]; then
  echo "⚠️  No .env file found. Copying from .env.example..."
  cp .env.example .env
  echo "✅ .env created. Edit it to add your OPENAI_API_KEY."
fi

# Start Docker services
echo "🐳 Starting Docker services (PostgreSQL + Redis)..."
cd infra/docker && docker compose up -d
cd ../..

# Wait for Postgres
echo "⏳ Waiting for PostgreSQL..."
sleep 3

# Run migrations
echo "📦 Running database migrations..."
PGPASSWORD=byggesoknad_dev psql -h localhost -U byggesoknad -d byggesoknad \
  -f infra/migrations/001_initial_schema.sql 2>/dev/null || true
PGPASSWORD=byggesoknad_dev psql -h localhost -U byggesoknad -d byggesoknad \
  -f infra/migrations/002_seed_rules.sql 2>/dev/null || true

echo ""
echo "🚀 Starting services..."
echo ""

# Start FastAPI backend
echo "🐍 Starting FastAPI backend on http://localhost:8000"
cd apps/api && python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
API_PID=$!
cd ../..

# Start Next.js frontend
echo "⚡ Starting Next.js frontend on http://localhost:3000"
cd apps/web && pnpm dev &
WEB_PID=$!
cd ../..

echo ""
echo "✅ Development environment started!"
echo "   Frontend: http://localhost:3000"
echo "   Backend:  http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services."

# Wait for Ctrl+C
trap "kill $API_PID $WEB_PID 2>/dev/null; docker compose -f infra/docker/docker-compose.yml down; exit 0" INT
wait
