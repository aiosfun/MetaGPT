#!/usr/bin/env python3
import os
import sys
import json
import re
import time
import threading
import subprocess
from pathlib import Path
from typing import Union, Optional

# Import MetaGPT LLM system
try:
    from metagpt.llm import LLM
    from metagpt.configs.llm_config import LLMConfig
    from metagpt.context import Context
    from metagpt.const import USE_CONFIG_TIMEOUT
except Exception as e:
    sys.stderr.write("MetaGPT not found. Install with: pip install metagpt\n")
    raise

# Initialize MetaGPT LLM context and configuration
# MetaGPT will automatically load configuration from ~/.metagpt/config2.yaml
try:
    context = Context()
    llm = context.llm()
    llm_config = context.config.llm
except Exception as e:
    # Fallback to manual config creation
    import yaml
    from metagpt.configs.llm_config import LLMConfig as MetaLLMConfig

    llm_config = MetaLLMConfig()
    config_paths = [
        Path.home() / ".metagpt/config2.yaml",
    ]

    for config_path in config_paths:
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                    if 'llm' in data:
                        llm_data = data['llm']
                        for key, value in llm_data.items():
                            if hasattr(llm_config, key):
                                setattr(llm_config, key, value)
                        break
            except Exception as e:
                sys.stderr.write(f"Warning: Failed to load config from {config_path}: {e}\n")
                continue

    llm = LLM(llm_config=llm_config)

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
    formatted = MD_BULLET.sub("- ", formatted)
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


# ---------- Content normalization helpers ----------
def normalize_content_list(content):
    """Simple helper to normalize content for message handling."""
    try:
        if isinstance(content, list):
            return content
        elif isinstance(content, str):
            return [{"type": "text", "text": content}]
        else:
            return [{"type": "text", "text": str(content)}]
    except Exception:
        return []


# Validate LLM configuration
if not llm_config.api_key or llm_config.api_key in ["", "YOUR_API_KEY", "sk-xxx"]:
    sys.stderr.write("❌ LLM API key not configured. Please set it in ~/.metagpt/config2.yaml\n")
    sys.exit(1)

# Get the model from config
AGENT_MODEL = llm_config.model or "claude-3-5-sonnet-20241022"


# ---------- System prompt ----------
SYSTEM = (
    f"You are a coding agent operating INSIDE the user's repository at {WORKDIR}.\n"
    "Follow this loop strictly: plan briefly → use TOOLS to act directly on files/shell → report concise results.\n"
    "Rules:\n"
    "- Prefer taking actions with tools (read/write/edit/bash) over long prose.\n"
    "- Keep outputs terse. Use bullet lists / checklists when summarizing.\n"
    "- Never invent file paths. Ask via reads or list directories first if unsure.\n"
    "- For edits, apply the smallest change that satisfies the request.\n"
    "- For bash, avoid destructive or privileged commands; stay inside the workspace.\n"
    "- After finishing, summarize what changed and how to run or test."
)


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


def dispatch_tool(tu: dict) -> dict:
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
async def query(messages: list, opts: Optional[dict] = None) -> list:
    """
    Query function using MetaGPT's LLM system.
    Handles both text responses and tool usage.
    """
    opts = opts or {}

    # Extract the last user message
    last_user_msg = None
    for msg in reversed(messages):
        if isinstance(msg, dict) and msg.get("role") == "user":
            content = msg.get("content", [])
            if isinstance(content, list):
                # Extract text from content blocks
                text_parts = []
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "text":
                        text_parts.append(item.get("text", ""))
                last_user_msg = "\n".join(text_parts)
            elif isinstance(content, str):
                last_user_msg = content
            break

    if not last_user_msg:
        # If no user message found, just return
        return messages

    spinner = Spinner()
    spinner.start()

    try:
        # Use MetaGPT's aask method with system prompt and tools info
        full_prompt = f"{SYSTEM}\n\nAvailable tools: {json.dumps(tools, indent=2)}\n\nUser: {last_user_msg}"

        # Ask the agent to respond with tool calls or plain text
        agent_response = await llm.aask(
            msg=full_prompt,
            timeout=USE_CONFIG_TIMEOUT,
            stream=False
        )

        spinner.stop()

        # Try to parse if the response contains tool calls
        # Look for tool call patterns in markdown code blocks
        import re

        # Pattern to match tool calls in various formats
        # Format 1: ```tool_name\nparameter="value"\n```
        # Format 2: ```tool_name\nparameter: value\n```
        tool_block_pattern = re.compile(r'```(\w+)\n(.*?)\n```', re.DOTALL)
        tool_matches = tool_block_pattern.findall(agent_response)

        # Also try to match single-line tool calls like write_file(path="file.txt", content="text")
        single_line_pattern = re.compile(r'(\w+)_file\(([^)]+)\)', re.DOTALL)
        single_line_matches = single_line_pattern.findall(agent_response)

        # Also match just write_file calls anywhere in the response
        direct_pattern = re.compile(r'write_file\(([^)]+)\)', re.DOTALL)
        direct_matches = direct_pattern.findall(agent_response)

        if tool_matches:
            for tool_name, tool_content in tool_matches:
                try:
                    if tool_name == "write_file" or tool_name == "write":
                        # Parse write tool content - handle both key="value" and key: value formats
                        path_match = re.search(r'path\s*[:=]\s*["\']([^"\']+)["\']', tool_content)
                        content_match = re.search(r'content\s*[:=]\s*["\']([^"\']*)["\']', tool_content)

                        if path_match:
                            path = path_match.group(1).strip()
                            content = content_match.group(1).strip() if content_match else ""

                            result = run_write({"path": path, "content": content})
                            print(f"[Tool result] {result}")

                            # Replace the tool call in the response
                            tool_block = f"```{tool_name}\n{tool_content}\n```"
                            agent_response = agent_response.replace(tool_block, f"[OK] Created file: {path}")

                        # Try alternative format without quotes
                        else:
                            path_match = re.search(r'path\s*[:=]\s*([^\n\s]+)', tool_content)
                            content_match = re.search(r'content\s*[:=]\s*(.*)', tool_content, re.DOTALL)

                            if path_match:
                                path = path_match.group(1).strip()
                                content = content_match.group(1).strip() if content_match else ""

                                result = run_write({"path": path, "content": content})
                                print(f"[Tool result] {result}")

                                # Replace the tool call in the response
                                tool_block = f"```{tool_name}\n{tool_content}\n```"
                                agent_response = agent_response.replace(tool_block, f"[OK] Created file: {path}")

                    elif tool_name == "bash":
                        # Parse bash tool content
                        command_match = re.search(r'command[:\s]+([^\n]+)', tool_content)
                        if command_match:
                            command = command_match.group(1).strip().strip('"\'')
                            result = run_bash({"command": command})
                            print(f"[Tool result] {result}")

                            # Replace the tool call in the response
                            tool_block = f"```{tool_name}\n{tool_content}\n```"
                            agent_response = agent_response.replace(tool_block, f"[OK] Executed: {command}\nResult: {result}")

                        # Check if the bash content contains tool calls like write_file(path="file.txt", content="text")
                        write_match = re.search(r'write_file\(([^)]+)\)', tool_content)
                        if write_match:
                            params_str = write_match.group(1)
                            path_match = re.search(r'path\s*=\s*["\']([^"\']+)["\']', params_str)
                            content_match = re.search(r'content\s*=\s*["\']([^"\']*)["\']', params_str)

                            if path_match:
                                path = path_match.group(1).strip()
                                content = content_match.group(1) if content_match else ""

                                result = run_write({"path": path, "content": content})
                                print(f"[Tool result] {result}")

                                # Replace the tool call in the response
                                tool_block = f"```{tool_name}\n{tool_content}\n```"
                                agent_response = agent_response.replace(tool_block, f"[OK] Created file: {path}")

                    elif tool_name == "read_file" or tool_name == "read":
                        # Parse read tool content
                        path_match = re.search(r'path[:\s]+([^\n]+)', tool_content)
                        if path_match:
                            path = path_match.group(1).strip().strip('"\'')
                            result = run_read({"path": path})
                            print(f"[Tool result] {result}")

                            # Replace the tool call in the response
                            tool_block = f"```{tool_name}\n{tool_content}\n```"
                            agent_response = agent_response.replace(tool_block, f"✅ Read file: {path}\nContent: {result}")

                except Exception as e:
                    print(f"Error executing tool {tool_name}: {e}")

        # Also try JSON format for tool calls
        json_pattern = re.compile(r'\{[^}]*"tool"[^}]*\}', re.DOTALL)
        json_tools = json_pattern.findall(agent_response)

        for tool_json in json_tools:
            try:
                tool_data = json.loads(tool_json)
                tool_name = tool_data.get("tool")
                if tool_name == "bash":
                    command = tool_data.get("command")
                    if command:
                        result = run_bash({"command": command})
                        print(f"[Tool result] {result}")
                        agent_response = agent_response.replace(tool_json, f"✅ Executed: {command}\nResult: {result}")
                elif tool_name == "write":
                    path = tool_data.get("path")
                    content = tool_data.get("content", "")
                    if path:
                        result = run_write({"path": path, "content": content})
                        print(f"[Tool result] {result}")
                        agent_response = agent_response.replace(tool_json, f"✅ Created file: {path}")
            except Exception as e:
                print(f"Error executing JSON tool: {e}")

        # Handle single-line tool calls like write_file(path="file.txt", content="text")
        if single_line_matches:
            for tool_name, params_str in single_line_matches:
                try:
                    if tool_name == "write":
                        # Parse parameters from write_file(path="file.txt", content="text")
                        path_match = re.search(r'path\s*=\s*["\']([^"\']+)["\']', params_str)
                        content_match = re.search(r'content\s*=\s*["\']([^"\']*)["\']', params_str)

                        if path_match:
                            path = path_match.group(1).strip()
                            content = content_match.group(1) if content_match else ""

                            result = run_write({"path": path, "content": content})
                            print(f"[Tool result] {result}")

                            # Replace the tool call in the response
                            tool_call_str = f"{tool_name}_file({params_str})"
                            agent_response = agent_response.replace(tool_call_str, f"[OK] Created file: {path}")

                except Exception as e:
                    print(f"Error executing single-line tool {tool_name}: {e}")

        # Handle direct write_file matches
        if direct_matches:
            for params_str in direct_matches:
                try:
                    # Parse parameters from write_file(path="file.txt", content="text")
                    path_match = re.search(r'path\s*=\s*["\']([^"\']+)["\']', params_str)
                    content_match = re.search(r'content\s*=\s*["\']([^"\']*)["\']', params_str)

                    if path_match:
                        path = path_match.group(1).strip()
                        content = content_match.group(1) if content_match else ""

                        result = run_write({"path": path, "content": content})
                        print(f"[Tool result] {result}")

                        # Replace the tool call in the response
                        tool_call_str = f"write_file({params_str})"
                        agent_response = agent_response.replace(tool_call_str, f"[OK] Created file: {path}")

                except Exception as e:
                    print(f"Error executing direct tool call: {e}")

        # Display the formatted response
        sys.stdout.write(format_markdown(agent_response or "") + "\n")

        messages.append({"role": "assistant", "content": [{"type": "text", "text": agent_response}]})
        return messages

    except Exception as e:
        spinner.stop()
        sys.stderr.write(f"Error during LLM query: {e}\n")
        return messages


async def main():
    clear_screen()
    render_banner("Tiny Kode Agent", "custom tools only")
    print(f"{INFO_COLOR}Workspace: {WORKDIR}{RESET}")
    print(f"{INFO_COLOR}Type \"exit\" or \"quit\" to leave.{RESET}\n")
    history: list = []
    while True:
        try:
            line = input(user_prompt_label())
        except EOFError:
            break
        if not line or line.strip().lower() in {"q", "quit", "exit"}:
            break
        print_divider()
        history.append({"role": "user", "content": [{"type": "text", "text": line}]})
        try:
            history = await query(history)
        except Exception as e:
            print(f"{ACCENT_COLOR}Error{RESET}: {str(e)}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
