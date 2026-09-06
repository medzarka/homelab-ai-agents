# Homelab AI Agents - Configuration & Setup Guide

This guide details the current state of the AI Agents stack (`homelab-ai-agents`), including what is automatically configured via Docker Compose, and what requires manual configuration in the respective web interfaces (Hermes Agents Dashboard & Open-WebUI) to fully utilize the Homelab deployment.

## 1. Architecture & What is Automatically Configured

Your setup is an advanced, private AI-centric framework deployed securely across your Swarm nodes (`zap-srv` and `oci01-flex`) over Tailscale. The following is already configured and wired together automatically via `compose.yaml` and `.env`:

### **Storage & Permissions (`init-volumes`)**
- The `init-volumes` service automatically creates the necessary directories (`/workspace`, `/output`, `/open-webui`) on the host system and sets the correct permissions (775) to ensure containers have read/write/execute access without permission denial errors.

### **Hermes Agent (`hermes-agent`)**
- **LLM / Vision:** Connected to LiteLLM Gateway (`http://litellm:4000/v1`) using the models `hermes-default` and `hermes-vision`.
- **Memory:** Connected to the Mem0 backend (`http://mem0-api:8000`).
- **Web Search & Extraction:** Connected to SearXNG (`http://searxng:8080`) and Firecrawl (`http://firecrawl-api:3036`).
- **Speech (STT):** Connected to Speaches (`http://speaches:8000/v1`) using the `faster-whisper-large-v3` model.
- **MCP Servers:** The `knowledge-mcp` and `agent-sandbox` URLs are present in `config/config.yaml`.
- **Routing & SSO:** Accessible at `https://hermes.bluewave.work` and `https://agents.bluewave.work`. Secured via Authelia (1-Factor Policy) and basic authentication.

### **Workspace Scanner (`workspace-scanner`)**
- Continually runs a Python script that incrementally hashes and indexes files from the `/workspace` directory into the Qdrant database using the Knowledge MCP server, skipping unchanged files and automatically removing deleted files.

### **Open-WebUI (`open-webui`)**
- **LLMs:** Connected to both LiteLLM and Ollama directly for failover and model selection.
- **RAG (Embeddings & Reranker):** Connected to TEI (`http://embeddings:80/v1` and `http://reranker:80`) for local, fast embedding creation.
- **RAG (Vector DB):** Connected directly to Qdrant (`http://qdrant:6333`).
- **Web Search:** SearXNG is natively integrated into Open-WebUI's RAG pipeline.
- **Audio (TTS & STT):** Connected to Speaches for voice input and text-to-speech output.
- **Routing:** Accessible at `https://open-webui.bluewave.work`.

---

## 2. Manual Configuration Required (Post-Deployment)

To take full advantage of this framework, you need to complete the following manual steps in the web interfaces:

### **A. Open-WebUI Configuration**
1. **Initial Admin Account:** Navigate to `https://open-webui.bluewave.work`. The first account created will be the Administrator.
2. **Verify Models:** Go to Settings -> Connections. Ensure that models from LiteLLM and Ollama are fetched successfully.
3. **Web Search Toggle:** Go to Settings -> Web Search. Ensure it is enabled. You can enable it per-chat using the search icon.
4. **Voice Settings:** Go to Settings -> Audio. Ensure the TTS Voice (`af_heart`) and the STT engine are correctly selected to utilize the local `Speaches` service instead of the browser's default.

### **B. Hermes Agents Dashboard Configuration**
*Access: `https://hermes.bluewave.work` (Requires Authelia login + Basic Auth configured in your `.env`)*

1. **Verify MCP Connections:**
   - **Important Issue:** The `config.yaml` file mounts environment variables using `${SANDBOX_API_KEY}` syntax. However, the Hermes Agent YAML parser does *not* automatically expand environment variables in headers (e.g., `Authorization: Bearer ${SANDBOX_API_KEY}`). 
   - **Action:** In the Hermes Dashboard, go to the **MCP Servers** section. Manually update the `agent_sandbox` connection to replace `${SANDBOX_API_KEY}` with your actual secure token from the `.env` file to ensure the sandbox accepts execution requests.
   - Do the same for `knowledge-mcp` if you enable API key authentication for it.

2. **GitHub Integration:** 
   - Ensure your GitHub token is provided via the Hermes Dashboard or confirm it is properly read from the environment to allow the agent to read/commit to repositories.

3. **Verify Tool Availability:**
   - Check the **Tools** tab in the dashboard to ensure Firecrawl, SearXNG, and Mem0 are showing as "Online" and functional.

---

## 3. Security & Enhancements Report

During my inspection of the architecture, I identified the following insights and security notes:

### **Security Notes (Resolved/Checked)**
- **GitHub Token & Secrets:** I verified that your sensitive keys (GitHub token, API keys, basic auth secrets) have been moved to the `.env` file. The `.env` file is properly included in `.gitignore` and is **not** tracked by Git. Only the `.env.example` file (which contains dummy placeholder data) is tracked, ensuring no sensitive information will be published to GitHub.
- **Gateway Protections:** Authelia is correctly intercepting traffic. `hermes` is listed under the `one_factor` policy in `authelia/configuration.yml`, and `open-webui` is securely routed through Traefik.

### **Identified Issues & Enhancements**
1. **Double Authentication on Hermes:** `hermes` is protected by *both* Authelia 1FA and Traefik Basic Auth (via the agent's internal basic auth configuration). You may want to disable the internal basic auth in Hermes if Authelia is deemed sufficient, to prevent prompting users twice.
2. **MCP Sandbox High Availability:** The Sandbox is configured to failover between `agent-sandbox-zap-srv` and `agent-sandbox-oci01-flex` in the gateway `routes.yaml`. This is a fantastic high-availability design for code execution! However, ensure that the network latency over Tailscale to `oci01-flex` doesn't cause timeouts during heavy code execution if it fails over.
3. **Environment Variable Expansion:** As mentioned, Hermes Agent does not dynamically replace `${VAR}` in nested fields in `config.yaml` at runtime. Using the UI dashboard to set API keys for tools/MCPs, or writing a pre-startup script to use `envsubst` to generate `config.yaml` before starting the Hermes container, is highly recommended.
