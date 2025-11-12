#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
WriteTasks with OpenSpec Integration

Enhanced task generation action that creates OpenSpec-compliant task specifications
with clear traceability from requirements to implementation.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import List, Optional, Union, Dict, Any

from pydantic import BaseModel, Field

from metagpt.actions import Action
from metagpt.actions.project_management import WriteTasks
from metagpt.actions.project_management_an import (
    REQUIRED_PACKAGES,
    REQUIRED_OTHER_LANGUAGE_PACKAGES,
    LOGIC_ANALYSIS,
    TASK_LIST,
    FULL_API_SPEC,
    SHARED_KNOWLEDGE,
    PM_NODE,
)
from metagpt.logs import logger
from metagpt.schema import AIMessage, Message
from metagpt.tools.tool_registry import register_tool
from metagpt.utils.common import (
    aread,
    awrite,
    rectify_pathname,
    save_json_to_markdown,
    to_markdown_code_block,
)
from metagpt.utils.project_repo import ProjectRepo

from metagpt.utils.openspec import (
    OpenSpecTemplateEngine,
    OpenSpecValidator,
    OpenSpecTask,
)


@register_tool(include_functions=["run"])
class WriteTasksWithOpenSpec(WriteTasks):
    """
    Enhanced WriteTasks action with OpenSpec compliance.

    Generates OpenSpec-compliant task specifications with clear requirement traceability
    and scenario-based implementation planning.
    """

    openspec_template_engine: OpenSpecTemplateEngine = Field(default_factory=OpenSpecTemplateEngine)
    openspec_validator: OpenSpecValidator = Field(default_factory=OpenSpecValidator)
    use_openspec: bool = Field(default=True, description="Whether to use OpenSpec format")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Initialize OpenSpec components
        self.openspec_template_engine = OpenSpecTemplateEngine()
        self.openspec_validator = OpenSpecValidator(strict_mode=False)

    async def generate_openspec_tasks(
        self,
        design_content: str,
        requirements: Optional[List[Dict[str, Any]]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> OpenSpecTaskSpecification:
        """Generate OpenSpec-compliant task specification.

        Args:
            design_content: System design content
            requirements: List of requirements to implement
            context: Additional context information

        Returns:
            OpenSpecTaskSpecification specification
        """
        logger.info("Generating OpenSpec task specification from design")

        # Extract task information using existing LLM capability
        task_data = await self._extract_tasks_with_llm(design_content, context)

        # Map requirements to tasks
        if requirements:
            task_data = self._map_requirements_to_tasks(task_data, requirements)

        # Create OpenSpec task specification
        task_spec = OpenSpecTaskSpecification(
            name=self._generate_task_spec_name(design_content),
            description=self._generate_task_spec_description(design_content),
            implementation_tasks=task_data.get("tasks", []),
            package_dependencies=task_data.get("package_dependencies", []),
            api_specifications=task_data.get("api_specifications"),
            shared_knowledge=task_data.get("shared_knowledge"),
        )

        # Update requirement mappings
        task_spec.update_requirement_mappings()

        # Validate the generated specification
        # Note: We would create a TaskValidator, but for now using basic validation
        errors = task_spec.get_validation_errors()
        if errors:
            logger.warning(f"OpenSpec task validation issues found: {len(errors)} issues")
            for error in errors[:3]:  # Log first 3 errors
                logger.debug(f"  {error}")

        return task_spec

    async def _extract_tasks_with_llm(
        self,
        design_content: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Extract and structure tasks using LLM.

        Args:
            design_content: System design content
            context: Additional context

        Returns:
            Structured task data
        """
        # Use existing PM_NODE with enhanced prompt for OpenSpec compliance
        prompt = self._create_openspec_task_extraction_prompt(design_content, context)

        try:
            # Use the existing LLM integration
            node = await PM_NODE.fill(req=prompt, llm=self.llm, schema="json")

            # Parse the response
            llm_result = node.instruct_content.model_dump() if hasattr(node, 'instruct_content') else {}

            # Convert to OpenSpec task format
            task_data = self._convert_llm_output_to_openspec_tasks(llm_result, design_content)
            return task_data

        except Exception as e:
            logger.error(f"Error extracting tasks with LLM: {e}")
            # Fallback to basic task generation
            return self._generate_fallback_tasks(design_content)

    def _create_openspec_task_extraction_prompt(
        self,
        design_content: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Create prompt for LLM to extract tasks with OpenSpec compliance.

        Args:
            design_content: System design content
            context: Additional context

        Returns:
            Formatted prompt string
        """
        context_str = ""
        if context:
            context_parts = []
            for key, value in context.items():
                if value:
                    context_parts.append(f"{key}: {value}")
            if context_parts:
                context_str = f"\nAdditional Context:\n" + "\n".join(context_parts)

        prompt = f"""
Analyze the following system design and generate implementation tasks in OpenSpec-compliant format.

System Design:
{design_content}
{context_str}

Please provide the tasks in the following structured format:
{{
    "tasks": [
        {{
            "task_id": "unique_task_id",
            "title": "Descriptive task title",
            "description": "Detailed description of what needs to be implemented",
            "implementation_type": "class|function|api|interface|component",
            "file_path": "path/to/target/file.py",
            "acceptance_criteria": [
                "Specific criteria that must be met for completion"
            ],
            "dependencies": ["task_ids that this depends on"],
            "priority": "critical|high|medium|low",
            "estimated_effort": "time estimate (e.g., '2 days', '4 hours')",
            "language": "python|javascript|typescript|etc",
            "framework": "react|fastapi|flask|etc",
            "test_requirements": [
                "Testing requirements for this task"
            ],
            "implementation_notes": "Specific guidance for implementation"
        }}
    ],
    "package_dependencies": [
        "required==1.0.0",
        "other_package>=2.0.0"
    ],
    "api_specifications": "OpenAPI spec if applicable",
    "shared_knowledge": "Common utilities, patterns, or knowledge to share"
}}

Guidelines for OpenSpec-compliant task generation:
1. Each task should be clearly traceable to a requirement or design component
2. Tasks should be specific and implementable by a single developer
3. Include clear acceptance criteria that can be objectively verified
4. Consider dependencies and logical order of implementation
5. Estimate realistic effort and assign appropriate priority
6. Include technical specifications (language, framework)
7. Provide implementation guidance and testing requirements
8. Group related functionality into logical tasks
"""
        return prompt

    def _convert_llm_output_to_openspec_tasks(
        self,
        llm_output: Dict[str, Any],
        design_content: str
    ) -> Dict[str, Any]:
        """Convert LLM output to OpenSpec task format.

        Args:
            llm_output: Raw LLM response
            design_content: Original design content

        Returns:
            Structured task data in OpenSpec format
        """
        tasks = []

        # Extract tasks from LLM output
        raw_tasks = llm_output.get("tasks", [])
        if not raw_tasks:
            return self._generate_fallback_tasks(design_content)

        for i, raw_task in enumerate(raw_tasks):
            # Create ImplementationTask
            task = ImplementationTask(
                task_id=raw_task.get("task_id", f"task_{i+1}"),
                title=raw_task.get("title", f"Task {i+1}"),
                description=raw_task.get("description", "Implementation task"),
                requirement_id=raw_task.get("requirement_id", f"REQ_{i+1}"),
                requirement_title=raw_task.get("requirement_title", f"Requirement {i+1}"),
                scenario_id=raw_task.get("scenario_id"),
                file_path=raw_task.get("file_path"),
                implementation_type=raw_task.get("implementation_type", "function"),
                acceptance_criteria=raw_task.get("acceptance_criteria", []),
                dependencies=raw_task.get("dependencies", []),
                priority=TaskPriority(raw_task.get("priority", "medium")),
                estimated_effort=raw_task.get("estimated_effort"),
                language=raw_task.get("language"),
                framework=raw_task.get("framework"),
                test_requirements=raw_task.get("test_requirements", []),
                implementation_notes=raw_task.get("implementation_notes")
            )
            tasks.append(task)

        return {
            "tasks": tasks,
            "package_dependencies": llm_output.get("package_dependencies", []),
            "api_specifications": llm_output.get("api_specifications"),
            "shared_knowledge": llm_output.get("shared_knowledge")
        }

    def _generate_fallback_tasks(self, design_content: str) -> Dict[str, Any]:
        """Generate fallback tasks when LLM extraction fails.

        Args:
            design_content: System design content

        Returns:
            Basic task structure
        """
        # Extract basic structure from design content
        lines = design_content.split('\n')
        components = []

        for line in lines:
            # Look for component or class definitions
            if any(keyword in line.lower() for keyword in ['class', 'component', 'module', 'service']):
                # Extract component name
                match = re.search(r'\b(\w+)\b', line)
                if match:
                    components.append(match.group(1))

        tasks = []
        for i, component in enumerate(components[:5]):  # Limit to 5 components
            task = ImplementationTask(
                task_id=f"task_{i+1}",
                title=f"Implement {component}",
                description=f"Implement the {component} component based on system design",
                requirement_id=f"REQ_{i+1}",
                requirement_title=f"Component Implementation Requirement {i+1}",
                implementation_type="class",
                file_path=f"{component.lower()}.py",
                acceptance_criteria=[
                    f"Component {component} is implemented correctly",
                    "Functionality matches design specifications",
                    "Code follows project conventions"
                ],
                priority=TaskPriority.MEDIUM,
                estimated_effort="1 day",
                language="python"
            )
            tasks.append(task)

        return {
            "tasks": tasks,
            "package_dependencies": [],
            "shared_knowledge": "Follow existing code patterns and conventions"
        }

    def _map_requirements_to_tasks(
        self,
        task_data: Dict[str, Any],
        requirements: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Map requirements to implementation tasks.

        Args:
            task_data: Current task data
            requirements: List of requirements

        Returns:
            Updated task data with requirement mappings
        """
        for i, task in enumerate(task_data.get("tasks", [])):
            if i < len(requirements):
                req = requirements[i]
                task["requirement_id"] = req.get("id", f"REQ_{i+1}")
                task["requirement_title"] = req.get("title", f"Requirement {i+1}")

                # Add requirement-specific acceptance criteria
                if req.get("acceptance_criteria"):
                    task["acceptance_criteria"].extend(req["acceptance_criteria"])

        return task_data

    def _generate_task_spec_name(self, design_content: str) -> str:
        """Generate a name for the task specification.

        Args:
            design_content: System design content

        Returns:
            Generated task specification name
        """
        # Extract key information from design
        lines = design_content.split('\n')
        for line in lines:
            if 'project' in line.lower() or 'system' in line.lower():
                # Extract project/system name
                words = re.findall(r'\b[A-Z][a-z]+\b', line)
                if words:
                    return f"{' '.join(words[:2])} Implementation Tasks"

        return "System Implementation Tasks"

    def _generate_task_spec_description(self, design_content: str) -> str:
        """Generate a description for the task specification.

        Args:
            design_content: System design content

        Returns:
            Generated description
        """
        first_lines = design_content.split('\n')[:3]
        description = "Implementation tasks derived from system design:\n"
        description += "\n".join(first_lines)

        if len(description) > 200:
            description = description[:200] + "..."

        return description

    async def run(
        self,
        with_messages: List[Message] = None,
        *,
        user_requirement: str = "",
        design_filename: str = "",
        output_pathname: str = "",
        use_openspec: Optional[bool] = None,
        **kwargs,
    ) -> Union[AIMessage, str]:
        """
        Write project tasks with OpenSpec support.

        Args:
            with_messages: Messages with context
            user_requirement: User's requirement description
            design_filename: Design document filename
            output_pathname: Output file path
            use_openspec: Whether to use OpenSpec format (overrides default)
            **kwargs: Additional arguments

        Returns:
            Generated task specification or AIMessage
        """
        # Determine whether to use OpenSpec
        should_use_openspec = use_openspec if use_openspec is not None else self.use_openspec

        if should_use_openspec:
            return await self._run_openspec(
                with_messages=with_messages,
                user_requirement=user_requirement,
                design_filename=design_filename,
                output_pathname=output_pathname,
                **kwargs,
            )
        else:
            # Fall back to original WriteTasks behavior
            return await super().run(
                with_messages=with_messages,
                user_requirement=user_requirement,
                design_filename=design_filename,
                output_pathname=output_pathname,
                **kwargs,
            )

    async def _run_openspec(
        self,
        with_messages: List[Message] = None,
        *,
        user_requirement: str = "",
        design_filename: str = "",
        output_pathname: str = "",
        **kwargs,
    ) -> Union[AIMessage, str]:
        """Run with OpenSpec format.

        Args:
            with_messages: Messages with context
            user_requirement: User requirement
            design_filename: Design filename
            output_pathname: Output path
            **kwargs: Additional arguments

        Returns:
            Generated OpenSpec task specification
        """
        if not with_messages:
            return await self._execute_openspec_api(
                user_requirement=user_requirement,
                design_filename=design_filename,
                output_pathname=output_pathname,
                **kwargs,
            )

        try:
            # Load design content
            self.repo = ProjectRepo(self.config.project_path)

            if design_filename:
                design_content = await aread(design_filename)
            else:
                # Use first available design file
                design_files = list(self.repo.docs.system_design.workdir.glob("*.json"))
                if design_files:
                    design_content = await aread(design_files[0])
                else:
                    raise ValueError("No design file found")

            # Extract requirements from messages if available
            requirements = self._extract_requirements_from_messages(with_messages)

            # Generate OpenSpec task specification
            task_spec = await self.generate_openspec_tasks(
                design_content=design_content,
                requirements=requirements,
                context={"user_requirement": user_requirement}
            )

            # Convert to markdown
            openspec_content = task_spec.to_markdown()

            # Save to file if path specified
            if output_pathname:
                await self._save_openspec_tasks(openspec_content, output_pathname, task_spec)

            # Return the OpenSpec task specification object for further processing
            return task_spec

        except Exception as e:
            logger.error(f"Error generating OpenSpec tasks: {e}")
            # Fallback to original task generation
            logger.info("Falling back to original task generation")
            return await super().run(
                with_messages=with_messages,
                user_requirement=user_requirement,
                design_filename=design_filename,
                output_pathname=output_pathname,
                **kwargs,
            )

    def _extract_requirements_from_messages(self, with_messages: List[Message]) -> List[Dict[str, Any]]:
        """Extract requirements from message history.

        Args:
            with_messages: List of messages

        Returns:
            List of requirements
        """
        requirements = []

        for message in with_messages:
            content = message.content.lower() if hasattr(message, 'content') else ""

            # Look for OpenSpec requirement markers
            if "requirement:" in content or "scenario:" in content:
                # Simple extraction - in a real implementation, this would be more sophisticated
                req_id = f"REQ_{len(requirements) + 1}"
                req_title = f"Requirement from message {len(requirements) + 1}"

                requirements.append({
                    "id": req_id,
                    "title": req_title,
                    "acceptance_criteria": ["Must fulfill specified functionality"]
                })

        return requirements

    async def _save_openspec_tasks(
        self,
        content: str,
        output_pathname: str,
        task_spec: OpenSpecTaskSpecification,
    ):
        """Save OpenSpec task content to file.

        Args:
            content: Markdown content
            output_pathname: Output file path
            task_spec: The OpenSpec task specification object
        """
        try:
            # Ensure directory exists
            output_path = Path(output_pathname)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Save markdown content
            await awrite(output_pathname, content)

            # Also save as JSON for structured access
            json_path = output_path.with_suffix('.json')
            json_content = task_spec.json(indent=2)
            await awrite(str(json_path), json_content)

            logger.info(f"OpenSpec task specification saved to: {output_pathname}")
            logger.info(f"OpenSpec task JSON saved to: {json_path}")

        except Exception as e:
            logger.error(f"Error saving OpenSpec tasks: {e}")
            raise

    async def _execute_openspec_api(
        self,
        *,
        user_requirement: str = "",
        design_filename: str = "",
        output_pathname: str = "",
        **kwargs,
    ) -> AIMessage:
        """Execute OpenSpec API version.

        Args:
            user_requirement: User requirement
            design_filename: Design filename
            output_pathname: Output path
            **kwargs: Additional arguments

        Returns:
            AIMessage with result
        """
        try:
            # Load design content
            if design_filename:
                design_content = await aread(design_filename)
            else:
                raise ValueError("Design filename is required for OpenSpec task generation")

            # Generate OpenSpec task specification
            task_spec = await self.generate_openspec_tasks(
                design_content=design_content,
                context={"user_requirement": user_requirement}
            )

            # Convert to markdown
            openspec_content = task_spec.to_markdown()

            # Save if path specified
            if output_pathname:
                await self._save_openspec_tasks(openspec_content, output_pathname, task_spec)

            # Create AIMessage result
            instruct_content = AIMessage.create_instruct_value(
                kvs={
                    "user_requirement": user_requirement,
                    "task_spec_name": task_spec.name,
                    "total_tasks": task_spec.total_tasks,
                    "overall_progress": task_spec.overall_progress,
                },
                class_name="WriteTasksWithOpenSpecOutput",
            )

            return AIMessage(
                content=openspec_content,
                instruct_content=instruct_content,
            )

        except Exception as e:
            logger.error(f"Error in OpenSpec API execution: {e}")
            raise