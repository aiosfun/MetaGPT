#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 15:04
@Author  : alexanderwu
@File    : project_manager.py
"""
from metagpt.actions import WriteTasks
from metagpt.actions.design_api import WriteDesign
from metagpt.actions.write_tasks_openspec import WriteTasksWithOpenSpec
from metagpt.logs import logger
from metagpt.roles.di.role_zero import RoleZero
from metagpt.utils.common import any_to_name, tool2name


class ProjectManager(RoleZero):
    """
    Represents a Project Manager role responsible for overseeing project execution and team efficiency.

    Attributes:
        name (str): Name of the project manager.
        profile (str): Role profile, default is 'Project Manager'.
        goal (str): Goal of the project manager.
        constraints (str): Constraints or limitations for the project manager.
        use_openspec (bool): Whether to use OpenSpec-compliant task generation.
    """

    name: str = "Eve"
    profile: str = "Project Manager"
    goal: str = (
        "break down tasks according to PRD/technical design, generate a task list, and analyze task "
        "dependencies to start with the prerequisite modules"
    )
    constraints: str = "use same language as user requirement"

    instruction: str = """Use WriteTasks tool to write a project task list"""
    max_react_loop: int = 1  # FIXME: Read and edit files requires more steps, consider later
    tools: list[str] = ["Editor:write,read,similarity_search", "RoleZero", "WriteTasks"]

    use_openspec: bool = True  # Enable OpenSpec by default

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        # Determine which WriteTasks action to use
        write_tasks_action = WriteTasksWithOpenSpec if self.use_openspec else WriteTasks

        # NOTE: The following init setting will only be effective when self.use_fixed_sop is changed to True
        self.enable_memory = False
        self.set_actions([write_tasks_action])
        self._watch([WriteDesign])

    def _update_tool_execution(self):
        # Choose the appropriate WriteTasks action based on OpenSpec setting
        write_tasks_action = WriteTasksWithOpenSpec if self.use_openspec else WriteTasks
        wt = write_tasks_action()
        self.tool_execution_map.update(
            {
                "WriteTasks.run": wt.run,
                "WriteTasks": wt.run,  # alias
            }
        )

    def set_openspec_mode(self, use_openspec: bool):
        """Enable or disable OpenSpec mode.

        Args:
            use_openspec: Whether to use OpenSpec-compliant task generation
        """
        self.use_openspec = use_openspec
        logger.info(f"ProjectManager OpenSpec mode set to: {use_openspec}")

        # Update actions if using fixed SOP
        if self.use_fixed_sop:
            write_tasks_action = WriteTasksWithOpenSpec if self.use_openspec else WriteTasks
            self.set_actions([write_tasks_action])
