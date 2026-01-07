#!/bin/bash

# Quick update script for Proper Prompts
# Run this after pulling latest code

set -e

DEPLOY_DIR="/opt/proper-prompts"

echo "Updating Proper Prompts..."

cd ${DEPLOY_DIR}

# Pull latest code (if using git)
# git pull origin main

# Rebuild and restart services
cd deploy
docker compose build --no-cache backend frontend
docker compose up -d

# Show status
docker compose ps

echo "Update complete!"

