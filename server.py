"""Pine SDK MCP Server."""
from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse

# Load environment variables from .env (if present) before reading os.getenv
load_dotenv()

SERVER_NAME = "pine-sdk-mcp"
SERVER_HOST = os.getenv("MCP_HOST", "0.0.0.0")
SERVER_PORT = int(os.getenv("MCP_PORT", "8080"))
TRANSPORT = os.getenv("MCP_TRANSPORT", "streamable-http")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

DOCS_ROOT: Path = Path(__file__).parent / "api-docs"

logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(SERVER_NAME)

mcp = FastMCP(name=SERVER_NAME, host=SERVER_HOST, port=SERVER_PORT)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _discover_apis() -> dict[str, Path]:
    """Scan DOCS_ROOT and return a mapping of apiName -> markdown file path."""
    if not DOCS_ROOT.exists():
        logger.warning("Docs root does not exist: %s", DOCS_ROOT)
        return {}
    apis: dict[str, Path] = {}
    for md_file in DOCS_ROOT.rglob("*.md"):
        if md_file.stem in apis:
            logger.warning("Duplicate API name '%s' at %s", md_file.stem, md_file)
            continue
        apis[md_file.stem] = md_file
    logger.debug("Discovered %d API doc(s)", len(apis))
    return apis


def _text_response(text: str) -> dict[str, Any]:
    """Build a standard MCP text-content response."""
    return {"content": [{"type": "text", "text": text}]}



# ---------------------------------------------------------------------------
# Tool registration
# ---------------------------------------------------------------------------
def register_api_docs_tools(mcp: FastMCP) -> None:
    """Register API documentation tools on the FastMCP server."""

    @mcp.tool(
        name="list_pinelabs_apis",
        description=(
            "List all available Pine Labs SDK APIs, grouped by category "
            "(e.g. 'transaction/doTransaction'). Call this first to "
            "discover valid api_name values for 'get_api_documentation'."
        ),
    )
    async def list_pinelabs_apis() -> dict[str, Any]:
        """Return the list of all available Pine SDK APIs, grouped by category."""
        logger.info("Tool invoked: list_pinelabs_apis")
        apis = _discover_apis()
        if not apis:
            return _text_response("No APIs found")
        listing = sorted(f"{p.parent.name}/{n}" for n, p in apis.items())
        logger.info("list_pinelabs_apis returning %d entries", len(listing))
        return _text_response("\n".join(listing))

    @mcp.tool(
        name="get_api_documentation",
        description=(
            "Fetch the OFFICIAL Pine Labs SDK documentation for a specific "
            "API by api_name. This is the SINGLE SOURCE OF TRUTH for the "
            "Pine Labs SDK.\n\n"
            "STRICT RULES — you MUST follow these when answering the user:\n"
            "1. Use ONLY the content returned by this tool. Do NOT add, "
            "infer, translate, or invent any API names, parameters, return "
            "types, error variants, or code examples that are not present "
            "in the returned markdown.\n"
            "2. The documentation lists supported languages explicitly "
            "(e.g. kotlin, python, swift). If the user asks about a "
            "language NOT listed (e.g. C++, Java, JavaScript, Go, Rust), "
            "reply that Pine Labs SDK does not document that language and "
            "stop — do NOT generate sample code in unsupported languages.\n"
            "3. If the user asks for a parameter, error, or behavior that "
            "is not in the returned doc, say 'not documented' instead of "
            "guessing.\n"
            "4. Quote field names, types and error variants verbatim from "
            "the returned JSON spec.\n"
            "5. If unsure which api_name to use, call 'list_pinelabs_apis' "
            "first; never guess an api_name."
        ),
    )
    async def get_api_documentation(api_name: str) -> dict[str, Any]:
        """Return the markdown documentation for the given Pine SDK API."""
        logger.info("Tool invoked: get_api_documentation(api_name=%r)", api_name)
        if not api_name or not api_name.strip():
            return _text_response("Error: 'api_name' is required and cannot be empty.")
        apis = _discover_apis()
        md_path = apis.get(api_name)
        if md_path is None:
            available = ", ".join(sorted(apis)) or "none"
            logger.warning("API not found: %s", api_name)
            return _text_response(
                f"API '{api_name}' not found. Available APIs: {available}"
            )
        try:
            doc = md_path.read_text(encoding="utf-8")
        except OSError as exc:
            logger.exception("Failed to read doc file %s", md_path)
            return _text_response(
                f"Error reading documentation for '{api_name}': {exc}"
            )
        logger.info("Returning %d chars of documentation for '%s'", len(doc), api_name)

        wrapped = (
            "=== AUTHORITATIVE PINE LABS SDK DOCUMENTATION ===\n"
            f"api_name: {api_name}\n"
            f"source_file: {md_path.relative_to(DOCS_ROOT.parent).as_posix()}\n"
            "\n"
            "RULES FOR THE ASSISTANT (do NOT ignore):\n"
            "- Answer ONLY using facts present below. If a detail is "
            "missing, say it is not documented.\n"
            "- The 'examples' array enumerates every supported language. "
            "Do NOT produce code in any language not listed there "
            "(e.g. C++, Java, JS, Go, Rust are NOT supported).\n"
            "- Do NOT invent parameter names, error variants, or return "
            "types that are not in the spec below.\n"
            "- Quote identifiers verbatim.\n"
            "\n"
            "--- BEGIN DOCUMENTATION ---\n"
            f"{doc}\n"
            "--- END DOCUMENTATION ---\n"
        )
        return _text_response(wrapped)


# Register tools on the module-level mcp instance
register_api_docs_tools(mcp)


# ---------------------------------------------------------------------------
# Friendly HTTP routes (so plain browser GETs don't 404)
# ---------------------------------------------------------------------------
_INFO_PAYLOAD = {
    "server": SERVER_NAME,
    "status": "ok",
    "transport": "streamable-http",
    "endpoint": "/mcp",
    "note": (
        "This is an MCP server. POST a JSON-RPC 'initialize' request to "
        "/mcp with header 'Accept: application/json, text/event-stream'."
    ),
}


@mcp.custom_route("/", methods=["GET"])
async def root(_: Request) -> JSONResponse:
    return JSONResponse(_INFO_PAYLOAD)


@mcp.custom_route("/health", methods=["GET"])
async def health(_: Request) -> JSONResponse:
    return JSONResponse({"status": "ok"})


def main() -> None:
    logger.info(
        "Starting %s on %s:%d (transport=%s, docs=%s)",
        SERVER_NAME, SERVER_HOST, SERVER_PORT, TRANSPORT, DOCS_ROOT,
    )
    mcp.run(transport=TRANSPORT)


if __name__ == "__main__":
    main()