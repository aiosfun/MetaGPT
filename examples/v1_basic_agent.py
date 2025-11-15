#!/usr/bin/env python3
"""
@Time    : 2025-11-15
@Author  : AI Assistant
@File    : v1_basic_agent.py
@Desc    : Basic agent example using MetaGPT framework's LLM configuration
"""

import asyncio
import sys
from pathlib import Path
from metagpt.llm import LLM
from metagpt.logs import logger

# ---------- Workspace & Helpers ----------
WORKDIR = Path.cwd()

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


class BasicAgent:
    """Basic agent using MetaGPT framework's LLM configuration"""

    def __init__(self):
        # Initialize LLM using MetaGPT's configuration
        self.llm = LLM()

    async def ask_and_print(self, question: str) -> str:
        """Ask LLM and print response"""
        logger.info(f"Q: {question}")

        # Add system prompt to the question
        full_question = f"{SYSTEM}\n\nUser request: {question}"

        try:
            rsp = await self.llm.aask(full_question, system_msgs=[SYSTEM])
            if hasattr(self.llm, "reasoning_content") and self.llm.reasoning_content:
                logger.info(f"Reasoning: {self.llm.reasoning_content}")
            logger.info(f"A: {rsp}")
            return rsp
        except Exception as e:
            logger.error(f"Error: {e}")
            return f"Error: {str(e)}"


async def main():
    """Main function using MetaGPT framework"""
    # Create basic agent
    agent = BasicAgent()

    print("Basic Agent initialized with MetaGPT framework!")
    print("Type 'exit' or 'quit' to leave.")
    print("Try sending a message like 'hello world' or 'help me understand this codebase'")

    while True:
        try:
            user_input = input("User >> ")
        except (EOFError, KeyboardInterrupt):
            break

        if not user_input or user_input.strip().lower() in {"q", "quit", "exit"}:
            break

        # Let the agent process the message
        try:
            response = await agent.ask_and_print(user_input)
            print(f"Agent: {response}")
        except Exception as e:
            print(f"Error: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())
