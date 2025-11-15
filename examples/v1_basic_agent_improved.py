#!/usr/bin/env python3
"""
@Time    : 2025-11-15
@Author  : AI Assistant
@File    : v1_basic_agent_improved.py
@Desc    : Improved basic agent with proper LLM tool integration using MetaGPT framework
"""

import asyncio
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List

from metagpt.llm import LLM
from metagpt.logs import logger
from metagpt.actions import Action, ActionOutput
from metagpt.roles import Role
from metagpt.schema import Message

# ---------- Workspace & Helpers ----------
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


# ---------- Tool Functions ----------
def run_bash(command: str, timeout_ms: int = 30000) -> str:
    """Execute shell command safely with Windows support"""
    if not command:
        raise ValueError("missing command")

    # Platform-specific dangerous command patterns
    import platform
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
def run_read_file(path: str, start_line: Optional[int] = None,
                  end_line: Optional[int] = None, max_chars: int = 100000) -> str:
    """Read file safely with optional line range"""
    fp = safe_path(path)
    text = fp.read_text("utf-8")
    lines = text.split("\n")

    # Handle line range
    start = (max(1, int(start_line or 1)) - 1) if start_line else 0
    if end_line is not None:
        end_val = int(end_line)
        end = len(lines) if end_val < 0 else max(start, end_val)
    else:
        end = len(lines)

    text = "\n".join(lines[start:end])
    return clamp_text(text, max_chars)


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


def run_edit_file(path: str, action: str, **kwargs) -> str:
    """Edit file with various actions"""
    fp = safe_path(path)
    text = fp.read_text("utf-8")

    if action == "replace":
        find = str(kwargs.get("find", ""))
        if not find:
            raise ValueError("edit_text.replace missing find")
        replaced = text.replace(find, str(kwargs.get("replace", "")))
        fp.write_text(replaced, encoding="utf-8")
        return f"replace done ({len(replaced.encode('utf-8'))} bytes)"

    elif action == "insert":
        line = int(kwargs.get("insert_after", -1))
        new_text = str(kwargs.get("new_text", ""))
        lines = text.split("\n")
        idx = max(-1, min(len(lines) - 1, line))
        lines[idx + 1:idx + 1] = [new_text]
        new_content = "\n".join(lines)
        fp.write_text(new_content, encoding="utf-8")
        return f"inserted after line {line}"

    elif action == "delete_range":
        rng = kwargs.get("range", [])
        if not (len(rng) == 2 and isinstance(rng[0], int) and isinstance(rng[1], int) and rng[1] >= rng[0]):
            raise ValueError("edit_text.delete_range invalid range")
        s, e = rng
        lines = text.split("\n")
        new_content = "\n".join([*lines[:s], *lines[e:]])
        fp.write_text(new_content, encoding="utf-8")
        return f"deleted lines [{s}, {e})"

    else:
        raise ValueError(f"unsupported edit action: {action}")


# ---------- Tool Schema Definitions ----------
TOOLS_SCHEMA = [
    {
        "name": "bash",
        "description": "Execute shell commands in the workspace directory. Automatically translates Unix commands to Windows on Windows systems (e.g., 'ls' → 'dir', 'pwd' → 'cd', 'cat' → 'type')",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "Shell command to execute. Supports both Unix and Windows commands."
                },
                "timeout_ms": {
                    "type": "integer",
                    "description": "Timeout in milliseconds (default: 30000)",
                    "default": 30000
                }
            },
            "required": ["command"]
        }
    },
    {
        "name": "read_file",
        "description": "Read a text file from the workspace",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to the file to read"
                },
                "start_line": {
                    "type": "integer",
                    "description": "Start line number (1-based, optional)"
                },
                "end_line": {
                    "type": "integer",
                    "description": "End line number (optional, -1 for end of file)"
                },
                "max_chars": {
                    "type": "integer",
                    "description": "Maximum characters to return (default: 100000)"
                }
            },
            "required": ["path"]
        }
    },
    {
        "name": "write_file",
        "description": "Write content to a file in the workspace",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to the file to write"
                },
                "content": {
                    "type": "string",
                    "description": "Content to write to the file"
                },
                "mode": {
                    "type": "string",
                    "enum": ["overwrite", "append"],
                    "description": "Write mode: 'overwrite' or 'append' (default: overwrite)",
                    "default": "overwrite"
                }
            },
            "required": ["path", "content"]
        }
    },
    {
        "name": "edit_file",
        "description": "Edit an existing file with various operations",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to the file to edit"
                },
                "action": {
                    "type": "string",
                    "enum": ["replace", "insert", "delete_range"],
                    "description": "Edit action to perform"
                }
            },
            "required": ["path", "action"],
            "allOf": [
                {
                    "if": {"properties": {"action": {"const": "replace"}}},
                    "then": {
                        "properties": {
                            "find": {"type": "string", "description": "Text to find"},
                            "replace": {"type": "string", "description": "Text to replace with"}
                        },
                        "required": ["find", "replace"]
                    }
                },
                {
                    "if": {"properties": {"action": {"const": "insert"}}},
                    "then": {
                        "properties": {
                            "insert_after": {"type": "integer", "description": "Line number to insert after"},
                            "new_text": {"type": "string", "description": "Text to insert"}
                        },
                        "required": ["insert_after", "new_text"]
                    }
                },
                {
                    "if": {"properties": {"action": {"const": "delete_range"}}},
                    "then": {
                        "properties": {
                            "range": {
                                "type": "array",
                                "items": {"type": "integer"},
                                "minItems": 2,
                                "maxItems": 2,
                                "description": "Line range to delete [start, end)"
                            }
                        },
                        "required": ["range"]
                    }
                }
            ]
        }
    }
]


class ToolUsingAction(Action):
    """Action that can use tools based on LLM decisions"""

    def __init__(self, system_prompt: str):
        super().__init__()
        self.system_prompt = system_prompt
        self.llm = LLM()

    async def run(self, message: str, **kwargs) -> ActionOutput:
        """Process message with tool support"""
        try:
            # Create conversation with system prompt and tools
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": message}
            ]

            # Add tools to the LLM call if supported
            response = await self._call_llm_with_tools(messages)

            return ActionOutput(content=response, instruct_content=response)

        except Exception as e:
            logger.error(f"Error in ToolUsingAction: {e}")
            return ActionOutput(content=f"Error: {str(e)}", instruct_content="")

    async def _call_llm_with_tools(self, messages: List[Dict]) -> str:
        """Call LLM with tool support"""
        try:
            # Try to use tools if LLM supports function calling
            if hasattr(self.llm, 'acode_completion'):
                # Use function calling if available
                response = await self._handle_function_calling(messages)
            else:
                # Fallback to simple text-based tool parsing
                response = await self._handle_text_based_tools(messages)

            return response

        except Exception as e:
            logger.error(f"Error in LLM tool calling: {e}")
            # Fallback to simple response without tools
            return await self.llm.aask(messages[-1]["content"])

    async def _handle_function_calling(self, messages: List[Dict]) -> str:
        """Handle function calling (if supported by LLM)"""
        # This would be implemented based on the specific LLM's function calling API
        # For now, we'll implement a text-based approach
        return await self._handle_text_based_tools(messages)

    async def _handle_text_based_tools(self, messages: List[Dict]) -> str:
        """Handle tool usage through text parsing with support for multiple tool executions"""

        # Create a comprehensive tool-using prompt
        tools_info = "\n\n=== AVAILABLE TOOLS ===\n"
        for tool in TOOLS_SCHEMA:
            tools_info += f"\nTool: {tool['name']}\n"
            tools_info += f"Description: {tool['description']}\n"
            tools_info += f"Parameters: {json.dumps(tool['parameters'], indent=2)}\n"

        enhanced_system_msg = (
            messages[0]["content"] +
            tools_info +
            "\n\n=== TOOL USAGE INSTRUCTIONS ===\n"
            "IMPORTANT: When you need to use tools, you MUST format your response EXACTLY like this:\n"
            "TOOL_CALL: tool_name\n"
            "PARAMETERS: {\"parameter\": \"value\"}\n\n"
            "EXAMPLES:\n"
            "TOOL_CALL: bash\n"
            "PARAMETERS: {\"command\": \"dir\"}\n\n"
            "TOOL_CALL: write_file\n"
            "PARAMETERS: {\"path\": \"test.py\", \"content\": \"print('hello')\"}\n\n"
            "For programming tasks like 'Write a snake game', you should:\n"
            "1. Use bash with 'dir' to check current directory\n"
            "2. Use write_file to create the complete game file\n"
            "3. Explain what you created\n\n"
            "You can make MULTIPLE tool calls in one response by repeating the format.\n"
            "ALWAYS include the TOOL_CALL and PARAMETERS blocks when you need to use tools!"
        )

        # Log the enhanced system message for debugging
        logger.info("Enhanced system message (first 500 chars):")
        logger.info(enhanced_system_msg[:500])

        # Get LLM response with the enhanced system message
        try:
            response = await self.llm.aask(messages[-1]["content"], system_msgs=[enhanced_system_msg])
            logger.info(f"LLM response (first 300 chars): {response[:300]}")

            # Check if response contains tool calls
            if "TOOL_CALL:" in response:
                logger.info("Tool calls detected in response")
                # Continue parsing and executing tools until no more tool calls
                max_iterations = 10  # Prevent infinite loops
                iteration = 0

                while "TOOL_CALL:" in response and iteration < max_iterations:
                    iteration += 1
                    logger.info(f"Tool execution iteration {iteration}")

                    # Parse and execute current tool calls
                    response = await self._parse_and_execute_tools(response)

                    # If there are still tool calls, ask LLM to continue based on results
                    if "TOOL_CALL:" in response:
                        # Create a new message asking LLM to continue with the results
                        continuation_prompt = (
                            f"Based on the tool results above, please continue with your task. "
                            f"If you need to use more tools, include them in your response. "
                            f"If you're done, provide your final answer.\n\n"
                            f"Original request: {messages[-1]['content']}"
                        )

                        response = await self.llm.aask(continuation_prompt, system_msgs=[enhanced_system_msg])
            else:
                logger.info("No tool calls detected in LLM response")
                # If no tool calls, the LLM might not have understood the instructions
                # Try again with a more explicit instruction


        except Exception as e:
            logger.error(f"Error in _handle_text_based_tools: {e}")
            return f"Error: {str(e)}"

        return response

    async def _parse_and_execute_tools(self, response: str) -> str:
        """Parse tool calls in response and execute them"""
        # Find tool calls - more flexible pattern
        tool_pattern = r"TOOL_CALL:\s*(\w+)\s*\nPARAMETERS:\s*({.*?})\s*(?=\n\n|\nTOOL_CALL:|$)"
        matches = re.findall(tool_pattern, response, re.DOTALL)

        enhanced_response = response

        for tool_name, params_str in matches:
            try:
                # Parse JSON parameters
                params = json.loads(params_str)
                logger.info(f"Executing tool: {tool_name} with params: {params}")

                # Execute the tool
                tool_result = await self._execute_tool(tool_name, params)
                logger.info(f"Tool result: {tool_result[:200]}...")

                # Replace the tool call with the result
                tool_call_text = f"TOOL_CALL: {tool_name}\nPARAMETERS: {params_str}"
                replacement = f"✅ Tool '{tool_name}' executed successfully:\n```\n{tool_result}\n```"
                enhanced_response = enhanced_response.replace(tool_call_text, replacement)

            except json.JSONDecodeError as e:
                # Replace tool call with JSON parsing error
                tool_call_text = f"TOOL_CALL: {tool_name}\nPARAMETERS: {params_str}"
                error_msg = f"❌ Tool '{tool_name}' failed - Invalid JSON: {str(e)}"
                enhanced_response = enhanced_response.replace(tool_call_text, error_msg)

            except Exception as e:
                # Replace tool call with general error message
                tool_call_text = f"TOOL_CALL: {tool_name}\nPARAMETERS: {params_str}"
                error_msg = f"❌ Tool '{tool_name}' failed: {str(e)}"
                enhanced_response = enhanced_response.replace(tool_call_text, error_msg)

        return enhanced_response

    async def _execute_tool(self, tool_name: str, params: Dict) -> str:
        """Execute a specific tool"""
        try:
            logger.info(f"Executing {tool_name} with params: {params}")

            if tool_name == "bash":
                result = run_bash(params["command"], params.get("timeout_ms", 30000))
                logger.info(f"Bash result: {result[:100]}...")
                return result

            elif tool_name == "read_file":
                result = run_read_file(
                    params["path"],
                    params.get("start_line"),
                    params.get("end_line"),
                    params.get("max_chars", 100000)
                )
                logger.info(f"Read file result: {result[:100]}...")
                return result

            elif tool_name == "write_file":
                result = run_write_file(
                    params["path"],
                    params["content"],
                    params.get("mode", "overwrite")
                )
                logger.info(f"Write file result: {result}")
                return result

            elif tool_name == "edit_file":
                result = run_edit_file(params["path"], params["action"], **params)
                logger.info(f"Edit file result: {result}")
                return result

            else:
                error_msg = f"Unknown tool: {tool_name}. Available tools: bash, read_file, write_file, edit_file"
                logger.error(error_msg)
                return error_msg

        except Exception as e:
            error_msg = f"Tool '{tool_name}' execution error: {str(e)}"
            logger.error(error_msg)
            return error_msg


class ImprovedBasicAgent(Role):
    """Improved Basic Agent with proper LLM tool integration"""

    name: str = "ImprovedBasicAgent"
    profile: str = "Coding Assistant with Tools"
    goal: str = "Help with coding tasks using available tools"
    constraints: str = "Use tools efficiently and provide helpful responses"
    desc: str = "An improved coding agent that can use tools based on LLM decisions"

    def __init__(self):
        super().__init__()

        # System prompt for the agent
        import platform
        platform_info = f" ({platform.system()})" if platform.system() else ""

        self.system_prompt = (
            f"You are a coding agent operating INSIDE the user's repository at {WORKDIR}{platform_info}.\n"
            "You have access to file operations and shell commands through tools.\n"
            "The bash tool automatically translates Unix commands to Windows when needed.\n"
            "Common translations: 'ls' → 'dir', 'pwd' → 'cd', 'cat' → 'type', 'rm' → 'del'\n"
            "Use tools to accomplish tasks and provide helpful responses.\n"
            "IMPORTANT: For complex tasks like creating programs, use a structured approach:\n"
            "1. First, check the current directory (bash/dir)\n"
            "2. Then create the necessary files (write_file)\n"
            "3. Finally, explain what you created\n"
            "Rules:\n"
            "- Use tools to read files, write files, edit files, and execute commands\n"
            "- For programming tasks, create complete, working code files\n"
            "- Always explain what you're doing and why\n"
            "- Be helpful and provide clear explanations\n"
            "- Stay within the workspace directory\n"
            "- Don't execute potentially dangerous commands\n"
            "- After using tools, explain the results and next steps\n"
            "- On Windows, use commands like 'dir', 'type', 'del', 'copy', 'move', 'findstr'\n"
            "- When asked to create a program, provide the complete code in a file, then explain how to run it"
        )

        # Set up the tool-using action
        self.set_actions([ToolUsingAction(self.system_prompt)])

    async def think(self) -> bool:
        """Always ready to process messages"""
        return True

    async def act(self) -> Message:
        """Process the latest message using tools as needed"""
        if not self.rc.news:
            return Message(content="No message to process", cause_by=self)

        latest_msg = self.rc.news[-1]

        # Use the tool-using action
        action = self.actions[0]
        response = await action.run(latest_msg.content)

        return Message(
            content=response.content if hasattr(response, 'content') else str(response),
            cause_by=self,
            sent_from=self
        )


async def main():
    """Main function with improved tool integration"""
    print("🚀 Improved Basic Agent with LLM Tool Integration")
    print(f"📁 Workspace: {WORKDIR}")
    print("Available tools: bash, read_file, write_file, edit_file")
    print("Type 'exit' or 'quit' to leave.\n")

    # Create the improved agent
    agent = ImprovedBasicAgent()

    # Interaction loop
    while True:
        try:
            user_input = input("User >> ")
        except (EOFError, KeyboardInterrupt):
            break

        if not user_input or user_input.strip().lower() in {"q", "quit", "exit"}:
            print("👋 Goodbye!")
            break

        # Create message and process
        user_message = Message(content=user_input, cause_by="user")

        # Simulate message receipt
        agent.rc.news = [user_message]

        try:
            # Let the agent process the message with tools
            response = await agent.act()
            print(f"\n🤖 Agent Response:")
            print(response.content)
            print("-" * 50)

        except Exception as e:
            print(f"❌ Error: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())