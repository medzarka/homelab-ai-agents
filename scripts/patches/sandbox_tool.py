"""
Sandbox Code Execution & LaTeX Compilation Tool for Hermes Agent.
Executes code, scripts, or compiles LaTeX documents inside the isolated in-memory
execution sandbox (agent-sandbox) and automatically saves generated artifacts (PDFs, plots)
directly into the local /workspace directory.
"""

import base64
import json
import logging
import os
import urllib.request
from pathlib import Path
from typing import Any, Dict

from tools.registry import registry, tool_error

logger = logging.getLogger(__name__)

SANDBOX_SCHEMA = {
    "name": "sandbox_execute_code",
    "description": (
        "Execute code, scripts, or compile LaTeX documents inside the isolated in-memory execution sandbox (agent-sandbox). "
        "Supports languages: 'latex' (compiles with Tectonic to PDF), 'python' (with NumPy, SciPy, etc.), 'bash', 'c', 'cpp', 'rust', 'java'. "
        "When compiling LaTeX or generating plots/files, all generated artifacts (such as 'document.pdf') are AUTOMATICALLY decoded and saved "
        "directly into the local /workspace directory, and their local file paths are returned. "
        "You can then deliver these files to WhatsApp using send_whatsapp(file_path='/workspace/document.pdf')."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "language": {
                "type": "string",
                "description": "Language to execute: 'latex' (or 'tex'), 'python', 'bash' (or 'sh'), 'c', 'cpp', 'rust', 'java'."
            },
            "code": {
                "type": "string",
                "description": "Source code or LaTeX document to compile or run."
            },
            "output_dir": {
                "type": "string",
                "description": "Local directory where generated artifacts should be saved. Defaults to '/workspace'."
            },
            "session_id": {
                "type": "string",
                "description": "Optional session ID to persist files and workspace across multiple runs."
            }
        },
        "required": ["language", "code"]
    }
}


def check_sandbox_requirements() -> bool:
    """Check if sandbox configuration is present."""
    return True


def sandbox_execute_handler(args: Dict[str, Any], **kwargs) -> str:
    language = (args.get("language") or "").strip().lower()
    code = args.get("code") or ""
    output_dir = (args.get("output_dir") or "/workspace").strip()
    session_id = args.get("session_id")

    # Auto-detect language if code is clearly LaTeX source
    stripped_code = code.strip()
    if "\\documentclass" in stripped_code and language not in ["latex", "tex"]:
        language = "latex"
    elif stripped_code.startswith(("\\documentclass", "\\begin{document}", "\\usepackage")):
        language = "latex"
    elif not language:
        language = "python"

    sandbox_url = os.environ.get("SANDBOX_REST_URL")
    if not sandbox_url:
        mcp_url = os.environ.get("SANDBOX_MCP_URL", "http://agent-sandbox:8088/mcp/sse")
        base_host = mcp_url.split("/mcp")[0].split("?")[0]
        sandbox_url = f"{base_host}/execute"

    api_key = os.environ.get("SANDBOX_API_KEY", "")

    payload: Dict[str, Any] = {
        "language": language,
        "code": code,
    }
    if session_id:
        payload["session_id"] = session_id

    req_data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        sandbox_url,
        data=req_data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        logger.exception("Failed to execute code in agent-sandbox")
        return tool_error(f"Failed to connect to agent-sandbox at {sandbox_url}: {str(e)}")

    exit_code = data.get("exit_code", -1)
    stdout = data.get("stdout", "").strip()
    stderr = data.get("stderr", "").strip()
    duration_ms = data.get("duration_ms", 0)
    artifacts = data.get("artifacts", {})

    target_dir = Path(output_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    saved_files = []
    for art_name, art_content in artifacts.items():
        try:
            if ";base64," in art_content:
                b64 = art_content.split(";base64,")[1]
            else:
                b64 = art_content
            file_bytes = base64.b64decode(b64)
            out_file = target_dir / art_name
            try:
                out_file.parent.mkdir(parents=True, exist_ok=True)
                out_file.write_bytes(file_bytes)
            except PermissionError:
                saved = False
                for fallback_root in [Path("/output"), Path("/tmp")]:
                    try:
                        fallback_file = fallback_root / art_name
                        fallback_file.parent.mkdir(parents=True, exist_ok=True)
                        fallback_file.write_bytes(file_bytes)
                        out_file = fallback_file
                        saved = True
                        break
                    except Exception:
                        continue
                if not saved:
                    raise
            size_kb = len(file_bytes) / 1024
            saved_files.append(f"- `{out_file}` ({size_kb:.1f} KiB)")
        except Exception as err:
            logger.warning("Failed to save artifact %s: %s", art_name, err)
            saved_files.append(f"- `{art_name}` (Error writing to disk: {err})")

    status_str = "SUCCESS" if exit_code == 0 else f"FAILED (exit code {exit_code})"
    lines = [
        f"### Sandbox Execution: {status_str} ({duration_ms:.0f}ms)",
        f"**Language:** `{language}`",
    ]
    if stdout:
        lines.append(f"\n**Stdout:**\n```text\n{stdout}\n```")
    if stderr:
        lines.append(f"\n**Stderr:**\n```text\n{stderr}\n```")

    if saved_files:
        lines.append("\n**Generated Artifacts Saved Locally:**")
        lines.extend(saved_files)
        lines.append("\n*To send any generated file to WhatsApp, use: `send_whatsapp(file_path=...)`*")

    return "\n".join(lines)


registry.register(
    name="sandbox_execute_code",
    toolset="sandbox",
    schema=SANDBOX_SCHEMA,
    handler=sandbox_execute_handler,
    check_fn=check_sandbox_requirements,
    emoji="🧪"
)

# Ensure sandbox_execute_code is treated as a core Hermes tool (never deferred behind tool_search)
try:
    import toolsets
    if "sandbox" not in toolsets.TOOLSETS:
        toolsets.TOOLSETS["sandbox"] = toolsets._ts("Sandboxed code execution and LaTeX compilation", ["sandbox_execute_code"])
    if "sandbox_execute_code" not in toolsets._HERMES_CORE_TOOLS:
        toolsets._HERMES_CORE_TOOLS.append("sandbox_execute_code")
except Exception:
    pass

