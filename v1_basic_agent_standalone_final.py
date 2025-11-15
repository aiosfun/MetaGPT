#!/usr/bin/env python3
"""
Final standalone version of v1_basic_agent.py using LLMTalker role.
Completely standalone - no MetaGPT imports to avoid dependency issues.
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


# ---------- Simple LLMTalker ----------
class SimpleLLMTalker:
    """Simple LLM communication handler"""
    
    def __init__(self, llm_client=None):
        self.llm_client = llm_client
        self.history = []
    
    async def talk_to_llm(self, message: str) -> str:
        """Send message to LLM and get response"""
        if not self.llm_client:
            return "No LLM client configured"
        
        try:
            # Simple implementation - in real usage, this would call the actual LLM
            # For demo purposes, return a mock response
            return f"LLM response to: {message}"
        except Exception as e:
            return f"Error: {str(e)}"
    
    def set_llm_client(self, llm_client):
        """Set the LLM client"""
        self.llm_client = llm_client


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


# ---------- Simple Message and Action Classes ----------
class Message:
    """Simple message class"""
    
    def __init__(self, content: str, cause_by=None, sent_from=None):
        self.content = content
        self.cause_by = cause_by
        self.sent_from = sent_from


class ActionOutput:
    """Simple action output class"""
    
    def __init__(self, content: str, instruct_content: str = ""):
        self.content = content
        self.instruct_content = instruct_content


class Action:
    """Simple action base class"""
    
    def __init__(self):
        pass
    
    async def run(self, message: str, **kwargs) -> ActionOutput:
        """Run the action - to be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement run method")


class TalkAction(Action):
    """Action that uses LLMTalker to communicate with LLM"""
    
    def __init__(self, llm_talker):
        self.llm_talker = llm_talker
    
    async def run(self, message: str, **kwargs) -> ActionOutput:
        """Send message to LLM and return response"""
        try:
            response = await self.llm_talker.talk_to_llm(message)
            return ActionOutput(content=response, instruct_content=response)
        except Exception as e:
            return ActionOutput(content=f"Error: {str(e)}", instruct_content="")


class BashAction(Action):
    """Action that executes bash commands"""
    
    async def run(self, command: str, **kwargs) -> ActionOutput:
        """Execute bash command and return output"""
        try:
            timeout_ms = int(kwargs.get("timeout_ms", 30000))
            result = run_bash({"command": command, "timeout_ms": timeout_ms})
            return ActionOutput(content=result, instruct_content=f"Executed: {command}")
        except Exception as e:
            return ActionOutput(content=f"Error: {str(e)}", instruct_content="")


class ReadFileAction(Action):
    """Action that reads files"""
    
    async def run(self, path: str, **kwargs) -> ActionOutput:
        """Read file and return content"""
        try:
            start_line = kwargs.get("start_line")
            end_line = kwargs.get("end_line")
            max_chars = kwargs.get("max_chars")
            
            input_obj = {"path": path}
            if start_line is not None:
                input_obj["start_line"] = start_line
            if end_line is not None:
                input_obj["end_line"] = end_line
            if max_chars is not None:
                input_obj["max_chars"] = max_chars
                
            result = run_read(input_obj)
            return ActionOutput(content=result, instruct_content=f"Read file: {path}")
        except Exception as e:
            return ActionOutput(content=f"Error: {str(e)}", instruct_content="")


class WriteFileAction(Action):
    """Action that writes files"""
    
    async def run(self, path: str, content: str, mode: str = "overwrite", **kwargs) -> ActionOutput:
        """Write file and return result"""
        try:
            result = run_write({"path": path, "content": content, "mode": mode})
            return ActionOutput(content=result, instruct_content=f"Written to: {path}")
        except Exception as e:
            return ActionOutput(content=f"Error: {str(e)}", instruct_content="")


class EditTextAction(Action):
    """Action that edits text files"""
    
    async def run(self, path: str, action: str, **kwargs) -> ActionOutput:
        """Edit file and return result"""
        try:
            input_obj = {"path": path, "action": action}
            input_obj.update(kwargs)
            result = run_edit(input_obj)
            return ActionOutput(content=result, instruct_content=f"Edited {path} with {action}")
        except Exception as e:
            return ActionOutput(content=f"Error: {str(e)}", instruct_content="")


# ---------- Core Agent ----------
class SimpleAgent:
    """Simplified agent using LLMTalker for LLM communication"""
    
    def __init__(self, llm_client=None):
        self.llm_talker = SimpleLLMTalker(llm_client)
        self.messages = []
        
    async def process_message(self, message: Message):
        """Process a message and return response"""
        self.messages.append(message)
        
        # Use LLMTalker to get response
        if self.llm_talker:
            response = await self.llm_talker.talk_to_llm(message.content)
        else:
            response = "No LLMTalker configured"
        
        print(f"{PRIMARY_COLOR}LLM Response:{RESET}")
        print(format_markdown(response))
        
        return response
    
    async def run(self):
        """Main agent loop"""
        clear_screen()
        render_banner("V1 Basic Agent with LLMTalker", "Standalone version using LLMTalker")
        print(f"{INFO_COLOR}Workspace: {WORKDIR}{RESET}")
        print(f"{INFO_COLOR}Type \"exit\" or \"quit\" to leave.{RESET}\n")
        
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
            
            # Create message and process
            message = Message(content=line)
            await self.process_message(message)
            
    def set_llm_client(self, llm_client):
        """Set the LLM client for LLMTalker"""
        if self.llm_talker:
            self.llm_talker.set_llm_client(llm_client)


def main():
    """Main function"""
    agent = SimpleAgent()
    
    # You can set an LLM client like this:
    # from your_llm_provider import YourLLMClient
    # agent.set_llm_client(YourLLMClient())
    
    agent.run()


if __name__ == "__main__":
    main()