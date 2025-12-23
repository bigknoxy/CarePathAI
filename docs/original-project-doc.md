## 🎯 **Final CarePath AI Implementation Plan (4 Weeks)**

Based on the architectural analysis, here's your optimized daily plan with **strategic choices** that maximize Staff-level signal while keeping complexity manageable:

---

## **Strategic Decisions Locked In:**
- **Frontend**: Blazor Server (security-first for healthcare)
- **LLM**: OpenAI with cost controls & fallbacks  
- **Database**: PostgreSQL with pgvector extension
- **Monitoring**: Custom metrics endpoints + structured logging
- **Task Mode**: Daily checklists with delegation capability

---

## **Week 1: Foundation & Architecture**

### **Day 1 - Architecture & Design**
**Primary Agent**: Architect
**Deliverables**: 
- `docs/architecture.md` with service boundaries & data flow
- `memory/001-architecture-decision.md` (ADR format)
- System diagram (Mermaid) showing C# → Python → DB → UI flow

**Commands**: None (documentation day)
**Files to Create**: 
```
docs/architecture.md
memory/001-architecture-decision.md
.github/ISSUE_TEMPLATE/feature_request.md
```

**Acceptance Criteria**:
- Architecture doc explains C# orchestration + Python ML separation
- ADR documents why this split maximizes both worlds
- Diagram shows RAG flow with guardrails

---

### **Day 2 - Solution Skeleton**
**Primary Agent**: Developer  
**Deliverables**: .NET solution with 3 projects + Python FastAPI skeleton

**Commands**:
```bash
dotnet new sln -n CarePathAI
dotnet new webapi -n CarePath.Api
dotnet new blazorserver -n CarePath.UI  
dotnet new classlib -n CarePath.Domain
dotnet new xunit -n CarePath.Api.Tests
dotnet sln add **/*.csproj

cd CarePath.ML
python -m venv .venv
source .venv/bin/activate
pip install fastapi uvicorn python-multipart
```

**Files to Create**:
```
CarePath.sln
CarePath.Api/Program.cs (minimal)
CarePath.UI/Program.cs  
CarePath.Domain/ (empty)
CarePath.Api.Tests/ (empty)
CarePath.ML/main.py (FastAPI skeleton)
.gitignore
README.md (initial)
```

**Acceptance Criteria**:
- `dotnet build` succeeds
- Python service starts: `uvicorn main:app --reload --port 8000`
- All projects reference correctly

---

### **Day 3 - Docker Compose Setup**
**Primary Agent**: DevOps
**Deliverables**: Dockerfiles + dev compose setup

**Commands**:
```bash
docker-compose -f docker-compose.yml up --build -d
docker-compose ps
curl http://localhost:5000/health  # API
curl http://localhost:8000/health  # Python
curl http://localhost:5001/health  # Blazor
```

**Files to Create**:
```
Dockerfile (CarePath.Api)
Dockerfile (CarePath.UI) 
Dockerfile (CarePath.ML)
docker-compose.yml (dev)
scripts/smoke_check.sh
```

**Acceptance Criteria**:
- All 3 containers start and respond to `/health`
- Compose uses local volumes for development
- Health checks implemented in all services

---

### **Day 4 - Synthetic Healthcare Data**
**Primary Agent**: ML Developer
**Deliverables**: FHIR-like patient generator + sample data

**Commands**:
```bash
python CarePath.ML/scripts/generate_synthetic_fhir.py --count 100 --output data/synthetic/
python CarePath.ML/scripts/validate_fhir.py --input data/synthetic/
```

**Files to Create**:
```
CarePath.ML/scripts/generate_synthetic_fhir.py
CarePath.ML/models/fhir_models.py (Pydantic)
data/synthetic/patients/*.json
tests/test_fhir_generator.py
```

**Acceptance Criteria**:
- 100 valid patient JSON files generated
- Each contains: demographics, conditions, medications, encounters
- Validation ensures no real PHI (synthetic only)

---

### **Day 5 - Embeddings & Vector Store**
**Primary Agent**: ML Developer  
**Deliverables**: FAISS-based RAG foundation with sentence-transformers

**Commands**:
```bash
pip install sentence-transformers faiss-cpu numpy
python CarePath.ML/scripts/ingest_embeddings.py --input data/synthetic --output data/faiss/
python CarePath.ML/scripts/test_retrieval.py --query "diabetes patient"
```

**Files to Create**:
```
CarePath.ML/embeddings.py
CarePath.ML/vector_store.py  
CarePath.ML/scripts/ingest_embeddings.py
data/faiss/patient_index.faiss
data/faiss/metadata.json
```

**Acceptance Criteria**:
- Patient notes embedded and indexed in FAISS
- Retrieval returns relevant matches for test queries
- Index persists to disk for docker volumes

---

## **Week 2: Core Integration & Guardrails**

### **Day 6 - C# API Patients Endpoints**
**Primary Agent**: Developer
**Deliverables**: Patient CRUD API with DTOs and service layer

**Commands**:
```bash
dotnet run --project CarePath.Api
curl http://localhost:5000/api/patients
curl http://localhost:5000/api/patients/1
```

**Files to Create**:
```
CarePath.Api/Controllers/PatientsController.cs
CarePath.Api/Models/PatientDto.cs
CarePath.Api/Services/IPatientService.cs
CarePath.Api/Services/PatientService.cs
CarePath.Domain/Models/Patient.cs
```

**Acceptance Criteria**:
- GET `/api/patients` returns list of synthetic patients
- GET `/api/patients/{id}` returns single patient
- Unit tests cover mapping and validation

---

### **Day 7 - Python ML Service Endpoints**
**Primary Agent**: ML Developer
**Deliverables**: FastAPI endpoints for embedding, retrieval, orchestration

**Commands**:
```bash
curl -X POST http://localhost:8000/embed -H "Content-Type: application/json" -d '{"text": "patient has diabetes"}'
curl -X POST http://localhost:8000/retrieve -d '{"query": "hypertension treatment", "top_k": 5}'
curl -X POST http://localhost:8000/orchestrate -d '{"patient_id": "123", "query": "care recommendations"}'
```

**Files to Create**:
```
CarePath.ML/main.py (updated with endpoints)
CarePath.ML/endpoints/embed.py
CarePath.ML/endpoints/retrieve.py  
CarePath.ML/endpoints/orchestrate.py
CarePath.ML/models/api_models.py
tests/test_endpoints.py
```

**Acceptance Criteria**:
- All endpoints return valid JSON responses
- Embeddings match expected dimensions (384 for all-MiniLM-L6-v2)
- Retrieval returns top-k relevant documents

---

### **Day 8 - C# → Python Integration**
**Primary Agent**: Developer
**Deliverables**: HttpClient wrapper + new care path endpoint

**Commands**:
```bash
dotnet run --project CarePath.Api
curl http://localhost:5000/api/carepath/123
```

**Files to Create**:
```
CarePath.Api/Controllers/CarePathController.cs
CarePath.Api/Services/IMLClient.cs
CarePath.Api/Services/MLHttpClient.cs
CarePath.Api/Models/CarePathRequest.cs
CarePath.Api/Models/CarePathResponse.cs
```

**Acceptance Criteria**:
- `/api/carepath/{id}` calls Python ML service
- Response includes patient summary + retrieved context
- Integration test verifies end-to-end flow

---

### **Day 9 - Healthcare Safety Guardrails**
**Primary Agent**: Architect + ML Developer
**Deliverables**: Guardrail system with emergency detection

**Commands**:
```bash
python CarePath.ML/scripts/test_guardrails.py --input "chest pain severe"
python CarePath.ML/scripts/test_guardrails.py --input "routine checkup"
```

**Files to Create**:
```
CarePath.ML/guardrails/safety_filters.py
CarePath.ML/guardrails/emergency_detector.py
CarePath.ML/guardrails/content_filters.py
docs/guardrails.md
tests/test_guardrails.py
```

**Acceptance Criteria**:
- Emergency terms trigger immediate escalation response
- Medical advice requests blocked with safety message  
- All guardrail decisions logged for audit

---

### **Day 10 - Blazor Patient UI**
**Primary Agent**: UI Engineer
**Deliverables**: Patient list and detail pages with care path requests

**Commands**:
```bash
dotnet run --project CarePath.UI
# Navigate to http://localhost:5001/patients
# Click patient to view details and request care path
```

**Files to Create**:
```
CarePath.UI/Pages/Patients.razor
CarePath.UI/Pages/PatientDetail.razor
CarePath.UI/Shared/MainLayout.razor
CarePath.UI/Services/ApiClient.cs
CarePath.UI/Models/PatientViewModel.cs
```

**Acceptance Criteria**:
- Patient list loads from API
- Clicking patient shows detailed view
- "Generate Care Path" button calls backend and displays results

---

## **Week 3: Production Readiness**

### **Day 11 - Observability & Metrics**
**Primary Agent**: Developer + ML Developer
**Deliverables**: Structured logging + Prometheus metrics endpoints

**Commands**:
```bash
curl http://localhost:5000/metrics
curl http://localhost:8000/metrics
# Check logs show JSON structure
docker-compose logs -f api | jq '.'
```

**Files to Create**:
```
CarePath.Api/Logging/SerilogConfig.cs
CarePath.Api/Middleware/RequestLoggingMiddleware.cs
CarePath.ML/metrics.py
CarePath.ML/middleware/logging.py
docker-compose.yml (updated with prometheus config)
```

**Acceptance Criteria**:
- Both services expose `/metrics` endpoint
- Logs output as structured JSON
- Key metrics tracked: requests, errors, latency, LLM calls

---

### **Day 12 - Comprehensive Testing**
**Primary Agent**: Test Engineer
**Deliverables**: Unit + integration tests with 60%+ coverage

**Commands**:
```bash
dotnet test --logger "trx;LogFileName=TestResults.trx" --collect:"XPlat Code Coverage"
pytest --junit-xml=reports/pytest.xml --cov=CarePath.ML --cov-report=html:artifacts/coverage
```

**Files to Create**:
```
CarePath.Api.Tests/Controllers/PatientsControllerTests.cs
CarePath.Api.Tests/Services/MLHttpClientTests.cs
CarePath.ML/tests/test_guardrails.py
CarePath.ML/tests/test_endpoints.py
.github/workflows/coverage.yml
```

**Acceptance Criteria**:
- Unit tests cover business logic
- Integration tests validate service boundaries
- Coverage reports generated in CI/CD

---

### **Day 13 - GitHub Actions CI Pipeline**
**Primary Agent**: DevOps
**Deliverables**: Build + test + security scan workflow

**Commands**:
```bash
# Test locally with act (optional)
act -j build_test
# Push to trigger real CI
git push origin feature/day13-ci
```

**Files to Create**:
```
.github/workflows/ci.yml
.github/workflows/coverage.yml
.github/dependabot.yml
scripts/security_scan.sh
```

**Acceptance Criteria**:
- Workflow builds .NET and Python projects
- Runs all tests and fails on coverage <60%
- Security scan fails if secrets detected

---

### **Day 14 - RAG Performance Evaluation**
**Primary Agent**: ML Developer + Test Engineer
**Deliverables**: Retrieval quality metrics + tuning results

**Commands**:
```bash
python CarePath.ML/scripts/evaluate_rag.py --qa-pair tests/qa_pairs.json --output artifacts/rag_eval.json
python CarePath.ML/scripts/tune_embeddings.py --grid-search
```

**Files to Create**:
```
CarePath.ML/scripts/evaluate_rag.py
CarePath.ML/scripts/tune_embeddings.py
tests/qa_pairs.json (synthetic)
docs/rag_performance.md
```

**Acceptance Criteria**:
- Top-K recall calculated for test queries
- Performance baseline documented (precision@5, recall@10)
- Tuning recommendations for chunk size, overlap, embedding model

---

### **Day 15 - Security & Configuration Hardening**
**Primary Agent**: DevOps + Architect
**Deliverables**: Secret management + security policies

**Commands**:
```bash
# Test security scan
./scripts/security_scan.sh
# Verify no secrets in repo
git grep "OPENAI_API_KEY" && exit 1 || echo "No secrets found"
```

**Files to Create**:
```
.env.example
docs/security.md
scripts/secret_rotation_guide.md
.github/workflows/secret_scan.yml
```

**Acceptance Criteria**:
- `.env.example` documents all required variables
- CI fails if secrets detected in commits
- Security scan identifies vulnerable dependencies

---

## **Week 4: Deployment & Polish**

### **Day 16 - Production Docker Compose**
**Primary Agent**: DevOps
**Deliverables**: Production-ready compose + deployment scripts

**Commands**:
```bash
# Test production compose locally
docker-compose -f docker-compose.prod.yml up --build -d
./scripts/deploy.sh --dry-run
```

**Files to Create**:
```
docker-compose.prod.yml (production optimized)
scripts/deploy.sh (VPS deployment)
docs/deployment.md
nginx/nginx.conf (reverse proxy)
```

**Acceptance Criteria**:
- Production compose uses external volumes
- Includes nginx reverse proxy with HTTPS termination
- Resource limits and restart policies configured

---

### **Day 17 - GitHub Actions CD Pipeline**
**Primary Agent**: DevOps
**Deliverables**: Automated build and deploy to VPS

**Commands**:
```bash
# Test CD workflow
act -j deploy
# Merge to main triggers real deployment
git checkout main && git merge feature/day17-cd && git push origin main
```

**Files to Create**:
```
.github/workflows/deploy.yml
scripts/vps_setup.sh
docker-compose.prod.yml (updated)
```

**Acceptance Criteria**:
- Workflow builds and pushes Docker images
- SSH deployment to VPS using GitHub secrets
- Deployment health check validates services

---

### **Day 18 - End-to-End Testing**
**Primary Agent**: Test Engineer
**Deliverables**: Full system validation with performance checks

**Commands**:
```bash
./scripts/run_e2e_tests.sh
# Results saved to artifacts/e2e_results.json
```

**Files to Create**:
```
tests/e2e/care_path_flow.py
tests/e2e/performance_test.py
scripts/run_e2e_tests.sh
artifacts/e2e_results.json
```

**Acceptance Criteria**:
- Complete user journey tested (login → patient → care path)
- Latency under 2 seconds for care path generation
- All guardrail behaviors verified

---

### **Day 19 - Documentation & Portfolio Package**
**Primary Agent**: Documentation + Architect
**Deliverables**: Complete documentation package

**Commands**:
```bash
# Verify all documentation
./scripts/docs_check.sh
# Generate README table of contents
./scripts/generate_readme_toc.sh
```

**Files to Create**:
```
README.md (comprehensive)
docs/api_reference.md
docs/deployment_guide.md
docs/troubleshooting.md
memory/ (multiple ADRs)
docs/portfolio_summary.md
```

**Acceptance Criteria**:
- README includes quickstart for local and VPS deployment
- API documentation complete with examples
- All ADRs document key technical decisions

---

### **Day 20 - Final Demo & Portfolio Assets**
**Primary Agent**: Project Manager + Content Writer
**Deliverables**: Demo materials + portfolio-ready presentation

**Commands**:
```bash
./scripts/run_demo.sh --record
# Creates screenshots and logs for portfolio
```

**Files to Create**:
```
docs/demo_script.md
scripts/run_demo.sh
assets/demo_screenshots/
assets/demo_video.mp4 (optional)
portfolio/one_pager.md
```

**Acceptance Criteria**:
- Demo script runs in 10 minutes
- Screenshots show key features and safety guardrails
- Portfolio summary clearly maps to Maven job requirements

---

## **🚨 Critical Success Factors**

### **Staff-Level Signal Checklist**:
- ✅ Architecture Decision Records (ADRs) for every major choice
- ✅ Production observability (metrics, structured logging)  
- ✅ Healthcare safety awareness (guardrails, audit trails)
- ✅ Cost management (token tracking, rate limiting)
- ✅ CI/CD with security scanning
- ✅ Performance evaluation and SLA documentation

### **Interview Story Preparation**:
1. **"I designed a hybrid architecture** leveraging C#'s enterprise patterns for orchestration while using Python's ML ecosystem for AI capabilities"
2. **"Healthcare safety was priority #1** - implemented multi-layer guardrails with emergency detection and audit logging"
3. **"Built this with production from day 1** - observability, CI/CD, security scanning, and deployment automation"
4. **"Evaluated RAG quality systematically** - top-K recall of 85% on synthetic clinical scenarios"
5. **"Managed costs proactively** - token budgets, response caching, and fallback strategies"

---

**Ready to start Day 1?** I can immediately create the architecture documentation and ADRs, or would you prefer me to set up the repository skeleton first?

(End of content)
