"""
OpenSpec Review Orchestrator

Orchestrates the review workflow for OpenSpec specifications, coordinating
validation, quality assessment, feedback collection, and improvement processes.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import asyncio
from datetime import datetime

from ..models.requirement import OpenSpecRequirement
from ..models.design import OpenSpecDesign
from ..models.task import OpenSpecTaskSpecification
from ..validators.base_validator import OpenSpecValidator, ValidationResult, ValidationIssue
from ..cross_ref.requirement_manager import RequirementCrossReferenceManager
from ..cross_ref.design_manager import DesignCrossReferenceManager


class ReviewStage(Enum):
    """Stages in the review workflow."""
    INITIATED = "initiated"
    VALIDATION = "validation"
    QUALITY_ASSESSMENT = "quality_assessment"
    STAKEHOLDER_REVIEW = "stakeholder_review"
    IMPROVEMENT = "improvement"
    COMPLETED = "completed"
    FAILED = "failed"


class ReviewPriority(Enum):
    """Priority levels for reviews."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ReviewItem:
    """An item being reviewed."""
    item_type: str  # "requirement", "design", "task"
    item_id: str
    content: Any
    priority: ReviewPriority = ReviewPriority.MEDIUM
    stage: ReviewStage = ReviewStage.INITIATED
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class ReviewFeedback:
    """Feedback collected during review."""
    reviewer_id: str
    review_item_id: str
    feedback_type: str  # "validation", "quality", "suggestion", "issue"
    category: str
    severity: str  # "low", "medium", "high", "critical"
    message: str
    suggestions: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class QualityGate:
    """A quality gate in the review process."""
    name: str
    description: str
    criteria: Dict[str, Any]
    required_pass_rate: float = 0.8
    is_blocking: bool = True


class ReviewOrchestrator:
    """Orchestrates the review workflow for OpenSpec specifications."""

    def __init__(self):
        """Initialize the review orchestrator."""
        self.validator = OpenSpecValidator()
        self.req_manager = RequirementCrossReferenceManager()
        self.design_manager = DesignCrossReferenceManager()

        self.review_items: Dict[str, ReviewItem] = {}
        self.feedback: Dict[str, List[ReviewFeedback]] = {}
        self.quality_gates: List[QualityGate] = []
        self.review_history: List[Dict[str, Any]] = []

        self._setup_default_quality_gates()

    def _setup_default_quality_gates(self):
        """Set up default quality gates."""
        self.quality_gates = [
            QualityGate(
                name="Format Compliance",
                description="Specification must follow OpenSpec format conventions",
                criteria={
                    "has_proper_structure": True,
                    "uses_shall_must_language": True,
                    "has_scenarios": True
                }
            ),
            QualityGate(
                name="Content Completeness",
                description="Specification must have complete content",
                criteria={
                    "has_all_requirements": True,
                    "requirements_are_testable": True,
                    "has_acceptance_criteria": True
                }
            ),
            QualityGate(
                name="Validation Pass Rate",
                description="Must pass minimum validation threshold",
                criteria={
                    "error_count": 0,
                    "warning_limit": 5,
                    "completion_score": 0.8
                }
            )
        ]

    async def submit_for_review(
        self,
        item_type: str,
        item_id: str,
        content: Any,
        priority: ReviewPriority = ReviewPriority.MEDIUM
    ) -> str:
        """Submit an item for review.

        Args:
            item_type: Type of item ("requirement", "design", "task")
            item_id: Unique identifier for the item
            content: The content to review
            priority: Review priority

        Returns:
            Review ID
        """
        review_id = f"{item_type}_{item_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        review_item = ReviewItem(
            item_type=item_type,
            item_id=item_id,
            content=content,
            priority=priority
        )

        self.review_items[review_id] = review_item
        self.feedback[review_id] = []

        # Start the review workflow
        await self._execute_review_workflow(review_id)

        return review_id

    async def _execute_review_workflow(self, review_id: str):
        """Execute the review workflow for an item."""
        review_item = self.review_items.get(review_id)
        if not review_item:
            return

        try:
            # Stage 1: Validation
            await self._run_validation_stage(review_id)

            # Stage 2: Quality Assessment
            await self._run_quality_assessment(review_id)

            # Stage 3: Quality Gate Evaluation
            gate_passed = await self._evaluate_quality_gates(review_id)

            if gate_passed:
                review_item.stage = ReviewStage.COMPLETED
            else:
                review_item.stage = ReviewStage.IMPROVEMENT
                await self._generate_improvement_suggestions(review_id)

        except Exception as e:
            review_item.stage = ReviewStage.FAILED
            await self._add_feedback(review_id, ReviewFeedback(
                reviewer_id="system",
                review_item_id=review_id,
                feedback_type="error",
                category="system",
                severity="critical",
                message=f"Review workflow failed: {str(e)}"
            ))

    async def _run_validation_stage(self, review_id: str):
        """Run the validation stage of review."""
        review_item = self.review_items[review_id]
        review_item.stage = ReviewStage.VALIDATION

        # Validate based on item type
        if review_item.item_type == "requirement":
            validation_result = self.validator.validate_requirement(review_item.content)
        elif review_item.item_type == "design":
            validation_result = self.validator.validate_design(review_item.content)
        elif review_item.item_type == "task":
            validation_result = self.validator.validate_task(review_item.content)
        else:
            validation_result = ValidationResult(
                is_valid=False,
                issues=[ValidationIssue(
                    level="error",
                    message=f"Unknown item type: {review_item.item_type}"
                )]
            )

        # Add validation feedback
        for issue in validation_result.issues:
            await self._add_feedback(review_id, ReviewFeedback(
                reviewer_id="validator",
                review_item_id=review_id,
                feedback_type="validation",
                category=issue.code or "general",
                severity=issue.level,
                message=issue.message,
                suggestions=issue.suggestions or []
            ))

    async def _run_quality_assessment(self, review_id: str):
        """Run the quality assessment stage."""
        review_item = self.review_items[review_id]
        review_item.stage = ReviewStage.QUALITY_ASSESSMENT

        # Perform quality checks
        quality_scores = await self._assess_quality(review_item)

        # Add quality feedback
        for aspect, score in quality_scores.items():
            if score < 0.7:  # Threshold for quality issues
                await self._add_feedback(review_id, ReviewFeedback(
                    reviewer_id="quality_assessor",
                    review_item_id=review_id,
                    feedback_type="quality",
                    category=aspect,
                    severity="medium" if score > 0.5 else "high",
                    message=f"Quality score for {aspect}: {score:.2f}",
                    suggestions=[f"Improve {aspect} to meet quality standards"]
                ))

    async def _assess_quality(self, review_item: ReviewItem) -> Dict[str, float]:
        """Assess the quality of a review item."""
        scores = {}

        if review_item.item_type == "requirement":
            scores = await self._assess_requirement_quality(review_item.content)
        elif review_item.item_type == "design":
            scores = await self._assess_design_quality(review_item.content)
        elif review_item.item_type == "task":
            scores = await self._assess_task_quality(review_item.content)

        return scores

    async def _assess_requirement_quality(self, requirement: OpenSpecRequirement) -> Dict[str, float]:
        """Assess the quality of a requirement specification."""
        scores = {}

        # Check completeness
        total_requirements = len(requirement.requirements)
        scores["completeness"] = min(1.0, total_requirements / 5.0)  # Assume 5+ is good

        # Check scenario coverage
        requirements_with_scenarios = sum(
            1 for req in requirement.requirements if req.scenarios
        )
        scores["scenario_coverage"] = (
            requirements_with_scenarios / total_requirements if total_requirements > 0 else 0.0
        )

        # Check traceability
        scores["traceability"] = 1.0 if requirement.cross_references else 0.5

        # Check clarity (basic heuristic)
        avg_description_length = sum(
            len(req.description.split()) for req in requirement.requirements
        ) / total_requirements if total_requirements > 0 else 0
        scores["clarity"] = min(1.0, avg_description_length / 20.0)  # 20+ words is good

        return scores

    async def _assess_design_quality(self, design: OpenSpecDesign) -> Dict[str, float]:
        """Assess the quality of a design specification."""
        scores = {}

        # Check component coverage
        scores["component_completeness"] = min(1.0, len(design.design_components) / 3.0)

        # Check requirement mapping
        mapped_requirements = len(set(mapping.requirement_id for mapping in design.requirements_mapping))
        scores["requirement_coverage"] = min(1.0, mapped_requirements / 5.0)

        # Check interface definitions
        components_with_interfaces = sum(
            1 for comp in design.design_components if comp.interfaces
        )
        scores["interface_definition"] = (
            components_with_interfaces / len(design.design_components) if design.design_components else 0.0
        )

        return scores

    async def _assess_task_quality(self, task_spec: OpenSpecTaskSpecification) -> Dict[str, float]:
        """Assess the quality of a task specification."""
        scores = {}

        # Check task completeness
        total_tasks = len(task_spec.tasks)
        scores["task_completeness"] = min(1.0, total_tasks / 5.0)

        # Check requirement traceability
        tasks_with_requirements = sum(
            1 for task in task_spec.tasks if task.requirement_ids
        )
        scores["requirement_traceability"] = (
            tasks_with_requirements / total_tasks if total_tasks > 0 else 0.0
        )

        # Check priority distribution
        tasks_with_priorities = sum(
            1 for task in task_spec.tasks if task.priority
        )
        scores["priority_assignment"] = (
            tasks_with_priorities / total_tasks if total_tasks > 0 else 0.0
        )

        return scores

    async def _evaluate_quality_gates(self, review_id: str) -> bool:
        """Evaluate quality gates for a review item."""
        review_item = self.review_items[review_id]
        feedback_list = self.feedback.get(review_id, [])

        all_passed = True

        for gate in self.quality_gates:
            passed = await self._check_quality_gate(gate, review_item, feedback_list)

            await self._add_feedback(review_id, ReviewFeedback(
                reviewer_id="quality_gate",
                review_item_id=review_id,
                feedback_type="quality_gate",
                category=gate.name,
                severity="high",
                message=f"Quality gate '{gate.name}': {'PASSED' if passed else 'FAILED'}",
                suggestions=[] if passed else [f"Address criteria for {gate.name}"]
            ))

            if gate.is_blocking and not passed:
                all_passed = False

        return all_passed

    async def _check_quality_gate(
        self,
        gate: QualityGate,
        review_item: ReviewItem,
        feedback_list: List[ReviewFeedback]
    ) -> bool:
        """Check if a quality gate is passed."""
        # Implementation would check specific criteria
        # For now, use a simplified approach

        if gate.name == "Format Compliance":
            # Check for validation errors related to format
            format_errors = [
                f for f in feedback_list
                if f.feedback_type == "validation" and f.severity == "error"
            ]
            return len(format_errors) == 0

        elif gate.name == "Content Completeness":
            # Check for high-severity quality issues
            high_severity_issues = [
                f for f in feedback_list
                if f.feedback_type == "quality" and f.severity in ["high", "critical"]
            ]
            return len(high_severity_issues) == 0

        elif gate.name == "Validation Pass Rate":
            # Check overall validation results
            error_count = len([
                f for f in feedback_list
                if f.feedback_type == "validation" and f.severity == "error"
            ])
            warning_count = len([
                f for f in feedback_list
                if f.feedback_type == "validation" and f.severity == "warning"
            ])

            return error_count == 0 and warning_count <= gate.criteria.get("warning_limit", 5)

        return True  # Default to passing for unknown gates

    async def _generate_improvement_suggestions(self, review_id: str):
        """Generate improvement suggestions for failed reviews."""
        review_item = self.review_items[review_id]
        feedback_list = self.feedback.get(review_id, [])

        # Analyze feedback patterns
        error_categories = {}
        for feedback in feedback_list:
            if feedback.severity in ["high", "critical"]:
                error_categories[feedback.category] = error_categories.get(feedback.category, 0) + 1

        # Generate targeted suggestions
        for category, count in error_categories.items():
            await self._add_feedback(review_id, ReviewFeedback(
                reviewer_id="improvement_generator",
                review_item_id=review_id,
                feedback_type="improvement",
                category=category,
                severity="medium",
                message=f"Address {count} issue(s) in {category}",
                suggestions=[
                    f"Review and revise {category} aspects",
                    "Consider stakeholder feedback",
                    "Run validation again after changes"
                ]
            ))

    async def _add_feedback(self, review_id: str, feedback: ReviewFeedback):
        """Add feedback to a review."""
        if review_id not in self.feedback:
            self.feedback[review_id] = []

        self.feedback[review_id].append(feedback)

        # Update review item timestamp
        if review_id in self.review_items:
            self.review_items[review_id].updated_at = datetime.now()

    async def add_stakeholder_feedback(
        self,
        review_id: str,
        stakeholder_id: str,
        feedback_type: str,
        category: str,
        severity: str,
        message: str,
        suggestions: List[str] = None
    ):
        """Add stakeholder feedback to a review."""
        feedback = ReviewFeedback(
            reviewer_id=stakeholder_id,
            review_item_id=review_id,
            feedback_type=feedback_type,
            category=category,
            severity=severity,
            message=message,
            suggestions=suggestions or []
        )

        await self._add_feedback(review_id, feedback)

    def get_review_status(self, review_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of a review."""
        review_item = self.review_items.get(review_id)
        if not review_item:
            return None

        feedback_list = self.feedback.get(review_id, [])

        # Calculate summary statistics
        error_count = len([f for f in feedback_list if f.severity == "error"])
        warning_count = len([f for f in feedback_list if f.severity == "warning"])
        suggestion_count = len([f for f in feedback_list if f.feedback_type == "suggestion"])

        return {
            "review_id": review_id,
            "item_type": review_item.item_type,
            "item_id": review_item.item_id,
            "stage": review_item.stage.value,
            "priority": review_item.priority.value,
            "created_at": review_item.created_at.isoformat(),
            "updated_at": review_item.updated_at.isoformat(),
            "error_count": error_count,
            "warning_count": warning_count,
            "suggestion_count": suggestion_count,
            "total_feedback": len(feedback_list)
        }

    def get_review_feedback(self, review_id: str) -> List[ReviewFeedback]:
        """Get all feedback for a review."""
        return self.feedback.get(review_id, [])

    async def resubmit_for_review(self, review_id: str, updated_content: Any):
        """Resubmit an item for review after improvements."""
        review_item = self.review_items.get(review_id)
        if not review_item:
            raise ValueError(f"Review {review_id} not found")

        # Update content and reset stage
        review_item.content = updated_content
        review_item.stage = ReviewStage.INITIATED
        review_item.updated_at = datetime.now()

        # Clear previous feedback
        self.feedback[review_id] = []

        # Restart review workflow
        await self._execute_review_workflow(review_id)

    def get_all_reviews(self) -> List[Dict[str, Any]]:
        """Get status of all reviews."""
        return [
            self.get_review_status(review_id)
            for review_id in self.review_items.keys()
        ]

    def add_quality_gate(self, gate: QualityGate):
        """Add a custom quality gate."""
        self.quality_gates.append(gate)