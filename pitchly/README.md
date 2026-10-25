# ⚡ Pitchly — AI Project Planning Copilot

> **Transform rough, unstructured thoughts into an actionable engineering roadmap and Kanban board.**

Pitchly is a full-stack, hackathon-ready AI planning copilot. Paste high-level bullet points, customer feedback, or raw startup pitches, and Pitchly decomposes them into modular tasks, flags architectural risks, and provisions an interactive Kanban board with live WebSocket updates and a generated `README.md`.

---

## 🏗️ Architecture Diagram

```mermaid
flowchart TD
    subgraph Client["Frontend Client (React + Vite)"]
        UI["Modern UI (Clean CSS Modules)"]
        Kanban["Drag & Drop Board (@dnd-kit)"]
        Suggestions["Suggestion Review Panel"]
        Chat["Copilot Chat Drawer"]
        WSClient["WebSocket Client Manager"]
    end

    subgraph Gateway["Reverse Proxy / Web Server"]
        Nginx["Nginx / Vite Proxy"]
    end

    subgraph Backend["Backend Application (Daphne ASGI + Django)"]
        ASGI["Daphne ASGI Server (:8000)"]
        DRF["Django REST Framework API"]
        Channels["Django Channels (WebSocket Consumer)"]
        Router["Model Router (plans/ai.py)"]
        Fallback["Rule-based Breakdown Engine"]
    end

    subgraph Storage["Persistence & State"]
        Postgres[("PostgreSQL 16 / SQLite")]
        MemChannel["Channel Layer (InMemory / Redis)"]
    end

    subgraph NebiusCloud["Nebius Token Factory / NVIDIA Open Models"]
        FastLLM["FAST_MODEL\n(e.g., Llama-3.1-8B-Instruct)\nRapid breakdown & JSON tasks"]
        ReasoningLLM["REASONING_MODEL\n(e.g., DeepSeek-R1-Distill-Llama-70B)\n'why', 'risk', 'tradeoff', 'explain'"]
    end

    UI --> Kanban & Suggestions & Chat
    Kanban & Suggestions & Chat -->|HTTP REST| Nginx
    WSClient <-->|WebSocket ws://| Nginx
    Nginx -->|/api/| DRF
    Nginx -->|/ws/| Channels
    Channels <--> MemChannel
    DRF --> Postgres
    DRF --> Router
    Router -->|Keywords: why, risk, tradeoff, explain| ReasoningLLM
    Router -->|Decomposition & General Chat| FastLLM
    Router -.->|Fallback if no API key| Fallback
    DRF -->|Broadcast Board Events| Channels
```

---

## 🧠 AI Model Strategy: Fast vs. Reasoning Split

Pitchly uses an intelligent dynamic routing strategy across NVIDIA and open-weights models served through **Nebius Token Factory**:

### 1. `FAST_MODEL` (`meta-llama/Meta-Llama-3.1-8B-Instruct`)
- **Purpose**: Rapid project decomposition, title extraction, structured JSON task generation, and general conversational replies.
- **Why**: Low latency (<1s response times), minimal token cost, and strict compliance with JSON schema generation. Perfect for instant interactivity when breaking down a new idea.

### 2. `REASONING_MODEL` (`deepseek-ai/DeepSeek-R1-Distill-Llama-70B` or `meta-llama/Meta-Llama-3.1-70B-Instruct`)
- **Purpose**: Deep architectural analysis, tradeoff evaluations, and risk mitigation.
- **Trigger**: Automatically engaged whenever a query contains analytical keywords:
  `["why", "risk", "compare", "tradeoff", "explain"]`.
- **Why**: Complex architectural choices (e.g. state management, caching strategies, asynchronous pipelines) benefit from step-by-step chain-of-thought reasoning that smaller models struggle to articulate.

> [!NOTE]
> *Model IDs*: Confirm exact model IDs in the [Nebius Token Factory catalog](https://studio.nebius.ai/). Pitchly defaults to standard OpenAI-compatible endpoints.

### Fallback Guarantee (Zero Credentials Demo Mode)
If `NEBIUS_API_KEY` is not provided or network access is unavailable, Pitchly automatically engages its **deterministic rule-based breakdown generator**. The generator analyzes sentence structure, bullet points, and keywords to build an initial board, ensuring demos never fail during a live presentation.

---

## 🔒 Crucial Architectural Rule: Human-in-the-Loop Suggestions

Pitchly strictly adheres to human-in-the-loop validation:
1. When a project idea is submitted (`POST /api/projects/`), proposed tasks and risks are saved exclusively as **Suggestions** (`kind='task'|'risk'|'note'`, `status='pending'`).
2. **The system NEVER writes directly to the `Tasks` table without explicit user approval.**
3. Review candidates in the **AI Suggestions** drawer:
   - Click **"✓ Accept to Board"** (`POST /api/suggestions/{id}/accept/`) to convert the candidate into a live Kanban `Task`.
   - Click **"✕ Dismiss"** (`POST /api/suggestions/{id}/reject/`) to discard.
4. Accepted tasks appear instantaneously across all connected clients via WebSockets.

---

## ⚙️ Environment Variables

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

| Variable | Description | Default |
| :--- | :--- | :--- |
| `NEBIUS_BASE_URL` | Nebius Token Factory base URL | `https://api.studio.nebius.ai/v1` |
| `NEBIUS_API_KEY` | Nebius API key (leave blank for demo fallback) | `""` |
| `FAST_MODEL` | Lightweight decomposition model ID | `meta-llama/Meta-Llama-3.1-8B-Instruct` |
| `REASONING_MODEL` | High-capacity reasoning model ID | `deepseek-ai/DeepSeek-R1-Distill-Llama-70B` |
| `DEBUG` | Django debug mode | `True` |
| `SECRET_KEY` | Django secret key | `django-insecure-pitchly...` |
| `DATABASE_URL` | PostgreSQL connection string (defaults to SQLite if blank) | `postgres://pitchly:pitchly_password@postgres:5432/pitchly_db` |
| `VITE_API_URL` | Frontend REST API base URL | `http://localhost:8000` |
| `VITE_WS_URL` | Frontend WebSocket base URL | `ws://localhost:8000` |

---

## 🚀 Quick Start with Docker Compose

Ensure Docker and Docker Compose are installed and running on your system.

```bash
# 1. Clone repository
git clone https://github.com/HariHaran9209/skills-copilot-codespaces-vscode.git
cd pitchly

# 2. Launch PostgreSQL, Daphne ASGI backend, and Nginx frontend
docker compose up --build
```

- **Frontend App**: [http://localhost:3000](http://localhost:3000) (or `http://localhost:5173`)
- **Backend API**: [http://localhost:8000/api/](http://localhost:8000/api/)
- **WebSocket Endpoint**: `ws://localhost:8000/ws/projects/{id}/`

---

## 💻 Running Locally on Laptop (Without Docker)

You can run Pitchly directly on your laptop using Python and Node.js with built-in SQLite:

### Backend (Terminal 1)

```bash
cd pitchly/backend

# 1. Install dependencies
pip install -r requirements.txt

# 2. Apply migrations (uses SQLite automatically when DATABASE_URL is unset)
python manage.py migrate

# 3. Start Daphne ASGI server (handles both HTTP and WebSockets)
daphne -b 127.0.0.1 -p 8000 pitchly_backend.asgi:application
```

### Frontend (Terminal 2)

```bash
cd pitchly/frontend

# 1. Install dependencies
npm install

# 2. Start Vite development server
npm run dev
```

Visit [http://localhost:5173](http://localhost:5173) in your browser.

---

## 🧪 Running Automated Tests

Run the comprehensive unit and integration test suite:

```bash
cd pitchly/backend
python manage.py test plans
```

The test suite validates:
- AI schema validation and markdown code-block cleaning
- Sentence and bullet-point fallback breakdown logic
- Model router keyword trigger detection (`why`, `risk`, `compare`, `tradeoff`, `explain`)
- Strict suggestion isolation (guaranteeing `POST /api/projects/` does not pollute `Tasks`)
- Suggestion acceptance and automatic Task creation (`POST /api/suggestions/{id}/accept/`)
- Markdown README generator endpoint (`GET /api/projects/{id}/readme/`)

---

## 💡 Sample Inputs to Try

Try pasting one of these samples into Pitchly's idea box:

### Sample 1: Real-time Audio AI Agent
```text
Build an AI voice agent for customer support.
- Connect incoming phone calls via Twilio Voice SIP trunk
- Stream live PCM audio to an LLM speech-to-text pipeline
- Query CRM databases for customer purchase history
- Provide automated issue resolution with low latency (<500ms)
- Human agent fallback escalation on sentiment frustration
```

### Sample 2: Edge IoT Anomaly Detection
```text
Edge IoT predictive maintenance gateway for manufacturing facilities. Gathers vibration and temperature telemetry over MQTT, analyzes anomalies using lightweight models, alerts operators on threshold breaches, and schedules work orders.
```

---

## 📦 REST API Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/projects/` | Submit `raw_input` to trigger AI breakdown and initialize project |
| `GET` | `/api/projects/` | List recent projects |
| `GET` | `/api/projects/{id}/` | Retrieve project with all tasks, suggestions, and chat messages |
| `PATCH` | `/api/tasks/{id}/` | Update task column (`todo`, `doing`, `done`), order, or estimate |
| `DELETE`| `/api/tasks/{id}/` | Remove task from board |
| `POST` | `/api/suggestions/{id}/accept/` | Accept suggestion (converts task suggestion to Kanban task) |
| `POST` | `/api/suggestions/{id}/reject/` | Reject suggestion |
| `POST` | `/api/projects/{id}/chat/` | Send follow-up question (routes to Fast or Reasoning model) |
| `GET` | `/api/projects/{id}/readme/` | Get generated `README.md` for project roadmap |

---

## 🔮 Known Limitations & Roadmap

1. **User Authentication**: Currently single-tenant / local session for hackathon ease of use. Multi-tenant JWT authentication can be integrated via `dj-rest-auth`.
2. **Streaming AI Tokens**: Follow-up chat currently returns complete responses; streaming token generation via Server-Sent Events (SSE) or WebSockets is the next planned enhancement.
3. **Third-Party Integrations**: Direct export of Kanban cards to GitHub Issues, Jira, or Linear.

---

## 📄 License

Distributed under the MIT License. See [LICENSE](LICENSE) for more details.
