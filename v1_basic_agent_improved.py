#!/usr/bin/env python3
import os
import sys
import json
import re
import time
import threading
import subprocess
import traceback
from pathlib import Path
from typing import Union, Optional, List, Dict, Any

try:
    from anthropic import Anthropic
except Exception as e:
    sys.stderr.write("Install with: pip install anthropic\n")
    raise

# Import configuration system
import yaml
from pathlib import Path

class LLMType:
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    CLAUDE = "claude"

class LLMConfig:
    def __init__(self):
        self.api_type = "anthropic"
        self.api_key = "sk-xxx"
        self.base_url = "https://api.moonshot.cn/anthropic"
        self.model = "kimi-k2-turbo-preview"
        self._load_from_file()

    def _load_from_file(self):
        """Load configuration from MetaGPT-style config files"""
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
                            self.api_type = llm_data.get('api_type', self.api_type)
                            self.api_key = llm_data.get('api_key', self.api_key)
                            self.base_url = llm_data.get('base_url', self.base_url)
                            self.model = llm_data.get('model', self.model)
                            break
                except Exception as e:
                    sys.stderr.write(f"Warning: Failed to load config from {config_path}: {e}\n")
                    continue

class Config:
    def __init__(self):
        self.llm = LLMConfig()

# Load configuration
config = Config()

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
        js = json.dumps(info, ensure_ascii=False, indent=2, default=str)
        out = js if len(js) <= 4000 else js[:4000] + "\n...<truncated>"
        print(f"⚠️  {tag}:")
        print(out)
    except Exception:
        print(f"⚠️  {tag}: (unserializable info)")


# ---------- Enhanced Content normalization helpers ----------
def validate_content_block(block: Any) -> Dict[str, Any]:
    """Validate and normalize a content block to prevent type errors"""
    if block is None:
        return {"type": "text", "text": ""}
    
    if isinstance(block, dict):
        # Ensure required fields exist and have correct types
        normalized = {}
        block_type = block.get("type", "text")
        
        if block_type == "text":
            normalized["type"] = "text"
            normalized["text"] = str(block.get("text", ""))
        elif block_type == "tool_use":
            normalized["type"] = "tool_use"
            normalized["id"] = str(block.get("id", ""))
            normalized["name"] = str(block.get("name", ""))
            normalized["input"] = block.get("input", {})
            if not isinstance(normalized["input"], dict):
                normalized["input"] = {}
        elif block_type == "tool_result":
            normalized["type"] = "tool_result"
            normalized["tool_use_id"] = str(block.get("tool_use_id", ""))
            normalized["content"] = str(block.get("content", ""))
            normalized["is_error"] = bool(block.get("is_error", False))
        else:
            # Fallback for unknown types
            normalized["type"] = "text"
            normalized["text"] = str(block)
        
        return normalized
    
    # Handle object attributes
    try:
        if hasattr(block, 'type'):
            block_type = getattr(block, 'type')
            if block_type == 'text':
                return {
                    "type": "text",
                    "text": str(getattr(block, 'text', ''))
                }
            elif block_type == 'tool_use':
                return {
                    "type": "tool_use",
                    "id": str(getattr(block, 'id', '')),
                    "name": str(getattr(block, 'name', '')),
                    "input": getattr(block, 'input', {}) or {}
                }
            elif block_type == 'tool_result':
                return {
                    "type": "tool_result",
                    "tool_use_id": str(getattr(block, 'tool_use_id', '')),
                    "content": str(getattr(block, 'content', '')),
                    "is_error": bool(getattr(block, 'is_error', False))
                }
    except Exception:
        pass
    
    # Ultimate fallback
    return {"type": "text", "text": str(block)}


def block_to_dict(block):
    """Convert SDK response block objects to plain dicts for reuse in messages.
    Enhanced with better error handling and type validation.
    """
    try:
        return validate_content_block(block)
    except Exception as e:
        log_error_debug("block_to_dict_error", {
            "error": str(e),
            "block_type": type(block).__name__,
            "block_repr": repr(block)[:500]
        })
        # Return safe fallback
        return {"type": "text", "text": f"[Error converting block: {str(e)}]"}


def normalize_content_list(content) -> List[Dict[str, Any]]:
    """Normalize content list with robust error handling"""
    if not content:
        return []
    
    try:
        if isinstance(content, list):
            return [block_to_dict(block) for block in content]
        elif isinstance(content, str):
            return [{"type": "text", "text": content}]
        else:
            return [block_to_dict(content)]
    except Exception as e:
        log_error_debug("normalize_content_list_error", {
            "error": str(e),
            "content_type": type(content).__name__,
            "content_preview": str(content)[:500]
        })
        return [{"type": "text", "text": f"[Error normalizing content: {str(e)}]"}]


def validate_message(message: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and normalize a message to prevent type errors"""
    if not isinstance(message, dict):
        return {"role": "user", "content": [{"type": "text", "text": str(message)}]}
    
    normalized = {
        "role": str(message.get("role", "user")),
        "content": normalize_content_list(message.get("content", []))
    }
    
    # Ensure role is valid
    if normalized["role"] not in ["user", "assistant", "system"]:
        normalized["role"] = "user"
    
    return normalized


# Wrapper class to make OpenAI client compatible with Anthropic interface
class OpenAIWrapper:
    def __init__(self, openai_client):
        self.client = openai_client
        self._messages = MessagesWrapper(self.client)

    @property
    def messages(self):
        return self._messages


class MessagesWrapper:
    def __init__(self, openai_client):
        self.client = openai_client

    def create(self, model=None, system=None, messages=None, tools=None, max_tokens=None, **kwargs):
        """Convert Anthropic-style API call to OpenAI format with enhanced error handling"""
        try:
            # Validate and normalize input messages
            normalized_messages = []
            for msg in (messages or []):
                normalized_messages.append(validate_message(msg))

            # Convert messages from Anthropic format to OpenAI format
            openai_messages = []

            # Add system message if provided
            if system:
                openai_messages.append({"role": "system", "content": str(system)})

            # Convert other messages with strict validation
            for msg in normalized_messages:
                role = msg.get("role")
                content = msg.get("content", [])

                if role == "user":
                    if isinstance(content, list):
                        # Handle tool results and text content with strict validation
                        msg_content = []
                        for item in content:
                            if isinstance(item, dict):
                                item_type = item.get("type", "text")
                                # Only allow valid OpenAI content types
                                if item_type == "text":
                                    text_content = item.get("text", "")
                                    msg_content.append({"type": "text", "text": str(text_content)})
                                elif item_type == "tool_result":
                                    tool_use_id = item.get("tool_use_id", "")
                                    result_content = item.get("content", "")
                                    # Convert tool_result to text for OpenAI compatibility
                                    if tool_use_id:
                                        msg_content.append({
                                            "type": "text",
                                            "text": f"Tool result for {tool_use_id}: {str(result_content)}"
                                        })
                                    else:
                                        msg_content.append({"type": "text", "text": str(result_content)})
                                # Skip any other content types that might cause errors
                        # Ensure we have valid content
                        if msg_content:
                            openai_messages.append({"role": "user", "content": msg_content})
                        else:
                            openai_messages.append({"role": "user", "content": "Empty content"})
                    else:
                        openai_messages.append({"role": "user", "content": str(content)})

                elif role == "assistant":
                    if isinstance(content, list):
                        # Handle tool use and text content with strict validation
                        msg_content = []
                        for item in content:
                            if isinstance(item, dict):
                                item_type = item.get("type", "text")
                                # Only allow valid OpenAI content types
                                if item_type == "text":
                                    text_content = item.get("text", "")
                                    msg_content.append({"type": "text", "text": str(text_content)})
                                elif item_type == "tool_use":
                                    tool_id = item.get("id", "")
                                    tool_name = item.get("name", "")
                                    tool_input = item.get("input", {})
                                    # Validate tool use data
                                    if tool_id and tool_name:
                                        msg_content.append({
                                            "type": "function",
                                            "id": str(tool_id),
                                            "function": {
                                                "name": str(tool_name),
                                                "arguments": json.dumps(tool_input if isinstance(tool_input, dict) else {})
                                            }
                                        })
                                # Skip any other content types that might cause errors
                        # Ensure we have valid content
                        if msg_content:
                            openai_messages.append({"role": "assistant", "content": msg_content})
                        else:
                            openai_messages.append({"role": "assistant", "content": "Empty content"})
                    else:
                        openai_messages.append({"role": "assistant", "content": str(content)})

            # Convert tools from Anthropic format to OpenAI format
            openai_tools = None
            if tools:
                openai_tools = []
                for tool in tools:
                    if isinstance(tool, dict):
                        openai_tools.append({
                            "type": "function",
                            "function": {
                                "name": tool.get("name", ""),
                                "description": tool.get("description", ""),
                                "parameters": tool.get("input_schema", {})
                            }
                        })

            # Final validation before API call
            if not openai_messages:
                raise ValueError("No messages to send to API")

            # Validate each message structure
            for i, msg in enumerate(openai_messages):
                if not isinstance(msg, dict):
                    raise ValueError(f"Message {i} is not a dict: {type(msg)}")
                if "role" not in msg or "content" not in msg:
                    raise ValueError(f"Message {i} missing required fields: {msg}")
                if msg["role"] not in ["system", "user", "assistant"]:
                    raise ValueError(f"Message {i} has invalid role: {msg['role']}")

                # Validate content structure
                content = msg["content"]
                if isinstance(content, list):
                    for j, item in enumerate(content):
                        if not isinstance(item, dict):
                            raise ValueError(f"Message {i} content item {j} is not a dict")
                        if "type" not in item:
                            raise ValueError(f"Message {i} content item {j} missing type: {item}")
                        if item["type"] not in ["text", "function"]:
                            raise ValueError(f"Message {i} content item {j} has invalid type: {item['type']}")
                elif not isinstance(content, str):
                    raise ValueError(f"Message {i} content is not string or list: {type(content)}")

            # Make the OpenAI API call
            response = self.client.chat.completions.create(
                model=model,
                messages=openai_messages,
                tools=openai_tools,
                max_tokens=max_tokens,
                **kwargs
            )

            # Convert OpenAI response back to Anthropic format
            class MockResponse:
                def __init__(self, openai_response):
                    self.content = []
                    self.stop_reason = "stop"

                    try:
                        message = openai_response.choices[0].message

                        # Add text content
                        if message.content:
                            self.content.append(type('TextBlock', (), {
                                'type': 'text',
                                'text': message.content
                            })())

                        # Add tool calls
                        if message.tool_calls:
                            self.stop_reason = "tool_use"
                            for tool_call in message.tool_calls:
                                self.content.append(type('ToolUseBlock', (), {
                                    'type': 'tool_use',
                                    'id': tool_call.id,
                                    'name': tool_call.function.name,
                                    'input': json.loads(tool_call.function.arguments or '{}')
                                })())
                    except Exception as e:
                        log_error_debug("mock_response_creation_error", {
                            "error": str(e),
                            "response_type": type(openai_response).__name__
                        })
                        # Add fallback text content
                        self.content.append(type('TextBlock', (), {
                            'type': 'text',
                            'text': f"[Error processing response: {str(e)}]"
                        })())

            return MockResponse(response)

        except Exception as e:
            log_error_debug("openai_wrapper_error", {
                "error": str(e),
                "model": model,
                "traceback": traceback.format_exc()
            })
            # Return a fallback response
            class FallbackResponse:
                def __init__(self, error_msg):
                    self.content = [type('TextBlock', (), {
                        'type': 'text',
                        'text': f"[API Error: {error_msg}]"
                    })()]
                    self.stop_reason = "stop"
            
            return FallbackResponse(str(e))


# ---------- SDK client ----------
# Get LLM configuration from MetaGPT config
llm_config = config.llm

# Initialize appropriate client based on API type
if llm_config.api_type in [LLMType.ANTHROPIC, LLMType.CLAUDE]:
    # Anthropic/Claude configuration
    if not llm_config.api_key or llm_config.api_key in ["", "YOUR_API_KEY", "sk-"]:
        sys.stderr.write("❌ LLM API key not configured. Please set it in config/config2.yaml\n")
        sys.exit(1)

    client = Anthropic(
        api_key=llm_config.api_key,
        base_url=llm_config.base_url if llm_config.base_url else None
    )
    AGENT_MODEL = llm_config.model or "claude-3-5-sonnet-20241022"

elif llm_config.api_type == LLMType.OPENAI:
    # OpenAI configuration - need to use OpenAI client
    try:
        from openai import OpenAI
        if not llm_config.api_key or llm_config.api_key in ["", "YOUR_API_KEY", "sk-"]:
            sys.stderr.write("❌ LLM API key not configured. Please set it in config/config2.yaml\n")
            sys.exit(1)

        client = OpenAI(
            api_key=llm_config.api_key,
            base_url=llm_config.base_url if llm_config.base_url else None
        )
        AGENT_MODEL = llm_config.model or "gpt-4-turbo"
        # Use OpenAI wrapper for compatibility
        client = OpenAIWrapper(client)

    except ImportError:
        sys.stderr.write("❌ OpenAI library not installed. Install with: pip install openai\n")
        sys.exit(1)

else:
    sys.stderr.write(f"❌ LLM type '{llm_config.api_type}' is not supported. Expected 'openai', 'anthropic', or 'claude'\n")
    sys.exit(1)


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
    try:
        cmd = str(input_obj.get("command") or "")
        if not cmd:
            raise ValueError("missing bash.command")
        if (
            subprocess is not None
            and ("rm -rf /" in cmd or "shutdown" in cmd or "reboot" in cmd or "sudo " in cmd)
        ):
            raise ValueError("blocked dangerous command")
        timeout_ms = int(input_obj.get("timeout_ms") or 30000)
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
    except Exception as e:
        return f"Error executing bash command: {str(e)}"


def run_read(input_obj: dict) -> str:
    try:
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
    except Exception as e:
        return f"Error reading file: {str(e)}"


def run_write(input_obj: dict) -> str:
    try:
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
    except Exception as e:
        return f"Error writing file: {str(e)}"


def run_edit(input_obj: dict) -> str:
    try:
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
    except Exception as e:
        return f"Error editing file: {str(e)}"


def dispatch_tool(tu: dict) -> dict:
    """Enhanced tool dispatcher with better error handling"""
    try:
        # Support both dict and SDK block objects
        def gv(obj, key, default=None):
            return obj.get(key, default) if isinstance(obj, dict) else getattr(obj, key, default)

        name = gv(tu, "name")
        input_obj = gv(tu, "input", {}) or {}
        tool_use_id = gv(tu, "id")

        if not name:
            return {"type": "tool_result", "tool_use_id": tool_use_id, "content": "Tool name missing", "is_error": True}

        if name == "bash":
            pretty_tool_line("Bash", (input_obj.get("command") if isinstance(input_obj, dict) else None))
            out = run_bash(input_obj if isinstance(input_obj, dict) else {})
            pretty_sub_line(clamp_text(out, 2000) if out else "(No content)")
            return {"type": "tool_result", "tool_use_id": tool_use_id, "content": out}
        elif name == "read_file":
            pretty_tool_line("Read", (input_obj.get("path") if isinstance(input_obj, dict) else None))
            out = run_read(input_obj if isinstance(input_obj, dict) else {})
            pretty_sub_line(clamp_text(out, 2000))
            return {"type": "tool_result", "tool_use_id": tool_use_id, "content": out}
        elif name == "write_file":
            pretty_tool_line("Write", (input_obj.get("path") if isinstance(input_obj, dict) else None))
            out = run_write(input_obj if isinstance(input_obj, dict) else {})
            pretty_sub_line(out)
            return {"type": "tool_result", "tool_use_id": tool_use_id, "content": out}
        elif name == "edit_text":
            action = input_obj.get("action") if isinstance(input_obj, dict) else None
            path_v = input_obj.get("path") if isinstance(input_obj, dict) else None
            pretty_tool_line("Edit", f"{action} {path_v}")
            out = run_edit(input_obj if isinstance(input_obj, dict) else {})
            pretty_sub_line(out)
            return {"type": "tool_result", "tool_use_id": tool_use_id, "content": out}
        else:
            return {"type": "tool_result", "tool_use_id": tool_use_id, "content": f"unknown tool: {name}", "is_error": True}
    except Exception as e:
        tool_use_id = tu.get("id") if isinstance(tu, dict) else getattr(tu, "id", None)
        log_error_debug("dispatch_tool_error", {
            "error": str(e),
            "tool_use": tu,
            "traceback": traceback.format_exc()
        })
        return {"type": "tool_result", "tool_use_id": tool_use_id, "content": f"Tool execution error: {str(e)}", "is_error": True}


# ---------- Enhanced Core loop ----------
def query(messages: list, opts: Optional[dict] = None) -> list:
    """Enhanced query function with robust error handling"""
    opts = opts or {}
    
    # Validate and normalize input messages
    try:
        normalized_messages = [validate_message(msg) for msg in messages]
    except Exception as e:
        log_error_debug("message_validation_error", {
            "error": str(e),
            "messages": messages
        })
        normalized_messages = [{"role": "user", "content": [{"type": "text", "text": "Error: Invalid message format"}]}]
    
    while True:
        spinner = Spinner()
        spinner.start()
        try:
            res = client.messages.create(
                model=AGENT_MODEL,
                system=SYSTEM,
                messages=normalized_messages,
                tools=tools,
                max_tokens=16000,
                **({"tool_choice": opts["tool_choice"]} if "tool_choice" in opts else {}),
            )
        except Exception as e:
            spinner.stop()
            log_error_debug("api_call_error", {
                "error": str(e),
                "model": AGENT_MODEL,
                "traceback": traceback.format_exc()
            })
            print(f"{ACCENT_COLOR}API Error{RESET}: {str(e)}")
            # Add error message to conversation and continue
            normalized_messages.append({
                "role": "assistant", 
                "content": [{"type": "text", "text": f"API Error: {str(e)}"}]
            })
            return normalized_messages
        finally:
            spinner.stop()

        tool_uses = []
        try:
            content = getattr(res, "content", [])
            if not isinstance(content, list):
                log_error_debug("invalid_content_type", {
                    "content_type": type(content).__name__,
                    "content": str(content)[:1000]
                })
                content = []
            
            for block in content:
                try:
                    # Normalize block to prevent type errors
                    normalized_block = validate_content_block(block)
                    btype = normalized_block.get("type")
                    
                    if btype == "text":
                        text = normalized_block.get("text", "")
                        if text:
                            sys.stdout.write(format_markdown(text) + "\n")
                    elif btype == "tool_use":
                        tool_uses.append(normalized_block)
                    else:
                        log_error_debug("unknown_block_type", {
                            "block_type": btype,
                            "block": normalized_block
                        })
                except Exception as block_error:
                    log_error_debug("block_processing_error", {
                        "error": str(block_error),
                        "block": str(block)[:500]
                    })
                    continue
                    
        except Exception as err:
            log_error_debug(
                "Iterating res.content failed",
                {
                    "error": str(err),
                    "stop_reason": getattr(res, "stop_reason", None),
                    "content_type": type(getattr(res, "content", None)).__name__,
                    "is_array": isinstance(getattr(res, "content", None), list),
                    "keys": list(res.__dict__.keys()) if hasattr(res, "__dict__") else [],
                    "preview": (json.dumps(res, default=lambda o: getattr(o, "__dict__", str(o)))[:2000] if res else ""),
                    "traceback": traceback.format_exc()
                },
            )
            # Add error message and continue
            normalized_messages.append({
                "role": "assistant", 
                "content": [{"type": "text", "text": f"Error processing response: {str(err)}"}]
            })
            return normalized_messages

        if getattr(res, "stop_reason", None) == "tool_use" and tool_uses:
            try:
                results = [dispatch_tool(tu) for tu in tool_uses]
                # Normalize results to prevent type errors
                normalized_results = [validate_content_block(result) for result in results]
                
                normalized_messages.append({"role": "assistant", "content": normalize_content_list(res.content)})
                normalized_messages.append({"role": "user", "content": normalized_results})
                continue
            except Exception as tool_error:
                log_error_debug("tool_execution_error", {
                    "error": str(tool_error),
                    "tool_uses": tool_uses,
                    "traceback": traceback.format_exc()
                })
                normalized_messages.append({
                    "role": "assistant", 
                    "content": [{"type": "text", "text": f"Tool execution error: {str(tool_error)}"}]
                })
                return normalized_messages

        # Final message normalization
        try:
            normalized_content = normalize_content_list(res.content)
            normalized_messages.append({"role": "assistant", "content": normalized_content})
        except Exception as final_error:
            log_error_debug("final_message_error", {
                "error": str(final_error),
                "traceback": traceback.format_exc()
            })
            normalized_messages.append({
                "role": "assistant", 
                "content": [{"type": "text", "text": f"Error finalizing response: {str(final_error)}"}]
            })
        
        return normalized_messages


def main():
    clear_screen()
    render_banner("Tiny Kode Agent (Improved)", "Enhanced error handling & robustness")
    print(f"{INFO_COLOR}Workspace: {WORKDIR}{RESET}")
    print(f"{INFO_COLOR}Type \"exit\" or \"quit\" to leave.{RESET}\n")
    history: list = []
    
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
        
        # Create properly formatted user message
        user_message = {
            "role": "user", 
            "content": [{"type": "text", "text": line}]
        }
        
        history.append(user_message)
        try:
            history = query(history)
        except Exception as e:
            print(f"{ACCENT_COLOR}Critical Error{RESET}: {str(e)}")
            log_error_debug("critical_error", {
                "error": str(e),
                "traceback": traceback.format_exc()
            })
            # Reset history to prevent cascading errors
            history = [{"role": "user", "content": [{"type": "text", "text": "Let's start fresh after the error."}]}]


if __name__ == "__main__":
    main()