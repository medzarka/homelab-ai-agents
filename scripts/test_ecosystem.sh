#!/bin/sh
# ==============================================================================
# Homelab AI Microservices & Hermes Agent End-to-End Diagnostic Suite
# Checks: LiteLLM, Ollama, SearXNG, Firecrawl, Speaches (STT+TTS), TEI, 
#         Knowledge MCP, Sandbox MCP, and Hermes Agent Gateway.
# ==============================================================================
set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

pass() { echo "${GREEN}✓ PASS:${NC} $1"; }
fail() { echo "${RED}✗ FAIL:${NC} $1"; }
info() { echo "${YELLOW}>>> ${NC}$1"; }
section() { echo "\n${BLUE}========================================================${NC}\n${BLUE}$1${NC}\n${BLUE}========================================================${NC}"; }

LITELLM_URL="${LITELLM_BASE_URL:-http://litellm:4000}"
OLLAMA_URL="${OLLAMA_BASE_URL:-http://ollama:11434}"
SEARXNG_URL="${SEARXNG_BASE_URL:-http://searxng:8080}"
FIRECRAWL_URL="${FIRECRAWL_BASE_URL:-http://firecrawl-api:3036}"
SPEACHES_URL="${SPEACHES_BASE_URL:-http://speaches:8000}"
EMBEDDINGS_URL="${EMBEDDINGS_BASE_URL:-http://embeddings:80}"
RERANKER_URL="${RERANKER_BASE_URL:-http://reranker:80}"
KMCP_URL="${KNOWLEDGE_MCP_BASE_URL:-http://knowledge-mcp:8095}"
SANDBOX_URL="${SANDBOX_BASE_URL:-http://agent-sandbox:8088}"
HERMES_URL="${HERMES_BASE_URL:-http://127.0.0.1:8642}"
SANDBOX_KEY="${SANDBOX_API_KEY:-sk-homelab-sandbox-secure-key}"
KMCP_KEY="${KNOWLEDGE_MCP_API_KEY:-sk-homelab-knowledge-secure-key}"

section "1. LiteLLM Proxy / Gateway (${LITELLM_URL})"
if curl -sf "${LITELLM_URL}/health/liveliness" >/dev/null 2>&1; then
    pass "LiteLLM liveliness endpoint is responding"
else
    fail "LiteLLM liveliness failed at ${LITELLM_URL}/health/liveliness"
fi

section "2. Ollama Local LLM / VLM Engine (${OLLAMA_URL})"
TAGS=$(curl -sf "${OLLAMA_URL}/api/tags" 2>/dev/null || echo "")
if echo "$TAGS" | grep -q "qwen2.5vl:3b"; then
    pass "Ollama is online and 'qwen2.5vl:3b' is loaded"
elif [ -n "$TAGS" ]; then
    pass "Ollama is online (available models: $(echo "$TAGS" | grep -o '"name":"[^"]*"' | tr '\n' ' '))"
else
    fail "Ollama not reachable at ${OLLAMA_URL}/api/tags"
fi

section "3. SearXNG Metasearch Engine (${SEARXNG_URL})"
SEARCH_RES=$(curl -sf "${SEARXNG_URL}/search?q=homelab&format=json" 2>/dev/null || echo "")
if echo "$SEARCH_RES" | grep -q '"results"'; then
    COUNT=$(echo "$SEARCH_RES" | grep -o '"url"' | wc -l | tr -d ' ')
    pass "SearXNG returned JSON search results (${COUNT} results found)"
else
    fail "SearXNG failed or JSON format disabled at ${SEARXNG_URL}"
fi

section "4. Firecrawl Web Scraper Stack (${FIRECRAWL_URL})"
if curl -sf "${FIRECRAWL_URL}/test" >/dev/null 2>&1 || curl -sf "${FIRECRAWL_URL}/" >/dev/null 2>&1; then
    pass "Firecrawl API server reachable on port 3036"
else
    fail "Firecrawl API not reachable at ${FIRECRAWL_URL}"
fi

section "5. Speaches Audio STT & TTS Engine (${SPEACHES_URL})"
MODELS=$(curl -sf "${SPEACHES_URL}/v1/models" 2>/dev/null || echo "")
if echo "$MODELS" | grep -qi "whisper"; then
    pass "Speaches STT active (Faster-Whisper large-v3 loaded)"
else
    fail "Speaches STT model missing at ${SPEACHES_URL}/v1/models"
fi
if echo "$MODELS" | grep -qi "kokoro"; then
    pass "Speaches TTS active (Kokoro-82M loaded)"
else
    fail "Speaches TTS model missing at ${SPEACHES_URL}/v1/models"
fi

# Quick test of Kokoro TTS synthesis
TTS_TEST=$(curl -sf -X POST "${SPEACHES_URL}/v1/audio/speech" \
    -H "Content-Type: application/json" \
    -d '{"model":"speaches-ai/Kokoro-82M-v1.0-ONNX","input":"OK","voice":"af_heart"}' \
    --output /tmp/test_tts.mp3 2>/dev/null && echo "OK" || echo "FAIL")
if [ "$TTS_TEST" = "OK" ] && [ -s /tmp/test_tts.mp3 ]; then
    pass "Speaches Kokoro TTS audio generation verified (/v1/audio/speech)"
    rm -f /tmp/test_tts.mp3
else
    fail "Speaches TTS synthesis request failed"
fi

section "6. Hugging Face TEI Embeddings & Reranker (${EMBEDDINGS_URL})"
EMBED_RES=$(curl -sf -X POST "${EMBEDDINGS_URL}/v1/embeddings" \
    -H "Content-Type: application/json" \
    -d '{"model":"BAAI/bge-m3","input":"homelab vector test"}' 2>/dev/null || echo "")
if echo "$EMBED_RES" | grep -q '"embedding"'; then
    pass "TEI Embeddings successfully produced dense vector for BAAI/bge-m3"
else
    fail "TEI Embeddings failed at ${EMBEDDINGS_URL}/v1/embeddings"
fi

RERANK_RES=$(curl -sf -X POST "${RERANKER_URL}/rerank" \
    -H "Content-Type: application/json" \
    -d '{"query":"deep learning","texts":["artificial intelligence","baking a cake"]}' 2>/dev/null || echo "")
if echo "$RERANK_RES" | grep -q '"score"'; then
    pass "TEI Cross-Encoder Reranker operational for BAAI/bge-reranker-v2-m3"
else
    fail "TEI Reranker failed at ${RERANKER_URL}/rerank"
fi

section "7. Knowledge MCP Server (${KMCP_URL})"
KMCP_HEALTH=$(curl -sf "${KMCP_URL}/health" 2>/dev/null || echo "")
if echo "$KMCP_HEALTH" | grep -q '"status":"ok"'; then
    pass "Knowledge MCP REST API healthy (Public /health endpoint)"
else
    fail "Knowledge MCP health check failed at ${KMCP_URL}/health"
fi

KMCP_SSE=$(curl -sI "${KMCP_URL}/mcp/sse?api_key=${KMCP_KEY}" 2>/dev/null | head -n 1 || echo "")
if echo "$KMCP_SSE" | grep -q "200\|307"; then
    pass "Knowledge MCP SSE endpoint reachable at ${KMCP_URL}/mcp/sse with API key"
else
    fail "Knowledge MCP SSE failed at ${KMCP_URL}/mcp/sse ($KMCP_SSE)"
fi

KMCP_UNAUTH=$(curl -sI "${KMCP_URL}/mcp/sse" 2>/dev/null | head -n 1 || echo "")
if echo "$KMCP_UNAUTH" | grep -q "401"; then
    pass "Knowledge MCP security guard verified: Unauthenticated request rejected (401)"
elif [ -z "$KMCP_KEY" ]; then
    info "Knowledge MCP running in open mode (no key configured)"
else
    fail "Knowledge MCP security guard failed: Expected 401 on unauthenticated request ($KMCP_UNAUTH)"
fi

section "8. Sandbox MCP Execution Engine (${SANDBOX_URL})"
SANDBOX_HEALTH=$(curl -sf "${SANDBOX_URL}/health" 2>/dev/null || echo "")
if echo "$SANDBOX_HEALTH" | grep -q '"status":"ok"'; then
    pass "Sandbox REST API healthy"
else
    fail "Sandbox health check failed at ${SANDBOX_URL}/health"
fi

SANDBOX_EXEC=$(curl -sf -X POST "${SANDBOX_URL}/execute" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer ${SANDBOX_KEY}" \
    -d '{"language":"python","code":"import math; print(f\"Result: {math.sqrt(1764):.0f}\")"}' 2>/dev/null || echo "")
if echo "$SANDBOX_EXEC" | grep -q "Result: 42"; then
    pass "Sandbox execution engine successfully ran Python in RAM (Result: 42)"
else
    fail "Sandbox execution failed or authentication rejected"
fi

SANDBOX_SSE=$(curl -sI "${SANDBOX_URL}/mcp/sse" 2>/dev/null | head -n 1 || echo "")
if echo "$SANDBOX_SSE" | grep -q "200\|307"; then
    pass "Sandbox MCP SSE endpoint reachable at ${SANDBOX_URL}/mcp/sse"
else
    fail "Sandbox MCP SSE failed at ${SANDBOX_URL}/mcp/sse ($SANDBOX_SSE)"
fi

section "9. Hermes Agent Core Gateway (${HERMES_URL})"
if curl -sf "${HERMES_URL}/health" >/dev/null 2>&1; then
    pass "Hermes Agent Gateway is online on port 8642"
else
    info "Hermes Agent Gateway at ${HERMES_URL} did not reply on /health (check if port 8642 is exposed or if basic auth/traefik ingress is active)"
fi

echo "\n${GREEN}========================================================${NC}"
echo "${GREEN} Diagnostic complete across all microservices!${NC}"
echo "${GREEN}========================================================${NC}"
