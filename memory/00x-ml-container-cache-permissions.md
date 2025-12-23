00001| One-Line Summary: ML container failures caused by a broken minimal Dockerfile CMD and writable cache permission errors (TRANSFORMERS_CACHE/HF_HOME).
00002| 
00003| Tags: ml, docker, permissions, cache
00004| 
00005| Context ➡️
00006| - Exact errors observed (from docker-compose logs and runtime):
00007|   - "python: can't open file '/app/basic_main.py'" (seen in compose logs when the container starts)
00008|   - "SyntaxError" originating from the inline CMD in carepath_ml/Dockerfile.minimal (Docker attempted to run invalid Python code as CMD)
00009|   - "PermissionError: [Errno 13] Permission denied: '/.cache'" (when running the ingest process as a non-root user inside the container)
00010| 
00011| - Files that triggered these errors:
00012|   - carepath_ml/Dockerfile.minimal (contains an inline CMD that is syntactically wrong / points to a non-existent basic_main.py)
00013|   - docker-compose.yml (service config that does not set TRANSFORMERS_CACHE/HF_HOME nor mounts a writable cache volume; likely runs processes as non-root user without a writable cache location)
00014| 
00015| - Reproduction commands:
00016|   1. Rebuild and run compose to reproduce startup errors:
00017|      - docker compose up --build --force-recreate
00018|   2. Inspect ML service logs:
00019|      - docker compose logs --tail 500 ml
00020|   3. Check running/stopped containers to find ml container id:
00021|      - docker ps -a --filter "name=ml"
00022|   4. View container logs directly:
00023|      - docker logs <ml-container-id>
00024|   5. Run the ingest process (shows cache permission error when executed as non-root inside container):
00025|      - docker compose run --rm ml bash -c "python -m ingest.scripts.run_ingest"
00026|   6. For quick local test of user permissions:
00027|      - docker run --rm -it --entrypoint bash <image> -c "id && python -c 'from pathlib import Path; p=Path("/.cache"); p.mkdir(exist_ok=True); p.write_text('x')'"
00028| 
00029| Decision ➡️
00030| - Replace the broken inline CMD in carepath_ml/Dockerfile.minimal and ensure the image starts a valid FastAPI/ASGI app entrypoint or a valid Python module path.
00031| - Configure docker-compose.yml to provide a writable cache location for Hugging Face / transformers by:
00032|   - Setting TRANSFORMERS_CACHE and HF_HOME environment variables to a mounted path (e.g., /cache).
00033|   - Mounting a host directory (./ml_cache) to /cache with writable permissions or using a named volume with correct permissions.
00034| - Ensure non-root runtime user can write to the cache directory by either:
00035|   - Mounting the host cache directory with the correct UID/GID ownership or mode.
00036|   - Using Docker's user mapping (user: "${UID}:${GID}") in compose for local dev.
00037|   - As a fallback, adjust container startup to chown the cache dir at runtime (entrypoint init) before dropping privileges.
00038| - Verify fixes by running the ingest script inside the container as the intended non-root user and confirming atomic writes/successful downloads.
00039| 
00040| Mitigation checklist (step-by-step commands developers can run):
00041| 
00042| 1) Fix the Dockerfile minimal CMD
00043|    - Open carepath_ml/Dockerfile.minimal and replace the invalid inline CMD with a proper ASGI/FastAPI entrypoint or correct Python module. Example replacement (copy-paste and adjust to your project):
00044|      - CMD ["uvicorn", "carepath_ml.main:app", "--host", "0.0.0.0", "--port", "8080"]
00045|    - Or ensure the file referenced by CMD exists in /app (e.g., /app/basic_main.py) and is syntactically valid.
00046|    - Rebuild image: docker compose build ml
00047| 
00048| 2) Add cache environment and mount in docker-compose.yml
00049|    - Edit docker-compose.yml -> service: ml and add:
00050|      environment:
00051|        - TRANSFORMERS_CACHE=/cache
00052|        - - HF_HOME=/cache
00053|      volumes:
00054|        - ./ml_cache:/cache:rw
00055|    - Create host cache dir and set writable perms for local dev:
00056|      - mkdir -p ./ml_cache && chmod 0777 ./ml_cache
00057|    - Recreate service: docker compose up -d --force-recreate ml
00058| 
00059| 3) Ensure correct ownership when running as non-root
00060|    - Option A (preferred for local dev): run container as your host user in compose (set environment or compose field):
00061|        user: "${UID:-1000}:${GID:-1000}"
00062|      then export UID/GID in your shell and docker compose up --build
00063|    - Option B: add an init step in the Dockerfile or entrypoint script to chown /cache to the runtime user before dropping privileges:
00064|        RUN mkdir -p /cache && chown -R appuser:appuser /cache
00065|    - Option C: use docker volume and run a one-off container to set correct ownership:
00066|        docker run --rm -v $(pwd)/ml_cache:/cache ubuntu chown -R 1000:1000 /cache
00067| 
00068| 4) Test with docker run --user and ingest script
00069|    - Test user permissions quickly:
00070|      docker run --rm --user 1000:1000 -v $(pwd)/ml_cache:/cache:rw <image> bash -c "python -c 'from pathlib import Path; p=Path("/cache/testfile"); p.write_text("ok"); print(p.read_text())'"
00071|    - Run the ingest task inside compose to confirm no PermissionError:
00072|      docker compose run --rm ml bash -c "python -m ingest.scripts.run_ingest"
00073|    - Confirm logs show successful download/caching and no PermissionError
00074| 
00075| 5) Verify atomic writes and final behavior
00076|    - Check that the cache dir contains model files and temporary files are handled atomically by the underlying library (transformers/huggingface sets .lock files). Run the ingest twice to confirm idempotency.
00077| 
00078| Outcome ➡️
00079| - Replacing the broken CMD prevents startup Python errors (no more "can't open /app/basic_main.py" and no SyntaxError from Dockerfile.minimal).
00080| - Setting TRANSFORMERS_CACHE/HF_HOME and mounting a writable cache dir resolves PermissionError to '/.cache' when running ingest as non-root.
00081| - Using correct user mapping or chown on mounted volumes ensures non-root processes can write the cache and the ML ingestion completes successfully. Developers should see successful model downloads and no cache-related PermissionError in logs.
00082| 
00083| Notes:
00084| - Prefer mounting a host cache directory in development to persist downloaded models across container rebuilds; in CI or production consider a shared persistent volume or an object-store-backed cache.
00085| - Avoid setting global 0777 in production; instead set ownership to the container runtime UID/GID.
00086| 
00087| Next steps / Recommended owners:
00088| - DevOps: fix docker-compose.yml, add mount and env vars, and validate CI images
00089| - Developer: fix carepath_ml/Dockerfile.minimal and ensure correct app entrypoint
00090| - Documentation: record this memory and update troubleshooting docs (this file)
00091| 
00092| Verification ➡️
00093| - Timestamp: 2025-12-23T19:18:17Z
00094| - Who applied fixes: DevOps & Developer
00095| - Files referenced while applying fixes:
00096|   - docker-compose.yml (project root)
00097|   - carepath_ml/Dockerfile.minimal
00098| - Commands run (summary) and outputs (short):
00099|   1) docker compose build ml
00100|      - Output summary: image built successfully; previously-failing inline CMD removed; build completed without syntax or file-not-found errors.
00101|   2) mkdir -p ./ml_cache && chmod 0775 ./ml_cache && ls -ld ./ml_cache
00102|      - Output summary: host cache directory exists with writable perms for owner/group (drwxrwxr-x).
00103|   3) docker compose up -d --force-recreate ml
00104|      - Output summary: ml service entered running state; health/startup logs show uvicorn (or ASGI) starting and binding to 0.0.0.0:8080.
00105|   4) docker compose logs --tail 200 ml
00106|      - Output summary: no SyntaxError, no "can't open file '/app/basic_main.py'" entries; log contains successful startup messages.
00107|   5) docker compose run --rm ml bash -c "id && ls -la /cache || true && python -m ingest.scripts.run_ingest"
00108|      - Output summary: process ran as non-root (UID:GID consistent with compose user mapping), /cache is writable, ingest completed without PermissionError and model files written into mounted ml_cache directory.
00109|   6) ls -la ./ml_cache | head -n 20
00110|      - Output summary: model files and directories present (expected transformer model artifacts), timestamps updated from ingest operation.
00111| - Final status: RESOLVED
00112| 
00113| 
00114| (End of file - memory updated with verification)
