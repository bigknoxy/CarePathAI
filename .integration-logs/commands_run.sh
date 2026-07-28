#!/bin/bash
# CarePathAI Integration Environment Setup Commands

# Environment setup
export UID=$(id -u)
export GID=$(id -g)
mkdir -p ./ml_cache
chmod 0755 ./ml_cache
export CAREPATH_DATA_DIR="/home/josh/projects/CarePathAI/carepath_ml/data"

# Build and start containers
docker compose build --no-cache
MY_UID=$(id -u) MY_GID=$(id -g) docker compose up -d

# Fix ML service Dockerfile reference and command
# (Manual edit of docker-compose.yml to use carepath_ml/Dockerfile instead of Dockerfile.minimal)
# (Manual edit of docker-compose.yml to add explicit command for ML service)
MY_UID=$(id -u) MY_GID=$(id -g) docker compose build --no-cache ml
MY_UID=$(id -u) MY_GID=$(id -g) docker compose up -d --force-recreate ml

# Ingestion (if needed - not required as files already exist)
docker compose run --rm ml bash -lc "python /app/scripts/ingest_embeddings.py --input_dir /app/data/synthetic --output_dir /app/data/faiss"

# Health checks
curl -s http://localhost:8000/health
curl -s http://localhost:5000/health
curl -s http://localhost:5001/health

# Status check
docker compose ps