#!/bin/bash
# restore.sh — Restore PostgreSQL database from backup
# Usage: bash scripts/restore.sh [/path/to/backup.sql.gz]
# If no path given, restores from the most recent backup.

set -euo pipefail

BACKUP_DIR=/home/viko/real-estate-watchdog/backups

# Resolve backup file
if [ -n "${1:-}" ]; then
    BACKUP_FILE="$1"
else
    BACKUP_FILE=$(ls -t "${BACKUP_DIR}"/*.sql.gz 2>/dev/null | head -1)
    if [ -z "${BACKUP_FILE}" ]; then
        echo "ERROR: No backup files found in ${BACKUP_DIR}"
        exit 1
    fi
fi

if [ ! -f "${BACKUP_FILE}" ]; then
    echo "ERROR: Backup file not found: ${BACKUP_FILE}"
    exit 1
fi

echo "[$(date -u +%FT%TZ)] Restoring from: ${BACKUP_FILE}"
echo "WARNING: This will overwrite the current database contents."
echo "Press Ctrl+C within 5 seconds to cancel..."
sleep 5

# Stop the watchdog app to prevent writes during restore
echo "[$(date -u +%FT%TZ)] Stopping watchdog service..."
docker compose stop watchdog

# Drop and recreate the database
echo "[$(date -u +%FT%TZ)] Dropping existing database..."
docker exec watchdog-db-1 psql -U watchdog -d postgres -c "DROP DATABASE IF EXISTS watchdog;"
docker exec watchdog-db-1 psql -U watchdog -d postgres -c "CREATE DATABASE watchdog OWNER watchdog;"

# Restore from backup
echo "[$(date -u +%FT%TZ)] Restoring data..."
gunzip -c "${BACKUP_FILE}" | docker exec -i watchdog-db-1 psql -U watchdog watchdog

echo "[$(date -u +%FT%TZ)] Restore complete."
echo "Restarting watchdog service..."
docker compose start watchdog

echo "[$(date -u +%FT%TZ)] Done. Run 'docker compose logs -f watchdog' to verify."
