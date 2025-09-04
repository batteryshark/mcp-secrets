#!/usr/bin/env python3
"""Async UI handler that spawns dialog and continues MCP flow."""

import os
import sys
import asyncio
import json
import platform
from pathlib import Path
from typing import Dict, Any, Optional
import logging

class AsyncUIHandler:
    """Async UI handler that spawns dialog without blocking MCP."""
    
    def __init__(self, handler_binary: Optional[str] = None):
        """Initialize with optional custom handler binary path."""
        self.handler_binary = handler_binary or self._get_default_binary()
    
    def _get_default_binary(self) -> str:
        """Get the best default binary for this platform."""
        base_path = Path(__file__).parent / "secrets_dialog" / "bin"

        # Platform-specific binaries (no dependencies!)
        if platform.system() == "Darwin":  # macOS
            return str(base_path / "macos_dialog")
        elif platform.system() == "Windows":
            return str(base_path / "windows_dialog.exe")
        else:  # Linux
            return str(base_path / "linux_dialog")

    async def collect_secrets_async(self, template: Dict[str, Any]) -> Optional[Dict[str, str]]:
        """Collect secrets using async subprocess.

        This spawns the dialog and returns immediately, allowing MCP to continue.
        The dialog runs independently and we await its completion.

        Args:
            template: The dialog template
            verification_code: The verification code to display in the dialog

        Returns:
            Collected secrets dict or None if cancelled
        """
        logging.info(f"Collecting secrets with template: {json.dumps(template)}")
        
        try:
            # Spawn the dialog process asynchronously
            process = await asyncio.create_subprocess_exec(
                self.handler_binary,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                stdin=asyncio.subprocess.PIPE
            )
            
            # Await completion (this is async, so MCP can continue other work)
            stdout, stderr = await process.communicate(input=json.dumps(template).encode())
            
            if process.returncode == 1:
                return None  # User cancelled
            elif process.returncode != 0:
                error_msg = stderr.decode().strip() if stderr else "Unknown error"
                raise Exception(f"UI dialog failed: {error_msg}")

            return json.loads(stdout.decode())
            
        except json.JSONDecodeError as e:
            raise Exception(f"Invalid JSON from dialog: {e}")
        except FileNotFoundError:
            raise Exception(f"Dialog binary not found: {self.handler_binary}")
        except Exception as e:
            raise Exception(f"Dialog error: {e}")
    

def get_async_ui_handler() -> AsyncUIHandler:
    """Get async UI handler with secure default binary selection."""
    # Always use default binary selection - no custom binaries for security
    return AsyncUIHandler()
