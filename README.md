> ### 🌐 [Homelab Sovereign Cluster Architecture](https://github.com/medzarka/homelab-nodes)
> This repository is a modular component of the **Homelab Sovereign Multi-Node Cluster** — an enterprise-grade, privacy-first, self-hosted infrastructure spanning cloud VPS, on-premise compute servers, and edge ARM nodes.
> 
> * **Zero-Trust Network**: Multi-host WireGuard mesh interconnect via **Tailscale** with strict **Firewalld** zoning (`iptables: false`).
> * **Unified Identity & Ingress**: Centralized reverse proxy via **Traefik v3**, **Authelia SSO (2FA)**, and **LLDAP Directory**.
> * **Cluster Orchestration & GitOps**: High-availability **Docker Swarm** managed declaratively via **Arcane Cockpit**.
> * **End-to-End Observability**: Centralized portal (**Homepage**), metrics (**Beszel**), real-time logs (**Dozzle**), and uptime monitoring (**Uptime Kuma**).
> * **Sovereign Local AI & Compute**: Distributed inference (**LiteLLM**, **Ollama**, **Qdrant**, **Mem0**, **Hermes Agents**).
> * **Private Cloud & Storage**: Encrypted data synchronization, automated backups, and multi-cloud mirrors.

---

# 🤖 Homelab AI Agents Stack

A dedicated, production-hardened AI Agent runtime and conversational interface stack consisting exclusively of:
- **Nous Research Hermes Agent:** Autonomous AI agent gateway, multi-personality co-pilot (Academic, Research, Grants, Tutoring), and tool execution engine.
- **Open-WebUI:** Full-featured conversational UI with multi-modal vision, SearXNG web search, Kokoro TTS / Faster-Whisper STT, and TEI RAG.
- **Workspace Knowledge Scanner:** Automated incremental walker that scans `/workspace`, computes SHA-256 hashes, and streams documents to Qdrant via Knowledge MCP.

All heavy backing services (Ollama, TEI Embeddings/Reranker, Speaches, Mem0, Neo4j, Qdrant, Knowledge MCP, Agent Sandbox MCP) are decoupled and consumed as microservices over the sovereign overlay network (`homelab_swarm_net`).

Multi-Arch Ready: Built and tested for both **AMD64** (Xeon/EPYC/Core) and **ARM64** (Ampere Altra / RK3588).

---

## 🏛️ Architecture & Service Integration

```mermaid
graph TD
    User([User / Browser]) -->|https://chat.bluewave.work| Traefik[Traefik v3 Gateway]
    User -->|https://agents.bluewave.work| Traefik
    
    Traefik -->|Port 8080| WebUI[Open-WebUI]
    Traefik -->|Port 9119| Hermes[Hermes Agent Gateway & Dashboard]
    
    subgraph "homelab-ai-agents"
        Hermes
        WebUI
        Scanner[Workspace Scanner Daemon]
    end
    
    subgraph "homelab-ai-tools (zap-srv)"
        Ollama[Ollama LLM/VLM]
        TEIEmbed[TEI Embeddings bge-m3]
        TEIRerank[TEI Reranker v2-m3]
        Speaches[Speaches Whisper STT & Kokoro TTS]
        SearXNG[SearXNG Web Search]
        Firecrawl[Firecrawl Web Scraper]
    end
    
    subgraph "homelab-ai-knowledge (oci01-flex)"
        Mem0[Mem0 REST API]
        Qdrant[(Qdrant Vector DB)]
        Neo4j[(Neo4j Graph DB)]
        KnowledgeMCP[Knowledge MCP Server]
    end
    
    subgraph "homelab-ai-sandbox (oci01-flex)"
        SandboxMCP[Agent Sandbox MCP Server]
    end
    
    Hermes -->|Episodic Memory| Mem0
    Hermes -->|Knowledge Tools (SSE)| KnowledgeMCP
    Hermes -->|Sandboxed Execution (SSE)| SandboxMCP
    Hermes -->|Search & Scrape| SearXNG
    Hermes -->|Speech Input| Speaches
    
    Scanner -->|Index /workspace| KnowledgeMCP
    KnowledgeMCP -->|Vectors| Qdrant
    
    WebUI -->|Chat LLMs| Ollama
    WebUI -->|Embeddings & Rerank| TEIEmbed
    WebUI -->|RAG Vectors| Qdrant
    WebUI -->|Audio Voice| Speaches
    WebUI -->|Web Search| SearXNG
```

---

## 🧠 Memory & Execution Design

### 1. Hybrid Memory Strategy
Hermes Agent utilizes a dual-tier memory system:
1. **Background Episodic Memory (Mem0 REST)**: Hermes natively flushes conversational context, personal facts, and preferences to `http://mem0-api:8000`. Memory recall is completely automated and zero-overhead.
2. **Semantic Knowledge & Graph RAG (Knowledge MCP)**: Hermes queries `http://knowledge-mcp:8095/sse` via explicit tool calls (`search_knowledge`, `query_knowledge_graph`) for deep factual search across course materials, research drafts, and homelab documentation.

### 2. Sandboxed Code Execution (Sandbox MCP)
Hermes Agent has its local terminal backend **disabled** for security (`terminal.backend: disabled`). All code compilation and execution requests (Bash, Python, C/C++, Java, Rust, LaTeX) are delegated to the dedicated in-memory sandbox (`http://agent-sandbox:8088/sse`).

### 3. Automated `/workspace` Knowledge Scanner
The `workspace-scanner` service runs an incremental file walker (`sync_workspace.py`):
- Walks `/workspace` and computes file SHA-256 hashes.
- Skips unchanged files in `<1ms` via `.knowledge_cache.json`.
- Streams new or modified documents (PDFs, Markdown, source code, images, audio) directly to Knowledge MCP with Base64 payload support for seamless cross-node ingestion.
- Automatically purges deleted files from Qdrant.

---

## 🚀 Quick Start

### 1. Configure Environment
```bash
cp .env.example .env
nano .env
```

### 2. Validate Compose Configuration
```bash
docker compose config
```

### 3. Launch the Stack
```bash
docker compose up -d
```

### 4. Monitor Logs
```bash
# Follow Hermes Agent logs
docker logs -f hermes-agent

# Follow Open-WebUI logs
docker logs -f open-webui

# Follow Workspace Knowledge Scanner
docker logs -f hermes_workspace_scanner
```

---

## 🔒 Security & Traefik Routing

- **Hermes Agent Dashboard:** Secured behind Authelia SSO (`https://agents.bluewave.work` / `https://hermes.bluewave.work`).
- **Open-WebUI:** Secured with Fail2ban and security headers (`https://chat.bluewave.work` / `https://open-webui.bluewave.work`).
- **Internal Swarm Overlay:** Communication with Ollama, TEI, Speaches, Mem0, Qdrant, and MCP servers traverses the encrypted Tailscale Swarm overlay network (`homelab_swarm_net`).
