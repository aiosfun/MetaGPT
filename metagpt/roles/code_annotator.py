#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pathlib import Path
from typing import Optional

from metagpt.actions.annotate_code import AnnotateCode
from metagpt.logs import logger
from metagpt.roles import Role
from metagpt.schema import Message


class CodeAnnotator(Role):
    name: str = "CodeAnnotator"
    profile: str = "Code Annotator"
    goal: str = "Add comprehensive documentation comments to source code files"
    constraints: str = (
        "Follow language-specific documentation conventions (PEP 257 for Python, JSDoc for JavaScript, etc.). "
        "Preserve original code logic and syntax. Create separate annotated files without modifying originals."
    )
    file_path: Optional[str] = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([AnnotateCode])
        self._set_react_mode(react_mode="by_order")

    async def _act(self) -> Message:
        logger.info(f"{self._setting}: ready to {self.rc.todo}")
        todo = self.rc.todo

        if not self.file_path:
            msg = self.get_memories(k=1)[0] if self.rc.memory.count() > 0 else None
            if not msg or not msg.content:
                logger.error("No input file or directory path provided")
                return Message(content="", role=self.profile, cause_by=type(todo))
            file_path = msg.content.strip()
        else:
            file_path = self.file_path

        logger.info(f"Annotating: {file_path}")

        result_path = await todo.run(file_path)

        if result_path:
            msg_content = f"Annotation complete. Output saved to: {result_path}"
        else:
            msg_content = f"Failed to annotate: {file_path}"

        msg = Message(content=msg_content, role=self.profile, cause_by=type(todo))
        return msg

    async def run(self, file_or_dir: str) -> Optional[str]:
        self.file_path = file_or_dir
        
        msg = Message(content=file_or_dir, role="User", cause_by=None)
        self.put_message(msg)

        response = await self.react()

        if response and "Output saved to:" in response.content:
            output_path = response.content.split("Output saved to:")[-1].strip()
            return output_path
        return None
