# 🚀 Homelab AI Agents Architecture & Configuration Guide

This guide provides a comprehensive breakdown of the integration between **Hermes Agent**, **Open-WebUI**, and all sovereign AI microservices running across your Homelab cluster (`zap-srv`, `oci01-flex`, and `zap-vps`).

It clearly demarcates **what is 100% automated via Docker Compose & configuration files**, and **what must be configured once inside the Open-WebUI or Hermes Agent web interfaces**.

---

## 📑 Table of Contents
1. [Cluster Microservices Architecture Matrix](#1-cluster-microservices-architecture-matrix)
2. [What is 100% Automated via Docker Compose & Config Files](#2-what-is-100-automated-via-docker-compose--config-files)
   - [Hermes Agent Automated Integration](#21-hermes-agent-automated-integration)
   - [Open-WebUI Automated Integration](#22-open-webui-automated-integration)
   - [Workspace Knowledge Scanner Automated Ingestion](#23-workspace-knowledge-scanner-automated-ingestion)
   - [Storage & Health Guard Automated Initialization](#24-storage--health-guard-automated-initialization)
3. [What Still Needs Configuration via the Web Interface](#3-what-still-needs-configuration-via-the-web-interface)
   - [Open-WebUI Web Interface Checklist (`https://open-webui.bluewave.work`)](#31-open-webui-web-interface-checklist)
   - [Hermes Agent Dashboard Checklist (`https://hermes.bluewave.work`)](#32-hermes-agent-dashboard-checklist)
4. [Step-by-Step UI Setup Walkthrough](#4-step-by-step-ui-setup-walkthrough)
5. [Operational Verification & Diagnostics](#5-operational-verification--diagnostics)

---

## 1. Cluster Microservices Architecture Matrix

All AI services communicate securely over the encrypted Docker Swarm overlay network (`homelab_swarm_net`). Neither `hermes-agent` nor `open-webui` expose raw host ports. Ingress is routed through Traefik with Cloudflare SSL and Authelia SSO.

| Microservice | Internal Endpoint | Handled in Docker Compose | Handled in Web UI | Primary Purpose |
| :--- | :--- | :---: | :---: | :--- |
| **LiteLLM Gateway** | `http://litellm:4000/v1` | ✅ Auto | ⚙️ Verify & Default | Unified Router for Cloud (Claude, Gemini, GPT) & Local LLMs |
| **Ollama Inference** | `http://ollama:11434/v1` | ✅ Auto | ⚙️ Verify & Refresh | Local sovereign models (`hermes3:8b`, `qwen2.5vl:3b`) |
| **TEI Embeddings** | `http://embeddings:80/v1` | ✅ Auto | ⚙️ Verify in Retrieval | Dense vector embeddings (`BAAI/bge-m3`, 1024-dim) |
| **TEI Reranker** | `http://reranker:80` | ✅ Auto | ⚙️ Verify in Retrieval | Cross-Encoder precision reranking (`BAAI/bge-reranker-v2-m3`) |
| **Speaches STT** | `http://speaches:8000/v1` | ✅ Auto | ⚙️ Test in Audio | Faster-Whisper Large-v3 Speech-to-Text |
| **Speaches TTS** | `http://speaches:8000/v1` | ✅ Auto | ⚙️ Select Voice in Audio | Kokoro-82M ONNX Text-to-Speech (`af_heart`) |
| **SearXNG Search** | `http://searxng:8080` | ✅ Auto | ⚙️ Toggle in Web Search | Privacy-first metasearch aggregation |
| **Firecrawl Scraper**| `http://firecrawl-api:3036` | ✅ Auto | — *(Hermes only)* | Deep web extraction & full Markdown rendering |
| **Mem0 Memory** | `http://mem0-api:8000` | ✅ Auto | — *(Hermes only)* | Episodic, turn-by-turn conversational memory recall |
| **Qdrant Vector DB** | `http://qdrant:6333` | ✅ Auto | ⚙️ Verify in Retrieval | Vector database storing RAG embeddings & workspace chunks |
| **Neo4j Graph DB** | `bolt://neo4j:7687` | ✅ Auto | — *(Knowledge MCP)* | Entity & relationship knowledge graph |
| **Knowledge MCP** | `http://knowledge-mcp:8095/sse` | ✅ Auto | — *(Hermes only)* | Semantic search & Cypher graph traversal tools |
| **Agent Sandbox MCP**| `http://agent-sandbox:8088/sse` | ✅ Auto | — *(Hermes only)* | In-memory code execution (Python, C++, Java, LaTeX) |

---

## 2. What is 100% Automated via Docker Compose & Config Files

You do **NOT** need to write scripts or manually configure backend files for the items below. They are baked into `compose.yaml` and `config/config.yaml`.

### 2.1 Hermes Agent Automated Integration
- **LLM Routing**: Automatically routes all requests to LiteLLM (`http://litellm:4000/v1`) using `${LITELLM_API_KEY}`. Pre-configures model aliases (`hermes-default`, `hermes-vision`, `hermes-compression`, `mistral-codestral-latest-22B`).
- **Execution Sandbox**: In-container terminal execution is disabled (`terminal.backend: disabled`). Hermes is wired directly to `http://agent-sandbox:8088/sse` with `${SANDBOX_API_KEY}` authentication for safe code execution in RAM.
- **Semantic & Graph Knowledge**: Wired to `http://knowledge-mcp:8095/sse` for automated RAG, document retrieval, and Neo4j graph queries.
- **Continuous Memory**: Configured with `memory.provider: mem0` pointing to `http://mem0-api:8000`. Hermes flushes facts every 6–10 turns automatically.
- **Web Intelligence**: Wired to SearXNG (`http://searxng:8080`) for live search and Firecrawl (`http://firecrawl-api:3036`) for Markdown scraping.
- **Speech Audio**: Configured with `stt.openai` pointing to Speaches (`http://speaches:8000/v1`) using `Systran/faster-whisper-large-v3`.
- **Pre-baked Personalities**:
  1. 🎓 `professor`: French academic co-pilot for ISET Kairouan (pedagogy, Docker/Proxmox labs, Bloom's taxonomy evaluations).
  2. 🔬 `researcher`: English scientific writer for SE&TIC Lab (speech processing, autism acoustic biomarkers, IEEE publications).
  3. ⚖️ `reviewer2`: Rigorous peer reviewer auditing methodology, statistical rigor, and baseline metrics.
  4. 💼 `grant_writer`: Bilingual EU/Tunisian project specialist (Erasmus+, Horizon Europe, AUF).
  5. 👨‍👧‍👧 `socratic_tutor`: Pedagogically calibrated tutor for daughters (Eya: English, Mariem & Sarra: French, Emna: Arabic).
  6. ⚡ `productivity_advisor`: Executive workflow and cognitive optimization coach.

### 2.2 Open-WebUI Automated Integration
- **Model Endpoints**: Injected via `OPENAI_API_BASE_URLS` and native `OLLAMA_BASE_URL` (`http://litellm:4000/v1` and `http://ollama:11434`).
- **Dense Vector RAG**: Pre-wired with `RAG_EMBEDDING_ENGINE=openai` pointing to `http://embeddings:80/v1` using `BAAI/bge-m3`.
- **Reranker**: Pre-wired with `RAG_RERANKING_ENGINE=tei` pointing to `http://reranker:80` using `BAAI/bge-reranker-v2-m3`.
- **Vector Store**: Pre-wired to `VECTOR_DB=qdrant` pointing to `http://qdrant:6333` with `${QDRANT_API_KEY}`.
- **Speech Audio**: Pre-wired with Whisper STT and Kokoro TTS (`af_heart`) on `http://speaches:8000/v1`.
- **Web Search**: Pre-wired to SearXNG with `SEARXNG_SEARCH_URL=http://searxng:8080/search?q=<query>`.
- **Timeout Protection**: `HTTP_TIMEOUT=1800` and `AIOHTTP_TIMEOUT=1800` prevent timeouts during heavy RAG and large model generation.

### 2.3 Workspace Knowledge Scanner Automated Ingestion
- Automatically scans `/srv/data/ai-agents/workspace/hermes/workspace` on `zap-srv` every 15 minutes (`SCAN_INTERVAL_SECONDS=900`).
- Computes SHA-256 hashes to skip unchanged files in `<1ms`.
- Encodes new or modified files (PDF, Markdown, code, audio, images) and streams them to Knowledge MCP (`http://knowledge-mcp:8095/index-file`), updating Qdrant collections.

### 2.4 Storage & Health Guard Automated Initialization
- `init-volumes` initializes directory permissions (`775`) on `/srv/data/ai-agents/workspace` and `/srv/data/ai-agents/open-webui`.
- Runs continuously with `sleep infinity` and an automated healthcheck so **Arcane Cockpit** marks the stack healthy without false-positive stopped warnings.

---

## 3. What Still Needs Configuration via the Web Interface

Because Open-WebUI stores state in its internal database (`webui.db`) and Hermes Agent manages interactive user sessions, the following one-time steps must be completed in the web UI.

### 3.1 Open-WebUI Web Interface Checklist
*(URL: `https://open-webui.bluewave.work`)*

- [ ] **First Account Creation**: The very first user to register automatically becomes the **Instance Administrator**.
- [ ] **Verify Model Connections** (`Admin Panel` $\rightarrow$ `Settings` $\rightarrow$ `Connections`):
  - Click the **Verify / Refresh** button next to LiteLLM and Ollama.
  - Verify that the models appear in the list (`hermes-default`, `hermes3:8b`, `qwen2.5vl:3b`, `claude-3-5-sonnet`, `gemini-2.0-flash`).
  - Set your preferred default model (e.g. `hermes-default` or `hermes3:8b`).
- [ ] **Verify Audio Playback** (`Admin Panel` $\rightarrow$ `Settings` $\rightarrow$ `Audio`):
  - Click **Verify** on STT (`http://speaches:8000/v1`).
  - Click **Verify** on TTS (`http://speaches:8000/v1`).
  - Ensure voice is set to `af_heart` (female) or `am_adam` (male).
- [ ] **Tune Document Retrieval Parameters** (`Admin Panel` $\rightarrow$ `Settings` $\rightarrow$ `Retrieval`):
  - Verify **Embedding Engine** shows `OpenAI` (`http://embeddings:80/v1`) with model `BAAI/bge-m3`.
  - Verify **Reranking Engine** shows `tei` (`http://reranker:80`) with model `BAAI/bge-reranker-v2-m3`.
  - Recommended RAG parameters:
    - **Top K**: `5`
    - **Score Threshold**: `0.50` (filters out irrelevant chunks)
- [ ] **Verify Web Search** (`Admin Panel` $\rightarrow$ `Settings` $\rightarrow$ `Web Search`):
  - Confirm **SearXNG Query URL** is `http://searxng:8080/search?q=<query>`.
  - Toggle **Enable Web Search** ON.

### 3.2 Hermes Agent Dashboard Checklist
*(URL: `https://hermes.bluewave.work`)*

- [ ] **Authelia SSO Authentication**: Authenticate using your Homelab SSO credentials.
- [ ] **Hermes Basic Auth Login**: Enter the credentials configured in `.env` (`HERMES_DASHBOARD_BASIC_AUTH_USERNAME=mgrsys`).
- [ ] **Active Personality Selection**:
  - Test persona switching in the prompt box:
    - Type `/profile professor` for teaching preparation.
    - Type `/profile researcher` for SE&TIC paper writing.
    - Type `/profile socratic_tutor` for family tutoring.
- [ ] **Verify MCP Tools Registration**:
  - Run `/tools` or inspect the startup log:
    - `agent_sandbox` tools must be present (`agent_sandbox_execute_code`, etc.).
    - `knowledge` tools must be present (`knowledge_search_knowledge`, `knowledge_query_knowledge_graph`, etc.).
- [ ] **Verify Episodic Memory**:
  - Type `/memory` to view current stored episodic memory points from Mem0.

---

## 4. Step-by-Step UI Setup Walkthrough

### Step 4.1: Accessing Open-WebUI
1. Open your browser and navigate to:
   ```
   https://open-webui.bluewave.work
   ```
2. Click **Sign Up** and create your master administrator account.
3. Open **Admin Panel** (bottom-left avatar $\rightarrow$ **Admin Panel**).
4. Navigate to **Settings** $\rightarrow$ **Connections**:
   - Ensure the OpenAI API URL shows: `http://litellm:4000/v1`
   - Ensure the Ollama API URL shows: `http://ollama:11434`
   - Click the green refresh/sync icon to import all models into the dropdown.

### Step 4.2: Testing Knowledge RAG in Open-WebUI
1. In Open-WebUI, click **Workspace** $\rightarrow$ **Knowledge**.
2. Click **+** to create a new collection (e.g., `Course-Algorithms` or `SETIC-Research`).
3. Drag and drop any PDF or Markdown document.
4. Watch the progress bar: Open-WebUI will vectorize the file via TEI (`bge-m3`) and save vectors to Qdrant (`http://qdrant:6333`).
5. Open a new chat, type `#` followed by your collection name, and ask questions against the document.

### Step 4.3: Testing Hermes Agent Personalities & Tools
1. Navigate to:
   ```
   https://hermes.bluewave.work
   ```
2. Log in through Authelia and the Hermes Basic Auth prompt.
3. In the chat prompt, test sandboxed execution:
   ```
   Hermes, run a Python script in the sandbox to generate the first 20 Fibonacci numbers.
   ```
   *Hermes will automatically invoke `agent_sandbox_execute_code` and print the output without running any code on the host machine.*
4. Test knowledge graph querying:
   ```
   Hermes, search the knowledge base for any papers discussing speech recognition biomarkers.
   ```
   *Hermes will invoke `knowledge_search_knowledge` and return passages reranked by TEI.*

---

## 5. Operational Verification & Diagnostics

Run these one-line health checks directly from **`zap-srv`** to verify all microservices respond within `<5ms`:

```bash
# 1. Test LiteLLM Proxy
curl -s http://100.83.191.68:4000/health/readiness | jq .

# 2. Test Local Ollama Models
curl -s http://localhost:11434/api/tags | jq '.models[].name'

# 3. Test TEI Dense Embeddings
curl -s -X POST http://localhost:80/embed \
  -H "Content-Type: application/json" \
  -d '{"inputs": "Homelab AI Verification"}' | head -c 80

# 4. Test TEI Cross-Encoder Reranker
curl -s -X POST http://localhost:8080/rerank \
  -H "Content-Type: application/json" \
  -d '{"query": "speech recognition", "texts": ["acoustic biomarkers in autism", "chocolate cake recipe"]}' | jq .

# 5. Test Speaches Whisper STT
curl -s http://localhost:8000/health | jq .

# 6. Test Knowledge MCP
curl -s http://100.83.191.68:8095/health | jq .

# 7. Test Agent Execution Sandbox
curl -s http://localhost:8088/health | jq .

# 8. Test Qdrant Vector DB
curl -s http://100.83.191.68:6333/collections | jq .

# 9. Trigger Instant Workspace Scan
docker exec -it hermes_workspace_scanner python3 /usr/local/bin/sync_workspace.py
```
