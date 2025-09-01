import asyncio
from fastmcp import Context
from mcp_secrets import secrets_manager
from typing import Dict, Any
import random 
import string

from .ui_handler import get_async_ui_handler


async def fetch_secrets(ctx: Context, secrets_info: Dict[str, Any]):
    """Fetch secrets using async dialog flow."""

    # Prepare fields without showing existing secret values for security
    fields = []
    for field_name in secrets_info.keys():
        field_copy = secrets_info[field_name].copy()
        field_copy["name"] = field_name
        # Don't pre-populate with existing values for security reasons
        fields.append(field_copy)

    verification_code = generate_verification_code()
    template = {
        "title": f"MCP Secrets for {secrets_manager.server_name}",
        "description": f"Verification Code: {verification_code}\n\nConfirm this code matches what's displayed in your MCP host before proceeding.",
        "fields": fields
    }

    # It's Go-Time!

    # 1. Spawn dialog FIRST (non-blocking)
    ui_handler = get_async_ui_handler()
    dialog_task = asyncio.create_task(ui_handler.collect_secrets_async(template))
    import json
    await ctx.info(json.dumps(template))
    # 2. THEN do MCP elicitation (keeps connection alive)
    await ctx.info("🔑 A credential dialog should appear. Fill it out, then click 'Continue' below.")
    # Please Drink Verification Can.
    result = await ctx.elicit(
        message="Secrets Requested [Code: " + verification_code + "] - Click 'Continue' when finished",
        response_type=None
    )
    
    if result.action != "accept":
        # Cancel the dialog task
        dialog_task.cancel()
        return False, "❌ Secrets fetch cancelled by user."
    
    # 3. Now await the dialog results
    try:
        secrets = await dialog_task
    except asyncio.CancelledError:
        return False, "❌ Dialog cancelled."
    
    if not secrets:
        return False, "❌ Dialog was cancelled by user."
    
    # 4. Store the secrets (only update if new value provided)
    for field_name, value in secrets.items():
        if value:  # Only update secrets with new non-empty values
            secrets_manager.store_secret(field_name, value)
    
    # 5. Return success message
    stored_count = len([v for v in secrets.values() if v])
    return True, f"✅ Successfully stored {stored_count} credentials."
        


# -- Utilities for Code Generation --
def generate_verification_code() -> str:
    """Generate a random 4-4 alphanumeric verification code.

    Returns:
        A verification code in format XXXX-XXXX (e.g., "XQ7K-9M2P")
    """
    chars = string.ascii_uppercase + string.digits
    part1 = ''.join(random.choices(chars, k=4))
    part2 = ''.join(random.choices(chars, k=4))
    return f"{part1}-{part2}"


