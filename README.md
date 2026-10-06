# Enterprise AI Customer Support Agent

An end-to-end AI customer support agent with a Retrieval-Augmented
Generation (RAG) pipeline over enterprise documents. Two CrewAI agents —
a **Knowledge Retriever** and a **Support Specialist** — work in sequence
on every question: one searches a FAISS vector index built from your
documents, the other writes a grounded answer and flags low-confidence
responses for human escalation.

## Architecture

```
┌─────────────┐      REST      ┌──────────────────────────────────────┐
│   React     │ ─────────────▶ │              FastAPI                  │
│  (Vite SPA) │ ◀───────────── │                                        │
└─────────────┘                │  /api/chat        /api/documents       │
                                │       │                  │            │
                                │       ▼                  ▼            │
                                │  ┌───────────┐    ┌──────────────┐    │
                                │  │ CrewAI     │    │ Document     │    │
                                │  │ Crew       │    │ ingestion    │    │
                                │  │ (Retriever │    │ (chunk +     │    │
                                │  │ + Support  │    │  embed)      │    │
                                │  │  agents)   │    └──────┬───────┘    │
                                │  └─────┬──────┘           │            │
                                │        │      shared FAISS index       │
                                │        └────────────┬─────────────────▶│
                                │                      ▼                 │
                                │            HuggingFace embeddings      │
                                │            + Google Gemini (LLM)       │
                                └──────────────────────────────────────┘
```

- **FastAPI** exposes `/api/chat` (ask a question), `/api/documents`
  (upload and index a document), and `/api/health`.
- **CrewAI + LangChain** orchestrate two agents: the retriever queries
  FAISS through a custom tool, the specialist writes the final answer
  strictly from what was retrieved.
- **Google Gemini** (via `langchain-google-genai`) is the LLM behind
  both agents.
- **FAISS** stores document embeddings (Hugging Face
  `sentence-transformers/all-MiniLM-L6-v2`) locally and persists to disk.
- **Escalation** is decided two ways at once: the specialist agent can
  say `ESCALATE: yes` in its own output, and the API independently
  checks retrieval confidence against a threshold — so a confidently
  wrong answer over a weak match still gets flagged.
- **React (Vite)** is a small console UI: upload documents, watch the
  knowledge base status, and chat with the agent with sources shown
  under each answer.

## Project layout

```
customer-support-agent/
├── backend/
│   ├── app/
│   │   ├── main.py                 FastAPI app + startup
│   │   ├── config.py                Settings (env-driven)
│   │   ├── api/routes.py            /chat, /documents, /health
│   │   ├── models/schemas.py        Request/response models
│   │   ├── services/
│   │   │   ├── vector_store.py      FAISS index build/load/persist
│   │   │   ├── retrieval_tool.py    CrewAI tool wrapping FAISS
│   │   │   └── agent_service.py     CrewAI agents, tasks, crew
│   │   └── data/documents/          Seed knowledge base (sample FAQ)
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── App.jsx, App.css
│   │   ├── api.js                   Backend client
│   │   └── components/
│   │       ├── StatusPanel.jsx      KB status + document upload
│   │       ├── MessageBubble.jsx    Chat bubble + sources + flags
│   │       └── Composer.jsx         Message input
│   ├── Dockerfile, nginx.conf
│   └── .env.example
└── docker-compose.yml
```

## Running it locally

### 1. Get a Gemini API key
Create one at https://aistudio.google.com/app/apikey — the free tier
is enough to try this out.

### 2. Backend

```bash
cd backend
cp .env.example .env        # then paste your GOOGLE_API_KEY into .env
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The app ships with a seed document (`app/data/documents/product_faq.md`)
covering billing, password resets, API limits, data export, uptime, and
cancellation — enough to try the agent immediately. It's indexed
automatically on first startup and cached to `app/data/faiss_index/`.

API docs: http://localhost:8000/docs

### 3. Frontend

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

Open http://localhost:5173.

### 4. Or run both with Docker Compose

```bash
cp backend/.env.example backend/.env   # add your GOOGLE_API_KEY
docker compose up --build
```

Backend on `:8000`, frontend on `:5173`.

## Trying it out

Ask things like:
- "How long is a data export link valid for?"
- "What happens if I cancel mid-billing-cycle?"
- "What's the API rate limit on the enterprise plan?"

Then upload your own `.txt`, `.md`, or `.pdf` from the sidebar and ask
about its contents — no restart needed, documents are indexed
immediately.

## Notes on production-readiness

This is a solid foundation, not a finished production system. Before
shipping it to real customers, you'd want to add:
- Authentication on the API and per-tenant document isolation
- A persistent vector DB (e.g. pgvector, Pinecone) instead of local FAISS
  if you need horizontal scaling
- Conversation memory across turns (currently each `/chat` call is
  stateless aside from the session id)
- Rate limiting and structured logging/tracing on the agent calls
- An actual human-escalation integration (ticket creation, Slack alert)
  instead of just a flag in the response
