# Troubleshooting

## ML container: missing ML packages / ingestion fails (cache permissions & broken minimal Dockerfile)

Short description
- ML service fails to start or ingestion fails because the minimal Dockerfile uses a broken inline CMD and the container cannot write to the default transformers/HF cache path (/.cache) when running as a non-root user.

Symptoms
- docker compose logs show: "python: can't open file '/app/basic_main.py'"
- A SyntaxError referenced from carepath_ml/Dockerfile.minimal inline CMD
- When running ingest, a PermissionError appears: "Permission denied: '/.cache'"
- Models never download or ingestion crashes repeatedly

Commands to inspect
- docker compose logs --tail 500 ml
- docker ps -a --filter "name=ml"
- docker logs <ml-container-id>
- docker compose run --rm ml bash -c "ls -la / && id && ls -la /.cache || true"

Immediate fixes (apply and then rebuild/recreate the ml service)
1) Fix Dockerfile minimal CMD
- Replace the invalid inline CMD in carepath_ml/Dockerfile.minimal with a valid ASGI/entrypoint, for example:
  CMD ["uvicorn", "carepath_ml.main:app", "--host", "0.0.0.0", "--port", "8080"]
- Or ensure the referenced basic_main.py exists and is valid in /app

2) Add cache env vars and a writable mount to docker-compose.yml (service: ml)
- Edit the ml service and add the following under that service:
  environment:
    - TRANSFORMERS_CACHE=/cache
    - HF_HOME=/cache
  volumes:
    - ./ml_cache:/cache:rw

- Create and set perms for local host cache dir (for development):
  mkdir -p ./ml_cache && chmod 0777 ./ml_cache

3) Ensure non-root user can write the cache
- Option A: run container as host user in compose (local dev):
    user: "${UID:-1000}:${GID:-1000}"
  Export UID/GID in your shell before running compose.
- Option B: initialize permissions inside image or with an init job to chown /cache to the runtime user.

After applying changes
- Rebuild and recreate ml service:
  docker compose up -d --build --force-recreate ml
- Check logs for absence of the earlier errors:
  docker compose logs --tail 200 ml
- Run the ingest task to confirm it completes without PermissionError:
  docker compose run --rm ml bash -c "python -m ingest.scripts.run_ingest"

If problems persist
- Confirm the ml container process user (docker exec -it <id> id) and that /cache is writable by that UID/GID
- Consider using a named Docker volume and a one-off chown container to set ownership


## Remediation applied (2025-12-23)

Summary
- DevOps & Developer applied fixes to the minimal Dockerfile and docker-compose ml service to provide a writable Hugging Face / transformers cache at /cache, set environment variables, and run the container as the host UID/GID for local development. The ml service now starts and ingestion completes without PermissionError.

docker-compose (ml service) snippet applied (exact):

services:
  ml:
    build:
      context: .
      dockerfile: carepath_ml/Dockerfile.minimal
    ports:
      - "8000:8000"
    volumes:
      - ./ml_cache:/cache:rw
      - ./carepath_ml/data:/app/data
    environment:
      - TRANSFORMERS_CACHE=/cache
      - HF_HOME=/cache
      - SENTENCE_TRANSFORMERS_HOME=/cache/sentence-transformers
      - CAREPATH_DATA_DIR=/app/data
    user: "${UID:-1000}:${GID:-1000}"
    restart: unless-stopped

Updated carepath_ml/Dockerfile.minimal (exact):

FROM python:3.11-slim
WORKDIR /app
COPY carepath_ml/ /app/
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 8000
CMD ["uvicorn", "simple_main:app", "--host", "0.0.0.0", "--port", "8000"]

Verification commands and expected outputs

1) Build image
- docker compose build ml
- Expected: Image builds successfully; no syntax errors from Dockerfile.minimal; pip installs complete.

2) Create host cache dir and set permissions
- mkdir -p ./ml_cache && chmod 0775 ./ml_cache && ls -ld ./ml_cache
- Expected: directory exists and is writable by owner/group (drwxrwxr-x)

3) Start service
- docker compose up -d --force-recreate ml
- Expected: ml service enters running state. docker compose ps shows ml as "Up".

4) Check logs
- docker compose logs --tail 200 ml
- Expected: No "can't open file" or SyntaxError entries; startup messages from uvicorn or ASGI app present.

5) Run ingest as non-root
- docker compose run --rm ml bash -c "id && ls -la /cache || true && python -m ingest.scripts.run_ingest"
- Expected: id shows non-root UID/GID (matching host mapping), /cache is writable, ingest completes without PermissionError and model artifacts are written to ./ml_cache.

Rollback note
- To roll back quickly, revert the docker-compose ml service changes and the Dockerfile.minimal to their previous versions and recreate the service. Keep in mind rollback will reintroduce the permission and CMD problems.

CI considerations
- In CI, avoid mounting host directories as volumes. Instead:
  - Use a named volume and run a one-off chown container to set ownership in CI, or
  - Build the image to create and chown /cache during image build to the expected runtime UID, or
  - Provide an object-store-backed cache and configure TRANSFORMERS_CACHE/HF_HOME accordingly.

