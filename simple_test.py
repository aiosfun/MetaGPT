#!/usr/bin/env python3
"""
Simple test to verify the core tool functions work
"""
import subprocess
import json
import platform
from pathlib import Path

WORKDIR = Path.cwd()
MAX_TOOL_RESULT_CHARS = 100_000

def safe_path(p: str) -> Path:
    """Ensure path is within workspace"""
    abs_path = (WORKDIR / str(p or "")).resolve()
    rel = abs_path.relative_to(WORKDIR) if abs_path.is_relative_to(WORKDIR) else None
    if rel is None:
        raise ValueError("Path escapes workspace")
    return abs_path

def clamp_text(s: str, n: int = MAX_TOOL_RESULT_CHARS) -> str:
    """Clamp text length"""
    if len(s) <= n:
        return s
    return s[:n] + f"\n\n...<truncated {len(s) - n} chars>"

def run_bash(command: str, timeout_ms: int = 30000) -> str:
    """Execute shell command safely with Windows support"""
    if not command:
        raise ValueError("missing command")

    # Platform-specific dangerous command patterns
    is_windows = platform.system().lower() == "windows"

    # Block dangerous commands for different platforms
    if is_windows:
        dangerous_patterns = [
            "format", "del /s", "rmdir /s", "shutdown", "reboot", "powershell -c",
            "cmd /c", "net user", "net localgroup", "reg delete", "format c:",
            "del c:\\windows", "rmdir c:\\windows", "sfc", "dism"
        ]
    else:
        dangerous_patterns = ["rm -rf /", "shutdown", "reboot", "sudo ", "format", "dd if="]

    command_lower = command.lower()
    if any(pattern in command_lower for pattern in dangerous_patterns):
        raise ValueError("blocked potentially dangerous command")

    try:
        # Handle Windows-specific command translations
        if is_windows:
            # Translate common Unix commands to Windows equivalents
            command_map = {
                "ls": "dir",
                "pwd": "cd",
                "clear": "cls",
                "cat": "type",
                "rm -rf": "rmdir /s /q",
                "rm": "del",
                "mkdir -p": "mkdir",
                "cp": "copy",
                "mv": "move",
                "grep": "findstr",
                "which": "where",
            }

            # Simple command translation for common cases
            for unix_cmd, windows_cmd in command_map.items():
                if command.strip().startswith(unix_cmd) and len(command.strip().split()) <= 2:
                    command = command.replace(unix_cmd, windows_cmd, 1)
                    break

        # Execute the command
        proc = subprocess.run(
            command,
            cwd=str(WORKDIR),
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout_ms / 1000.0,
            creationflags=subprocess.CREATE_NO_WINDOW if is_windows else 0,
        )

        # Combine stdout and stderr
        out = "\n".join([x for x in [proc.stdout, proc.stderr] if x]).strip()
        return clamp_text(out or "(no output)")

    except subprocess.TimeoutExpired:
        return "(timeout)"
    except FileNotFoundError:
        return f"Command not found: {command.split()[0] if command else 'unknown'}"
    except Exception as e:
        return f"Error executing command: {str(e)}"

def run_write_file(path: str, content: str, mode: str = "overwrite") -> str:
    """Write file safely"""
    fp = safe_path(path)
    fp.parent.mkdir(parents=True, exist_ok=True)

    if mode == "append" and fp.exists():
        with fp.open("a", encoding="utf-8") as f:
            f.write(content)
    else:
        fp.write_text(content, encoding="utf-8")

    bytes_len = len(content.encode("utf-8"))
    rel = fp.relative_to(WORKDIR)
    return f"wrote {bytes_len} bytes to {rel}"

def test_tools():
    """Test the core tool functions"""
    print("Testing core tool functions...")

    # Test 1: Write snake game
    print("\n1. Creating snake game...")
    snake_code = '''#!/usr/bin/env python3
import turtle
import time
import random

# Snake Game
def snake_game():
    print("Snake game would start here!")
    return "Game running"

if __name__ == "__main__":
    print("Use W/A/S/D to control snake")
    snake_game()
'''

    try:
        result = run_write_file("snake_game.py", snake_code, "overwrite")
        print(f"Write result: {result}")

        # Check if file exists
        if Path("snake_game.py").exists():
            print("SUCCESS: File was created!")
            size = Path("snake_game.py").stat().st_size
            print(f"File size: {size} bytes")

            # Read and verify content
            with open("snake_game.py", "r") as f:
                content = f.read()
                print(f"First 100 chars: {content[:100]}...")
        else:
            print("ERROR: File was NOT created!")

    except Exception as e:
        print(f"ERROR: {e}")

    # Test 2: Run bash command
    print("\n2. Testing bash command...")
    try:
        result = run_bash("dir")
        print(f"Dir command successful, got {len(result)} characters")
        print(f"First 100 chars: {result[:100]}...")
    except Exception as e:
        print(f"ERROR: {e}")

    # Test 3: Run Windows echo
    print("\n3. Testing echo command...")
    try:
        result = run_bash("echo Hello World")
        print(f"Echo result: {result}")
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    test_tools()