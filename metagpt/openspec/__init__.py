"""
OpenSpec integration for MetaGPT.

This package provides OpenSpec-compliant specification generation,
validation, and management capabilities for MetaGPT's multi-agent workflow.
"""

from .template_engine import OpenSpecTemplateEngine
from .models.requirement import OpenSpecRequirement, Requirement, Scenario
from .models.design import OpenSpecDesign, DesignComponent, RequirementMapping, CrossReference
from .models.task import OpenSpecTaskSpecification, ImplementationTask, TaskStatus, TaskPriority
from .validators.base_validator import OpenSpecValidator
from .review.orchestrator import ReviewOrchestrator, ReviewStage, ReviewPriority

__all__ = [
    "OpenSpecTemplateEngine",
    "OpenSpecRequirement",
    "OpenSpecDesign",
    "OpenSpecTaskSpecification",
    "OpenSpecValidator",
    "ReviewOrchestrator",
    "ReviewStage",
    "ReviewPriority",
    "Requirement",
    "Scenario",
    "ImplementationTask",
    "TaskStatus",
    "TaskPriority",
]

__version__ = "0.1.0"