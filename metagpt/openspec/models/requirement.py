"""
OpenSpec Requirement Models

Pydantic models for OpenSpec requirement specifications.
"""

from __future__ import annotations

from enum import Enum
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, validator


class RequirementOperation(str, Enum):
    """Types of requirement operations in OpenSpec deltas."""
    ADDED = "ADDED"
    MODIFIED = "MODIFIED"
    REMOVED = "REMOVED"
    RENAMED = "RENAMED"


class Scenario(BaseModel):
    """Represents a scenario in OpenSpec format."""
    name: Optional[str] = Field(None, description="Name of the scenario")
    given: Optional[str] = Field(None, description="Given condition")
    when: Optional[str] = Field(None, description="When condition")
    then: Optional[str] = Field(None, description="Then condition")

    @validator('name')
    def validate_name(cls, v):
        """Validate scenario name format."""
        if v is not None and (not v or not v.strip()):
            raise ValueError("Scenario name cannot be empty if provided")
        return v.strip() if v else None

    def to_markdown(self) -> str:
        """Convert scenario to OpenSpec markdown format."""
        scenario_title = self.name or "Scenario"
        lines = [f"#### {scenario_title}"]
        if self.given:
            lines.append(f"**Given** {self.given}")
        if self.when:
            lines.append(f"**When** {self.when}")
        if self.then:
            lines.append(f"**Then** {self.then}")
        return "\n".join(lines)


class Requirement(BaseModel):
    """Represents a requirement in OpenSpec format."""
    id: str = Field(..., description="Unique identifier for the requirement")
    title: str = Field(..., description="Title of the requirement")
    description: str = Field(..., description="Description of the requirement")
    scenarios: List[Scenario] = Field(..., description="List of scenarios")
    acceptance_criteria: Optional[List[str]] = Field(None, description="Acceptance criteria")
    priority: Optional[str] = Field(None, description="Priority level")
    category: Optional[str] = Field(None, description="Requirement category")
    tags: List[str] = Field(default_factory=list, description="Tags for classification")

    @validator('title')
    def validate_title(cls, v):
        """Validate requirement title."""
        if not v or not v.strip():
            raise ValueError("Requirement title cannot be empty")
        return v.strip()

    @validator('scenarios')
    def validate_scenarios(cls, v):
        """Validate that at least one scenario exists."""
        if not v:
            raise ValueError("Requirement must have at least one scenario")
        return v

    @validator('description')
    def validate_description(cls, v):
        """Validate requirement description."""
        if not v or not v.strip():
            raise ValueError("Requirement description cannot be empty")
        return v.strip()

    def to_markdown(self) -> str:
        """Convert requirement to OpenSpec markdown format."""
        lines = [
            f"### Requirement: {self.title}",
            self.description,
            ""
        ]

        for scenario in self.scenarios:
            lines.append(scenario.to_markdown())
            lines.append("")

        if self.acceptance_criteria:
            lines.append("#### Acceptance Criteria:")
            for criterion in self.acceptance_criteria:
                lines.append(f"- {criterion}")
            lines.append("")

        return "\n".join(lines)


class RemovedRequirement(BaseModel):
    """Represents a removed requirement with migration info."""
    title: str = Field(..., description="Title of the removed requirement")
    reason: str = Field(..., description="Reason for removal")
    migration: Optional[str] = Field(None, description="Migration guidance")


class RenamedRequirement(BaseModel):
    """Represents a renamed requirement."""
    from_name: str = Field(..., description="Original name")
    to_name: str = Field(..., description="New name")


class OpenSpecRequirement(BaseModel):
    """Complete OpenSpec requirement specification."""
    name: str = Field(..., description="Name of the specification")
    version: str = Field(default="1.0", description="Specification version")
    description: Optional[str] = Field(None, description="Specification description")

    # Requirements by operation type
    added_requirements: List[Requirement] = Field(default_factory=list, description="New requirements")
    modified_requirements: List[Requirement] = Field(default_factory=list, description="Modified requirements")
    removed_requirements: List[RemovedRequirement] = Field(default_factory=list, description="Removed requirements")
    renamed_requirements: List[RenamedRequirement] = Field(default_factory=list, description="Renamed requirements")

    # Metadata
    created_at: Optional[str] = Field(None, description="Creation timestamp")
    updated_at: Optional[str] = Field(None, description="Last update timestamp")
    authors: List[str] = Field(default_factory=list, description="Authors of the specification")
    reviewers: List[str] = Field(default_factory=list, description="Reviewers of the specification")

    # Cross-references
    dependencies: List[str] = Field(default_factory=list, description="Dependencies on other specs")
    dependents: List[str] = Field(default_factory=list, description="Specs that depend on this one")

    @validator('name')
    def validate_name(cls, v):
        """Validate specification name."""
        if not v or not v.strip():
            raise ValueError("Specification name cannot be empty")
        return v.strip()

    def has_requirements(self) -> bool:
        """Check if specification has any requirements."""
        return bool(
            self.added_requirements or
            self.modified_requirements or
            self.removed_requirements or
            self.renamed_requirements
        )

    def get_all_requirements(self) -> List[Requirement]:
        """Get all requirement objects (excluding removed ones)."""
        return self.added_requirements + self.modified_requirements

    def get_scenarios_by_name(self, scenario_name: str) -> List[tuple[Requirement, Scenario]]:
        """Find all scenarios with the given name."""
        matches = []
        for req in self.get_all_requirements():
            for scenario in req.scenarios:
                if scenario.name.lower() == scenario_name.lower():
                    matches.append((req, scenario))
        return matches

    def to_markdown(self) -> str:
        """Convert specification to OpenSpec markdown format."""
        lines = [f"# {self.name}"]

        if self.description:
            lines.append(self.description)
            lines.append("")

        # Added Requirements
        if self.added_requirements:
            lines.append("## ADDED Requirements")
            lines.append("")
            for req in self.added_requirements:
                lines.append(req.to_markdown())
                lines.append("")

        # Modified Requirements
        if self.modified_requirements:
            lines.append("## MODIFIED Requirements")
            lines.append("")
            for req in self.modified_requirements:
                lines.append(req.to_markdown())
                lines.append("")

        # Removed Requirements
        if self.removed_requirements:
            lines.append("## REMOVED Requirements")
            lines.append("")
            for req in self.removed_requirements:
                lines.append(f"### Requirement: {req.title}")
                lines.append(f"**Reason**: {req.reason}")
                if req.migration:
                    lines.append(f"**Migration**: {req.migration}")
                lines.append("")

        # Renamed Requirements
        if self.renamed_requirements:
            lines.append("## RENAMED Requirements")
            lines.append("")
            for req in self.renamed_requirements:
                lines.append(f"- FROM: `{req.from_name}`")
                lines.append(f"- TO: `{req.to_name}`")
                lines.append("")

        return "\n".join(lines).rstrip()

    def get_validation_errors(self) -> List[str]:
        """Get validation errors for this specification."""
        errors = []

        if not self.has_requirements():
            errors.append("Specification must have at least one requirement")

        # Validate requirements
        for i, req in enumerate(self.added_requirements):
            try:
                req.dict()  # This will trigger Pydantic validation
            except Exception as e:
                errors.append(f"Added requirement {i+1} validation error: {str(e)}")

        for i, req in enumerate(self.modified_requirements):
            try:
                req.dict()  # This will trigger Pydantic validation
            except Exception as e:
                errors.append(f"Modified requirement {i+1} validation error: {str(e)}")

        return errors