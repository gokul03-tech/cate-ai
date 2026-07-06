# LexOrch-KG — Explainable Agentic Legal Reasoning
## Judicial Decision Support Platform

> ⚖️ **IMPORTANT DISCLAIMER**: LexOrch-KG is a decision **SUPPORT** tool only. It does NOT replace judges, lawyers, or legal professionals. All AI-generated recommendations require review by qualified human legal experts before any legal action is taken.

---

## 🏛️ Overview

**LexOrch-KG** is a production-quality AI legal decision support platform that:

- Accepts legal documents (PDF, DOCX, TXT — including scanned PDFs via OCR)
- Runs an **8-agent AI pipeline** using LangGraph for multi-step analysis
- Builds a **Knowledge Graph** in Neo4j connecting legal entities and relationships
- Retrieves similar precedents using **RAG** (ChromaDB + BAAI/bge-base-en-v1.5 embeddings)
- Conducts **adversarial multi-agent debate** (Prosecution, Defense, Judge, Consensus)
- Generates **explainable recommendations** with confidence scores and reasoning chains
- Produces professional **PDF, JSON, and HTML reports** using ReportLab
- Provides a full **React 19** frontend with dark mode, Knowledge Graph visualization, and more

---

## 🛠 Tech Stack

| Layer | Technology |
|-------|------------|
| **Backend** | Python 3.11, FastAPI, SQLAlchemy 2.0, Alembic, Uvicorn, Loguru |
| **AI Pipeline** | LangGraph, LangChain, Groq (default), OpenAI, Ollama |
| **Embeddings** | BAAI/bge-base-en-v1.5 (Sentence Transformers) |
| **Databases** | PostgreSQL 16, Neo4j 5 Community, ChromaDB |
| **NLP** | spaCy (en_core_web_sm), Tesseract OCR, PyMuPDF, pdfplumber |
| **Reports** | ReportLab, Jinja2 |
| **Frontend** | React 19, TypeScript, Vite, TailwindCSS, React Router, ReactFlow |
| **Auth** | JWT, bcrypt, Refresh Token Rotation, RBAC |
| **Containers** | Docker, Docker Compose |

---

## 🚀 Quick Start

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running
- A free [Groq API key](https://console.groq.com) (or OpenAI key)
- 8GB RAM minimum (for AI models)

### 1. Clone / navigate to project

```bash
cd cate-ai
```

### 2. Set your API key

Edit `backend/.env` and set your Groq API key:

```env
GROQ_API_KEY=your-groq-api-key-here
```

### 3. Start all services

```bash
docker compose up --build
```

First startup takes **5-10 minutes** — it downloads the embedding model (~500MB) and spaCy models.

### 4. Access the platform

| Service | URL |
|---------|-----|
| **Frontend** | http://localhost:3000 |
| **Backend API** | http://localhost:8000 |
| **API Docs** | http://localhost:8000/docs |
| **Neo4j Browser** | http://localhost:7474 |
| **ChromaDB** | http://localhost:8001 |

### 5. Login

Default admin credentials:
- Email: `admin@lexorch.ai`
- Password: `AdminLex@2024`

---

## 👤 User Roles

| Role | Permissions |
|------|-------------|
| **Admin** | Full access, user management, audit logs |
| **Judge** | View all cases, approve/reject AI recommendations |
| **Lawyer** | Upload cases, submit reviews, download reports |
| **Analyst** | Upload cases, view analysis, download reports |
| **Viewer** | Read-only access to completed cases |

---

## 🤖 AI Agent Pipeline

| Step | Agent | Responsibility |
|------|-------|---------------|
| 1 | **CaseUnderstandingAgent** | Text extraction, OCR, chunking, summarization |
| 2 | **EntityExtractionAgent** | spaCy NER + LLM entity extraction |
| 3 | **KnowledgeGraphAgent** | Neo4j node/relationship insertion |
| 4 | **RetrievalAgent** | ChromaDB embedding storage + semantic search |
| 5 | **ReasoningAgent** | Legal logic, rule application, precedent comparison |
| 6 | **DebateAgent** | Prosecution / Defense / Judge / Consensus debate |
| 7 | **ExplainabilityAgent** | XAI reasoning chain, confidence, disclaimer |
| 8 | **ReportAgent** | PDF + JSON + HTML report generation |

---

## 📊 Knowledge Graph Schema

### Nodes
`Case` · `Judge` · `Court` · `Person` · `Law` · `Act` · `Evidence` · `Witness` · `Precedent` · `Organization` · `Location`

### Relationships
- `(Person)-[:ACCUSED_IN]->(Case)`
- `(Case)-[:HEARD_IN]->(Court)`
- `(Case)-[:USES]->(Law)`
- `(Case)-[:CITES]->(Precedent)`
- `(Judge)-[:DECIDED]->(Case)`
- `(Evidence)-[:SUPPORTS]->(Case)`
- `(Case)-[:SIMILAR_TO]->(Case)`

---

## 🗄️ Database Schema

### PostgreSQL Tables
`users` · `cases` · `case_metadata` · `legal_entities` · `retrieved_precedents` · `agent_executions` · `debate_results` · `explainability` · `human_reviews` · `reports` · `audit_logs`

---

## 🖥️ Frontend Pages

| Page | Path |
|------|------|
| Landing | `/` |
| Login | `/login` |
| Register | `/register` |
| Dashboard | `/dashboard` |
| Upload Case | `/upload` |
| Case History | `/cases` |
| Case Detail | `/cases/:id` |
| Knowledge Graph | `/cases/:id/graph` |
| Agent Timeline | `/cases/:id/timeline` |
| Debate Viewer | `/cases/:id/debate` |
| Explainability | `/cases/:id/explain` |
| Reports | `/cases/:id/reports` |
| Admin Panel | `/admin` |
| Profile | `/profile` |

---

## 🔑 API Endpoints

### Authentication
```
POST /api/v1/auth/register    — Register user
POST /api/v1/auth/login       — Login (returns JWT pair)
POST /api/v1/auth/refresh     — Refresh access token
POST /api/v1/auth/logout      — Logout
GET  /api/v1/auth/me          — Current user profile
```

### Cases
```
POST /api/v1/cases/upload         — Upload document
POST /api/v1/cases/{id}/analyze   — Trigger AI pipeline
GET  /api/v1/cases/               — List cases
GET  /api/v1/cases/{id}           — Case detail
GET  /api/v1/cases/{id}/entities  — Extracted entities
GET  /api/v1/cases/{id}/knowledge-graph  — KG data
GET  /api/v1/cases/{id}/debate    — Debate transcript
GET  /api/v1/cases/{id}/explainability   — XAI report
POST /api/v1/cases/{id}/review    — Submit human review
```

### Reports
```
GET /api/v1/reports/{case_id}            — List reports
GET /api/v1/reports/{report_id}/download — Download report
```

### Admin
```
GET    /api/v1/admin/users           — List users
PATCH  /api/v1/admin/users/{id}      — Update user
DELETE /api/v1/admin/users/{id}      — Deactivate user
GET    /api/v1/admin/audit-logs      — Audit logs
GET    /api/v1/admin/stats           — Dashboard stats
```

---

## ⚙️ Development Setup (Without Docker)

### Backend
```bash
cd backend
python -m venv .venv
.venv/Scripts/activate  # Windows
pip install -r requirements.txt
python -m spacy download en_core_web_sm

# Set environment variables (edit .env)
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Required services (local):
- PostgreSQL running on port 5432
- Neo4j running on port 7687
- ChromaDB running on port 8001

---

## 📁 Project Structure

```
cate-ai/
├── docker-compose.yml
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── .env
│   └── app/
│       ├── main.py           # FastAPI app factory
│       ├── core/             # config, security, database, logging
│       ├── api/v1/           # auth, cases, reports, admin routers
│       ├── agents/           # 8 AI agents + orchestrator
│       ├── infrastructure/   # postgres, neo4j, chromadb clients
│       ├── repositories/     # data access layer
│       ├── services/         # business logic
│       └── schemas/          # Pydantic DTOs
└── frontend/
    ├── Dockerfile
    ├── src/
    │   ├── App.tsx           # Router
    │   ├── lib/              # api client, auth context
    │   ├── components/       # Layout, shared components
    │   └── pages/            # All 13 pages
    └── tailwind.config.js
```

---

## 🔒 Security Features

- JWT access tokens (30 min) + refresh tokens (7 days) with rotation
- bcrypt password hashing
- Role-based access control (RBAC) on every endpoint
- Audit log for all significant actions
- CORS protection
- File type and size validation
- Mandatory AI disclaimer on every recommendation

---

## ⚠️ Legal Disclaimer

**LexOrch-KG is a decision SUPPORT tool only.**

All AI-generated analysis, recommendations, and reports:
- Are for informational purposes only
- Do NOT constitute legal advice
- Do NOT replace the judgment of qualified legal professionals
- Must be reviewed by judges, lawyers, or legal experts before any legal action
- May contain errors, biases, or incomplete analysis

The developers of LexOrch-KG accept no liability for decisions made based solely on AI output.

---

## 📄 License

MIT License — See LICENSE file for details.

Built with ❤️ using FastAPI · React · LangGraph · Neo4j · ChromaDB
