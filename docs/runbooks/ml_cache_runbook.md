ML cache permissions runbook

Purpose
- Step-by-step runbook for reproducing, applying, and verifying the cache-permissions remediation for the ml service (TRANSFORMERS_CACHE / HF_HOME). Copy-paste ready commands for DevOps & Developers.

Prerequisites
- Docker Engine + Docker Compose v2
- Project root checked out where docker-compose.yml lives
- Sufficient permissions to create host directories and run docker commands

1) Create host cache directory and set permissions

# create directory
mkdir -p ./ml_cache
# set ownership to your current user (recommended) and permissive group write for dev
chown $(id -u):$(id -g) ./ml_cache || true
chmod 0775 ./ml_cache
# verify
ls -ld ./ml_cache

Expected output (example)
# drwxrwxr-x 2 1000 1000 4096 Dec 23 19:18 ./ml_cache

2) Compose edits (add env vars and mount)

# Ensure the ml service in docker-compose.yml contains the following snippet EXACTLY under services:
#
#  ml:
#    build:
#      context: .
#      dockerfile: carepath_ml/Dockerfile.minimal
#    ports:
#      - "8000:8000"
#    volumes:
#      - ./ml_cache:/cache:rw
#      - ./carepath_ml/data:/app/data
#    environment:
#      - TRANSFORMERS_CACHE=/cache
#      - HF_HOME=/cache
#      - SENTENCE_TRANSFORMERS_HOME=/cache/sentence-transformers
#      - CAREPATH_DATA_DIR=/app/data
#    user: "${UID:-1000}:${GID:-1000}"
#    restart: unless-stopped

# After editing, run a quick lint of compose (optional)
docker compose config --quiet

3) If using a named volume (CI / production) — set ownership with one-off container

# Example: set ownership for a named volume called ml_cache_vol
docker volume create ml_cache_vol || true
# run a short container to chown
docker run --rm -v ml_cache_vol:/cache:rw alpine sh -c "chown -R 1000:1000 /cache"

# If you prefer a host dir mapped, set ownership on host instead:
# docker run --rm -v $(pwd)/ml_cache:/cache:rw alpine sh -c "chown -R 1000:1000 /cache"

4) Build and bring up the ml service

# Build image
docker compose build ml

# Run ml stand-alone (recreate)
docker compose up -d --force-recreate ml

# Confirm service status
docker compose ps | grep ml || docker compose ps

5) One-off commands to set ownership of named volumes (alternate)

# Example: chown named volume content to UID:GID 1000:1000
docker run --rm -v pgdata:/var/lib/postgresql/data alpine sh -c "chown -R 1000:1000 /var/lib/postgresql/data"

# For ml named volume
docker run --rm -v ml_cache_vol:/cache alpine sh -c "chown -R 1000:1000 /cache"

6) Verify inside the running container

# check user and cache perms inside container
docker compose exec ml bash -c "id && ls -ld /cache && ls -la /cache | head -n 30"

# expected: id shows non-root UID/GID (e.g., uid=1000 gid=1000), /cache owned by that UID/GID and writable

# create a test file as the runtime user
docker compose exec ml bash -c "python -c 'from pathlib import Path; p=Path(\"/cache/_runbook_test\"); p.write_text(\"ok\"); print(p.exists())' && ls -la /cache/_runbook_test"

# expected: True and file listed with write permissions

# run the ingest task to confirm no PermissionError
docker compose run --rm ml bash -c "python -m ingest.scripts.run_ingest"

# expected: ingest completes; logs show model downloads and files are written to host ./ml_cache

7) Troubleshooting quick checks

- If container fails to start or healthcheck fails:
  - docker compose logs --tail 200 ml
  - docker ps -a --filter "name=ml"
  - docker logs <container-id>

- If PermissionError persists:
  - Confirm the runtime UID/GID inside container: docker compose exec ml id
  - Confirm /cache ownership and mode: docker compose exec ml ls -ld /cache
  - If using host mount, confirm host permissions: ls -ld ./ml_cache
  - If using named volume, run a one-off chown container (see section 3)

- If Dockerfile CMD or module errors appear on startup:
  - Check carepath_ml/Dockerfile.minimal CMD and ensure it references an existing module (eg. simple_main:app or carepath_ml.main:app)
  - docker compose build ml && docker compose up --force-recreate ml and review logs

- If pip packages missing during runtime:
  - Ensure requirements.txt includes sentence-transformers, transformers, numpy (and any optional dependencies); check build logs for pip install errors: docker compose build ml

8) Reverting / Rollback

# To revert the fix quickly
# - Restore previous docker-compose.yml and carepath_ml/Dockerfile.minimal from VCS
# - Recreate service
#
docker compose up -d --force-recreate ml

Notes and recommendations
- Avoid 0777 on host cache in production. Prefer setting ownership to the runtime UID/GID (chown) or building the image to create the cache directory with correct ownership.
- CI: use named volumes and one-off chown containers or bake chown into your image build step.

Owners
- Recommended owner: DevOps (apply compose changes, volume ownership) and Developer (adjust Dockerfile, entrypoint, and verify ingest behavior)

End of runbook
