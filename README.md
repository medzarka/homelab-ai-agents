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

A complete self-hosted AI Agent runtime, long-term conversational memory, vector database, and chat interface powered by:
- **Nous Research Hermes Agent:** Autonomous AI agent gateway, tools, and execution engine.
- **Open-WebUI:** Full-featured conversational UI with multi-modal vision, SearXNG web search, and Docling RAG.
- **Qdrant:** High-performance vector database for document embeddings and semantic recall.
- **Mem0 Conversational Memory:** Hybrid vector (`PostgreSQL + pgvector`) and graph (`Neo4j`) long-term memory engine.

Optimized for **ARM64 and AMD64** Linux/Docker hosts.

---

## 🏛️ Architecture Overview

```mermaid
graph TD
    User([User / Browser]) -->|Port 3030| WebUI[Open-WebUI Chat Interface]
    User -->|Port 8642 / 9119| Hermes[Hermes Agent Gateway & Dashboard]
    
    WebUI -->|Chat Completions| LiteLLM[LiteLLM Proxy / AI Models]
    WebUI -->|Vector Search / RAG| Qdrant[(Qdrant Vector DB)]
    WebUI -->|Web Search| SearXNG[SearXNG Search Engine]
    WebUI -->|Doc Parsing| Docling[Docling Document Converter]
    
    Hermes -->|LiteLLM API| LiteLLM
    Hermes -->|Semantic Recall| Qdrant
    Hermes -->|Memory REST| Mem0API[Mem0 API Server]
    Mem0API -->|Vector Store| PGVector[(PostgreSQL + pgvector)]
    Mem0API -->|Knowledge Graph| Neo4j[(Neo4j Graph Database)]
```

---

## 🚀 Quick Start

### 1. Clone & Configure Environment
```bash
cp .env.example .env
nano .env
```
Generate strong random keys:
```bash
openssl rand -hex 16
```

### 2. Deploy the Stack
```bash
docker compose up -d
```
The `init-volumes` container will automatically initialize the host directory structure and set proper UID/GID permissions for PostgreSQL (`999:999`), Neo4j (`7474:7474`), and Open-WebUI.

---

## ⚙️ Hardware & Performance Tuning (32GB RAM Node)

- **Open-WebUI & LiteLLM:** Configured with 4 parallel worker threads to leverage the RK3588's 8 CPU cores.
- **PostgreSQL (`pgvector`):** Shared memory (`shm_size`) is set to `512mb` for fast vector similarity searches.
- **Neo4j Graph Database:** Initial heap is allocated to `1GB`, max heap to `2GB`, and page cache to `1GB` for high-throughput entity extraction and graph relationship queries.
- **Log Rotation:** All services have JSON log rotation enabled (`10m`, max 3 files) to prevent storage exhaustion.

---

## 🔒 Security Best Practices

- Ensure `.env` is **never** committed to version control (`.gitignore` protects this by default).
- The `shared_net` Docker network attaches to your reverse proxy (Caddy / Traefik / Dockhand) with `external: true`.
- Change default passwords for `MEM0_PG_PASSWORD`, `NEO4J_PASSWORD`, `WEBUI_SECRET_KEY`, and `HERMES_DASHBOARD_BASIC_AUTH_PASSWORD`.
