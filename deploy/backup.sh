#!/bin/bash

# Backup script for Proper Prompts
# Can be added to crontab for automatic backups

set -e

DEPLOY_DIR="/opt/proper-prompts"
BACKUP_DIR="/opt/backups/proper-prompts"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

mkdir -p ${BACKUP_DIR}

echo "Creating backup..."

cd ${DEPLOY_DIR}/deploy

# Backup database
docker compose exec -T postgres pg_dump -U proper_prompts proper_prompts > ${BACKUP_DIR}/db_${TIMESTAMP}.sql
gzip ${BACKUP_DIR}/db_${TIMESTAMP}.sql

# Backup environment
cp .env ${BACKUP_DIR}/env_${TIMESTAMP}

# Backup logs
tar -czf ${BACKUP_DIR}/logs_${TIMESTAMP}.tar.gz ../logs/ 2>/dev/null || true

# Clean old backups (keep last 30 days)
find ${BACKUP_DIR} -name "*.sql.gz" -mtime +30 -delete
find ${BACKUP_DIR} -name "*.tar.gz" -mtime +30 -delete
find ${BACKUP_DIR} -name "env_*" -mtime +30 -delete

echo "Backup completed: ${BACKUP_DIR}"
ls -la ${BACKUP_DIR}

