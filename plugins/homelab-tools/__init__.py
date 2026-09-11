"""
Homelab Native Tools Plugin for Hermes Agent.
Provides:
1. sandbox_execute_code: Isolated multi-language code execution and LaTeX compilation in agent-sandbox.
2. send_whatsapp: Native WhatsApp message and document/media attachment delivery.
"""

from __future__ import annotations

import base64
import json
import logging
import os
import urllib.request
from pathlib import Path
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger("hermes.plugins.homelab_tools")

# ==============================================================================
# 1. SANDBOX EXECUTION TOOL (Python, Bash, C, C++, Java, Rust, LaTeX)
# ==============================================================================

SANDBOX_SCHEMA = {
    "name": "sandbox_execute_code",
    "description": (
        "Execute code, scripts, or compile LaTeX documents inside the isolated in-memory execution sandbox (agent-sandbox). "
        "Supports languages: 'latex' (compiles with Tectonic to PDF), 'python' (with NumPy, SciPy, etc.), 'bash' (or 'sh'), 'c', 'cpp', 'rust', 'java'. "
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


def _check_sandbox_available() -> bool:
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
        return f"Error: Failed to connect to agent-sandbox at {sandbox_url}: {str(e)}"

    exit_code = data.get("exit_code", -1)
    stdout = data.get("stdout", "").strip()
    stderr = data.get("stderr", "").strip()
    duration_ms = data.get("duration_ms", 0)
    artifacts = data.get("artifacts", {})

    target_dir = Path(output_dir)
    try:
        target_dir.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass

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
                # Fallback to /output or /tmp if target directory is restricted
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


# ==============================================================================
# 2. WHATSAPP DELIVERY TOOL
# ==============================================================================

WHATSAPP_SCHEMA = {
    "name": "send_whatsapp",
    "description": (
        "Send a message and/or a file attachment (PDF, image, document, audio) to Mohamed Zarka on WhatsApp. "
        "If 'file_path' is provided (e.g. '/workspace/document.pdf'), the file is sent as a native WhatsApp attachment. "
        "Use this tool whenever the user asks to send a message, PDF, plot, report, or file to their WhatsApp."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "message": {
                "type": "string",
                "description": "Text message or caption to accompany the message or file attachment."
            },
            "file_path": {
                "type": "string",
                "description": "Absolute path to a local file to send as an attachment (e.g. '/workspace/document.pdf'). Relative paths like 'document.pdf' will be resolved in /workspace."
            },
            "recipient": {
                "type": "string",
                "description": "Target recipient name, phone number, or JID. Defaults to Mohamed Zarka (the configured home channel)."
            }
        }
    }
}


def _check_whatsapp_available() -> bool:
    return True


def _resolve_file_path(file_path: str) -> Path | None:
    """Resolve file path against absolute path or standard directories."""
    raw = Path(file_path.strip())
    if raw.is_file():
        return raw.resolve()

    ws = Path("/workspace") / file_path.strip().lstrip("/")
    if ws.is_file():
        return ws.resolve()

    out = Path("/output") / file_path.strip().lstrip("/")
    if out.is_file():
        return out.resolve()

    tmp = Path("/tmp") / file_path.strip().lstrip("/")
    if tmp.is_file():
        return tmp.resolve()

    return None


def send_whatsapp_handler(args: Dict[str, Any], **kwargs) -> str:
    message = (args.get("message") or "").strip()
    raw_file_path = (args.get("file_path") or "").strip()
    recipient = (args.get("recipient") or "").strip()

    if not message and not raw_file_path:
        return "Error: At least one of 'message' or 'file_path' must be provided."

    resolved_path = None
    if raw_file_path:
        resolved_path = _resolve_file_path(raw_file_path)
        if resolved_path is None:
            return (
                f"Error: File not found: '{raw_file_path}'. "
                f"Checked exact path, /workspace/{raw_file_path}, /output/{raw_file_path}, and /tmp/{raw_file_path}."
            )

    default_home = os.environ.get("WHATSAPP_HOME_CHANNEL", "Mohamed Zarka")
    target_ref = recipient if recipient else default_home
    target = f"whatsapp:{target_ref}"

    body_parts = []
    if resolved_path:
        body_parts.append(f"MEDIA:{resolved_path}")
    if message:
        body_parts.append(message)

    formatted_message = "\n".join(body_parts)

    try:
        from tools.send_message_tool import send_message_tool
        result = send_message_tool({
            "action": "send",
            "target": target,
            "message": formatted_message
        })
        return result
    except Exception as e:
        logger.exception("Failed to dispatch message to WhatsApp")
        return f"Error: Failed to dispatch to WhatsApp: {str(e)}"


# ==============================================================================
# 3. PLUGIN REGISTRATION ENTRYPOINT
# ==============================================================================

def register(ctx) -> None:
    """Register homelab tools. Invoked automatically by Hermes PluginManager."""
    ctx.register_tool(
        name="sandbox_execute_code",
        toolset="sandbox",
        schema=SANDBOX_SCHEMA,
        handler=sandbox_execute_handler,
        check_fn=_check_sandbox_available,
        emoji="🧪"
    )
    ctx.register_tool(
        name="send_whatsapp",
        toolset="whatsapp",
        schema=WHATSAPP_SCHEMA,
        handler=send_whatsapp_handler,
        check_fn=_check_whatsapp_available,
        emoji="💬"
    )
    logger.info("Homelab tools plugin registered: sandbox_execute_code, send_whatsapp")
