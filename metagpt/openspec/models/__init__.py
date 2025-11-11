"""
OpenSpec Data Models

Pydantic models for OpenSpec specification structure and validation.
"""

from .requirement import (
    OpenSpecRequirement,
    Requirement,
    Scenario,
    RequirementOperation,
)
from .design import (
    OpenSpecDesign,
    DesignComponent,
    RequirementMapping,
    CrossReference,
)
from .task import (
    OpenSpecTaskSpecification,
    ImplementationTask,
    TaskMapping,
    TaskStatus,
    TaskPriority,
)

__all__ = [
    "OpenSpecRequirement",
    "Requirement",
    "Scenario",
    "RequirementOperation",
    "OpenSpecDesign",
    "DesignComponent",
    "RequirementMapping",
    "CrossReference",
    "OpenSpecTaskSpecification",
    "ImplementationTask",
    "TaskMapping",
    "TaskStatus",
    "TaskPriority",
]