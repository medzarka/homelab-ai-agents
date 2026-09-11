"""
WhatsApp Messaging & File Delivery Tool for Hermes Agent.
Enables the agent to deliver text messages, documents, PDFs, and media attachments
directly to Mohamed Zarka on WhatsApp.
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict

from tools.registry import registry, tool_error

logger = logging.getLogger(__name__)

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


def check_whatsapp_requirements() -> bool:
    """Always available when WhatsApp platform is configured."""
    return True


def _resolve_file_path(file_path: str) -> Path | None:
    """Resolve file path against absolute path or workspace directory."""
    raw = Path(file_path.strip())
    if raw.is_file():
        return raw.resolve()

    # Try resolving in workspace
    ws = Path("/workspace") / file_path.strip().lstrip("/")
    if ws.is_file():
        return ws.resolve()

    # Try resolving in output
    out = Path("/output") / file_path.strip().lstrip("/")
    if out.is_file():
        return out.resolve()

    return None


def send_whatsapp_handler(args: Dict[str, Any], **kwargs) -> str:
    message = (args.get("message") or "").strip()
    raw_file_path = (args.get("file_path") or "").strip()
    recipient = (args.get("recipient") or "").strip()

    if not message and not raw_file_path:
        return tool_error("At least one of 'message' or 'file_path' must be provided.")

    resolved_path = None
    if raw_file_path:
        resolved_path = _resolve_file_path(raw_file_path)
        if resolved_path is None:
            return tool_error(
                f"File not found: '{raw_file_path}'. Checked exact path, /workspace/{raw_file_path}, and /output/{raw_file_path}."
            )

    # Determine WhatsApp destination target
    default_home = os.environ.get("WHATSAPP_HOME_CHANNEL", "Mohamed Zarka")
    target_ref = recipient if recipient else default_home
    target = f"whatsapp:{target_ref}"

    # Build message body. If file is present, prefix with MEDIA:<path> directive
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
        return tool_error(f"Failed to dispatch to WhatsApp: {str(e)}")


registry.register(
    name="send_whatsapp",
    toolset="whatsapp",
    schema=WHATSAPP_SCHEMA,
    handler=send_whatsapp_handler,
    check_fn=check_whatsapp_requirements,
    emoji="💬"
)

# Ensure send_whatsapp is treated as a core Hermes tool (never deferred behind tool_search)
try:
    import toolsets
    if "whatsapp" not in toolsets.TOOLSETS:
        toolsets.TOOLSETS["whatsapp"] = toolsets._ts("WhatsApp messaging and file delivery", ["send_whatsapp"])
    if "send_whatsapp" not in toolsets._HERMES_CORE_TOOLS:
        toolsets._HERMES_CORE_TOOLS.append("send_whatsapp")
except Exception:
    pass

