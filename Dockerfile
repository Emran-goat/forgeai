FROM node:20-slim AS frontend-build
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci --ignore-scripts
COPY frontend/ ./
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

FROM python:3.12-slim AS backend-build
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY --from=backend-build /install /usr/local
COPY backend/ ./backend/
COPY demo/ ./demo/
COPY pyproject.toml .

# Copy built Next.js standalone output
COPY --from=frontend-build /app/frontend/.next/standalone/ ./frontend-standalone/
COPY --from=frontend-build /app/frontend/.next/static ./frontend-standalone/.next/static
COPY --from=frontend-build /app/frontend/public ./frontend-standalone/public

RUN useradd -m appuser
USER appuser

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV HOST=0.0.0.0
ENV PORT=8000

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port 8000 & node /app/frontend-standalone/server.js & wait"]
