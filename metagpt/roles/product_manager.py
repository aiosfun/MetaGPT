#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 14:43
@Author  : alexanderwu
@File    : product_manager.py
@Modified By: liushaojie, 2024/10/17.
"""
from typing import Optional

from metagpt.actions import UserRequirement, WritePRD
from metagpt.actions.prepare_documents import PrepareDocuments
from metagpt.actions.search_enhanced_qa import SearchEnhancedQA
from metagpt.actions.write_prd_openspec import WritePRDWithOpenSpec
from metagpt.logs import logger
from metagpt.prompts.product_manager import PRODUCT_MANAGER_INSTRUCTION
from metagpt.roles.di.role_zero import RoleZero
from metagpt.roles.role import RoleReactMode
from metagpt.tools.libs.browser import Browser
from metagpt.tools.libs.editor import Editor
from metagpt.utils.common import any_to_name, any_to_str, tool2name
from metagpt.utils.git_repository import GitRepository


class ProductManager(RoleZero):
    """
    Represents a Product Manager role responsible for product development and management.

    Attributes:
        name (str): Name of the product manager.
        profile (str): Role profile, default is 'Product Manager'.
        goal (str): Goal of the product manager.
        constraints (str): Constraints or limitations for the product manager.
        use_openspec (bool): Whether to use OpenSpec-compliant requirement generation.
    """

    name: str = "Alice"
    profile: str = "Product Manager"
    goal: str = "Create a Product Requirement Document or market research/competitive product research."
    constraints: str = "utilize the same language as the user requirements for seamless communication"
    instruction: str = PRODUCT_MANAGER_INSTRUCTION
    tools: list[str] = ["RoleZero", Browser.__name__, Editor.__name__, SearchEnhancedQA.__name__]

    todo_action: str = any_to_name(WritePRD)
    use_openspec: bool = True  # Enable OpenSpec by default

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        # Determine which WritePRD action to use
        write_prd_action = WritePRDWithOpenSpec if self.use_openspec else WritePRD

        if self.use_fixed_sop:
            self.enable_memory = False
            self.set_actions([PrepareDocuments(send_to=any_to_str(self)), write_prd_action])
            self._watch([UserRequirement, PrepareDocuments])
            self.rc.react_mode = RoleReactMode.BY_ORDER

    def _update_tool_execution(self):
        # Choose the appropriate WritePRD action based on OpenSpec setting
        write_prd_action = WritePRDWithOpenSpec if self.use_openspec else WritePRD
        wp = write_prd_action()
        self.tool_execution_map.update(tool2name(write_prd_action, ["run"], wp.run))

    async def _think(self) -> bool:
        """Decide what to do"""
        if not self.use_fixed_sop:
            return await super()._think()

        if GitRepository.is_git_dir(self.config.project_path) and not self.config.git_reinit:
            self._set_state(1)
        else:
            self._set_state(0)
            self.config.git_reinit = False
            # Set the appropriate todo action based on OpenSpec setting
            write_prd_action = WritePRDWithOpenSpec if self.use_openspec else WritePRD
            self.todo_action = any_to_name(write_prd_action)
        return bool(self.rc.todo)

    def set_openspec_mode(self, use_openspec: bool):
        """Enable or disable OpenSpec mode.

        Args:
            use_openspec: Whether to use OpenSpec-compliant requirement generation
        """
        self.use_openspec = use_openspec
        logger.info(f"ProductManager OpenSpec mode set to: {use_openspec}")

        # Update actions if using fixed SOP
        if self.use_fixed_sop:
            write_prd_action = WritePRDWithOpenSpec if self.use_openspec else WritePRD
            self.set_actions([PrepareDocuments(send_to=any_to_str(self)), write_prd_action])

        # Update todo action
        self.todo_action = any_to_name(write_prd_action)
