FROM node:20-slim AS frontend-build
WORKDIR /app/frontend
COPY frontend/package.json ./
RUN npm install --ignore-scripts
COPY frontend/ ./
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

FROM python:3.12-slim
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./backend/
COPY demo/ ./demo/
COPY pyproject.toml .

COPY --from=frontend-build /app/frontend/.next/standalone/ ./frontend/
COPY --from=frontend-build /app/frontend/.next/static ./frontend/.next/static
COPY --from=frontend-build /app/frontend/public ./frontend/public

RUN mkdir -p /tmp/data && chmod 777 /tmp/data

# ponytail: one sh script, no process manager. uvicorn = backend (internal 8000),
# node = front-facing on Render's $PORT. node is foreground so Render's port scan
# sees it; uvicorn dies -> container exits -> Render restarts.
RUN printf '#!/bin/sh\n\
set -e\n\
uvicorn backend.main:app --host 127.0.0.1 --port 8000 &\n\
UVICORN_PID=$!\n\
node /app/frontend/server.js\n\
EXIT=$?\n\
kill $UVICORN_PID 2>/dev/null || true\n\
exit $EXIT\n' > /start.sh && chmod +x /start.sh

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
# node standalone server.js reads HOSTNAME (not HOST); bind all interfaces so Render can scan it.
ENV HOSTNAME=0.0.0.0
# Render injects PORT=10000 at runtime. Do NOT override PORT here — Next.js must bind Render's $PORT.
ENV UVICORN_HOST=127.0.0.1
ENV UVICORN_PORT=8000

EXPOSE 8000

# Render ignores HEALTHCHECK on free tier, but keep a probe on the front-facing port ($PORT).
HEALTHCHECK --interval=30s --timeout=5s --retries=3 --start-period=15s \
  CMD curl -f "http://127.0.0.1:${PORT:-10000}/" || exit 1

CMD ["/start.sh"]
