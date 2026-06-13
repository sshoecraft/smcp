"""Ask SMCP Server - exposes one external LLM as a single 'query' MCP tool."""

import logging
import sys
from typing import Any, Dict, Optional

import httpx
from mcp.server.fastmcp import FastMCP
from smcp import handshake as smcp_handshake, check_credentials_schema

from ask_smcp_server.clients import ask as dispatch_ask, VENDOR_DISPLAY
from ask_smcp_server.config import AskConfig

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s - %(levelname)s] - %(message)s",
)
logger = logging.getLogger(__name__)

CREDENTIALS_SCHEMA = {
    "required": {
        "ASK_TYPE": "Vendor type — one of: gemini, openai, anthropic",
        "ASK_API_KEY": "API key for the selected vendor",
    },
    "optional": {
        "ASK_MODEL": "Override the type's default model (gemini: gemini-3.1-flash-lite, openai: gpt-5.4-nano, anthropic: claude-haiku-4-5)",
        "ASK_BASE_URL": "Override the vendor's default endpoint (lets openai-type cover Grok/xAI, vLLM, etc.)",
        "ASK_MAX_TOKENS": "Default max_tokens for completions (default: 65536). Note: this is the per-response output cap (max_output_tokens), not the model's context window.",
        "ASK_SYSTEM": "Default system prompt (default: 'You are a helpful AI assistant.')",
        "ASK_TIMEOUT": "HTTP request timeout in seconds (default: 600). Deep reasoning calls can take minutes.",
        "ASK_THINKING_LEVEL": "Gemini-only. Thinking effort: minimal, low, medium, high (default: high). Lower values reclaim visible-output budget at the cost of reasoning depth.",
        "ASK_REASONING_EFFORT": "OpenAI reasoning-model-only (gpt-5/o-series). Reasoning effort: minimal, low, medium, high (default: unset = model default). Lower values reclaim visible-output budget at the cost of reasoning depth.",
        "ASK_AUTO_CONTINUE": "All vendors. If the response hits the output cap (MAX_TOKENS/length/max_tokens) with visible text, issue a single bounded continuation call (default: 1). Set 0 to disable.",
        "LOG_LEVEL": "Logging level (default: INFO)",
    },
}


def create_server(config: AskConfig, http: httpx.AsyncClient) -> FastMCP:
    """Create and configure the MCP server with a single 'query' tool."""
    mcp = FastMCP("AskSMCP")

    vendor = VENDOR_DISPLAY.get(config.type, config.type)
    description = (
        f"Send a prompt to {vendor} ({config.model}) and return its reply. "
        f"Use this when you want a second opinion or different perspective from {vendor}."
    )

    @mcp.tool(name="query", description=description)
    async def query(
        prompt: str,
        system: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
    ) -> Dict[str, str]:
        """Send a prompt to the configured LLM and return its reply.

        Args:
            prompt: The question or task to send.
            system: System prompt override (default: configured ASK_SYSTEM).
            model: Per-call model override (default: configured ASK_MODEL).
            max_tokens: Per-call max_tokens override (default: configured ASK_MAX_TOKENS).
        """
        if not prompt or not prompt.strip():
            return {"success": "false", "error": "prompt is required", "model": model or config.model}

        result = await dispatch_ask(
            config,
            http,
            prompt=prompt,
            system=system if system is not None else config.system,
            model=model or config.model,
            max_tokens=max_tokens if max_tokens else config.max_tokens,
        )
        return {key: str(value) for key, value in result.items()}

    return mcp


def main():
    """Main entry point for the Ask SMCP service."""
    check_credentials_schema(CREDENTIALS_SCHEMA)

    try:
        creds = smcp_handshake()

        log_level = creds.get("LOG_LEVEL", "INFO")
        logging.getLogger().setLevel(getattr(logging, log_level.upper(), logging.INFO))

        config = AskConfig.from_smcp_creds(creds)
        logger.info(
            f"Ask SMCP service starting: type={config.type} model={config.model} "
            f"base_url={config.base_url} timeout={config.timeout}s "
            f"thinking_level={config.thinking_level} auto_continue={config.auto_continue}"
            f" reasoning_effort={config.reasoning_effort}"
        )

        http = httpx.AsyncClient(timeout=config.timeout)
        mcp = create_server(config, http)
        mcp.run(transport="stdio")

    except ValueError as exc:
        logger.error(f"Configuration error: {exc}")
        sys.exit(2)
    except Exception as exc:
        logger.error(f"Error starting Ask SMCP service: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
