# 🚀 Complete Setup & Optimization Guide for Homelab AI Agents

This guide walks you through completing the post-deployment configuration of **Hermes Agent** and **Open-WebUI** to maximize the capabilities of all sovereign AI microservices running across your cluster.

---

## 📑 Table of Contents
1. [Cluster Microservices Inventory](#1-cluster-microservices-inventory)
2. [Step 1: Deploying the Stack on `zap-srv`](#step-1-deploying-the-stack-on-zap-srv)
3. [Step 2: Configuring Open-WebUI Admin Interface](#step-2-configuring-open-webui-admin-interface)
4. [Step 3: Mastering Hermes Agent Personalities & Tools](#step-3-mastering-hermes-agent-personalities--tools)
5. [Step 4: Leveraging Hybrid Memory (Mem0 + Knowledge MCP)](#step-4-leveraging-hybrid-memory-mem0--knowledge-mcp)
6. [Step 5: Sandboxed Code Execution via MCP](#step-5-sandboxed-code-execution-via-mcp)
7. [Step 6: Workspace Indexing & Knowledge Ingestion](#step-6-workspace-indexing--knowledge-ingestion)
8. [Verification & Health Diagnostics](#verification--health-diagnostics)

---

## 1. Cluster Microservices Inventory

All services communicate over the internal encrypted Docker Swarm overlay network (`homelab_swarm_net`). No host ports are exposed:

| Service | Internal Swarm Endpoint | External Secure URL | Purpose |
| :--- | :--- | :--- | :--- |
| **LiteLLM Gateway** | `http://litellm:4000/v1` | `https://litellm.bluewave.work` | Cloud & Local LLM Router (Claude, Gemini, GPT) |
| **Ollama Inference** | `http://ollama:11434/v1` | `https://ollama.bluewave.work` | Local LLMs (`hermes3:8b`) & Vision (`qwen2.5vl:3b`) |
| **TEI Embeddings** | `http://embeddings:80/v1` | `https://embeddings.bluewave.work` | High-speed Dense Embeddings (`BAAI/bge-m3`) |
| **TEI Reranker** | `http://reranker:80` | `https://reranker.bluewave.work` | Cross-Encoder Reranker (`BAAI/bge-reranker-v2-m3`) |
| **Speaches Audio** | `http://speaches:8000/v1` | `https://audio.bluewave.work` | STT (`Whisper-Large-v3`) & TTS (`Kokoro-82M ONNX`) |
| **SearXNG Search** | `http://searxng:8080` | `https://search.bluewave.work` | Privacy-first Web Metasearch |
| **Firecrawl Scraper**| `http://firecrawl-api:3036` | `https://scraper.bluewave.work` | Full-page Markdown web crawler & scraper |
| **Mem0 Memory** | `http://mem0-api:8000` | `https://mem0.bluewave.work` | Turn-by-turn conversational episodic memory |
| **Qdrant Vector DB** | `http://qdrant:6333` | `https://qdrant.bluewave.work` | Vector store for RAG & workspace knowledge |
| **Neo4j Graph DB** | `bolt://neo4j:7687` | `https://neo4j.bluewave.work` | Entity & relationship knowledge graph |
| **Knowledge MCP** | `http://knowledge-mcp:8095/sse` | `https://knowledge-mcp.bluewave.work` | Semantic Search & Cypher Graph query tools |
| **Sandbox MCP** | `http://agent-sandbox:8088/sse` | `https://sandbox.bluewave.work` | In-memory code execution (Bash, Python, C++, Java, LaTeX) |

---

## Step 1: Deploying the Stack on `zap-srv`

Connect to **`zap-srv`** (22 Cores, 48 GB RAM) via SSH:

```bash
cd ~/homelab-ai-agents
git pull origin main

# Validate configuration
docker compose config

# Start Hermes Agent, Workspace Scanner, and Open-WebUI
docker compose up -d

# Verify all 3 containers are running
docker compose ps
```

---

## Step 2: Configuring Open-WebUI Admin Interface

Navigate in your browser to: **`https://chat.bluewave.work`**

### 2.1 First-Time Account Creation
1. The first account registered automatically receives **Admin privileges**.
2. Create your administrator account using your academic/professional email.

### 2.2 Verify Model Connections (`Admin Panel` -> `Settings` -> `Connections`)
The compose configuration pre-injects LiteLLM and Ollama:
* **OpenAI API Endpoints**:
  - `http://litellm:4000/v1` (Key: `${LITELLM_MASTER_KEY}`)
  - `http://ollama:11434/v1` (Key: `ollama`)
* Click the **Verify / Refresh** button to verify that all models appear (`hermes3:8b`, `qwen2.5vl:3b`, `claude-3-5-sonnet`, `gemini-2.0-flash`, `gpt-4o`).

### 2.3 Audio Settings (`Admin Panel` -> `Settings` -> `Audio`)
Configure real-time Speech-to-Text and Text-to-Speech using your local Speaches instance:
* **Speech-to-Text (STT)**:
  - **Engine**: `OpenAI`
  - **API Base URL**: `http://speaches:8000/v1`
  - **API Key**: *(leave blank or any string)*
  - **Model**: `Systran/faster-whisper-large-v3`
* **Text-to-Speech (TTS)**:
  - **Engine**: `OpenAI`
  - **API Base URL**: `http://speaches:8000/v1`
  - **API Key**: *(leave blank or any string)*
  - **Model**: `speaches-ai/Kokoro-82M-v1.0-ONNX`
  - **Voice**: `af_heart` (or `am_adam`, `bf_emma`)

### 2.4 Document RAG & Embedding Settings (`Admin Panel` -> `Settings` -> `Retrieval`)
Configure dense vector search and cross-encoder reranking:
* **Embedding Engine**: `OpenAI`
  - **Embedding URL**: `http://embeddings:80/v1`
  - **API Key**: *(leave blank)*
  - **Embedding Model**: `BAAI/bge-m3`
* **Reranking Engine**: `tei` (Text Embeddings Inference)
  - **TEI Base URL**: `http://reranker:80`
  - **Reranker Model**: `BAAI/bge-reranker-v2-m3`
* **Vector Database**: `Qdrant`
  - **Qdrant URL**: `http://qdrant:6333`
  - **Qdrant API Key**: `${QDRANT_API_KEY}`
* **RAG Top-K**: `5`
* **Relevance Score Threshold**: `0.50`

### 2.5 Web Search Integration (`Admin Panel` -> `Settings` -> `Web Search`)
* **Enable Web Search**: `ON`
* **Search Engine**: `SearXNG`
* **SearXNG Query URL**: `http://searxng:8080/search?q=<query>`

---

## Step 3: Mastering Hermes Agent Personalities & Tools

Access the Hermes Dashboard at: **`https://agents.bluewave.work`** *(Authelia SSO protected)*.

Hermes Agent is configured with 6 specialized personas tailored to your workflow:

### 1. 🎓 `professor` (Teaching at ISET Kairouan)
* **Language**: French.
* **Focus**: Computer Science pedagogy (Algorithms & Data Structures, Big Data, Machine Learning, Agentic AI).
* **Workflow**: Designs Bloom-aligned syllabi, crystal-clear French lecture notes, reproducible Docker/Proxmox lab guides, and Continuous Verification Loop (CVL) evaluations.
* **Code/LaTeX Execution**: Automatically delegates lab code tests and LaTeX exam compilation to `agent_sandbox` MCP.

### 2. 🔬 `researcher` (Senior Scientist at SE&TIC Lab)
* **Language**: English.
* **Focus**: Robust Speech Recognition, Autism acoustic biomarker detection, Ultrasound rock analysis with ML, and AI in Education.
* **Workflow**: Produces publication-grade IEEE/Springer manuscripts, rigorous mathematical equations, and PyTorch experiment validation with strict metrics (Accuracy, EER, F1-Score).

### 3. ⚖️ `reviewer2` (Strict IEEE Peer Reviewer)
* **Language**: English.
* **Focus**: Audits experimental methodologies, checks baseline comparisons, identifies potential data leakage, and scrutinizes statistical significance.

### 4. 💼 `grant_writer` (International Project Funding)
* **Language**: English (Erasmus+, Horizon Europe) & French (DAF, AUF).
* **Focus**: Builds structured Logical Frameworks (LogFrames), precise Work Packages (WPs), Gantt milestones, and measurable socio-economic impact matrices tailored for Tunisian higher education.

### 5. 👨‍👧‍👧 `socratic_tutor` (Calibrated Pedagogical Tutor for Daughters)
* **Pedagogical Rule**: Never gives direct answers immediately; uses progressive scaffolding and Socratic questioning.
* **Calibrated Languages**:
  - **Eya** (University Year 2): English (Algorithms, data structures, system architecture).
  - **Mariem** (High School Year 2 - Sciences): French (Math, Physics, Chemistry, SVT).
  - **Sarra** (High School Year 1 - Python/Math): French (Python programming, algebra, geometry).
  - **Emna** (Basic School Year 2 / 8ème de base): Modern Standard Arabic (*العربية الفصحى*) with engaging, simplified analogies.

### 6. ⚡ `productivity_advisor` (Executive Meta-Coach)
* **Language**: English.
* **Focus**: Audits time allocation across Teaching, Research, Grants, and Family; detects context-switching friction; and provides proactive productivity recommendations.

---

## Step 4: Leveraging Hybrid Memory (Mem0 + Knowledge MCP)

Hermes operates with a dual-layer memory system:

### 1. Episodic Dialogue Memory (Mem0 REST)
* **How it works**: Hermes automatically flushes dialogue facts, user preferences, and project updates to `http://mem0-api:8000` in the background.
* **Benefit**: Zero manual intervention. When you start a new conversation and mention *"Continue where we left off on the autism speech dataset"*, Hermes recalls previous facts automatically.

### 2. Semantic Document & Graph RAG (Knowledge MCP)
Hermes possesses explicit tools connected via SSE:
* **`search_knowledge`**:
  - *Prompt*: *"Hermes, search our knowledge base for the acoustic feature extraction parameters used in the SE&TIC journal paper."*
  - *Action*: Hermes executes `search_knowledge(query="acoustic feature extraction", collection="workspace")`, which retrieves relevant passages from Qdrant and reranks them with the TEI Cross-Encoder.
* **`query_knowledge_graph`**:
  - *Prompt*: *"Find all research projects connected to speaker recognition and check their associated datasets."*
  - *Action*: Hermes executes a Cypher query on Neo4j to traverse entity connections.

---

## Step 5: Sandboxed Code Execution via MCP

Local container command execution is disabled (`terminal.backend: disabled`) for security. Hermes delegates 100% of execution to the in-memory **Agent Sandbox MCP**:

### Example Interactions
1. **Python Data Analysis**:
   > *"Hermes, write a script to calculate the Equal Error Rate (EER) on this prediction array and run it in the sandbox."*
   - Hermes generates the code, invokes `agent_sandbox.execute_code(language="python", code=...)`, and returns the stdout and execution time.
2. **C / C++ / Java Execution**:
   > *"Test this graph traversal algorithm in C++20 with custom test cases."*
   - Hermes compiles and executes the program in RAM via GCC/G++ with strict timeouts.
3. **LaTeX Document Compilation**:
   > *"Compile this IEEE conference paper draft into a PDF."*
   - Hermes invokes Tectonic in the sandbox and verifies that the PDF compiles without errors.

---

## Step 6: Workspace Indexing & Knowledge Ingestion

Hermes and the Knowledge Walker use the persistent workspace directory on `zap-srv`:
`/srv/data/ai-agents/workspace/hermes/workspace`

### 1. Adding Documents to Knowledge
Simply drop your files into `/srv/data/ai-agents/workspace/hermes/workspace`:
- **PDFs**: Lecture notes, IEEE papers, grant proposals (automatically OCR'd and parsed page-by-page).
- **Code & Text**: Python scripts, C/C++ files, Markdown documents (`.md`).
- **Audio**: Speech recordings (`.wav`, `.mp3`) automatically transcribed by Whisper.
- **Images**: Architectural diagrams, charts (analyzed by Qwen2.5-VL).

### 2. Automatic Periodic Scanning
The `workspace-scanner` container runs in the background:
- **Scan Interval**: Every 15 minutes (configurable via `SCAN_INTERVAL_SECONDS`).
- **SHA-256 Incremental Cache**: Skips unchanged files in `<1ms`.
- **Distributed Ingestion**: Encodes new/modified documents as Base64 and streams them to Knowledge MCP on `oci01-flex`, storing vectors into Qdrant.
- **Automatic Cleanup**: Deleting a file from `/workspace` removes its vectors from Qdrant during the next scan.

### 3. On-Demand Instant Indexing
To trigger an immediate scan without waiting 15 minutes:
```bash
docker exec -it hermes_workspace_scanner python3 /usr/local/bin/sync_workspace.py
```
Or directly inside Hermes Agent:
> *"Hermes, run the workspace sync script to index the new slides I just uploaded."*

---

## Verification & Health Diagnostics

Run these one-line commands from `zap-srv` to verify that all inter-service connections are operational:

```bash
# 1. Test LiteLLM Gateway
curl -s http://100.83.191.68:4000/health/readiness | jq .

# 2. Test Local Ollama Models
curl -s http://localhost:11434/api/tags | jq '.models[].name'

# 3. Test TEI Embeddings
curl -s -X POST http://localhost:80/embed \
  -H "Content-Type: application/json" \
  -d '{"inputs": "Homelab AI Verification"}' | head -c 80

# 4. Test TEI Reranker
curl -s -X POST http://localhost:8080/rerank \
  -H "Content-Type: application/json" \
  -d '{"query": "machine learning", "texts": ["deep neural network", "chocolate cake recipe"]}' | jq .

# 5. Test Speaches Whisper STT
curl -s http://localhost:8000/health | jq .

# 6. Test Knowledge MCP
curl -s http://100.83.191.68:8095/health | jq .

# 7. Test Agent Sandbox MCP
curl -s http://100.83.191.68:8088/health | jq .

# 8. Test Qdrant Vector Store
curl -s http://100.83.191.68:6333/collections | jq .
```

---

## 🔒 Summary Checklist for Daily Production Use

- [x] Stack running on **`zap-srv`** (22 Cores, 48 GB RAM).
- [x] Zero exposed host ports (`ports:` omitted in `compose.yaml`).
- [x] Ingress routed via Traefik:
  - Open-WebUI: `https://chat.bluewave.work`
  - Hermes Dashboard: `https://agents.bluewave.work` (Authelia SSO)
- [x] Hybrid Memory active (Mem0 automatic recall + Knowledge MCP on-demand search).
- [x] Sandbox MCP active for all compilation & script execution.
- [x] Incremental `/workspace` scanner active (auto-indexing every 15 minutes).
- [x] Reboot resilience guaranteed via `homelab-boot-guard.service` in `homelab-nodes`.
