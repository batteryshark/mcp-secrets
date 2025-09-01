import os

from fastmcp import FastMCP
from fastmcp import Context
from fastmcp.exceptions import ToolError

from mcp_secrets import secrets_manager
from mcp_secrets.fetcher import fetch_secrets

### SERVER SPECIFIC SECRETS INFO ###
SECRETS_INFO = {
    "api_key": {
        "label": "API Key",
        "field_type": "password",
        "required": True,
        "help_text": "Your secret API key from the service dashboard"
    },
    "endpoint": {
        "label": "API Endpoint",
        "field_type": "url",
        "default": "https://api.example.com",
        "required": True,
        "help_text": "The base URL for API requests"
    },
    "timeout": {
        "label": "Request Timeout (seconds)",
        "field_type": "text",
        "default": "30",
        "required": False,
        "help_text": "How long to wait for API responses"
    }
}



# Initialize MCP server
mcp = FastMCP(
    name="MCP Secrets Example",
    instructions=(
        """
        Reference implementation for MCP servers using secrets management.

        This server demonstrates best practices for:
        - Secure credential storage and retrieval
        - Interactive credential elicitation
        - Authentication middleware
        - Modular tool organization

        Use setup_api_credentials to configure your API credentials,
        then use check_api_credentials to verify they're stored correctly,
        and make_api_request to test API integration.
        """
    ),
)

# Initialize secrets manager for this server
secrets_manager.initialize(mcp.name)

# Register tools
@mcp.tool
async def some_tool_that_needs_secrets(ctx: Context) -> str:
    """
    This is a tool that needs secrets and will demonstrate the credential handling.
    """
    all_secrets_present = secrets_manager.ensure_secrets(["api_key","endpoint","timeout"])
    if all_secrets_present:
        ctx.info("All secrets present")
    else:
        ctx.info("Some secrets are missing")
        status,message = await fetch_secrets(ctx, SECRETS_INFO)
        if not status:
            raise ToolError(message)
        
        ctx.info(message)
        
    return "Secrets Tool OK!"

@mcp.tool
async def clear_secrets(ctx: Context) -> str:
    """
    Reset the secrets manager.
    """
    secrets_manager.clear_secrets()
    return "OK!"



def main():
    """Entry point function for running the server."""
    mcp_host = os.getenv("HOST", "127.0.0.1")
    mcp_port = os.getenv("PORT", None)
    if mcp_port:
        mcp.run(port=int(mcp_port), host=mcp_host, transport="streamable-http")
    else:
        mcp.run()


if __name__ == "__main__":
    main()