"""
Unit tests for OpenSpec components.

Tests individual OpenSpec components in isolation.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, AsyncMock

from metagpt.openspec.models.requirement import Requirement, Scenario
from metagpt.openspec.models.design import DesignComponent, RequirementMapping, CrossReference
from metagpt.openspec.models.task import ImplementationTask, TaskStatus, TaskPriority
from metagpt.openspec.validators.base_validator import ValidationResult, ValidationIssue
from metagpt.openspec.review.orchestrator import ReviewItem, ReviewFeedback, QualityGate, ReviewStage


class TestRequirementModels:
    """Test requirement data models."""

    def test_requirement_creation(self):
        """Test requirement model creation."""
        scenario = Scenario(
            given="user wants to login",
            when="user provides valid credentials",
            then="user is authenticated"
        )

        requirement = Requirement(
            id="REQ-001",
            title="User Login",
            description="System SHALL authenticate users",
            priority="high",
            acceptance_criteria=["Valid users can login", "Invalid users are rejected"],
            scenarios=[scenario]
        )

        assert requirement.id == "REQ-001"
        assert requirement.title == "User Login"
        assert requirement.priority == "high"
        assert len(requirement.scenarios) == 1
        assert requirement.scenarios[0].given == "user wants to login"

    def test_scenario_validation(self):
        """Test scenario model validation."""
        # Valid scenario
        scenario = Scenario(
            given="test condition",
            when="test action",
            then="test result"
        )
        assert scenario.given == "test condition"
        assert scenario.when == "test action"
        assert scenario.then == "test result"

        # Scenario with optional fields
        scenario_with_options = Scenario(
            given="test condition",
            when="test action",
            then="test result",
            and_conditions=["additional condition"],
            but_conditions=["exception condition"]
        )
        assert len(scenario_with_options.and_conditions) == 1
        assert len(scenario_with_options.but_conditions) == 1


class TestDesignModels:
    """Test design data models."""

    def test_design_component_creation(self):
        """Test design component model creation."""
        component = DesignComponent(
            name="API Service",
            purpose="Handle REST API requests",
            element_type="service",
            description="Microservice for API handling",
            interfaces=[
                {
                    "name": "user_api",
                    "description": "User management API",
                    "input_type": "UserRequest",
                    "output_type": "UserResponse",
                    "protocol": "HTTP/REST"
                }
            ],
            dependencies=["Database", "Auth Service"],
            sub_components=["Request Handler", "Response Builder"],
            technology="Python/FastAPI",
            behavior="Processes incoming requests and returns responses",
            performance_requirements="< 100ms response time",
            security_considerations="Input validation and rate limiting"
        )

        assert component.name == "API Service"
        assert component.element_type == "service"
        assert len(component.interfaces) == 1
        assert component.interfaces[0]["name"] == "user_api"
        assert len(component.dependencies) == 2
        assert component.technology == "Python/FastAPI"

    def test_requirement_mapping_creation(self):
        """Test requirement mapping model creation."""
        mapping = RequirementMapping(
            requirement_id="REQ-001",
            requirement_title="User Authentication",
            design_elements=["Auth Service", "User Database"],
            implementation_notes="Use OAuth 2.0 for authentication",
            verification_method="Automated tests and manual review"
        )

        assert mapping.requirement_id == "REQ-001"
        assert mapping.requirement_title == "User Authentication"
        assert len(mapping.design_elements) == 2
        assert mapping.verification_method == "Automated tests and manual review"

    def test_cross_reference_creation(self):
        """Test cross-reference model creation."""
        cross_ref = CrossReference(
            reference_type="requirement",
            target="REQ-001",
            description="Related requirement for user management"
        )

        assert cross_ref.reference_type == "requirement"
        assert cross_ref.target == "REQ-001"
        assert cross_ref.description == "Related requirement for user management"


class TestTaskModels:
    """Test task data models."""

    def test_implementation_task_creation(self):
        """Test implementation task model creation."""
        task = ImplementationTask(
            id="TASK-001",
            title="Implement User Authentication",
            description="Create authentication service with OAuth 2.0",
            requirement_ids=["REQ-001", "REQ-002"],
            status=TaskStatus.PENDING,
            priority=TaskPriority.HIGH,
            estimated_hours=24,
            dependencies=["TASK-002"],  # Database setup
            assignee="developer1",
            acceptance_criteria=[
                "OAuth 2.0 flow is implemented",
                "Token validation works",
                "Error handling is in place"
            ],
            deliverables=[
                "Authentication service code",
                "Unit tests",
                "API documentation"
            ],
            progress_percentage=0,
            notes="Waiting for database setup to begin"
        )

        assert task.id == "TASK-001"
        assert task.status == TaskStatus.PENDING
        assert task.priority == TaskPriority.HIGH
        assert task.estimated_hours == 24
        assert len(task.requirement_ids) == 2
        assert len(task.acceptance_criteria) == 3
        assert task.progress_percentage == 0

    def test_task_status_enum(self):
        """Test task status enumeration."""
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.IN_PROGRESS.value == "in_progress"
        assert TaskStatus.COMPLETED.value == "completed"
        assert TaskStatus.BLOCKED.value == "blocked"
        assert TaskStatus.CANCELLED.value == "cancelled"

    def test_task_priority_enum(self):
        """Test task priority enumeration."""
        assert TaskPriority.LOW.value == "low"
        assert TaskPriority.MEDIUM.value == "medium"
        assert TaskPriority.HIGH.value == "high"
        assert TaskPriority.CRITICAL.value == "critical"


class TestValidationComponents:
    """Test validation components."""

    def test_validation_result_creation(self):
        """Test validation result model creation."""
        issues = [
            ValidationIssue(
                level="error",
                code="REQ_001",
                message="Requirement must have an ID",
                line_number=1,
                suggestions=["Add requirement ID"]
            ),
            ValidationIssue(
                level="warning",
                code="REQ_002",
                message="Consider adding acceptance criteria",
                suggestions=["Add acceptance criteria for better testability"]
            )
        ]

        result = ValidationResult(
            is_valid=False,
            issues=issues,
            summary="Validation failed with 1 error and 1 warning"
        )

        assert not result.is_valid
        assert len(result.issues) == 2
        assert result.issues[0].level == "error"
        assert result.issues[1].level == "warning"
        assert "Validation failed" in result.summary

    def test_validation_issue_creation(self):
        """Test validation issue model creation."""
        issue = ValidationIssue(
            level="error",
            code="FORMAT_001",
            message="Invalid format detected",
            line_number=10,
            column_number=5,
            file_path="requirements.md",
            context="Line with format error",
            suggestions=["Fix format", "Follow OpenSpec conventions"]
        )

        assert issue.level == "error"
        assert issue.code == "FORMAT_001"
        assert issue.line_number == 10
        assert issue.column_number == 5
        assert len(issue.suggestions) == 2


class TestReviewComponents:
    """Test review workflow components."""

    def test_review_item_creation(self):
        """Test review item model creation."""
        item = ReviewItem(
            item_type="requirement",
            item_id="REQ-001",
            content={"title": "Test Requirement"},
            priority="high"
        )

        assert item.item_type == "requirement"
        assert item.item_id == "REQ-001"
        assert item.priority == "high"
        assert item.stage == ReviewStage.INITIATED
        assert isinstance(item.created_at, datetime)

    def test_review_feedback_creation(self):
        """Test review feedback model creation."""
        feedback = ReviewFeedback(
            reviewer_id="product_manager",
            review_item_id="REQ-001",
            feedback_type="suggestion",
            category="clarity",
            severity="medium",
            message="Consider making this requirement more specific",
            suggestions=["Add measurable criteria", "Define acceptance tests"]
        )

        assert feedback.reviewer_id == "product_manager"
        assert feedback.feedback_type == "suggestion"
        assert feedback.category == "clarity"
        assert feedback.severity == "medium"
        assert len(feedback.suggestions) == 2

    def test_quality_gate_creation(self):
        """Test quality gate model creation."""
        gate = QualityGate(
            name="Completeness Check",
            description="Verify that all required sections are present",
            criteria={
                "has_overview": True,
                "has_requirements": True,
                "has_acceptance_criteria": True
            },
            required_pass_rate=0.9,
            is_blocking=True
        )

        assert gate.name == "Completeness Check"
        assert gate.required_pass_rate == 0.9
        assert gate.is_blocking
        assert gate.criteria["has_overview"]

    def test_review_stage_enum(self):
        """Test review stage enumeration."""
        assert ReviewStage.INITIATED.value == "initiated"
        assert ReviewStage.VALIDATION.value == "validation"
        assert ReviewStage.COMPLETED.value == "completed"
        assert ReviewStage.FAILED.value == "failed"


class TestTemplateEngine:
    """Test template engine functionality."""

    def test_template_engine_initialization(self):
        """Test template engine initialization."""
        from metagpt.openspec.template_engine import OpenSpecTemplateEngine

        engine = OpenSpecTemplateEngine()
        assert engine is not None

        # Check that built-in templates are loaded
        available_templates = engine.list_templates()
        assert "requirement" in available_templates
        assert "design" in available_templates
        assert "task" in available_templates

    def test_custom_template_loading(self):
        """Test loading custom templates."""
        from metagpt.openspec.template_engine import OpenSpecTemplateEngine

        engine = OpenSpecTemplateEngine()

        # Test adding custom template
        custom_template = """
# {{ title }}

{{ description }}

## Criteria
{% for criteria in criteria %}
- {{ criteria }}
{% endfor %}
        """.strip()

        engine.add_template("custom", custom_template)

        # Render custom template
        data = {
            "title": "Custom Template Test",
            "description": "Testing custom template functionality",
            "criteria": ["Criteria 1", "Criteria 2"]
        }

        rendered = engine.render_template("custom", data)
        assert "Custom Template Test" in rendered
        assert "Criteria 1" in rendered
        assert "Criteria 2" in rendered

    def test_template_validation(self):
        """Test template validation."""
        from metagpt.openspec.template_engine import OpenSpecTemplateEngine

        engine = OpenSpecTemplateEngine()

        # Test valid template
        valid_template = "{{ title }} - {{ description }}"
        is_valid = engine.validate_template("test_template", valid_template)
        assert is_valid

        # Test invalid template (syntax error)
        invalid_template = "{{ title"  # Missing closing brace
        is_valid = engine.validate_template("invalid_template", invalid_template)
        assert not is_valid


class TestCrossReferenceManagers:
    """Test cross-reference managers."""

    def test_requirement_cross_reference_manager(self):
        """Test requirement cross-reference manager."""
        from metagpt.openspec.cross_ref.requirement_manager import RequirementCrossReferenceManager

        manager = RequirementCrossReferenceManager()

        # Test adding requirements
        requirement = Mock()
        requirement.name = "Test Requirement"
        requirement.requirements = [
            Mock(id="REQ-001"),
            Mock(id="REQ-002")
        ]

        manager.add_requirement(requirement)

        # Test getting requirements
        requirements = manager.get_all_requirements()
        assert len(requirements) >= 1

    def test_design_cross_reference_manager(self):
        """Test design cross-reference manager."""
        from metagpt.openspec.cross_ref.design_manager import DesignCrossReferenceManager

        manager = DesignCrossReferenceManager()

        # Test traceability verification
        uncovered = manager.verify_traceability()
        assert isinstance(uncovered, list)

        # Test design reference validation
        errors = manager.validate_design_references()
        assert isinstance(errors, list)

    def test_task_cross_reference_manager(self):
        """Test task cross-reference manager."""
        from metagpt.openspec.cross_ref.task_manager import TaskTraceabilityManager

        manager = TaskTraceabilityManager()

        # Test coverage analysis
        analysis = manager.analyze_coverage()
        assert isinstance(analysis, dict)

        # Test gap detection
        gaps = manager.detect_gaps()
        assert isinstance(gaps, list)


if __name__ == "__main__":
    pytest.main([__file__])