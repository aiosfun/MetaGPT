#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 14:43
@Author  : alexanderwu
@File    : architect.py
"""
from typing import Optional

from pydantic import Field

from metagpt.actions.design_api import WriteDesign
from metagpt.actions.design_api_openspec import WriteDesignWithOpenSpec
from metagpt.actions.write_prd import WritePRD
from metagpt.logs import logger
from metagpt.prompts.di.architect import ARCHITECT_EXAMPLE, ARCHITECT_INSTRUCTION
from metagpt.roles.di.role_zero import RoleZero
from metagpt.roles.role import RoleReactMode
from metagpt.tools.libs.terminal import Terminal
from metagpt.utils.common import any_to_name, any_to_str, tool2name


class Architect(RoleZero):
    """
    Represents an Architect role in a software development process.

    Attributes:
        name (str): Name of the architect.
        profile (str): Role profile, default is 'Architect'.
        goal (str): Primary goal or responsibility of the architect.
        constraints (str): Constraints or guidelines for the architect.
        use_openspec (bool): Whether to use OpenSpec-compliant design generation.
    """

    name: str = "Bob"
    profile: str = "Architect"
    goal: str = "design a concise, usable, complete software system. output the system design."
    constraints: str = (
        "make sure the architecture is simple enough and use  appropriate open source "
        "libraries. Use same language as user requirement"
    )
    terminal: Terminal = Field(default_factory=Terminal, exclude=True)
    instruction: str = ARCHITECT_INSTRUCTION
    tools: list[str] = [
        "Editor:write,read,similarity_search",
        "RoleZero",
        "Terminal:run_command",
    ]

    todo_action: str = any_to_name(WriteDesign)
    use_openspec: bool = True  # Enable OpenSpec by default

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        # Determine which WriteDesign action to use
        write_design_action = WriteDesignWithOpenSpec if self.use_openspec else WriteDesign

        # NOTE: The following init setting will only be effective when self.use_fixed_sop is changed to True
        self.enable_memory = False
        # Initialize actions specific to the Architect role
        self.set_actions([write_design_action])

        # Set events or actions the Architect should watch or be aware of
        self._watch({WritePRD})

        # Update todo action
        self.todo_action = any_to_name(write_design_action)

    def _retrieve_experience(self) -> str:
        return ARCHITECT_EXAMPLE

    def _update_tool_execution(self):
        # Choose the appropriate WriteDesign action based on OpenSpec setting
        write_design_action = WriteDesignWithOpenSpec if self.use_openspec else WriteDesign
        wd = write_design_action()
        self.tool_execution_map.update(tool2name(write_design_action, ["run"], wd.run))
        self.tool_execution_map.update({"Terminal.run_command": self.terminal.run_command})

    async def _think(self) -> bool:
        """Decide what to do"""
        if not self.use_fixed_sop:
            return await super()._think()

        # Set the appropriate todo action based on OpenSpec setting
        write_design_action = WriteDesignWithOpenSpec if self.use_openspec else WriteDesign
        self.todo_action = any_to_name(write_design_action)
        return bool(self.rc.todo)

    def set_openspec_mode(self, use_openspec: bool):
        """Enable or disable OpenSpec mode.

        Args:
            use_openspec: Whether to use OpenSpec-compliant design generation
        """
        self.use_openspec = use_openspec
        logger.info(f"Architect OpenSpec mode set to: {use_openspec}")

        # Determine which WriteDesign action to use
        write_design_action = WriteDesignWithOpenSpec if self.use_openspec else WriteDesign

        # Update actions if using fixed SOP
        if self.use_fixed_sop:
            self.set_actions([write_design_action])

        # Update todo action
        self.todo_action = any_to_name(write_design_action)
