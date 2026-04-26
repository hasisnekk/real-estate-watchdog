FROM python:3.12-slim

WORKDIR /app

# System dependencies: curl (healthchecks), libpq-dev + gcc (asyncpg/psycopg2 build)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first (layer-cached unless requirements.txt changes)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application source
COPY src/ ./src/
COPY config/ ./config/

# Create runtime directories that will be bind-mounted in production.
# These serve as fallback locations when running without docker compose.
RUN mkdir -p data/spool data/logs data/seed data/backups

CMD ["python", "-m", "src.main"]
