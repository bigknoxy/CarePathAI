# Memory: Strategic Architecture Decisions

**Context**: 4-week CarePath AI implementation for Staff-level ML/AI Engineer portfolio  
**Date**: 2025-12-22  
**Decision Point**: Final architecture choices for implementation  

## 🎯 Core Decisions Made

### 1. Blazor Server Architecture
**Decision**: Blazor Server over Blazor WASM  
**Rationale**: Server-side PHI security, simpler deployment, SignalR expertise demonstration  
**Impact**: Reduces client-side attack surface, shows security-first healthcare mindset  

### 2. OpenAI as LLM Provider  
**Decision**: OpenAI with cost controls over Gemini/Anthropic  
**Rationale**: Industry recognition, superior documentation, better ecosystem support  
**Impact**: Demonstrates production AI cost management and token optimization  

### 3. PostgreSQL Database  
**Decision**: PostgreSQL with pgvector over SQL Server  
**Rationale**: VPS compatibility, built-in vector capabilities, no licensing costs  
**Impact**: Shows understanding of modern database extensions and cost optimization  

### 4. Custom Monitoring Approach  
**Decision**: Metrics endpoints + structured logs over full Prometheus/Grafana stack  
**Rationale**: Practical engineering judgment, VPS resource constraints, targeted AI metrics  
**Impact**: Demonstrates when NOT to use complex tools - senior engineering signal  

### 5. Hybrid Task Organization  
**Decision**: Agent delegation + daily milestone tracking  
**Rationale**: Demonstrates technical leadership while maintaining accountability  
**Impact**: Shows team coordination and project management capabilities  

## 📊 Portfolio Optimization Strategy

**Primary Signal**: Technical judgment and healthcare domain expertise  
**Secondary Signal**: Production-ready patterns without over-engineering  

**Interview Focus Areas**:
- Architecture decision documentation (ADRs)
- Healthcare security and compliance patterns
- AI cost management and optimization
- Practical trade-off discussions  

## 🚀 Risk Mitigation

**Timeline**: Daily check-ins against weekly milestones  
**Technical**: Early service contracts and integration testing  
**Scope**: Strict feature prioritization based on Staff-level competency matrix  

## 💡 Key Insight

The goal is **Staff-level signal**, not production infrastructure complexity. Maven values understanding of **when to use what** more than deploying every tool. Each decision should have a clear "why" that demonstrates senior technical judgment.

---
*This memory file should be referenced for all subsequent implementation decisions to maintain strategic alignment.*