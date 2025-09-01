#!/usr/bin/env python3
import asyncio
import json
import subprocess
import sys
from pathlib import Path

async def test_binary():
    # Load template
    with open('ex.json', 'r') as f:
        template = json.load(f)

    binary_path = Path(__file__).parent / "mcp_secrets" / "dialog_bin" / "macos_dialog"
    print(f"Testing binary: {binary_path}")
    print(f"Binary exists: {binary_path.exists()}")
    print(f"Binary executable: {binary_path.stat().st_mode & 0o111}")

    # Try the current method (passing JSON as arg)
    print("\n=== Testing current method (arg) ===")
    try:
        process = await asyncio.create_subprocess_exec(
            str(binary_path), json.dumps(template),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        print(f"Return code: {process.returncode}")
        print(f"Stdout: {stdout.decode()}")
        print(f"Stderr: {stderr.decode()}")
    except Exception as e:
        print(f"Error: {e}")

    # Try with stdin
    print("\n=== Testing with stdin ===")
    try:
        process = await asyncio.create_subprocess_exec(
            str(binary_path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            stdin=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate(input=json.dumps(template).encode())
        print(f"Return code: {process.returncode}")
        print(f"Stdout: {stdout.decode()}")
        print(f"Stderr: {stderr.decode()}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_binary())
