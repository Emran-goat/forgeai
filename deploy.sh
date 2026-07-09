#!/bin/bash
set -euo pipefail

echo "==> ForgeAI Deploy"

if [ ! -f .env ]; then
  echo "Creating .env from .env.example..."
  cp .env.example .env
  echo "Edit .env and add your FIREWORKS_API_KEY"
  exit 1
fi

echo "==> Building Docker image..."
docker compose build

echo "==> Starting services..."
docker compose up -d

echo "==> Waiting for health check..."
for i in $(seq 1 30); do
  if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
    echo "==> ForgeAI is running!"
    echo "    Backend:  http://localhost:8000"
    echo "    Frontend: http://localhost:3000"
    echo "    API Docs: http://localhost:8000/docs"
    echo "    Health:   http://localhost:8000/health"
    exit 0
  fi
  sleep 2
done

echo "==> Health check failed. Checking logs..."
docker compose logs --tail=20
exit 1
