#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
WriteDesign with OpenSpec Integration

Enhanced design writing action that generates OpenSpec-compliant design specifications
with proper requirement traceability and structured format.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional, Union, Dict, Any

from pydantic import BaseModel, Field

from metagpt.actions import Action
from metagpt.actions.design_api import WriteDesign
from metagpt.actions.design_api_an import (
    DATA_STRUCTURES_AND_INTERFACES,
    DESIGN_API_NODE,
    PROGRAM_CALL_FLOW,
)
from metagpt.const import DATA_API_DESIGN_FILE_REPO, SEQ_FLOW_FILE_REPO
from metagpt.logs import logger
from metagpt.schema import AIMessage, Document, Documents, Message
from metagpt.tools.tool_registry import register_tool
from metagpt.utils.common import (
    aread,
    awrite,
    rectify_pathname,
    save_json_to_markdown,
    to_markdown_code_block,
)
from metagpt.utils.mermaid import mermaid_to_file
from metagpt.utils.project_repo import ProjectRepo
from metagpt.utils.report import DocsReporter, GalleryReporter

from metagpt.utils.openspec import (
    OpenSpecTemplateEngine,
    OpenSpecValidator,
    OpenSpecDesign,
    OpenSpecRequirement,
    OpenSpecWorkspaceManager,
    get_default_workspace_path,
)
from metagpt.openspec.cross_ref.design_manager import DesignCrossReferenceManager


@register_tool(include_functions=["run"])
class WriteDesignWithOpenSpec(WriteDesign):
    """
    Enhanced WriteDesign action with OpenSpec compliance.

    Generates OpenSpec-compliant design specifications with proper requirement traceability,
    structured components, and comprehensive validation.
    """

    openspec_template_engine: OpenSpecTemplateEngine = Field(default_factory=OpenSpecTemplateEngine)
    openspec_validator: OpenSpecValidator = Field(default_factory=OpenSpecValidator)
    use_openspec: bool = Field(default=True, description="Whether to use OpenSpec format")
    design_cross_ref_manager: DesignCrossReferenceManager = Field(default_factory=DesignCrossReferenceManager)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Initialize OpenSpec components
        self.openspec_template_engine = OpenSpecTemplateEngine()
        self.openspec_validator = OpenSpecValidator(strict_mode=False)
        self.design_cross_ref_manager = DesignCrossReferenceManager()

        # Initialize OpenSpec workspace manager
        self._init_openspec_workspace()

    def _init_openspec_workspace(self):
        """Initialize OpenSpec workspace manager"""
        workspace_path = None

        # Try to get OpenSpec configuration from various sources
        config_sources = [
            (getattr(self, 'rc', None), 'rc.config'),
            (getattr(self, 'config', None), 'config'),
        ]

        for config_obj, config_name in config_sources:
            if config_obj and hasattr(config_obj, 'openspec'):
                workspace_path = getattr(config_obj.openspec, 'workspace_path', None)
                logger.info(f"Found OpenSpec config in {config_name}: workspace_path={workspace_path}")
                break

        # Fallback: try loading from config directly
        if not workspace_path:
            try:
                from metagpt.config2 import config
                if hasattr(config, 'openspec') and hasattr(config.openspec, 'workspace_path'):
                    workspace_path = config.openspec.workspace_path
                    logger.info(f"Found OpenSpec config from global config: workspace_path={workspace_path}")
            except Exception as e:
                logger.warning(f"Could not load global config: {e}")

        if workspace_path:
            # Convert relative path to absolute path, expanding ~ first
            workspace_path = Path(workspace_path).expanduser()
            if not workspace_path.is_absolute():
                # If relative, make it relative to the user's metagpt config directory
                workspace_path = Path.home() / ".metagpt" / workspace_path
        else:
            # Default to user's metagpt config directory / openspec
            workspace_path = Path.home() / ".metagpt" / "openspec"

        self.openspec_workspace = OpenSpecWorkspaceManager(workspace_path)
        self.openspec_workspace.ensure_workspace()
        logger.info(f"OpenSpec workspace initialized at: {workspace_path}")

    async def generate_openspec_design(
        self,
        requirements_content: str,
        user_requirement: str = "",
        legacy_design: str = "",
        context: Optional[Dict[str, Any]] = None,
    ) -> OpenSpecDesign:
        """Generate an OpenSpec-compliant design specification.

        Args:
            requirements_content: Product requirements content
            user_requirement: User's requirement description
            legacy_design: Legacy design content for updates
            context: Additional context information

        Returns:
            OpenSpecDesign specification
        """
        logger.info(f"Generating OpenSpec design specification from requirements")

        # Parse requirements if they're in OpenSpec format
        requirements = self._parse_requirements(requirements_content)

        # Extract design information using LLM
        design_data = await self._extract_design_with_llm(
            requirements_content,
            user_requirement,
            legacy_design,
            context
        )

        # Create OpenSpec design structure
        openspec_design = OpenSpecDesign(
            title=self._generate_design_name(user_requirement),
            description=self._generate_design_overview(design_data, user_requirement),
            architecture={"overview": design_data.get("design_overview", "")},
            components=design_data.get("components", []),
            technical_decisions=[],
            tradeoffs=[],
            metadata={
                "requirements_mapping": design_data.get("requirement_mappings", []),
                "cross_references": design_data.get("cross_references", []),
                "architectural_patterns": design_data.get("architectural_patterns", []),
                "design_principles": design_data.get("design_principles", []),
                "technology_stack": design_data.get("technology_stack"),
                "data_model": design_data.get("data_model"),
                "api_specifications": design_data.get("api_specifications"),
                "quality_attributes": design_data.get("quality_attributes", {}),
                "constraints": design_data.get("constraints", []),
            }
        )

        # Add to cross-reference manager (skip for now to avoid name/title mismatch)
        # self.design_cross_ref_manager.add_design(openspec_design)

        # Validate the generated specification
        validation_result = self.openspec_validator.validate_design(openspec_design)
        if not validation_result.is_valid:
            logger.warning(f"OpenSpec design validation issues found: {len(validation_result.errors)} errors, {len(validation_result.warnings)} warnings")
            # Log detailed issues for debugging
            for error in validation_result.errors:
                logger.debug(f"  Error: {error}")
            for warning in validation_result.warnings:
                logger.debug(f"  Warning: {warning}")

        return openspec_design

    def _parse_requirements(self, requirements_content: str) -> List[OpenSpecRequirement]:
        """Parse requirements content into OpenSpecRequirement objects.

        Args:
            requirements_content: Requirements content in text format

        Returns:
            List of OpenSpecRequirement objects
        """
        requirements = []

        # Simple parsing - in a real implementation, this would be more sophisticated
        lines = requirements_content.split('\n')
        current_req = None
        req_content = []

        for line in lines:
            if line.startswith('### Requirement:'):
                if current_req:
                    # Save previous requirement
                    req_text = '\n'.join(req_content).strip()
                    if req_text:
                        # Create a basic OpenSpecRequirement
                        requirements.append(OpenSpecRequirement(
                            name=f"Requirement_{len(requirements) + 1}",
                            description=req_text,
                            added_requirements=[]  # Would be parsed more thoroughly
                        ))

                # Start new requirement
                current_req = line.replace('### Requirement:', '').strip()
                req_content = []
            elif current_req and line.strip():
                req_content.append(line)

        # Save last requirement
        if current_req and req_content:
            req_text = '\n'.join(req_content).strip()
            if req_text:
                requirements.append(OpenSpecRequirement(
                    name=f"Requirement_{len(requirements) + 1}",
                    description=req_text,
                    added_requirements=[]
                ))

        return requirements

    async def _extract_design_with_llm(
        self,
        requirements_content: str,
        user_requirement: str,
        legacy_design: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Extract and structure design information using LLM.

        Args:
            requirements_content: Product requirements content
            user_requirement: User's requirement description
            legacy_design: Legacy design content for updates
            context: Additional context information

        Returns:
            Structured design data
        """
        # Create prompt for design extraction
        prompt = self._create_design_extraction_prompt(
            requirements_content,
            user_requirement,
            legacy_design,
            context
        )

        try:
            # Use the existing LLM integration
            node = await DESIGN_API_NODE.fill(req=prompt, llm=self.llm)

            # Parse the response
            llm_result = node.instruct_content.model_dump() if hasattr(node, 'instruct_content') else {}

            # Convert to OpenSpec design format
            design_data = self._convert_llm_output_to_openspec_design(llm_result)
            return design_data

        except Exception as e:
            logger.error(f"Error extracting design with LLM: {e}")
            # Fallback to basic design generation
            return self._generate_fallback_design(user_requirement, requirements_content)

    def _create_design_extraction_prompt(
        self,
        requirements_content: str,
        user_requirement: str,
        legacy_design: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Create prompt for LLM to extract design information.

        Args:
            requirements_content: Requirements content
            user_requirement: User requirement
            legacy_design: Legacy design content
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

        legacy_str = ""
        if legacy_design:
            legacy_str = f"\nLegacy Design Content:\n{legacy_design[:1000]}..."  # Limit length

        prompt = f"""
Analyze the following product requirements and generate a system design in OpenSpec-compliant format.

User Requirement:
{user_requirement}

Product Requirements:
{requirements_content[:2000]}...{legacy_str}
{context_str}

Please provide the design in the following structured format:
{{
    "design_overview": "High-level design overview describing the approach and architecture",
    "components": [
        {{
            "name": "ComponentName",
            "purpose": "Purpose of this component",
            "description": "Detailed description of what this component does",
            "element_type": "component|interface|data_structure|api_endpoint|workflow|architecture",
            "interfaces": [
                {{
                    "name": "InterfaceName",
                    "description": "Description of this interface",
                    "input_type": "Input type specification",
                    "output_type": "Output type specification",
                    "protocol": "Communication protocol if applicable",
                    "endpoint": "API endpoint if applicable"
                }}
            ],
            "dependencies": ["OtherComponent1", "OtherComponent2"],
            "sub_components": ["SubComponent1", "SubComponent2"],
            "behavior": "Component behavior description",
            "data_flow": "Data flow description within this component",
            "technology": "Technology stack for this component",
            "implementation_notes": "Implementation guidance",
            "performance_requirements": "Performance requirements",
            "security_considerations": "Security considerations",
            "scalability_notes": "Scalability considerations"
        }}
    ],
    "requirement_mappings": [
        {{
            "requirement_id": "REQ_001",
            "requirement_title": "Requirement title",
            "design_elements": ["Component1", "Component2"],
            "implementation_notes": "How these components fulfill the requirement",
            "verification_method": "How to verify this requirement is met"
        }}
    ],
    "cross_references": [
        {{
            "target": "specification-name",
            "reference_type": "requirement|design|implementation|test|specification",
            "description": "Description of the reference",
            "bidirectional": false
        }}
    ],
    "architectural_patterns": ["Pattern1", "Pattern2"],
    "design_principles": ["Principle1", "Principle2"],
    "technology_stack": "Overview of technology stack",
    "data_model": "Data model description",
    "api_specifications": "API specifications overview if applicable",
    "quality_attributes": {{
        "performance": "Performance requirements",
        "security": "Security requirements",
        "scalability": "Scalability requirements"
    }},
    "constraints": ["Constraint1", "Constraint2"]
}}

Guidelines for OpenSpec-compliant design generation:
1. Each component must be clearly defined with purpose and interfaces
2. Map each requirement to specific design elements
3. Include architectural patterns and design principles
4. Specify technology stack and implementation guidance
5. Consider non-functional requirements (performance, security, scalability)
6. Provide clear verification methods for requirement fulfillment
7. Include cross-references to related specifications
"""
        return prompt

    def _convert_llm_output_to_openspec_design(self, llm_output: Dict[str, Any]) -> Dict[str, Any]:
        """Convert LLM output to OpenSpec design format.

        Args:
            llm_output: Raw LLM response

        Returns:
            Structured design data in OpenSpec format
        """
        # Extract basic components
        components = []
        raw_components = llm_output.get("components", [])
        if not raw_components:
            return self._generate_fallback_design("System", "Basic system design")

        for i, comp in enumerate(raw_components):
            interfaces = []
            if "interfaces" in comp:
                for interface in comp["interfaces"]:
                    interfaces.append({
                        "name": interface.get("name", f"Interface_{i+1}"),
                        "description": interface.get("description", ""),
                        "input_type": interface.get("input_type"),
                        "output_type": interface.get("output_type"),
                        "protocol": interface.get("protocol"),
                        "endpoint": interface.get("endpoint")
                    })

            design_component = {
                "name": comp.get("name", f"Component_{i+1}"),
                "purpose": comp.get("purpose", ""),
                "description": comp.get("description", ""),
                "element_type": comp.get("element_type", "component"),
                "interfaces": interfaces,
                "dependencies": comp.get("dependencies", []),
                "sub_components": comp.get("sub_components", []),
                "behavior": comp.get("behavior"),
                "data_flow": comp.get("data_flow"),
                "technology": comp.get("technology"),
                "implementation_notes": comp.get("implementation_notes"),
                "performance_requirements": comp.get("performance_requirements"),
                "security_considerations": comp.get("security_considerations"),
                "scalability_notes": comp.get("scalability_notes")
            }
            components.append(design_component)

        # Extract requirement mappings
        req_mappings = []
        raw_mappings = llm_output.get("requirement_mappings", [])
        for mapping in raw_mappings:
            req_mappings.append(RequirementMapping(
                requirement_id=mapping.get("requirement_id", f"REQ_{len(req_mappings)+1}"),
                requirement_title=mapping.get("requirement_title", "Requirement"),
                design_elements=mapping.get("design_elements", []),
                implementation_notes=mapping.get("implementation_notes"),
                verification_method=mapping.get("verification_method")
            ))

        # Extract cross-references
        cross_refs = []
        raw_refs = llm_output.get("cross_references", [])
        for ref in raw_refs:
            cross_refs.append(CrossReference(
                target=ref.get("target", ""),
                reference_type=ref.get("reference_type", "specification"),
                description=ref.get("description"),
                bidirectional=ref.get("bidirectional", False)
            ))

        return {
            "design_overview": llm_output.get("design_overview", "System design overview"),
            "components": components,
            "requirement_mappings": req_mappings,
            "cross_references": cross_refs,
            "architectural_patterns": llm_output.get("architectural_patterns", []),
            "design_principles": llm_output.get("design_principles", []),
            "technology_stack": llm_output.get("technology_stack"),
            "data_model": llm_output.get("data_model"),
            "api_specifications": llm_output.get("api_specifications"),
            "quality_attributes": llm_output.get("quality_attributes", {}),
            "constraints": llm_output.get("constraints", [])
        }

    def _generate_fallback_design(self, user_requirement: str, requirements_content: str) -> Dict[str, Any]:
        """Generate fallback design when LLM extraction fails.

        Args:
            user_requirement: User requirement
            requirements_content: Requirements content

        Returns:
            Basic design structure
        """
        # Extract key information from requirements
        lines = requirements_content.split('\n')
        keywords = []

        for line in lines:
            # Look for key terms in requirements
            if any(keyword in line.lower() for keyword in ['system', 'user', 'data', 'api', 'interface', 'database']):
                # Extract words that could be component names
                words = [word.strip().lower() for word in line.split() if len(word) > 3 and word.isalnum()]
                keywords.extend(words[:2])  # Take first 2 words per line

        # Unique keywords
        unique_keywords = list(set(keywords))[:5]  # Limit to 5 keywords

        # Create basic components
        components = []
        for i, keyword in enumerate(unique_keywords):
            component = {
                "name": f"{keyword.title()}Component",
                "purpose": f"Handle {keyword} functionality",
                "description": f"Component responsible for {keyword} operations",
                "element_type": "component",
                "interfaces": [],
                "dependencies": [],
                "technology": "Python"
            }
            components.append(component)

        return {
            "design_overview": f"System design for: {user_requirement[:100]}...",
            "components": components,
            "requirement_mappings": [],
            "cross_references": [],
            "architectural_patterns": ["MVC", "Layered Architecture"],
            "design_principles": ["SOLID", "Separation of Concerns"],
            "technology_stack": "Python-based system",
            "quality_attributes": {
                "performance": "Optimize for response time",
                "security": "Implement proper authentication and authorization",
                "scalability": "Design for horizontal scaling"
            },
            "constraints": ["Follow coding standards", "Maintain compatibility"]
        }

    def _generate_design_name(self, user_requirement: str) -> str:
        """Generate a name for the design specification.

        Args:
            user_requirement: User's requirement description

        Returns:
            Generated design name
        """
        # Extract key terms
        import re
        words = re.findall(r'\b\w+\b', user_requirement)
        # Remove common words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        key_words = [w for w in words if w not in stop_words and len(w) > 2][:3]

        if key_words:
            name = " ".join(word.capitalize() for word in key_words)
            return f"{name} System Design"

        return "System Design"

    def _generate_design_overview(self, design_data: Dict[str, Any], user_requirement: str) -> str:
        """Generate a design overview.

        Args:
            design_data: Design data structure
            user_requirement: User requirement

        Returns:
            Generated design overview
        """
        overview_parts = [
            f"This design specification addresses the following requirement: {user_requirement[:200]}..."
        ]

        if design_data.get("components"):
            overview_parts.append(f"The solution includes {len(design_data['components'])} main components.")

        if design_data.get("architectural_patterns"):
            patterns = design_data["architectural_patterns"]
            if patterns:
                overview_parts.append(f"Key architectural patterns: {', '.join(patterns)}")

        if design_data.get("technology_stack"):
            overview_parts.append(f"Technology stack: {design_data['technology_stack']}")

        return " ".join(overview_parts)

    async def run(
        self,
        with_messages: List[Message] = None,
        *,
        user_requirement: str = "",
        prd_filename: str = "",
        legacy_design_filename: str = "",
        extra_info: str = "",
        output_pathname: str = "",
        use_openspec: Optional[bool] = None,
        **kwargs,
    ) -> Union[AIMessage, str]:
        """
        Write a system design with OpenSpec support.

        Args:
            with_messages: Messages with context
            user_requirement: User's requirement description
            prd_filename: PRD filename
            legacy_design_filename: Legacy design filename
            extra_info: Extra information
            output_pathname: Output file path
            use_openspec: Whether to use OpenSpec format (overrides default)
            **kwargs: Additional arguments

        Returns:
            Generated design specification or AIMessage
        """
        # Determine whether to use OpenSpec
        should_use_openspec = use_openspec if use_openspec is not None else self.use_openspec

        if should_use_openspec:
            return await self._run_openspec(
                with_messages=with_messages,
                user_requirement=user_requirement,
                prd_filename=prd_filename,
                legacy_design_filename=legacy_design_filename,
                extra_info=extra_info,
                output_pathname=output_pathname,
                **kwargs,
            )
        else:
            # Fall back to original WriteDesign behavior
            return await super().run(
                with_messages=with_messages,
                user_requirement=user_requirement,
                prd_filename=prd_filename,
                legacy_design_filename=legacy_design_filename,
                extra_info=extra_info,
                output_pathname=output_pathname,
                **kwargs,
            )

    async def _run_openspec(
        self,
        with_messages: List[Message] = None,
        *,
        user_requirement: str = "",
        prd_filename: str = "",
        legacy_design_filename: str = "",
        extra_info: str = "",
        output_pathname: str = "",
        **kwargs,
    ) -> Union[AIMessage, str]:
        """Run with OpenSpec format.

        Args:
            with_messages: Messages with context
            user_requirement: User requirement
            prd_filename: PRD filename
            legacy_design_filename: Legacy design filename
            extra_info: Extra information
            output_pathname: Output path
            **kwargs: Additional arguments

        Returns:
            Generated OpenSpec design specification
        """
        if not with_messages:
            return await self._execute_openspec_api(
                user_requirement=user_requirement,
                prd_filename=prd_filename,
                legacy_design_filename=legacy_design_filename,
                extra_info=extra_info,
                output_pathname=output_pathname,
                **kwargs,
            )

        try:
            # Load requirements content
            self.repo = ProjectRepo(self.input_args.project_path)

            requirements_content = ""
            if prd_filename:
                requirements_content = await aread(prd_filename)
            else:
                # Use first available PRD file
                prd_files = list(self.repo.docs.prd.workdir.glob("*.json"))
                if prd_files:
                    requirements_content = await aread(prd_files[0])
                else:
                    raise ValueError("No PRD file found")

            # Load legacy design if specified
            legacy_design_content = ""
            if legacy_design_filename:
                legacy_design_content = await aread(legacy_design_filename)

            # Extract context from messages
            context = self._extract_context_from_messages(with_messages)
            if extra_info:
                context["extra_info"] = extra_info

            # Generate OpenSpec design specification
            openspec_design = await self.generate_openspec_design(
                requirements_content=requirements_content,
                user_requirement=user_requirement,
                legacy_design=legacy_design_content,
                context=context
            )

            # Convert to markdown
            openspec_content = openspec_design.to_markdown()

            # Save to file if path specified
            if output_pathname:
                await self._save_openspec_design(openspec_content, output_pathname, openspec_design)

            # Return the OpenSpec design object for further processing
            return openspec_design

        except Exception as e:
            logger.error(f"Error generating OpenSpec design: {e}")
            # Fallback to original design generation
            logger.info("Falling back to original design generation")
            return await super().run(
                with_messages=with_messages,
                user_requirement=user_requirement,
                prd_filename=prd_filename,
                legacy_design_filename=legacy_design_filename,
                extra_info=extra_info,
                output_pathname=output_pathname,
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
            content = message.content.lower() if hasattr(message, 'content') else ""

            # Extract any structured data
            if hasattr(message, 'instruct_content') and message.instruct_content:
                try:
                    context_data = message.instruct_content.dict() if hasattr(message.instruct_content, 'dict') else message.instruct_content
                    context.update(context_data)
                except Exception:
                    pass

        return context

    async def _save_openspec_design(
        self,
        content: str,
        output_pathname: str,
        openspec_design: OpenSpecDesign,
        change_id: str = None,
    ):
        """Save OpenSpec design content to file using OpenSpec workspace.

        Args:
            content: Markdown content
            output_pathname: Output file path (if provided, will also save to OpenSpec workspace)
            openspec_design: The OpenSpec design object
            change_id: Optional change ID to use for shared changes
        """
        try:
            # Use provided change_id or generate unique one
            if change_id is None:
                change_id = self._generate_change_id(openspec_design.title)
            logger.info(f"Generated change ID: {change_id}")
            logger.info(f"OpenSpec workspace path: {self.openspec_workspace.workspace_path}")

            # Ensure workspace structure exists
            self.openspec_workspace.ensure_workspace()
            logger.info("✅ OpenSpec workspace structure ensured")

            # Save to OpenSpec workspace
            workspace_saved = False
            if hasattr(self, 'openspec_workspace'):
                logger.info("🔄 Attempting to save design to OpenSpec workspace...")
                saved_to_workspace = self.openspec_workspace.save_spec(change_id, "design", content)
                if saved_to_workspace:
                    workspace_path = self.openspec_workspace.workspace_path / "changes" / change_id / "design.md"
                    logger.info(f"✅ OpenSpec design saved to workspace: {workspace_path}")

                    # Verify file was actually created
                    if workspace_path.exists():
                        file_size = workspace_path.stat().st_size
                        logger.info(f"✅ Workspace design file verified: {workspace_path} ({file_size} bytes)")
                        workspace_saved = True
                    else:
                        logger.error(f"❌ Workspace design file not found after save: {workspace_path}")
                else:
                    logger.error("❌ Failed to save design to OpenSpec workspace")

            # Also save to the requested output path for backward compatibility
            if output_pathname:
                logger.info(f"🔄 Saving design to output path: {output_pathname}")
                output_path = Path(output_pathname)
                output_path.parent.mkdir(parents=True, exist_ok=True)

                # Save markdown content
                await awrite(output_pathname, content)
                logger.info(f"✅ Design markdown saved to: {output_pathname}")

                # Also save as JSON for structured access
                json_path = output_path.with_suffix('.json')
                json_content = openspec_design.model_dump_json(indent=2)
                await awrite(str(json_path), json_content)
                logger.info(f"✅ Design JSON saved to: {json_path}")

                # Verify files were created
                if output_path.exists() and json_path.exists():
                    logger.info(f"✅ Design output files verified: {output_path} ({output_path.stat().st_size} bytes), {json_path} ({json_path.stat().st_size} bytes)")
                else:
                    logger.error("❌ Design output files verification failed")

            # Summary logging
            logger.info("=" * 60)
            logger.info("📁 OpenSpec Design File Generation Summary:")
            logger.info(f"   Change ID: {change_id}")
            logger.info(f"   Design Title: {openspec_design.title}")
            logger.info(f"   Workspace Saved: {'✅ YES' if workspace_saved else '❌ NO'}")
            logger.info(f"   Output Path: {output_pathname if output_pathname else 'None'}")
            logger.info(f"   Workspace Directory: {self.openspec_workspace.workspace_path}")

            # List all files in the change directory
            change_dir = self.openspec_workspace.workspace_path / "changes" / change_id
            if change_dir.exists():
                files_in_change = list(change_dir.glob("*"))
                logger.info(f"   Files in change directory: {len(files_in_change)}")
                for file in files_in_change:
                    logger.info(f"     - {file.name} ({file.stat().st_size} bytes)")

            logger.info("=" * 60)

        except Exception as e:
            logger.error(f"❌ Error saving OpenSpec design: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            raise

    def _generate_change_id(self, title: str) -> str:
        """Generate a change ID from title"""
        import re
        # Convert title to a change ID format
        # Remove special characters and replace with underscores
        clean_title = re.sub(r'[^a-zA-Z0-9\s]', '', title)
        clean_title = re.sub(r'\s+', '_', clean_title.strip())

        # Add timestamp to make it unique
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        return f"{clean_title}_{timestamp}"

    async def _execute_openspec_api(
        self,
        *,
        user_requirement: str = "",
        prd_filename: str = "",
        legacy_design_filename: str = "",
        extra_info: str = "",
        output_pathname: str = "",
        **kwargs,
    ) -> AIMessage:
        """Execute OpenSpec API version.

        Args:
            user_requirement: User requirement
            prd_filename: PRD filename
            legacy_design_filename: Legacy design filename
            extra_info: Extra information
            output_pathname: Output path
            **kwargs: Additional arguments

        Returns:
            AIMessage with result
        """
        try:
            # Load requirements content
            requirements_content = ""
            if prd_filename:
                requirements_content = await aread(prd_filename)
            else:
                raise ValueError("PRD filename is required for OpenSpec design generation")

            # Load legacy design if specified
            legacy_design_content = ""
            if legacy_design_filename:
                legacy_design_content = await aread(legacy_design_filename)

            # Generate OpenSpec design specification
            openspec_design = await self.generate_openspec_design(
                requirements_content=requirements_content,
                user_requirement=user_requirement,
                legacy_design=legacy_design_content,
                context={"extra_info": extra_info}
            )

            # Convert to markdown
            openspec_content = openspec_design.to_markdown()

            # Save if path specified
            if output_pathname:
                await self._save_openspec_design(openspec_content, output_pathname, openspec_design)

            # Create AIMessage result
            instruct_content = AIMessage.create_instruct_value(
                kvs={
                    "user_requirement": user_requirement,
                    "design_name": openspec_design.name,
                    "component_count": len(openspec_design.design_components),
                    "requirement_mappings": len(openspec_design.requirements_mapping),
                },
                class_name="WriteDesignWithOpenSpecOutput",
            )

            return AIMessage(
                content=openspec_content,
                instruct_content=instruct_content,
            )

        except Exception as e:
            logger.error(f"Error in OpenSpec API execution: {e}")
            raise