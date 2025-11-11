#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
WritePRD with OpenSpec Integration

Enhanced PRD writing action that generates OpenSpec-compliant requirements.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional, Union, Dict, Any

from pydantic import BaseModel, Field

from metagpt.actions import Action, ActionOutput
from metagpt.actions.action_node import ActionNode
from metagpt.actions.write_prd import WritePRD
from metagpt.const import REQUIREMENT_FILENAME
from metagpt.logs import logger
from metagpt.schema import AIMessage, Document, Documents, Message
from metagpt.utils.common import (
    CodeParser,
    aread,
    awrite,
    rectify_pathname,
    save_json_to_markdown,
    to_markdown_code_block,
)
from metagpt.utils.file_repository import FileRepository
from metagpt.utils.mermaid import mermaid_to_file
from metagpt.utils.project_repo import ProjectRepo
from metagpt.utils.report import DocsReporter, GalleryReporter

from metagpt.openspec import (
    OpenSpecTemplateEngine,
    OpenSpecRequirement,
    OpenSpecValidator,
    Requirement,
    Scenario,
)
from metagpt.openspec.models.requirement import RequirementOperation


class WritePRDWithOpenSpec(WritePRD):
    """
    Enhanced PRD writing action with OpenSpec compliance.

    Generates OpenSpec-compliant requirement specifications with structured
    format and scenario-based definitions.
    """

    openspec_template_engine: OpenSpecTemplateEngine = Field(default_factory=OpenSpecTemplateEngine)
    openspec_validator: OpenSpecValidator = Field(default_factory=OpenSpecValidator)
    use_openspec: bool = Field(default=True, description="Whether to use OpenSpec format")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Initialize OpenSpec components
        self.openspec_template_engine = OpenSpecTemplateEngine()
        self.openspec_validator = OpenSpecValidator(strict_mode=False)

    async def generate_openspec_requirement(
        self,
        user_requirement: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> OpenSpecRequirement:
        """Generate an OpenSpec-compliant requirement specification.

        Args:
            user_requirement: User's requirement description
            context: Additional context information

        Returns:
            OpenSpecRequirement specification
        """
        logger.info(f"Generating OpenSpec requirement for: {user_requirement[:100]}...")

        # Extract requirements using LLM
        requirements_data = await self._extract_requirements_with_llm(user_requirement, context)

        # Create OpenSpec requirement structure
        openspec_req = OpenSpecRequirement(
            name=self._generate_requirement_name(user_requirement),
            version="1.0",
            description=self._generate_requirement_description(user_requirement, requirements_data),
            added_requirements=requirements_data.get("requirements", []),
        )

        # Validate the generated specification
        validation_result = self.openspec_validator.validate(openspec_req)
        if not validation_result.is_valid:
            logger.warning(f"OpenSpec validation issues found: {validation_result.get_summary()}")
            # Log detailed issues for debugging
            for issue in validation_result.issues:
                logger.debug(f"  {issue}")

        return openspec_req

    async def _extract_requirements_with_llm(
        self,
        user_requirement: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Extract and structure requirements using LLM.

        Args:
            user_requirement: Raw user requirement
            context: Additional context

        Returns:
            Structured requirements data
        """
        # Create prompt for requirement extraction
        prompt = self._create_requirement_extraction_prompt(user_requirement, context)

        # Use the existing LLM capability from WritePRD
        llm_result = await self._llm_generate_requirements(prompt)

        # Parse and structure the result
        requirements_data = self._parse_llm_requirements_output(llm_result)

        return requirements_data

    def _create_requirement_extraction_prompt(
        self,
        user_requirement: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Create prompt for LLM to extract requirements.

        Args:
            user_requirement: Raw user requirement
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
Extract and structure the following user requirement into OpenSpec-compliant requirements.

User Requirement:
{user_requirement}
{context_str}

Please provide the requirements in the following JSON format:
{{
    "requirements": [
        {{
            "title": "Requirement title",
            "description": "Detailed description of the requirement",
            "scenarios": [
                {{
                    "name": "Scenario name",
                    "given": "Precondition/context",
                    "when": "Action/trigger",
                    "then": "Expected outcome"
                }}
            ],
            "acceptance_criteria": ["Criterion 1", "Criterion 2"],
            "priority": "high|medium|low",
            "category": "functional|non-functional|constraint"
        }}
    ]
}}

Guidelines:
1. Break down complex requirements into smaller, manageable ones
2. Each requirement must have at least one scenario with Given/When/Then structure
3. Use clear, specific language without ambiguity
4. Include acceptance criteria that can be objectively verified
5. Assign appropriate priority and category
6. Focus on what the system should do, not how to implement it
"""
        return prompt

    async def _llm_generate_requirements(self, prompt: str) -> str:
        """Generate requirements using LLM.

        Args:
            prompt: The formatted prompt

        Returns:
            LLM response text
        """
        # Use the existing LLM integration from parent class
        # This is a simplified version - in practice, you'd use the actual LLM API
        try:
            # For now, return a mock response
            # In a real implementation, this would call the LLM
            mock_response = '''{
    "requirements": [
        {
            "title": "Core Functionality Implementation",
            "description": "Implement the core functionality based on user requirements",
            "scenarios": [
                {
                    "name": "Successful operation",
                    "given": "System is initialized and inputs are valid",
                    "when": "User performs the required action",
                    "then": "System processes the request and returns expected result"
                }
            ],
            "acceptance_criteria": [
                "System handles valid inputs correctly",
                "System provides appropriate feedback",
                "Error conditions are handled gracefully"
            ],
            "priority": "high",
            "category": "functional"
        }
    ]
}'''
            return mock_response
        except Exception as e:
            logger.error(f"Error generating requirements with LLM: {e}")
            raise

    def _parse_llm_requirements_output(self, llm_output: str) -> Dict[str, Any]:
        """Parse LLM output into structured requirements data.

        Args:
            llm_output: Raw LLM response

        Returns:
            Parsed requirements data
        """
        def add_ids_to_requirements(requirements):
            """Add unique IDs to requirements if missing."""
            for i, req in enumerate(requirements):
                if 'id' not in req:
                    req['id'] = f"REQ-{i+1:03d}"
            return requirements

        try:
            # Try to parse as JSON
            data = json.loads(llm_output)
            if 'requirements' in data:
                data['requirements'] = add_ids_to_requirements(data['requirements'])
            return data
        except json.JSONDecodeError:
            logger.warning("LLM output is not valid JSON, attempting to extract with regex")
            # Fallback: try to extract JSON from the text
            import re
            json_match = re.search(r'\\{[\\s\\S]*\\}', llm_output)
            if json_match:
                try:
                    data = json.loads(json_match.group())
                    if 'requirements' in data:
                        data['requirements'] = add_ids_to_requirements(data['requirements'])
                    return data
                except json.JSONDecodeError:
                    pass

            # Last resort: create a basic requirement structure
            logger.warning("Could not parse LLM output, creating basic requirement structure")
            return {
                "requirements": [
                    {
                        "id": "REQ-001",
                        "title": "Main Requirement",
                        "description": llm_output[:200] + "..." if len(llm_output) > 200 else llm_output,
                        "scenarios": [
                            {
                                "name": "Basic scenario",
                                "given": "System is ready",
                                "when": "User interacts with the system",
                                "then": "System responds appropriately"
                            }
                        ],
                        "acceptance_criteria": ["Requirement is fulfilled"],
                        "priority": "medium",
                        "category": "functional"
                    }
                ]
            }

    def _generate_requirement_name(self, user_requirement: str) -> str:
        """Generate a name for the requirement specification.

        Args:
            user_requirement: User's requirement description

        Returns:
            Generated requirement name
        """
        # Extract key terms and create a concise name
        import re
        words = re.findall(r'\\b\\w+\\b', user_requirement.lower())
        # Remove common words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        key_words = [w for w in words if w not in stop_words and len(w) > 2][:5]

        if key_words:
            name = " ".join(word.capitalize() for word in key_words)
            return name

        return "System Requirements"

    def _generate_requirement_description(self, user_requirement: str, requirements_data: Dict[str, Any]) -> str:
        """Generate a description for the requirement specification.

        Args:
            user_requirement: Original user requirement
            requirements_data: Structured requirements data

        Returns:
            Generated description
        """
        requirements = requirements_data.get("requirements", [])
        req_count = len(requirements)

        description = f"This specification defines {req_count} requirement{'s' if req_count != 1 else ''} "
        description += f"derived from the following user request: {user_requirement}"

        if req_count > 1:
            description += f"\\n\\nThe requirements cover various aspects including {', '.join(req.get('category', 'functional') for req in requirements[:3])}"

        return description

    async def run(
        self,
        with_messages: List[Message] = None,
        *,
        user_requirement: str = "",
        output_pathname: str = "",
        legacy_prd_filename: str = "",
        extra_info: str = "",
        use_openspec: Optional[bool] = None,
        **kwargs,
    ) -> Union[AIMessage, str]:
        """
        Write a Product Requirement Document with OpenSpec support.

        Args:
            user_requirement: User's requirement description
            output_pathname: Output file path
            legacy_prd_filename: Legacy PRD filename for reference
            extra_info: Additional information
            use_openspec: Whether to use OpenSpec format (overrides default)
            **kwargs: Additional arguments

        Returns:
            Generated PRD content or AIMessage
        """
        # Determine whether to use OpenSpec
        should_use_openspec = use_openspec if use_openspec is not None else self.use_openspec

        if should_use_openspec:
            return await self._run_openspec(
                with_messages=with_messages,
                user_requirement=user_requirement,
                output_pathname=output_pathname,
                legacy_prd_filename=legacy_prd_filename,
                extra_info=extra_info,
                **kwargs,
            )
        else:
            # Fall back to original WritePRD behavior
            return await super().run(
                with_messages=with_messages,
                user_requirement=user_requirement,
                output_pathname=output_pathname,
                legacy_prd_filename=legacy_prd_filename,
                extra_info=extra_info,
                **kwargs,
            )

    async def _run_openspec(
        self,
        with_messages: List[Message] = None,
        *,
        user_requirement: str = "",
        output_pathname: str = "",
        legacy_prd_filename: str = "",
        extra_info: str = "",
        **kwargs,
    ) -> Union[AIMessage, str]:
        """Run with OpenSpec format.

        Args:
            with_messages: Messages with context
            user_requirement: User requirement
            output_pathname: Output path
            legacy_prd_filename: Legacy PRD filename
            extra_info: Extra information
            **kwargs: Additional arguments

        Returns:
            Generated OpenSpec specification
        """
        if not with_messages:
            return await self._execute_openspec_api(
                user_requirement=user_requirement,
                output_pathname=output_pathname,
                legacy_prd_filename=legacy_prd_filename,
                extra_info=extra_info,
                **kwargs,
            )

        # Extract context from messages
        context = self._extract_context_from_messages(with_messages)

        # Generate OpenSpec requirement
        try:
            openspec_requirement = await self.generate_openspec_requirement(
                user_requirement=user_requirement,
                context=context
            )

            # Convert to markdown
            openspec_content = openspec_requirement.to_markdown()

            # Save to file if path specified
            if output_pathname:
                await self._save_openspec_content(openspec_content, output_pathname, openspec_requirement)

            # Return the OpenSpec requirement object for further processing
            return openspec_requirement

        except Exception as e:
            logger.error(f"Error generating OpenSpec requirement: {e}")
            # Fallback to original PRD generation
            logger.info("Falling back to original PRD generation")
            return await super().run(
                with_messages=with_messages,
                user_requirement=user_requirement,
                output_pathname=output_pathname,
                legacy_prd_filename=legacy_prd_filename,
                extra_info=extra_info,
                **kwargs,
            )

    def _extract_context_from_messages(self, with_messages: List[Message]) -> Dict[str, Any]:
        """Extract context information from messages.

        Args:
            with_messages: List of messages

        Returns:
            Context dictionary
        """
        context = {}

        for message in with_messages:
            if hasattr(message, 'content') and message.content:
                # Extract key information from message content
                content_lower = message.content.lower()
                if any(keyword in content_lower for keyword in ['project', 'system', 'application']):
                    context['project_context'] = message.content[:500]  # Limit length

                # Extract any structured data
                if hasattr(message, 'instruct_content') and message.instruct_content:
                    try:
                        context_data = message.instruct_content.dict() if hasattr(message.instruct_content, 'dict') else message.instruct_content
                        context.update(context_data)
                    except Exception:
                        pass

        return context

    async def _save_openspec_content(
        self,
        content: str,
        output_pathname: str,
        openspec_requirement: OpenSpecRequirement,
    ):
        """Save OpenSpec content to file.

        Args:
            content: Markdown content
            output_pathname: Output file path
            openspec_requirement: The OpenSpec requirement object
        """
        try:
            # Ensure directory exists
            output_path = Path(output_pathname)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Save markdown content
            await awrite(output_pathname, content)

            # Also save as JSON for structured access
            json_path = output_path.with_suffix('.json')
            json_content = openspec_requirement.json(indent=2)
            await awrite(str(json_path), json_content)

            logger.info(f"OpenSpec specification saved to: {output_pathname}")
            logger.info(f"OpenSpec JSON saved to: {json_path}")

        except Exception as e:
            logger.error(f"Error saving OpenSpec content: {e}")
            raise

    async def _execute_openspec_api(
        self,
        *,
        user_requirement: str = "",
        output_pathname: str = "",
        legacy_prd_filename: str = "",
        extra_info: str = "",
        **kwargs,
    ) -> AIMessage:
        """Execute OpenSpec API version.

        Args:
            user_requirement: User requirement
            output_pathname: Output path
            legacy_prd_filename: Legacy PRD filename
            extra_info: Extra information
            **kwargs: Additional arguments

        Returns:
            AIMessage with result
        """
        # Generate OpenSpec requirement
        context = {}
        if extra_info:
            context['extra_info'] = extra_info

        openspec_requirement = await self.generate_openspec_requirement(
            user_requirement=user_requirement,
            context=context
        )

        # Convert to markdown
        openspec_content = openspec_requirement.to_markdown()

        # Save if path specified
        if output_pathname:
            await self._save_openspec_content(openspec_content, output_pathname, openspec_requirement)

        # Create AIMessage result
        instruct_content = AIMessage.create_instruct_value(
            kvs={
                "user_requirement": user_requirement,
                "requirement_name": openspec_requirement.name,
                "requirement_count": len(openspec_requirement.get_all_requirements()),
                "validation_summary": self.openspec_validator.validate(openspec_requirement).get_summary(),
            },
            class_name="WritePRDWithOpenSpecOutput",
        )

        return AIMessage(
            content=openspec_content,
            instruct_content=instruct_content,
        )