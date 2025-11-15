#!/usr/bin/env python3
"""
Updated v1_basic_agent.py using MetaGPT framework with LLMTalker role.
Removes all LLM configuration and uses LLMTalker for all LLM communication.
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
from metagpt.actions import Action, ActionOutput
from metagpt.schema import Message
from metagpt.logs import logger


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


# ---------- Actions ----------
class TalkAction(Action):
    """Action that uses LLMTalker to communicate with LLM"""
    
    def __init__(self, llm_talker: LLMTalker):
        self.llm_talker = llm_talker
    
    async def run(self, message: str, **kwargs) -> ActionOutput:
        """Send message to LLM and return response"""
        try:
            response = await self.llm_talker.talk_to_llm(message)
            return ActionOutput(content=response, instruct_content=response)
        except Exception as e:
            logger.error(f"Error in TalkAction: {e}")
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
            logger.error(f"Error in BashAction: {e}")
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
            logger.error(f"Error in ReadFileAction: {e}")
            return ActionOutput(content=f"Error: {str(e)}", instruct_content="")


class WriteFileAction(Action):
    """Action that writes files"""
    
    async def run(self, path: str, content: str, mode: str = "overwrite", **kwargs) -> ActionOutput:
        """Write file and return result"""
        try:
            result = run_write({"path": path, "content": content, "mode": mode})
            return ActionOutput(content=result, instruct_content=f"Written to: {path}")
        except Exception as e:
            logger.error(f"Error in WriteFileAction: {e}")
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
            logger.error(f"Error in EditTextAction: {e}")
            return ActionOutput(content=f"Error: {str(e)}", instruct_content="")


# ---------- Core Agent ----------
from metagpt.roles import Role

class V1BasicAgent(Role):
    """V1 Basic Agent using MetaGPT framework with LLMTalker"""
    
    name: str = "V1BasicAgent"
    profile: str = "Coding Agent"
    goal: str = "Help with coding tasks using tools and LLMTalker"
    constraints: str = "Use tools efficiently and provide concise responses"
    desc: str = "A basic coding agent that uses LLMTalker for LLM communication"
    
    def __init__(self, llm_config=None):
        super().__init__()
        
        # Initialize LLMTalker
        self.llm_talker = LLMTalker()
        if llm_config:
            self.llm_talker.set_llm_client(llm_config)
        
        # Set up actions
        self.set_actions([
            TalkAction(self.llm_talker),
            BashAction(),
            ReadFileAction(),
            WriteFileAction(),
            EditTextAction()
        ])
    
    async def think(self) -> bool:
        """Always ready to process messages"""
        return True
    
    async def act(self) -> Message:
        """Process the latest message using appropriate action"""
        if not self.rc.news:
            return Message(content="No message to process", cause_by=self)
        
        # Get the latest message
        latest_msg = self.rc.news[-1]
        content = latest_msg.content if hasattr(latest_msg, 'content') else str(latest_msg)
        
        # Simple routing based on message content
        content_lower = content.lower()
        
        if "bash" in content or any(cmd in content for cmd in ["ls", "pwd", "cat", "echo"]):
            # Extract command from message
            if " " in content:
                parts = content.split(" ", 1)
                command = parts[1] if len(parts) > 1 else content
            else:
                command = content.replace("bash ", "")
            
            action = BashAction()
            response = await action.run(command)
            
        elif "read" in content and "file" in content:
            # Extract file path from message
            if " " in content:
                parts = content.split(" ", 2)
                file_path = parts[1] if len(parts) > 1 else content
            else:
                file_path = content.replace("read file ", "")
            
            action = ReadFileAction()
            response = await action.run(file_path)
            
        elif "write" in content and "file" in content:
            # Extract file path and content from message
            if " " in content:
                parts = content.split(" ", 2)
                file_path = parts[1] if len(parts) > 1 else content
                file_content = parts[2] if len(parts) > 2 else ""
            else:
                # Simple format: "write file <path> <content>"
                remaining = content.replace("write file ", "")
                if " " in remaining:
                    file_path, file_content = remaining.split(" ", 1)
                else:
                    file_path = remaining
                    file_content = ""
            
            action = WriteFileAction()
            response = await action.run(file_path, file_content)
            
        elif "edit" in content and "file" in content:
            # Extract edit details from message
            if " " in content:
                parts = content.split(" ", 3)
                file_path = parts[1] if len(parts) > 1 else content
                edit_action = parts[2] if len(parts) > 2 else "replace"
                edit_params = {}
                
                # Parse additional parameters
                for i, param in enumerate(parts[3:], 1):
                    if "=" in param:
                        key, value = param.split("=", 1)
                        edit_params[key] = value
                
            else:
                file_path = content.replace("edit file ", "")
                edit_action = "replace"
                edit_params = {}
            
            action = EditTextAction()
            response = await action.run(file_path, edit_action, **edit_params)
            
        else:
            # Default to talk action
            action = TalkAction(self.llm_talker)
            response = await action.run(content)
        
        # Return the response as a message
        return Message(
            content=response.content if hasattr(response, 'content') else str(response),
            cause_by=self.rc.todo,
            sent_from=self
        )


def main():
    clear_screen()
    render_banner("V1 Basic Agent with LLMTalker", "Using MetaGPT framework with LLMTalker role")
    print(f"{INFO_COLOR}Workspace: {WORKDIR}{RESET}")
    print(f"{INFO_COLOR}Type \"exit\" or \"quit\" to leave.{RESET}\n")
    print(f"{INFO_COLOR}Refer to examples/agent_with_llm_talker.py for usage pattern.{RESET}\n")
    
    # Initialize agent
    agent = V1BasicAgent()
    
    # Example interaction loop
    async def interaction_loop():
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
            user_message = Message(content=line, cause_by="user")
            
            # Simulate receiving message
            agent.rc.news = [user_message]
            
            # Let agent process the message
            response = await agent.act()
            
            print(f"{PRIMARY_COLOR}Agent Response:{RESET}")
            print(format_markdown(response.content))
    
    # Run the interaction loop
    asyncio.run(interaction_loop())


if __name__ == "__main__":
    main()