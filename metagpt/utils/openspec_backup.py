#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2025/11/12
@Author  : OpenSpec Integration
@File    : openspec.py
"""

import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, validator

import logging


class ValidationResult(BaseModel):
    """Result of OpenSpec validation"""
    is_valid: bool
    errors: List[str] = []
    warnings: List[str] = []
    suggestions: List[str] = []


class OpenSpecSpec(BaseModel):
    """Base class for OpenSpec specifications"""
    title: str
    description: str
    version: str = "1.0.0"
    metadata: Dict[str, Any] = {}

    @validator('title')
    def validate_title(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError("Title cannot be empty")
        return v.strip()


class OpenSpecRequirement(OpenSpecSpec):
    """OpenSpec requirement specification"""
    scenarios: List[Dict[str, Any]] = []
    acceptance_criteria: List[str] = []
    priority: str = "medium"  # high, medium, low

    @validator('priority')
    def validate_priority(cls, v):
        if v not in ['high', 'medium', 'low']:
            raise ValueError("Priority must be high, medium, or low")
        return v


class OpenSpecDesign(OpenSpecSpec):
    """OpenSpec design specification"""
    architecture: Dict[str, Any] = {}
    components: List[Dict[str, Any]] = []
    technical_decisions: List[Dict[str, Any]] = []
    tradeoffs: List[Dict[str, Any]] = []


class OpenSpecTask(OpenSpecSpec):
    """OpenSpec task specification"""
    requirement_id: str = ""
    design_id: str = ""
    implementation_steps: List[str] = []
    test_cases: List[str] = []
    dependencies: List[str] = []


class OpenSpecValidator:
    """OpenSpec validation and formatting utilities"""

    def __init__(self, strict_mode: bool = True):
        self.strict_mode = strict_mode

    def validate_requirement(self, requirement: Union[Dict, OpenSpecRequirement]) -> ValidationResult:
        """Validate OpenSpec requirement"""
        errors = []
        warnings = []
        suggestions = []

        if isinstance(requirement, dict):
            try:
                requirement = OpenSpecRequirement(**requirement)
            except Exception as e:
                return ValidationResult(is_valid=False, errors=[f"Invalid requirement format: {e}"])

        # Basic validation
        if not requirement.scenarios:
            warnings.append("No scenarios defined - consider adding user scenarios")
            suggestions.append("Add at least one user scenario to improve requirement clarity")

        if not requirement.acceptance_criteria:
            errors.append("Acceptance criteria are required")
            suggestions.append("Define clear acceptance criteria for requirement validation")

        if len(requirement.description) < 50:
            warnings.append("Description is quite short - consider adding more detail")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions
        )

  def validate_design(self, design: Union[Dict, OpenSpecDesign]) -> ValidationResult:
        """Validate OpenSpec design"""
        errors = []
        warnings = []
        suggestions = []

        if isinstance(design, dict):
            try:
                design = OpenSpecDesign(**design)
            except Exception as e:
                return ValidationResult(is_valid=False, errors=[f"Invalid design format: {e}"])

        # Basic validation
        if not design.components:
            warnings.append("No components defined - consider adding system components")
            suggestions.append("Define system components to improve architecture clarity")

        if not design.technical_decisions:
            warnings.append("No technical decisions documented")
            suggestions.append("Document key technical decisions and their rationale")

        if not design.architecture:
            errors.append("Architecture description is required")
            suggestions.append("Provide a clear architecture overview")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions
        )

  def validate_task(self, task: Union[Dict, OpenSpecTask]) -> ValidationResult:
        """Validate OpenSpec task"""
        errors = []
        warnings = []
        suggestions = []

        if isinstance(task, dict):
            try:
                task = OpenSpecTask(**task)
            except Exception as e:
                return ValidationResult(is_valid=False, errors=[f"Invalid task format: {e}"])

        # Basic validation
        if not task.implementation_steps:
            errors.append("Implementation steps are required")
            suggestions.append("Break down the task into clear implementation steps")

        if not task.test_cases:
            warnings.append("No test cases defined")
            suggestions.append("Define test cases to ensure task completion criteria")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions
        )


class OpenSpecTemplateEngine:
    """Template rendering and management for OpenSpec"""

  def __init__(self, template_dir: Optional[Path] = None):
        self.template_dir = template_dir
        self.default_templates = self._get_default_templates()

  def _get_default_templates(self) -> Dict[str, str]:
        """Get default OpenSpec templates"""
        return {
            "requirement": '''# {title}

## Description
{description}

## Scenarios
{scenarios}

## Acceptance Criteria
{acceptance_criteria}

## Priority
{priority}

## Metadata
{metadata}
''',
            "design": '''# {title}

## Description
{description}

## Architecture
{architecture}

## Components
{components}

## Technical Decisions
{technical_decisions}

## Trade-offs
{tradeoffs}

## Metadata
{metadata}
''',
            "task": '''# {title}

## Description
{description}

## Requirement ID
{requirement_id}

## Design ID
{design_id}

## Implementation Steps
{implementation_steps}

## Test Cases
{test_cases}

## Dependencies
{dependencies}

## Metadata
{metadata}
'''
        }

  def render_requirement(self, requirement: OpenSpecRequirement) -> str:
        """Render requirement specification"""
        scenarios_text = ""
        for i, scenario in enumerate(requirement.scenarios, 1):
            scenarios_text += f"### Scenario {i}\n"
            for key, value in scenario.items():
                scenarios_text += f"- **{key}**: {value}\n"
            scenarios_text += "\n"

        acceptance_criteria_text = ""
        for i, criterion in enumerate(requirement.acceptance_criteria, 1):
            acceptance_criteria_text += f"{i}. {criterion}\n"

        metadata_text = ""
        for key, value in requirement.metadata.items():
            metadata_text += f"- **{key}**: {value}\n"

        template = self.default_templates["requirement"]
        return template.format(
            title=requirement.title,
            description=requirement.description,
            scenarios=scenarios_text,
            acceptance_criteria=acceptance_criteria_text,
            priority=requirement.priority,
            metadata=metadata_text
        )

  def render_design(self, design: OpenSpecDesign) -> str:
        """Render design specification"""
        architecture_text = design.architecture.get('overview', '') if design.architecture else ""

        components_text = ""
        for i, component in enumerate(design.components, 1):
            components_text += f"### Component {i}: {component.get('name', 'Unnamed')}\n"
            for key, value in component.items():
                if key != 'name':
                    components_text += f"- **{key}**: {value}\n"
            components_text += "\n"

        tech_decisions_text = ""
        for i, decision in enumerate(design.technical_decisions, 1):
            tech_decisions_text += f"### Decision {i}: {decision.get('title', 'Untitled')}\n"
            tech_decisions_text += f"**Description**: {decision.get('description', '')}\n"
            tech_decisions_text += f"**Rationale**: {decision.get('rationale', '')}\n\n"

        tradeoffs_text = ""
        for i, tradeoff in enumerate(design.tradeoffs, 1):
            tradeoffs_text += f"### Trade-off {i}\n"
            for key, value in tradeoff.items():
                tradeoffs_text += f"- **{key}**: {value}\n"
            tradeoffs_text += "\n"

        metadata_text = ""
        for key, value in design.metadata.items():
            metadata_text += f"- **{key}**: {value}\n"

        template = self.default_templates["design"]
        return template.format(
            title=design.title,
            description=design.description,
            architecture=architecture_text,
            components=components_text,
            technical_decisions=tech_decisions_text,
            tradeoffs=tradeoffs_text,
            metadata=metadata_text
        )

  def render_task(self, task: OpenSpecTask) -> str:
        """Render task specification"""
        steps_text = ""
        for i, step in enumerate(task.implementation_steps, 1):
            steps_text += f"{i}. {step}\n"

        test_cases_text = ""
        for i, test_case in enumerate(task.test_cases, 1):
            test_cases_text += f"{i}. {test_case}\n"

        dependencies_text = ""
        for dep in task.dependencies:
            dependencies_text += f"- {dep}\n"

        metadata_text = ""
        for key, value in task.metadata.items():
            metadata_text += f"- **{key}**: {value}\n"

        template = self.default_templates["task"]
        return template.format(
            title=task.title,
            description=task.description,
            requirement_id=task.requirement_id,
            design_id=task.design_id,
            implementation_steps=steps_text,
            test_cases=test_cases_text,
            dependencies=dependencies_text,
            metadata=metadata_text
        )


class OpenSpecGenerator:
    """OpenSpec spec creation and management utilities"""

  def __init__(self, validator: Optional[OpenSpecValidator] = None, template_engine: Optional[OpenSpecTemplateEngine] = None):
        self.validator = validator or OpenSpecValidator()
        self.template_engine = template_engine or OpenSpecTemplateEngine()

  def generate_requirement(self, title: str, description: str, **kwargs) -> OpenSpecRequirement:
        """Generate an OpenSpec requirement"""
        return OpenSpecRequirement(
            title=title,
            description=description,
            **kwargs
        )

  def generate_design(self, title: str, description: str, **kwargs) -> OpenSpecDesign:
        """Generate an OpenSpec design"""
        return OpenSpecDesign(
            title=title,
            description=description,
            **kwargs
        )

  def generate_task(self, title: str, description: str, **kwargs) -> OpenSpecTask:
        """Generate an OpenSpec task"""
        return OpenSpecTask(
            title=title,
            description=description,
            **kwargs
        )

  def format_requirement(self, requirement: OpenSpecRequirement) -> str:
        """Format requirement as markdown"""
        return self.template_engine.render_requirement(requirement)

  def format_design(self, design: OpenSpecDesign) -> str:
        """Format design as markdown"""
        return self.template_engine.render_design(design)

  def format_task(self, task: OpenSpecTask) -> str:
        """Format task as markdown"""
        return self.template_engine.render_task(task)


class OpenSpecIntegrator:
    """Role integration utilities for OpenSpec"""

    @staticmethod
    def should_use_openspec(config: Dict[str, Any]) -> bool:
        """Check if OpenSpec should be used based on configuration"""
        return config.get('openspec', {}).get('enabled', False)

    @staticmethod
    def get_validation_mode(config: Dict[str, Any]) -> str:
        """Get validation mode from configuration"""
        return config.get('openspec', {}).get('validation_mode', 'strict')

    @staticmethod
    def get_output_format(config: Dict[str, Any]) -> str:
        """Get output format from configuration"""
        return config.get('openspec', {}).get('output_format', 'openspec')

    @staticmethod
    def should_auto_validate(config: Dict[str, Any]) -> bool:
        """Check if auto-validation is enabled"""
        return config.get('openspec', {}).get('auto_validate', True)


def openspec_available() -> bool:
    """Check if OpenSpec CLI is available"""
    try:
        result = subprocess.run(['openspec', '--version'],
                              capture_output=True, text=True, timeout=10)
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def get_default_workspace_path() -> Path:
    """Get default OpenSpec workspace path"""
    return Path.cwd() / "openspec"


class OpenSpecCLIWrapper:
    """Wrapper for OpenSpec CLI operations"""

  def __init__(self, cli_path: str = "openspec", timeout: int = 60, retry_attempts: int = 3):
        self.cli_path = cli_path
        self.timeout = timeout
        self.retry_attempts = retry_attempts

  def execute_command(self, command: List[str], input_data: Optional[str] = None) -> Dict[str, Any]:
        """Execute OpenSpec CLI command with error handling and retries"""
        last_error = None

        for attempt in range(self.retry_attempts):
            try:
                cmd = [self.cli_path] + command

                result = subprocess.run(
                    cmd,
                    input=input_data,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout,
                    check=False
                )

                return {
                    "success": result.returncode == 0,
                    "stdout": result.stdout.strip(),
                    "stderr": result.stderr.strip(),
                    "return_code": result.returncode,
                    "command": " ".join(cmd)
                }

            except subprocess.TimeoutExpired as e:
                last_error = f"Command timeout after {self.timeout}s: {e}"
                if attempt == self.retry_attempts - 1:
                    break

            except FileNotFoundError:
                return {
                    "success": False,
                    "stdout": "",
                    "stderr": f"OpenSpec CLI not found at '{self.cli_path}'. Please install or specify correct path.",
                    "return_code": -1,
                    "command": self.cli_path
                }

            except Exception as e:
                last_error = f"Unexpected error: {e}"
                if attempt == self.retry_attempts - 1:
                    break

        return {
            "success": False,
            "stdout": "",
            "stderr": last_error or "Command failed after all retry attempts",
            "return_code": -1,
            "command": " ".join([self.cli_path] + command)
        }

  def validate_spec(self, spec_content: str, spec_type: str = "requirement") -> Dict[str, Any]:
        """Validate OpenSpec specification"""
        command = ["validate", "--type", spec_type]
        return self.execute_command(command, input_data=spec_content)

  def generate_template(self, spec_type: str, template_name: Optional[str] = None) -> Dict[str, Any]:
        """Generate OpenSpec template"""
        command = ["template", "--type", spec_type]
        if template_name:
            command.extend(["--name", template_name])
        return self.execute_command(command)

        def format_spec(self, spec_content: str, output_format: str = "markdown") -> Dict[str, Any]:
        """Format OpenSpec specification"""
        command = ["format", "--output", output_format]
        return self.execute_command(command, input_data=spec_content)

        def create_change_proposal(self, title: str, description: str, workspace_path: str = ".") -> Dict[str, Any]:
        """Create OpenSpec change proposal"""
        command = ["proposal", "create", "--title", title, "--description", description, "--workspace", workspace_path]
        return self.execute_command(command)

        def list_changes(self, workspace_path: str = ".", status: Optional[str] = None) -> Dict[str, Any]:
        """List OpenSpec changes"""
        command = ["changes", "list", "--workspace", workspace_path]
        if status:
            command.extend(["--status", status])
        return self.execute_command(command)

        def get_version(self) -> Dict[str, Any]:
        """Get OpenSpec CLI version"""
        return self.execute_command(["--version"])

  def is_available(self) -> bool:
        """Check if OpenSpec CLI is available and working"""
        try:
            result = self.get_version()
            return result["success"]
        except Exception:
            return False


class OpenSpecWorkspaceManager:
    """Manages OpenSpec workspace and file structure"""

  def __init__(self, workspace_path: Path):
        self.workspace_path = Path(workspace_path)
        self.changes_dir = self.workspace_path / "changes"
        self.archive_dir = self.workspace_path / "archive"
        self.specs_dir = self.workspace_path / "specs"

  def ensure_workspace(self) -> bool:
        """Ensure workspace structure exists"""
        try:
            self.workspace_path.mkdir(parents=True, exist_ok=True)
            self.changes_dir.mkdir(exist_ok=True)
            self.archive_dir.mkdir(exist_ok=True)
            self.specs_dir.mkdir(exist_ok=True)
            return True
        except Exception as e:
            print(f"Failed to create workspace: {e}")
            return False

  def create_change_directory(self, change_id: str) -> Path:
        """Create directory for a change proposal"""
        change_dir = self.changes_dir / change_id
        change_dir.mkdir(parents=True, exist_ok=True)
        return change_dir

  def archive_change(self, change_id: str) -> bool:
        """Archive a change proposal"""
        try:
            change_dir = self.changes_dir / change_id
            if change_dir.exists():
                archive_target = self.archive_dir / change_id
                if archive_target.exists():
                    # Remove existing archive
                    import shutil
                    shutil.rmtree(archive_target)
                change_dir.rename(archive_target)
                return True
            return False
        except Exception as e:
            print(f"Failed to archive change {change_id}: {e}")
            return False

  def list_changes(self, include_archived: bool = False) -> List[str]:
        """List all change IDs"""
        changes = []

        if self.changes_dir.exists():
            changes.extend([d.name for d in self.changes_dir.iterdir() if d.is_dir()])

        if include_archived and self.archive_dir.exists():
            archived = [f"archived:{d.name}" for d in self.archive_dir.iterdir() if d.is_dir()]
            changes.extend(archived)

        return sorted(changes)

  def get_change_path(self, change_id: str) -> Optional[Path]:
        """Get path to change directory"""
        change_path = self.changes_dir / change_id
        if change_path.exists():
            return change_path

        # Check archived changes
        archived_path = self.archive_dir / change_id
        if archived_path.exists():
            return archived_path

        return None

  def save_spec(self, change_id: str, spec_name: str, content: str) -> bool:
        """Save specification content"""
        try:
            change_dir = self.create_change_directory(change_id)
            spec_file = change_dir / f"{spec_name}.md"
            spec_file.write_text(content, encoding='utf-8')
            return True
        except Exception as e:
            print(f"Failed to save spec {spec_name} for change {change_id}: {e}")
            return False

  def load_spec(self, change_id: str, spec_name: str) -> Optional[str]:
        """Load specification content"""
        try:
            change_dir = self.get_change_path(change_id)
            if not change_dir:
                return None

            spec_file = change_dir / f"{spec_name}.md"
            if spec_file.exists():
                return spec_file.read_text(encoding='utf-8')
            return None
        except Exception as e:
            print(f"Failed to load spec {spec_name} for change {change_id}: {e}")
            return None