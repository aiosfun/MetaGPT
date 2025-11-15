#!/usr/bin/env python3
"""
Simplified v1_basic_agent.py using MetaGPT framework with LLMTalker role.
Avoids problematic imports and focuses on core functionality.
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

# Import only essential MetaGPT components
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


# ---------- Simple Role Base ----------
class SimpleRole:
    """Simplified role base without complex MetaGPT dependencies"""
    
    def __init__(self, name: str, profile: str, goal: str):
        self.name = name
        self.profile = profile
        self.goal = goal
        self.llm_talker = None
        self.actions = []
        self.rc = type('RoleContext', (), {
            'memory': type('Memory', (), {}),
            'msg_buffer': type('MessageQueue', (), {}),
            'state': -1,
            'todo': None,
            'watch': set(),
            'news': [],
            'react_mode': 'react',
            'max_react_loop': 1
        })
    
    def set_actions(self, actions):
        """Set actions for the role"""
        self.actions = actions
    
    def set_llm_talker(self, llm_talker):
        """Set LLMTalker for LLM communication"""
        self.llm_talker = llm_talker
    
    async def think(self) -> bool:
        """Always ready to process messages"""
        return True
    
    async def act(self) -> Message:
        """Process the latest message using appropriate action"""
        if not self.rc.news:
            return Message(content="No message to process", cause_by=self)
        
        # Get the latest message
        latest_msg = self.rc.news[-1]
        
        # Use LLMTalker to process the message
        if self.llm_talker and latest_msg:
            try:
                response = await self.llm_talker.talk_to_llm(latest_msg.content)
                return Message(content=response, cause_by=self)
            except Exception as e:
                logger.error(f"Error in LLMTalker processing: {e}")
                return Message(content=f"Error: {str(e)}", cause_by=self)
        
        return Message(content="No LLMTalker configured", cause_by=self)


# ---------- Actions ----------
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
            logger.error(f"Error in TalkAction: {e}")
            return ActionOutput(content=f"Error: {str(e)}", instruct_content="")


class BashAction(Action):
    """Action that executes bash commands"""
    
    async def run(self, command: str, **kwargs) -> ActionOutput:
        """Execute bash command and return output"""
        try:
            timeout_ms = int(kwargs.get("timeout_ms", 30000))
            result = run_bash_command(command, timeout_ms)
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
            
            result = read_file_content(path, start_line, end_line, max_chars)
            return ActionOutput(content=result, instruct_content=f"Read file: {path}")
        except Exception as e:
            logger.error(f"Error in ReadFileAction: {e}")
            return ActionOutput(content=f"Error: {str(e)}", instruct_content="")


class WriteFileAction(Action):
    """Action that writes files"""
    
    async def run(self, path: str, content: str, mode: str = "overwrite", **kwargs) -> ActionOutput:
        """Write file and return result"""
        try:
            result = write_file_content(path, content, mode)
            return ActionOutput(content=result, instruct_content=f"Written to: {path}")
        except Exception as e:
            logger.error(f"Error in WriteFileAction: {e}")
            return ActionOutput(content=f"Error: {str(e)}", instruct_content="")


# ---------- Tool executors ----------
def run_bash_command(command: str, timeout_ms: int = 30000) -> str:
    """Execute bash command safely"""
    if (
        subprocess is not None
        and ("rm -rf /" in command or "shutdown" in command or "reboot" in command or "sudo " in command)
    ):
        raise ValueError("blocked dangerous command")
    
    try:
        proc = subprocess.run(
            command,
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


def read_file_content(path: str, start_line=None, end_line=None, max_chars=None) -> str:
    """Read file content safely"""
    fp = safe_path(path)
    text = fp.read_text("utf-8")
    lines = text.split("\n")
    
    start = (max(1, int(start_line or 1)) - 1) if start_line else 0
    if isinstance(end_line, int):
        end_val = end_line
        end = len(lines) if end_val < 0 else max(start, end_val)
    else:
        end = len(lines)
    
    text = "\n".join(lines[start:end])
    max_chars = int(max_chars or 100_000)
    return clamp_text(text, max_chars)


def write_file_content(path: str, content: str, mode: str = "overwrite") -> str:
    """Write file content safely"""
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


# ---------- Main Agent ----------
class V1BasicAgent(SimpleRole):
    """V1 Basic Agent using simplified MetaGPT framework with LLMTalker"""
    
    def __init__(self, llm_client=None):
        super().__init__(
            name="V1BasicAgent",
            profile="Coding Agent", 
            goal="Help with coding tasks using tools",
            constraints="Use tools efficiently and provide concise responses"
        )
        
        # Set LLMTalker
        if llm_client:
            self.set_llm_talker(LLMTalker())
            self.llm_talker.set_llm_client(llm_client)
        
        # Set up actions
        self.set_actions([
            TalkAction(self.llm_talker) if self.llm_talker else None,
            BashAction(),
            ReadFileAction(),
            WriteFileAction(),
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
            command = content
            if " " in content:
                parts = content.split(" ", 1)
                command = parts[1] if len(parts) > 1 else content
            
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
            
            action = TalkAction(self.llm_talker) if self.llm_talker else None
            edit_response = await action.run(f"edit file {file_path} {edit_action}")
            # Combine edit response with file content
            response = await action.run(f"read file {file_path}")
            
        else:
            # Default to talk action
            action = TalkAction(self.llm_talker) if self.llm_talker else None
            response = await action.run(content)
        
        # Return the response as a message
        return Message(
            content=response.content if hasattr(response, 'content') else str(response),
            cause_by=self.rc.todo,
            sent_from=self
        )


def main():
    clear_screen()
    render_banner("V1 Basic Agent with LLMTalker", "Simplified MetaGPT framework with LLMTalker")
    print(f"{INFO_COLOR}Workspace: {WORKDIR}{RESET}")
    print(f"{INFO_COLOR}Type \"exit\" or \"quit\" to leave.{RESET}\n")
    
    # Simple LLM initialization (you can modify this)
    llm_client = None  # Set your LLM client here if needed
    
    # Initialize agent
    agent = V1BasicAgent(llm_client=llm_client)
    
    print("V1 Basic Agent with LLMTalker initialized!")
    print("Try commands like:")
    print("  'talk to llm: hello world'")
    print("  'bash: ls'")
    print("  'read file: README.md'")
    print("  'write file: test.txt hello world'")
    print("  'edit file: test.txt replace hello hi'")
    
    # Simple message processing loop
    async def process_messages():
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
    asyncio.run(process_messages())


if __name__ == "__main__":
    main()