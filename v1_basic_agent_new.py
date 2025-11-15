#!/usr/bin/env python3
"""
Modified v1_basic_agent.py using LLMTalker role for LLM communication.
Removes all LLM configuration and uses LLMTalker instead.
"""
import os
import sys
import json
import re
import time
import threading
import subprocess
import asyncio
from pathlib import Path
from typing import Union, Optional

# Import MetaGPT components
from metagpt.roles.llm_talker import LLMTalker
from metagpt.provider import HumanProvider
from metagpt.schema import Message

# ---------- Workspace & Helpers ----------
WORKDIR = Path.cwd()
MAX_TOOL_RESULT_CHARS = 100_000

RESET = "\x1b[0m"
PRIMARY_COLOR = "\x1b[38;2;120;200;255m"
ACCENT_COLOR = "\x1b[38;2;150;140;255m"
INFO_COLOR = "\x1b[38;2;110;110;110m"
PROMPT_COLOR = "\x1b[38;2;120;200;255m"
DIVIDER = "\n"


MD_BOLD = re.compile(r"\*\*(.+?)\*\*")
MD_CODE = re.compile(r"`([^`]+)`")
MD_HEADING = re.compile(r"^(#{1,6})\s*(.+)$", re.MULTILINE)
MD_BULLET = re.compile(r"^\s*[-\*]\s+", re.MULTILINE)


def clear_screen() -> None:
    if sys.stdout.isatty():
        sys.stdout.write("\033c")
        sys.stdout.flush()


def render_banner(title: str, subtitle: Optional[str] = None) -> None:
    print(f"{PRIMARY_COLOR}{title}{RESET}")
    if subtitle:
        print(f"{ACCENT_COLOR}{subtitle}{RESET}")
    print()


def user_prompt_label() -> str:
    return f"{ACCENT_COLOR}{RESET} {PROMPT_COLOR}User{RESET}{INFO_COLOR} >> {RESET}"


def print_divider() -> None:
    print(DIVIDER, end="")


def format_markdown(text: str) -> str:
    if not text or text.lstrip().startswith("\x1b"):
        return text

    def bold_repl(match: re.Match[str]) -> str:
        return f"\x1b[1m{match.group(1)}\x1b[0m"

    def code_repl(match: re.Match[str]) -> str:
        return f"\x1b[38;2;255;214;102m{match.group(1)}\x1b[0m"

    def heading_repl(match: re.Match[str]) -> str:
        return f"\x1b[1m{match.group(2)}\x1b[0m"

    formatted = MD_BOLD.sub(bold_repl, text)
    formatted = MD_CODE.sub(code_repl, formatted)
    formatted = MD_HEADING.sub(heading_repl, formatted)
    formatted = MD_BULLET.sub("• ", formatted)
    return formatted


def safe_path(p: str) -> Path:
    abs_path = (WORKDIR / str(p or "")).resolve()
    rel = abs_path.relative_to(WORKDIR) if abs_path.is_relative_to(WORKDIR) else None
    if rel is None:
        raise ValueError("Path escapes workspace")
    return abs_path


def clamp_text(s: str, n: int = MAX_TOOL_RESULT_CHARS) -> str:
    if len(s) <= n:
        return s
    return s[:n] + f"\n\n...<truncated {len(s) - n} chars>"


def pretty_tool_line(kind: str, title: Optional[str]) -> None:
    body = f"{kind}({title})…" if title else kind
    glow = f"{ACCENT_COLOR}\x1b[1m"
    print(f"{glow}⏺ {body}{RESET}")


def pretty_sub_line(text: str) -> None:
    lines = text.splitlines() or [""]
    for line in lines:
        print(f"  ⎿ {format_markdown(line)}")


# Minimal spinner for model waits
class Spinner:
    def __init__(self, label: str = "Waiting for model") -> None:
        self.label = label
        self.frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self.color = "\x1b[38;2;255;229;92m"
        self._stop = threading.Event()
        self._thread = None

    def start(self):
        if not sys.stdout.isatty() or self._thread is not None:
            return
        self._stop.clear()

        def run():
            start_ts = time.time()
            index = 0
            while not self._stop.is_set():
                elapsed = time.time() - start_ts
                frame = self.frames[index % len(self.frames)]
                styled = f"{self.color}{frame} {self.label} ({elapsed:.1f}s)\x1b[0m"
                sys.stdout.write("\r" + styled)
                sys.stdout.flush()
                index += 1
                time.sleep(0.08)

        self._thread = threading.Thread(target=run, daemon=True)
        self._thread.start()

    def stop(self):
        if self._thread is None:
            return
        self._stop.set()
        self._thread.join(timeout=1)
        self._thread = None
        try:
            # clear current line
            sys.stdout.write("\r\x1b[2K")
            sys.stdout.flush()
        except Exception:
            pass


def log_error_debug(tag: str, info) -> None:
    try:
        js = json.dumps(info, ensure_ascii=False, indent=2)
        out = js if len(js) <= 4000 else js[:4000] + "\n...<truncated>"
        print(f"⚠️  {tag}:")
        print(out)
    except Exception:
        print(f"⚠️  {tag}: (unserializable info)")


# ---------- Tools ----------
tools = [
    {
        "name": "bash",
        "description": (
            "Execute a shell command inside the project workspace. Use for scaffolding, "
            "formatting, running scripts, etc."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "Shell command to run"},
                "timeout_ms": {"type": "integer", "minimum": 1000, "maximum": 120000},
            },
            "required": ["command"],
            "additionalProperties": False,
        },
    },
    {
        "name": "read_file",
        "description": "Read a UTF-8 text file. Optionally slice by line range or clamp length.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "start_line": {"type": "integer", "minimum": 1},
                "end_line": {"type": "integer", "minimum": -1},
                "max_chars": {"type": "integer", "minimum": 1, "maximum": 200000},
            },
            "required": ["path"],
            "additionalProperties": False,
        },
    },
    {
        "name": "write_file",
        "description": "Create or overwrite/append a UTF-8 text file. Use overwrite unless explicitly asked to append.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "content": {"type": "string"},
                "mode": {"type": "string", "enum": ["overwrite", "append"], "default": "overwrite"},
            },
            "required": ["path", "content"],
            "additionalProperties": False,
        },
    },
    {
        "name": "edit_text",
        "description": "Small, precise text edits. Choose one action: replace | insert | delete_range.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "action": {"type": "string", "enum": ["replace", "insert", "delete_range"]},
                "find": {"type": "string"},
                "replace": {"type": "string"},
                "insert_after": {"type": "integer", "minimum": -1},
                "new_text": {"type": "string"},
                "range": {"type": "array", "items": {"type": "integer"}, "minItems": 2, "maxItems": 2},
            },
            "required": ["path", "action"],
            "additionalProperties": False,
        },
    },
]


# ---------- Tool executors ----------
def run_bash(input_obj: dict) -> str:
    cmd = str(input_obj.get("command") or "")
    if not cmd:
        raise ValueError("missing bash.command")
    if (
        subprocess is not None
        and ("rm -rf /" in cmd or "shutdown" in cmd or "reboot" in cmd or "sudo " in cmd)
    ):
        raise ValueError("blocked dangerous command")
    timeout_ms = int(input_obj.get("timeout_ms") or 30000)
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(WORKDIR),
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout_ms / 1000.0,
        )
        out = "\n".join([x for x in [proc.stdout, proc.stderr] if x]).strip()
        return clamp_text(out or "(no output)")
    except subprocess.TimeoutExpired:
        return "(timeout)"


def run_read(input_obj: dict) -> str:
    fp = safe_path(input_obj.get("path"))
    text = fp.read_text("utf-8")
    lines = text.split("\n")
    start = (max(1, int(input_obj.get("start_line") or 1)) - 1) if input_obj.get("start_line") else 0
    if isinstance(input_obj.get("end_line"), int):
        end_val = input_obj.get("end_line")
        end = len(lines) if end_val < 0 else max(start, end_val)
    else:
        end = len(lines)
    text = "\n".join(lines[start:end])
    max_chars = int(input_obj.get("max_chars") or 100_000)
    return clamp_text(text, max_chars)


def run_write(input_obj: dict) -> str:
    fp = safe_path(input_obj.get("path"))
    fp.parent.mkdir(parents=True, exist_ok=True)
    content = input_obj.get("content") or ""
    mode = input_obj.get("mode")
    if mode == "append" and fp.exists():
        with fp.open("a", encoding="utf-8") as f:
            f.write(content)
    else:
        fp.write_text(content, encoding="utf-8")
    bytes_len = len(content.encode("utf-8"))
    rel = fp.relative_to(WORKDIR)
    return f"wrote {bytes_len} bytes to {rel}"


def run_edit(input_obj: dict) -> str:
    fp = safe_path(input_obj.get("path"))
    text = fp.read_text("utf-8")
    action = input_obj.get("action")
    if action == "replace":
        find = str(input_obj.get("find") or "")
        if not find:
            raise ValueError("edit_text.replace missing find")
        replaced = text.replace(find, str(input_obj.get("replace") or ""))
        fp.write_text(replaced, encoding="utf-8")
        return f"replace done ({len(replaced.encode('utf-8'))} bytes)"
    elif action == "insert":
        line = int(input_obj.get("insert_after") if input_obj.get("insert_after") is not None else -1)
        lines = text.split("\n")
        idx = max(-1, min(len(lines) - 1, line))
        lines[idx + 1:idx + 1] = [str(input_obj.get("new_text") or "")]
        nxt = "\n".join(lines)
        fp.write_text(nxt, encoding="utf-8")
        return f"inserted after line {line}"
    elif action == "delete_range":
        rng = input_obj.get("range") or []
        if not (len(rng) == 2 and isinstance(rng[0], int) and isinstance(rng[1], int) and rng[1] >= rng[0]):
            raise ValueError("edit_text.delete_range invalid range")
        s, e = rng
        lines = text.split("\n")
        nxt = "\n".join([*lines[:s], *lines[e:]])
        fp.write_text(nxt, encoding="utf-8")
        return f"deleted lines [{s}, {e})"
    else:
        raise ValueError(f"unsupported edit_text.action: {action}")


def dispatch_tool(tu: dict, llm_talker) -> dict:
    """Enhanced tool dispatcher using llm_talker for LLM communication"""
    try:
        # Support both dict and SDK block objects
        def gv(obj, key, default=None):
            return obj.get(key, default) if isinstance(obj, dict) else getattr(obj, key, default)

        name = gv(tu, "name")
        input_obj = gv(tu, "input", {}) or {}
        tool_use_id = gv(tu, "id")

        if name == "bash":
            pretty_tool_line("Bash", (input_obj.get("command") if isinstance(input_obj, dict) else None))
            out = run_bash(input_obj if isinstance(input_obj, dict) else {})
            pretty_sub_line(clamp_text(out, 2000) if out else "(No content)")
            return {"type": "tool_result", "tool_use_id": tool_use_id, "content": out}
        if name == "read_file":
            pretty_tool_line("Read", (input_obj.get("path") if isinstance(input_obj, dict) else None))
            out = run_read(input_obj if isinstance(input_obj, dict) else {})
            pretty_sub_line(clamp_text(out, 2000))
            return {"type": "tool_result", "tool_use_id": tool_use_id, "content": out}
        if name == "write_file":
            pretty_tool_line("Write", (input_obj.get("path") if isinstance(input_obj, dict) else None))
            out = run_write(input_obj if isinstance(input_obj, dict) else {})
            pretty_sub_line(out)
            return {"type": "tool_result", "tool_use_id": tool_use_id, "content": out}
        if name == "edit_text":
            action = input_obj.get("action") if isinstance(input_obj, dict) else None
            path_v = input_obj.get("path") if isinstance(input_obj, dict) else None
            pretty_tool_line("Edit", f"{action} {path_v}")
            out = run_edit(input_obj if isinstance(input_obj, dict) else {})
            pretty_sub_line(out)
            return {"type": "tool_result", "tool_use_id": tool_use_id, "content": out}
        return {"type": "tool_result", "tool_use_id": tool_use_id, "content": f"unknown tool: {name}", "is_error": True}
    except Exception as e:
        tool_use_id = tu.get("id") if isinstance(tu, dict) else getattr(tu, "id", None)
        return {"type": "tool_result", "tool_use_id": tool_use_id, "content": str(e), "is_error": True}


# ---------- Core loop ----------
class SimpleAgent:
    """Simplified agent using LLMTalker for LLM communication"""
    
    def __init__(self, llm_client=None):
        self.llm_talker = LLMTalker()
        if llm_client:
            self.llm_talker.set_llm_client(llm_client)
        self.history = []
        
    def format_user_message(self, content: str) -> dict:
        """Format user message for LLM"""
        return {
            "role": "user",
            "content": [{"type": "text", "text": content}]
        }
    
    def format_system_message(self, content: str) -> dict:
        """Format system message for LLM"""
        return {
            "role": "system", 
            "content": content
        }
    
    async def query(self, user_input: str) -> str:
        """Process user input and return LLM response"""
        spinner = Spinner()
        spinner.start()
        
        try:
            # Add system message and user message to history
            system_msg = self.format_system_message(
                f"You are a coding agent operating INSIDE the user's repository at {WORKDIR}.\n"
                "Follow this loop strictly: plan briefly → use TOOLS to act directly on files/shell → report concise results.\n"
                "Rules:\n"
                "- Prefer taking actions with tools (read/write/edit/bash) over long prose.\n"
                "- Keep outputs terse. Use bullet lists / checklists when summarizing.\n"
                "- Never invent file paths. Ask via reads or list directories first if unsure.\n"
                "- For edits, apply the smallest change that satisfies the request.\n"
                "- For bash, avoid destructive or privileged commands; stay inside the workspace.\n"
                "- After finishing, summarize what changed and how to run or test.\n"
                f"\n\nYou have access to these tools: {json.dumps(tools, indent=2)}"
            )
            
            user_msg = self.format_user_message(user_input)
            
            # Create messages for LLM
            messages = [system_msg, user_msg]
            
            # Send to LLM via llm_talker
            response = await self.llm_talker.talk_to_llm(
                json.dumps(messages[-1])  # Send last message as context
            )
            
            # Check if response contains tool calls
            if "tool_use" in response or "function" in response:
                # Handle tool execution
                tool_response = await self.handle_tool_calls(response)
                if tool_response:
                    # Continue conversation with tool results
                    followup = await self.llm_talker.talk_to_llm(
                        f"Tool results: {json.dumps(tool_response)}\n\nPlease continue with the task."
                    )
                    return followup
                else:
                    return response
            else:
                return response
                
        except Exception as e:
            log_error_debug("query_error", {
                "error": str(e),
                "user_input": user_input
            })
            return f"Error: {str(e)}"
        finally:
            spinner.stop()
    
    async def handle_tool_calls(self, response: str) -> dict:
        """Parse and execute tool calls from LLM response"""
        try:
            # Simple parsing - look for tool patterns in response
            # This is a simplified implementation
            # In a real scenario, you'd use proper JSON/function calling parsing
            
            # For now, just return response as-is
            # The tool execution would be handled by the LLM itself
            return {"response": response}
            
        except Exception as e:
            log_error_debug("tool_call_error", {
                "error": str(e),
                "response": response
            })
            return {"error": str(e)}


def main():
    clear_screen()
    render_banner("Tiny Kode Agent with LLMTalker", "Using LLMTalker role for LLM communication")
    print(f"{INFO_COLOR}Workspace: {WORKDIR}{RESET}")
    print(f"{INFO_COLOR}Type \"exit\" or \"quit\" to leave.{RESET}\n")
    
    # Initialize agent
    agent = SimpleAgent()
    
    while True:
        try:
            line = input(user_prompt_label())
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break
        if not line or line.strip().lower() in {"q", "quit", "exit"}:
            print("Goodbye!")
            break
        print_divider()
        
        # Process user input
        try:
            response = asyncio.run(agent.query(line))
            print(f"{PRIMARY_COLOR}LLM Response:{RESET}")
            print(format_markdown(response))
        except Exception as e:
            print(f"{ACCENT_COLOR}Error{RESET}: {str(e)}")


if __name__ == "__main__":
    main()