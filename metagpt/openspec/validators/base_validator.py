"""
OpenSpec Base Validator

Core validation framework for OpenSpec specifications.
"""

from __future__ import annotations

from enum import Enum
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass, field
from abc import ABC, abstractmethod

from pydantic import BaseModel

from ..models.requirement import OpenSpecRequirement
from ..models.design import OpenSpecDesign


class ValidationLevel(str, Enum):
    """Severity levels for validation issues."""
    ERROR = "error"      # Critical issues that must be fixed
    WARNING = "warning"  # Issues that should be reviewed
    INFO = "info"        # Informational messages


@dataclass
class ValidationIssue:
    """Represents a validation issue."""
    level: ValidationLevel
    message: str
    location: Optional[str] = None  # File path or component name
    line_number: Optional[int] = None
    suggestion: Optional[str] = None
    rule_id: Optional[str] = None

    def __str__(self) -> str:
        """String representation of the issue."""
        location_str = f" [{self.location}]" if self.location else ""
        line_str = f":{self.line_number}" if self.line_number else ""
        suggestion_str = f"\n  Suggestion: {self.suggestion}" if self.suggestion else ""
        return f"{self.level.value.upper()}{location_str}{line_str}: {self.message}{suggestion_str}"


@dataclass
class ValidationResult:
    """Result of a validation operation."""
    is_valid: bool = field(default=False)
    issues: List[ValidationIssue] = field(default_factory=list)
    summary: Optional[str] = None

    @property
    def errors(self) -> List[ValidationIssue]:
        """Get only error-level issues."""
        return [issue for issue in self.issues if issue.level == ValidationLevel.ERROR]

    @property
    def warnings(self) -> List[ValidationIssue]:
        """Get only warning-level issues."""
        return [issue for issue in self.issues if issue.level == ValidationLevel.WARNING]

    @property
    def infos(self) -> List[ValidationIssue]:
        """Get only info-level issues."""
        return [issue for issue in self.issues if issue.level == ValidationLevel.INFO]

    def add_error(self, message: str, location: Optional[str] = None, suggestion: Optional[str] = None):
        """Add an error issue."""
        self.issues.append(ValidationIssue(
            level=ValidationLevel.ERROR,
            message=message,
            location=location,
            suggestion=suggestion
        ))

    def add_warning(self, message: str, location: Optional[str] = None, suggestion: Optional[str] = None):
        """Add a warning issue."""
        self.issues.append(ValidationIssue(
            level=ValidationLevel.WARNING,
            message=message,
            location=location,
            suggestion=suggestion
        ))

    def add_info(self, message: str, location: Optional[str] = None):
        """Add an info issue."""
        self.issues.append(ValidationIssue(
            level=ValidationLevel.INFO,
            message=message,
            location=location
        ))

    def has_errors(self) -> bool:
        """Check if there are any errors."""
        return len(self.errors) > 0

    def has_warnings(self) -> bool:
        """Check if there are any warnings."""
        return len(self.warnings) > 0

    def get_summary(self) -> str:
        """Get a summary of the validation result."""
        error_count = len(self.errors)
        warning_count = len(self.warnings)
        info_count = len(self.infos)

        parts = []
        if error_count > 0:
            parts.append(f"{error_count} error{'s' if error_count != 1 else ''}")
        if warning_count > 0:
            parts.append(f"{warning_count} warning{'s' if warning_count != 1 else ''}")
        if info_count > 0:
            parts.append(f"{info_count} info message{'s' if info_count != 1 else ''}")

        if not parts:
            return "No issues found"

        return "Validation found: " + ", ".join(parts)


class BaseValidator(ABC):
    """Base class for OpenSpec validators."""

    def __init__(self, strict_mode: bool = False):
        """Initialize the validator.

        Args:
            strict_mode: If True, warnings are treated as errors
        """
        self.strict_mode = strict_mode

    @abstractmethod
    def validate(self, spec: Union[OpenSpecRequirement, OpenSpecDesign]) -> ValidationResult:
        """Validate a specification.

        Args:
            spec: The specification to validate

        Returns:
            ValidationResult with validation issues
        """
        pass

    def _validate_basic_structure(self, spec: Union[OpenSpecRequirement, OpenSpecDesign], result: ValidationResult):
        """Validate basic specification structure."""
        if not spec.name or not spec.name.strip():
            result.add_error("Specification must have a name", location="root")

        if hasattr(spec, 'version') and not spec.version:
            result.add_warning("Specification should have a version", location="root")

    def _validate_markdown_format(self, markdown_content: str, result: ValidationResult):
        """Validate that markdown follows OpenSpec conventions."""
        lines = markdown_content.split('\n')

        for i, line in enumerate(lines, 1):
            # Check for proper scenario formatting
            if 'Scenario:' in line:
                if not line.startswith('#### Scenario:'):
                    result.add_error(
                        "Scenarios must use '#### Scenario:' format",
                        location=f"line {i}",
                        suggestion="Change to '#### Scenario: Your scenario name'"
                    )

            # Check for proper requirement formatting
            if line.startswith('### Requirement:'):
                if not line.strip():
                    result.add_error(
                        "Requirement titles cannot be empty",
                        location=f"line {i}",
                        suggestion="Provide a requirement title after '### Requirement:'"
                    )

            # Check for proper operation headers
            if line.startswith('##') and any(op in line for op in ['ADDED', 'MODIFIED', 'REMOVED', 'RENAMED']):
                expected_patterns = ['## ADDED Requirements', '## MODIFIED Requirements',
                                   '## REMOVED Requirements', '## RENAMED Requirements']
                if not any(pattern in line for pattern in expected_patterns):
                    result.add_warning(
                        "Requirement operation headers should follow OpenSpec format",
                        location=f"line {i}",
                        suggestion="Use '## ADDED Requirements', '## MODIFIED Requirements', etc."
                    )

    def _check_scenario_structure(self, spec: Union[OpenSpecRequirement, OpenSpecDesign], result: ValidationResult):
        """Check that scenarios have proper structure."""
        if isinstance(spec, OpenSpecRequirement):
            for req_idx, req in enumerate(spec.get_all_requirements()):
                for scenario_idx, scenario in enumerate(req.scenarios):
                    # Check that scenarios have at least one of the Gherkin elements
                    if not (scenario.given or scenario.when or scenario.then):
                        result.add_error(
                            f"Scenario '{scenario.name}' must have at least one of: Given, When, Then",
                            location=f"requirement {req_idx + 1}, scenario {scenario_idx + 1}",
                            suggestion="Add at least one of Gherkin elements (Given, When, Then)"
                        )

                    # Check for proper scenario naming
                    if not scenario.name or not scenario.name.strip():
                        result.add_error(
                            "Scenario name cannot be empty",
                            location=f"requirement {req_idx + 1}, scenario {scenario_idx + 1}",
                            suggestion="Provide a meaningful name for the scenario"
                        )


class OpenSpecValidator(BaseValidator):
    """Main OpenSpec validator that combines requirement and design validation."""

    def __init__(self, strict_mode: bool = False):
        """Initialize the validator.

        Args:
            strict_mode: If True, warnings are treated as errors
        """
        super().__init__(strict_mode)

        # Import specific validators here to avoid circular imports
        from .requirement_validator import RequirementValidator
        from .design_validator import DesignValidator

        self.requirement_validator = RequirementValidator(strict_mode)
        self.design_validator = DesignValidator(strict_mode)

    def validate(self, spec: Union[OpenSpecRequirement, OpenSpecDesign]) -> ValidationResult:
        """Validate an OpenSpec specification.

        Args:
            spec: The specification to validate

        Returns:
            ValidationResult with validation issues
        """
        if isinstance(spec, OpenSpecRequirement):
            return self.requirement_validator.validate(spec)
        elif isinstance(spec, OpenSpecDesign):
            return self.design_validator.validate(spec)
        else:
            result = ValidationResult()
            result.add_error(
                f"Unknown specification type: {type(spec)}",
                suggestion="Provide either OpenSpecRequirement or OpenSpecDesign"
            )
            return result

    def validate_markdown(self, markdown_content: str, spec_type: str = "requirement") -> ValidationResult:
        """Validate OpenSpec markdown format.

        Args:
            markdown_content: The markdown content to validate
            spec_type: Type of specification ("requirement" or "design")

        Returns:
            ValidationResult with validation issues
        """
        result = ValidationResult()

        # Basic markdown structure validation
        self._validate_markdown_format(markdown_content, result)

        # Type-specific validation
        if spec_type == "requirement":
            # Check for requirement-specific patterns
            if "## ADDED Requirements" not in markdown_content and \
               "## MODIFIED Requirements" not in markdown_content and \
               "## REMOVED Requirements" not in markdown_content:
                result.add_warning(
                    "Requirement specification should have at least one operation section",
                    suggestion="Add '## ADDED Requirements', '## MODIFIED Requirements', or '## REMOVED Requirements'"
                )

        elif spec_type == "design":
            # Check for design-specific patterns
            if "## Design Components" not in markdown_content:
                result.add_warning(
                    "Design specification should have a '## Design Components' section",
                    suggestion="Add design components to describe the solution architecture"
                )

        result.is_valid = not result.has_errors()
        result.summary = result.get_summary()
        return result