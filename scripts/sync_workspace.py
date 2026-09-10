#!/usr/bin/env python3
"""
Homelab Smart Knowledge Walker & Incremental Sync Engine
-------------------------------------------------------
Recursively walks /workspace, computes SHA-256 hashes, skips unchanged files (<1ms),
and indexes new/modified documents, code, images, and audio into Qdrant via Knowledge MCP.
"""

import os
import sys
import json
import time
import base64
import hashlib
from pathlib import Path
import urllib.request
import urllib.parse
from typing import Dict, Any, List

def compute_sha256(file_path: Path) -> str:
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def sync_workspace(
    target_dir: str = "/workspace",
    server_url: str = "http://knowledge-mcp:8095",
    collection: str = "workspace",
    cache_file: str = ".knowledge_cache.json",
    extensions: List[str] = None,
    api_key: str = None
):
    base_path = Path(target_dir).resolve()
    if not base_path.exists():
        print(f"❌ Error: Target directory '{target_dir}' does not exist.")
        sys.exit(1)

    cache_path = base_path / cache_file
    state: Dict[str, Any] = {}
    if cache_path.exists():
        try:
            state = json.loads(cache_path.read_text(encoding="utf-8"))
        except Exception:
            state = {}

    allowed_exts = set(extensions or [
        ".pdf", ".md", ".txt", ".py", ".json", ".yaml", ".yml",
        ".sh", ".c", ".cpp", ".rs", ".java", ".docx", ".xlsx",
        ".png", ".jpg", ".jpeg", ".webp", ".mp3", ".wav", ".m4a"
    ])

    req_headers = {"Content-Type": "application/json"}
    if api_key:
        req_headers["Authorization"] = f"Bearer {api_key}"

    print("=" * 70)
    print(f"🚀 [Knowledge Walker] Scanning '{base_path}' -> Collection: '{collection}'")
    print(f"   MCP Endpoint: {server_url}/index-file")
    print("=" * 70)

    current_files = {}
    indexed_count = 0
    skipped_count = 0
    failed_count = 0

    # 1. Walk filesystem
    for root, dirs, files in os.walk(base_path):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ["node_modules", "venv", "__pycache__", "build", "dist", "output"]]
        for f in files:
            if f.startswith(".") or f == cache_file:
                continue
            fp = Path(root) / f
            if fp.suffix.lower() in allowed_exts:
                current_files[str(fp.resolve())] = fp

    # 2. Check for new or modified files
    for file_str, fp in current_files.items():
        try:
            file_hash = compute_sha256(fp)
            cached = state.get(file_str, {})

            if cached.get("sha256") == file_hash:
                skipped_count += 1
                continue

            print(f"⚙️  Indexing: {fp.name} ({fp.stat().st_size / 1024:.1f} KB)...")
            file_bytes = fp.read_bytes()
            b64_content = base64.b64encode(file_bytes).decode("utf-8")
            payload = json.dumps({
                "file_path": file_str,
                "collection": collection,
                "tags": [fp.suffix.replace(".", "")],
                "file_content_base64": b64_content
            }).encode("utf-8")

            req = urllib.request.Request(
                f"{server_url}/index-file",
                data=payload,
                headers=req_headers
            )
            with urllib.request.urlopen(req, timeout=300) as resp:
                res = json.loads(resp.read().decode("utf-8"))
                result_msg = res.get("result", "")
                if "❌" in result_msg or "Failed" in result_msg:
                    print(f"   ⚠️ Warning: {result_msg}")
                    failed_count += 1
                else:
                    state[file_str] = {
                        "sha256": file_hash,
                        "indexed_at": time.time(),
                        "size_bytes": fp.stat().st_size
                    }
                    indexed_count += 1
                    print(f"   ✅ Indexed: {fp.name}")

        except Exception as e:
            print(f"   ❌ Error processing {fp.name}: {str(e)}")
            failed_count += 1

    # 3. Clean up deleted files from state
    deleted_paths = [p for p in state.keys() if p not in current_files]
    for dp in deleted_paths:
        try:
            print(f"🗑️  Removing deleted file from Qdrant: {Path(dp).name}...")
            payload = json.dumps({
                "file_path": dp,
                "collection": collection
            }).encode("utf-8")
            req = urllib.request.Request(
                f"{server_url}/delete-file",
                data=payload,
                headers=req_headers
            )
            urllib.request.urlopen(req, timeout=30)
            del state[dp]
        except Exception as e:
            print(f"   ⚠️ Could not delete {dp} from Qdrant: {e}")

    # 4. Save updated state cache
    try:
        cache_path.write_text(json.dumps(state, indent=2), encoding="utf-8")
    except Exception as e:
        print(f"⚠️ Warning: Could not save cache to {cache_path}: {e}")

    print("=" * 70)
    print(f"✨ [Knowledge Walker] Finished! Indexed: {indexed_count} | Skipped: {skipped_count} | Failed: {failed_count}")
    print("=" * 70)

if __name__ == "__main__":
    target = os.environ.get("WORKSPACE_DIR", "/workspace")
    server = os.environ.get("KNOWLEDGE_MCP_HTTP_URL", "http://knowledge-mcp:8095")
    coll = os.environ.get("QDRANT_COLLECTION", "workspace")
    key = os.environ.get("KNOWLEDGE_MCP_API_KEY", "")
    sync_workspace(target_dir=target, server_url=server, collection=coll, api_key=key)
