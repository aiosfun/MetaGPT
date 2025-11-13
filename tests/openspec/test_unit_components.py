"""
Comprehensive Unit Tests for OpenSpec Components

Tests all OpenSpec utility classes, actions, and roles with >90% coverage.
Includes edge cases, error handling, and performance considerations.
"""

import pytest
import asyncio
import time
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from pathlib import Path
import tempfile
import json

from metagpt.logs import logger

# Import OpenSpec components
from metagpt.openspec.models.requirement import Requirement, Scenario
from metagpt.openspec.models.design import DesignComponent, RequirementMapping, CrossReference
from metagpt.openspec.models.task import ImplementationTask, TaskStatus, TaskPriority
from metagpt.openspec.validators.base_validator import OpenSpecValidator, ValidationResult, ValidationIssue
from metagpt.openspec.review.orchestrator import ReviewOrchestrator, ReviewStage, ReviewPriority
from metagpt.openspec.template_engine import OpenSpecTemplateEngine


class TestRequirementModels:
    """Test requirement data models with comprehensive coverage."""

    def test_requirement_creation_valid(self):
        """Test requirement creation with valid data."""
        scenario = Scenario(
            given="user wants to login",
            when="user provides valid credentials",
            then="user is authenticated successfully"
        )

        requirement = Requirement(
            id="REQ-001",
            title="User Authentication",
            description="The system SHALL authenticate users before granting access",
            priority="high",
            acceptance_criteria=[
                "Users can login with valid credentials",
                "Invalid login attempts are rejected",
                "Session management is implemented"
            ],
            scenarios=[scenario]
        )

        assert requirement.id == "REQ-001"
        assert requirement.title == "User Authentication"
        assert requirement.priority == "high"
        assert len(requirement.acceptance_criteria) == 3
        assert len(requirement.scenarios) == 1
        assert requirement.scenarios[0].given == "user wants to login"

    def test_requirement_creation_minimal(self):
        """Test requirement creation with minimal data."""
        requirement = Requirement(
            id="REQ-002",
            title="Minimal Requirement",
            description="Basic requirement description"
        )

        assert requirement.id == "REQ-002"
        assert requirement.title == "Minimal Requirement"
        assert requirement.description == "Basic requirement description"
        assert requirement.priority is None
        assert requirement.acceptance_criteria == []
        assert requirement.scenarios == []

    def test_requirement_creation_with_optional_fields(self):
        """Test requirement creation with all optional fields."""
        scenario_with_conditions = Scenario(
            given="user is logged in",
            when="user attempts to access protected resource",
            then="access is granted if user has permissions",
            and_conditions=["user session is active", "resource exists"],
            but_conditions=["user is not suspended", "resource is not locked"]
        )

        requirement = Requirement(
            id="REQ-003",
            title="Complex Requirement",
            description="Requirement with all optional fields",
            priority="critical",
            acceptance_criteria=["Criteria 1", "Criteria 2"],
            scenarios=[scenario_with_conditions],
            tags=["security", "authentication"],
            metadata={"source": "stakeholder_meeting", "priority_score": 9}
        )

        assert requirement.tags == ["security", "authentication"]
        assert requirement.metadata["source"] == "stakeholder_meeting"
        assert len(requirement.scenarios[0].and_conditions) == 2
        assert len(requirement.scenarios[0].but_conditions) == 2

    def test_requirement_invalid_id(self):
        """Test requirement creation with invalid ID."""
        with pytest.raises(ValueError):
            Requirement(
                id="",  # Empty ID should raise error
                title="Invalid ID Requirement",
                description="This should fail"
            )

    def test_requirement_invalid_priority(self):
        """Test requirement creation with invalid priority."""
        with pytest.raises(ValueError):
            Requirement(
                id="REQ-004",
                title="Invalid Priority Requirement",
                description="This should fail",
                priority="invalid_priority"
            )

    def test_requirement_to_dict(self):
        """Test requirement serialization to dictionary."""
        requirement = Requirement(
            id="REQ-005",
            title="Serialization Test",
            description="Test serialization functionality"
        )

        req_dict = requirement.to_dict()
        
        assert isinstance(req_dict, dict)
        assert req_dict["id"] == "REQ-005"
        assert req_dict["title"] == "Serialization Test"
        assert req_dict["description"] == "Test serialization functionality"

    def test_requirement_from_dict(self):
        """Test requirement deserialization from dictionary."""
        req_dict = {
            "id": "REQ-006",
            "title": "Deserialization Test",
            "description": "Test deserialization functionality",
            "priority": "medium",
            "acceptance_criteria": ["Test criterion"],
            "scenarios": []
        }

        requirement = Requirement.from_dict(req_dict)
        
        assert requirement.id == "REQ-006"
        assert requirement.title == "Deserialization Test"
        assert requirement.priority == "medium"
        assert len(requirement.acceptance_criteria) == 1

    def test_requirement_equality(self):
        """Test requirement equality comparison."""
        req1 = Requirement(id="REQ-007", title="Test", description="Test")
        req2 = Requirement(id="REQ-007", title="Test", description="Test")
        req3 = Requirement(id="REQ-008", title="Test", description="Test")

        assert req1 == req2
        assert req1 != req3

    def test_requirement_hash(self):
        """Test requirement hashing for use in sets/dicts."""
        req1 = Requirement(id="REQ-009", title="Test", description="Test")
        req2 = Requirement(id="REQ-009", title="Test", description="Test")

        req_set = {req1, req2}
        assert len(req_set) == 1  # Should be deduplicated

    def test_scenario_validation(self):
        """Test scenario validation."""
        # Valid scenario
        valid_scenario = Scenario(
            given="valid condition",
            when="valid action",
            then="valid result"
        )
        assert valid_scenario.is_valid()

        # Invalid scenario (missing required fields)
        with pytest.raises(ValueError):
            Scenario(
                given="condition",
                when="action"
                # Missing 'then' field
            )

    def test_scenario_with_optional_conditions(self):
        """Test scenario with AND/BUT conditions."""
        scenario = Scenario(
            given="user is authenticated",
            when="user requests sensitive data",
            then="data is returned if authorized",
            and_conditions=["user has valid session", "data exists"],
            but_conditions=["user is not blocked", "data is not restricted"]
        )

        assert len(scenario.and_conditions) == 2
        assert len(scenario.but_conditions) == 2
        assert "user has valid session" in scenario.and_conditions
        assert "user is not blocked" in scenario.but_conditions


class TestDesignModels:
    """Test design data models with comprehensive coverage."""

    def test_design_component_creation_valid(self):
        """Test design component creation with valid data."""
        component = DesignComponent(
            name="Authentication Service",
            purpose="Handle user authentication and authorization",
            element_type="service",
            description="Microservice for authentication operations",
            interfaces=[
                {
                    "name": "login_api",
                    "description": "User login endpoint",
                    "input_type": "LoginRequest",
                    "output_type": "AuthResponse",
                    "protocol": "HTTP/REST"
                }
            ],
            dependencies=["Database", "Cache Service"],
            sub_components=["Login Handler", "Token Manager"],
            technology="Python/FastAPI",
            behavior="Processes authentication requests",
            performance_requirements="< 200ms response time",
            security_considerations="Input validation and rate limiting"
        )

        assert component.name == "Authentication Service"
        assert component.element_type == "service"
        assert len(component.interfaces) == 1
        assert len(component.dependencies) == 2
        assert component.technology == "Python/FastAPI"

    def test_design_component_creation_minimal(self):
        """Test design component creation with minimal data."""
        component = DesignComponent(
            name="Minimal Component",
            purpose="Basic functionality",
            element_type="component"
        )

        assert component.name == "Minimal Component"
        assert component.purpose == "Basic functionality"
        assert component.element_type == "component"
        assert component.interfaces == []
        assert component.dependencies == []

    def test_design_component_invalid_element_type(self):
        """Test design component creation with invalid element type."""
        with pytest.raises(ValueError):
            DesignComponent(
                name="Invalid Component",
                purpose="Test invalid type",
                element_type="invalid_type"
            )

    def test_design_component_interface_validation(self):
        """Test design component interface validation."""
        # Valid interface
        valid_interface = {
            "name": "test_api",
            "description": "Test API endpoint",
            "input_type": "TestRequest",
            "output_type": "TestResponse",
            "protocol": "HTTP/REST"
        }

        component = DesignComponent(
            name="Test Component",
            purpose="Test interface validation",
            element_type="service",
            interfaces=[valid_interface]
        )

        assert len(component.interfaces) == 1
        assert component.interfaces[0]["name"] == "test_api"

        # Invalid interface (missing required fields)
        invalid_interface = {
            "name": "invalid_api"
            # Missing required fields
        }

        with pytest.raises(ValueError):
            DesignComponent(
                name="Invalid Component",
                purpose="Test invalid interface",
                element_type="service",
                interfaces=[invalid_interface]
            )

    def test_requirement_mapping_creation(self):
        """Test requirement mapping creation."""
        mapping = RequirementMapping(
            requirement_id="REQ-001",
            requirement_title="User Authentication",
            design_elements=["Auth Service", "User Database"],
            implementation_notes="Use OAuth 2.0 with JWT tokens",
            verification_method="Automated tests and manual review"
        )

        assert mapping.requirement_id == "REQ-001"
        assert mapping.requirement_title == "User Authentication"
        assert len(mapping.design_elements) == 2
        assert "OAuth 2.0" in mapping.implementation_notes
        assert mapping.verification_method == "Automated tests and manual review"

    def test_requirement_mapping_minimal(self):
        """Test requirement mapping creation with minimal data."""
        mapping = RequirementMapping(
            requirement_id="REQ-002",
            requirement_title="Basic Requirement",
            design_elements=["Component A"]
        )

        assert mapping.requirement_id == "REQ-002"
        assert len(mapping.design_elements) == 1
        assert mapping.implementation_notes is None
        assert mapping.verification_method is None

    def test_cross_reference_creation(self):
        """Test cross-reference creation."""
        cross_ref = CrossReference(
            reference_type="requirement",
            target="REQ-001",
            description="Related authentication requirement"
        )

        assert cross_ref.reference_type == "requirement"
        assert cross_ref.target == "REQ-001"
        assert cross_ref.description == "Related authentication requirement"

    def test_cross_reference_invalid_type(self):
        """Test cross-reference creation with invalid type."""
        with pytest.raises(ValueError):
            CrossReference(
                reference_type="invalid_type",
                target="REQ-001",
                description="Invalid reference"
            )

    def test_design_component_to_dict(self):
        """Test design component serialization."""
        component = DesignComponent(
            name="Test Component",
            purpose="Test serialization",
            element_type="component"
        )

        comp_dict = component.to_dict()
        
        assert isinstance(comp_dict, dict)
        assert comp_dict["name"] == "Test Component"
        assert comp_dict["purpose"] == "Test serialization"
        assert comp_dict["element_type"] == "component"

    def test_design_component_from_dict(self):
        """Test design component deserialization."""
        comp_dict = {
            "name": "Deserialized Component",
            "purpose": "Test deserialization",
            "element_type": "service",
            "technology": "Node.js/Express"
        }

        component = DesignComponent.from_dict(comp_dict)
        
        assert component.name == "Deserialized Component"
        assert component.element_type == "service"
        assert component.technology == "Node.js/Express"


class TestTaskModels:
    """Test task data models with comprehensive coverage."""

    def test_implementation_task_creation_valid(self):
        """Test implementation task creation with valid data."""
        task = ImplementationTask(
            id="TASK-001",
            title="Implement User Authentication",
            description="Create authentication service with OAuth 2.0",
            requirement_ids=["REQ-001", "REQ-002"],
            status=TaskStatus.PENDING,
            priority=TaskPriority.HIGH,
            estimated_hours=24,
            dependencies=["TASK-002"],
            assignee="developer_1",
            acceptance_criteria=[
                "OAuth 2.0 flow is implemented",
                "JWT token management works",
                "Error handling is comprehensive"
            ],
            deliverables=[
                "Authentication service code",
                "Unit tests",
                "API documentation"
            ],
            progress_percentage=0,
            notes="Waiting for database setup"
        )

        assert task.id == "TASK-001"
        assert task.status == TaskStatus.PENDING
        assert task.priority == TaskPriority.HIGH
        assert task.estimated_hours == 24
        assert len(task.requirement_ids) == 2
        assert len(task.acceptance_criteria) == 3
        assert task.progress_percentage == 0

    def test_implementation_task_creation_minimal(self):
        """Test implementation task creation with minimal data."""
        task = ImplementationTask(
            id="TASK-002",
            title="Minimal Task",
            description="Basic task description"
        )

        assert task.id == "TASK-002"
        assert task.title == "Minimal Task"
        assert task.status == TaskStatus.PENDING  # Default value
        assert task.priority == TaskPriority.MEDIUM  # Default value
        assert task.estimated_hours == 0  # Default value
        assert task.progress_percentage == 0  # Default value

    def test_implementation_task_invalid_status(self):
        """Test implementation task creation with invalid status."""
        with pytest.raises(ValueError):
            ImplementationTask(
                id="TASK-003",
                title="Invalid Status Task",
                description="This should fail",
                status="invalid_status"
            )

    def test_implementation_task_invalid_priority(self):
        """Test implementation task creation with invalid priority."""
        with pytest.raises(ValueError):
            ImplementationTask(
                id="TASK-004",
                title="Invalid Priority Task",
                description="This should fail",
                priority="invalid_priority"
            )

    def test_implementation_task_progress_validation(self):
        """Test implementation task progress percentage validation."""
        # Valid progress values
        task1 = ImplementationTask(
            id="TASK-005",
            title="Valid Progress 0",
            description="Valid 0% progress",
            progress_percentage=0
        )
        assert task1.progress_percentage == 0

        task2 = ImplementationTask(
            id="TASK-006",
            title="Valid Progress 100",
            description="Valid 100% progress",
            progress_percentage=100
        )
        assert task2.progress_percentage == 100

        # Invalid progress values
        with pytest.raises(ValueError):
            ImplementationTask(
                id="TASK-007",
                title="Invalid Progress Negative",
                description="Invalid negative progress",
                progress_percentage=-10
            )

        with pytest.raises(ValueError):
            ImplementationTask(
                id="TASK-008",
                title="Invalid Progress Over 100",
                description="Invalid >100% progress",
                progress_percentage=150
            )

    def test_implementation_task_status_transitions(self):
        """Test implementation task status transitions."""
        task = ImplementationTask(
            id="TASK-009",
            title="Status Transition Test",
            description="Test status transitions"
        )

        # Valid transitions
        task.update_status(TaskStatus.IN_PROGRESS)
        assert task.status == TaskStatus.IN_PROGRESS

        task.update_status(TaskStatus.COMPLETED)
        assert task.status == TaskStatus.COMPLETED

        # Test completed task with 100% progress
        task.progress_percentage = 100
        assert task.is_completed()

        # Test blocked task
        task.update_status(TaskStatus.BLOCKED)
        assert task.status == TaskStatus.BLOCKED
        assert task.is_blocked()

    def test_implementation_task_progress_update(self):
        """Test implementation task progress updates."""
        task = ImplementationTask(
            id="TASK-010",
            title="Progress Update Test",
            description="Test progress updates"
        )

        # Valid progress updates
        task.update_progress(25)
        assert task.progress_percentage == 25

        task.update_progress(50)
        assert task.progress_percentage == 50

        task.update_progress(100)
        assert task.progress_percentage == 100
        assert task.status == TaskStatus.COMPLETED  # Auto-update status

        # Invalid progress updates
        with pytest.raises(ValueError):
            task.update_progress(-5)

        with pytest.raises(ValueError):
            task.update_progress(150)

    def test_implementation_task_dependencies(self):
        """Test implementation task dependency management."""
        task = ImplementationTask(
            id="TASK-011",
            title="Dependency Test",
            description="Test dependency management",
            dependencies=["TASK-012", "TASK-013"]
        )

        assert len(task.dependencies) == 2
        assert "TASK-012" in task.dependencies
        assert "TASK-013" in task.dependencies

        # Add dependency
        task.add_dependency("TASK-014")
        assert len(task.dependencies) == 3
        assert "TASK-014" in task.dependencies

        # Remove dependency
        task.remove_dependency("TASK-012")
        assert len(task.dependencies) == 2
        assert "TASK-012" not in task.dependencies

        # Check if task has dependencies
        assert task.has_dependencies()

        # Check if specific dependency exists
        assert task.has_dependency("TASK-013")
        assert not task.has_dependency("TASK-012")

    def test_implementation_task_to_dict(self):
        """Test implementation task serialization."""
        task = ImplementationTask(
            id="TASK-015",
            title="Serialization Test",
            description="Test serialization functionality"
        )

        task_dict = task.to_dict()
        
        assert isinstance(task_dict, dict)
        assert task_dict["id"] == "TASK-015"
        assert task_dict["title"] == "Serialization Test"
        assert task_dict["status"] == TaskStatus.PENDING.value

    def test_implementation_task_from_dict(self):
        """Test implementation task deserialization."""
        task_dict = {
            "id": "TASK-016",
            "title": "Deserialization Test",
            "description": "Test deserialization functionality",
            "status": "in_progress",
            "priority": "high",
            "estimated_hours": 16
        }

        task = ImplementationTask.from_dict(task_dict)
        
        assert task.id == "TASK-016"
        assert task.title == "Deserialization Test"
        assert task.status == TaskStatus.IN_PROGRESS
        assert task.priority == TaskPriority.HIGH
        assert task.estimated_hours == 16


class TestOpenSpecValidator:
    """Test OpenSpec validator with comprehensive coverage."""

    @pytest.fixture
    def validator(self):
        """Create a validator instance for testing."""
        return OpenSpecValidator()

    @pytest.mark.asyncio
    async def test_validate_requirement_valid(self, validator):
        """Test validating a valid requirement."""
        scenario = Scenario(
            given="user wants to login",
            when="user provides valid credentials",
            then="user is authenticated"
        )

        requirement = Requirement(
            id="REQ-VALID-001",
            title="Valid Requirement",
            description="A valid requirement for testing",
            priority="high",
            acceptance_criteria=["Valid criterion 1", "Valid criterion 2"],
            scenarios=[scenario]
        )

        result = await validator.validate_requirement(requirement)
        
        assert result.is_valid
        assert len(result.issues) == 0
        assert result.summary == "Requirement validation passed"

    @pytest.mark.asyncio
    async def test_validate_requirement_invalid_id(self, validator):
        """Test validating requirement with invalid ID."""
        requirement = Requirement(
            id="",  # Invalid empty ID
            title="Invalid ID Requirement",
            description="This should fail validation"
        )

        result = await validator.validate_requirement(requirement)
        
        assert not result.is_valid
        assert len(result.issues) > 0
        assert any(issue.code == "REQ_001" for issue in result.issues)  # ID validation error

    @pytest.mark.asyncio
    async def test_validate_requirement_missing_scenarios(self, validator):
        """Test validating requirement without scenarios."""
        requirement = Requirement(
            id="REQ-NO-SCENARIOS",
            title="No Scenarios Requirement",
            description="Requirement without scenarios",
            acceptance_criteria=["Some criterion"]
            # Missing scenarios
        )

        result = await validator.validate_requirement(requirement)
        
        assert not result.is_valid
        assert any(issue.code == "REQ_002" for issue in result.issues)  # Missing scenarios error

    @pytest.mark.asyncio
    async def test_validate_design_component_valid(self, validator):
        """Test validating a valid design component."""
        component = DesignComponent(
            name="Valid Component",
            purpose="Valid component for testing",
            element_type="service",
            interfaces=[
                {
                    "name": "test_api",
                    "description": "Test API",
                    "input_type": "TestRequest",
                    "output_type": "TestResponse",
                    "protocol": "HTTP/REST"
                }
            ]
        )

        result = await validator.validate_design_component(component)
        
        assert result.is_valid
        assert len(result.issues) == 0

    @pytest.mark.asyncio
    async def test_validate_design_component_invalid_type(self, validator):
        """Test validating design component with invalid type."""
        component = DesignComponent(
            name="Invalid Type Component",
            purpose="Component with invalid type",
            element_type="invalid_type"
        )

        result = await validator.validate_design_component(component)
        
        assert not result.is_valid
        assert any(issue.code == "DESIGN_001" for issue in result.issues)  # Invalid type error

    @pytest.mark.asyncio
    async def test_validate_implementation_task_valid(self, validator):
        """Test validating a valid implementation task."""
        task = ImplementationTask(
            id="TASK-VALID-001",
            title="Valid Task",
            description="A valid task for testing",
            requirement_ids=["REQ-001"],
            status=TaskStatus.PENDING,
            priority=TaskPriority.HIGH,
            acceptance_criteria=["Valid criterion"],
            deliverables=["Valid deliverable"]
        )

        result = await validator.validate_task(task)
        
        assert result.is_valid
        assert len(result.issues) == 0

    @pytest.mark.asyncio
    async def test_validate_implementation_task_invalid_progress(self, validator):
        """Test validating task with invalid progress."""
        task = ImplementationTask(
            id="TASK-INVALID-PROGRESS",
            title="Invalid Progress Task",
            description="Task with invalid progress",
            progress_percentage=150  # Invalid > 100%
        )

        result = await validator.validate_task(task)
        
        assert not result.is_valid
        assert any(issue.code == "TASK_001" for issue in result.issues)  # Invalid progress error

    @pytest.mark.asyncio
    async def test_validate_cross_references(self, validator):
        """Test cross-reference validation."""
        # Create test data with cross-references
        requirements = [
            Requirement(id="REQ-001", title="Req 1", description="Requirement 1"),
            Requirement(id="REQ-002", title="Req 2", description="Requirement 2")
        ]

        designs = [
            DesignComponent(
                name="Design 1",
                purpose="Design component 1",
                element_type="service"
            )
        ]

        tasks = [
            ImplementationTask(
                id="TASK-001",
                title="Task 1",
                description="Implementation task 1",
                requirement_ids=["REQ-001"]
            )
        ]

        result = await validator.validate_cross_references(requirements, designs, tasks)
        
        assert result.is_valid
        assert len(result.issues) == 0

    @pytest.mark.asyncio
    async def test_validate_cross_references_broken_links(self, validator):
        """Test cross-reference validation with broken links."""
        requirements = [
            Requirement(id="REQ-001", title="Req 1", description="Requirement 1")
        ]

        # Task references non-existent requirement
        tasks = [
            ImplementationTask(
                id="TASK-001",
                title="Task 1",
                description="Implementation task 1",
                requirement_ids=["REQ-999"]  # Non-existent requirement
            )
        ]

        result = await validator.validate_cross_references(requirements, [], tasks)
        
        assert not result.is_valid
        assert any(issue.code == "XREF_001" for issue in result.issues)  # Broken reference error

    def test_validation_result_creation(self):
        """Test validation result creation."""
        issues = [
            ValidationIssue(
                level="error",
                code="TEST_001",
                message="Test error message",
                line_number=10,
                suggestions=["Fix suggestion 1", "Fix suggestion 2"]
            ),
            ValidationIssue(
                level="warning",
                code="TEST_002",
                message="Test warning message"
            )
        ]

        result = ValidationResult(
            is_valid=False,
            issues=issues,
            summary="Validation failed with errors and warnings"
        )

        assert not result.is_valid
        assert len(result.issues) == 2
        assert result.issues[0].level == "error"
        assert result.issues[1].level == "warning"
        assert result.summary == "Validation failed with errors and warnings"

    def test_validation_issue_creation(self):
        """Test validation issue creation."""
        issue = ValidationIssue(
            level="error",
            code="TEST_003",
            message="Test issue message",
            line_number=15,
            column_number=20,
            file_path="test_file.md",
            context="Context line",
            suggestions=["Suggestion 1", "Suggestion 2"]
        )

        assert issue.level == "error"
        assert issue.code == "TEST_003"
        assert issue.line_number == 15
        assert issue.column_number == 20
        assert issue.file_path == "test_file.md"
        assert issue.context == "Context line"
        assert len(issue.suggestions) == 2

    def test_validation_issue_invalid_level(self):
        """Test validation issue creation with invalid level."""
        with pytest.raises(ValueError):
            ValidationIssue(
                level="invalid_level",
                code="TEST_004",
                message="Test message"
            )


class TestReviewOrchestrator:
    """Test review orchestrator with comprehensive coverage."""

    @pytest.fixture
    def orchestrator(self):
        """Create a review orchestrator instance for testing."""
        return ReviewOrchestrator()

    @pytest.mark.asyncio
    async def test_submit_for_review_requirement(self, orchestrator):
        """Test submitting a requirement for review."""
        requirement = Requirement(
            id="REQ-REVIEW-001",
            title="Review Test Requirement",
            description="Requirement for review testing"
        )

        review_id = await orchestrator.submit_for_review(
            item_type="requirement",
            item_id="REQ-REVIEW-001",
            content=requirement,
            priority=ReviewPriority.HIGH
        )

        assert review_id is not None
        assert isinstance(review_id, str)

        # Check review status
        status = orchestrator.get_review_status(review_id)
        assert status is not None
        assert status["item_type"] == "requirement"
        assert status["item_id"] == "REQ-REVIEW-001"
        assert status["priority"] == "high"

    @pytest.mark.asyncio
    async def test_submit_for_review_design(self, orchestrator):
        """Test submitting a design for review."""
        design = DesignComponent(
            name="Review Test Design",
            purpose="Design for review testing",
            element_type="service"
        )

        review_id = await orchestrator.submit_for_review(
            item_type="design",
            item_id="REVIEW-TEST-DESIGN",
            content=design,
            priority=ReviewPriority.MEDIUM
        )

        assert review_id is not None

        status = orchestrator.get_review_status(review_id)
        assert status["item_type"] == "design"
        assert status["item_id"] == "REVIEW-TEST-DESIGN"
        assert status["priority"] == "medium"

    @pytest.mark.asyncio
    async def test_add_stakeholder_feedback(self, orchestrator):
        """Test adding stakeholder feedback to a review."""
        requirement = Requirement(
            id="REQ-FEEDBACK-001",
            title="Feedback Test Requirement",
            description="Requirement for feedback testing"
        )

        review_id = await orchestrator.submit_for_review(
            item_type="requirement",
            item_id="REQ-FEEDBACK-001",
            content=requirement
        )

        # Add stakeholder feedback
        await orchestrator.add_stakeholder_feedback(
            review_id=review_id,
            stakeholder_id="product_manager",
            feedback_type="suggestion",
            category="clarity",
            severity="medium",
            message="Consider making this requirement more specific",
            suggestions=["Add measurable criteria", "Define acceptance tests"]
        )

        # Check feedback was added
        feedback = orchestrator.get_review_feedback(review_id)
        assert len(feedback) > 0

        stakeholder_feedback = [f for f in feedback if f.reviewer_id == "product_manager"]
        assert len(stakeholder_feedback) == 1
        assert stakeholder_feedback[0].category == "clarity"
        assert stakeholder_feedback[0].severity == "medium"
        assert len(stakeholder_feedback[0].suggestions) == 2

    @pytest.mark.asyncio
    async def test_quality_gates_evaluation(self, orchestrator):
        """Test quality gate evaluation during review."""
        requirement = Requirement(
            id="REQ-QUALITY-001",
            title="Quality Gate Test",
            description="Requirement for quality gate testing",
            acceptance_criteria=["Criterion 1", "Criterion 2"],
            scenarios=[
                Scenario(
                    given="test condition",
                    when="test action",
                    then="test result"
                )
            ]
        )

        review_id = await orchestrator.submit_for_review(
            item_type="requirement",
            item_id="REQ-QUALITY-001",
            content=requirement
        )

        # Wait for review to complete (simulated)
        await asyncio.sleep(0.1)

        # Check feedback for quality gate results
        feedback = orchestrator.get_review_feedback(review_id)
        quality_gate_feedback = [f for f in feedback if f.feedback_type == "quality_gate"]
        assert len(quality_gate_feedback) > 0

        # Check that quality gates were evaluated
        gate_categories = set(f.category for f in quality_gate_feedback)
        expected_gates = {"Format Compliance", "Content Completeness", "Validation Pass Rate"}
        assert len(gate_categories.intersection(expected_gates)) >= 2

    def test_get_review_status_nonexistent(self, orchestrator):
        """Test getting status for non-existent review."""
        status = orchestrator.get_review_status("non_existent_review_id")
        assert status is None

    def test_get_review_feedback_nonexistent(self, orchestrator):
        """Test getting feedback for non-existent review."""
        feedback = orchestrator.get_review_feedback("non_existent_review_id")
        assert feedback == []

    @pytest.mark.asyncio
    async def test_review_workflow_stages(self, orchestrator):
        """Test review workflow progression through stages."""
        requirement = Requirement(
            id="REQ-WORKFLOW-001",
            title="Workflow Test Requirement",
            description="Requirement for workflow testing"
        )

        review_id = await orchestrator.submit_for_review(
            item_type="requirement",
            item_id="REQ-WORKFLOW-001",
            content=requirement
        )

        # Check initial stage
        status = orchestrator.get_review_status(review_id)
        assert status["stage"] == ReviewStage.INITIATED.value

        # Wait for automated processing
        await asyncio.sleep(0.1)

        # Check that review progressed
        updated_status = orchestrator.get_review_status(review_id)
        assert updated_status["stage"] in [stage.value for stage in ReviewStage]

    @pytest.mark.asyncio
    async def test_batch_review_submission(self, orchestrator):
        """Test submitting multiple items for review."""
        requirements = [
            Requirement(id=f"REQ-BATCH-{i:03d}", title=f"Batch Requirement {i}", description=f"Description {i}")
            for i in range(1, 4)
        ]

        review_ids = []
        for req in requirements:
            review_id = await orchestrator.submit_for_review(
                item_type="requirement",
                item_id=req.id,
                content=req
            )
            review_ids.append(review_id)

        assert len(review_ids) == 3
        assert all(review_id is not None for review_id in review_ids)

        # Check all reviews exist
        for review_id in review_ids:
            status = orchestrator.get_review_status(review_id)
            assert status is not None
            assert status["item_type"] == "requirement"


class TestOpenSpecTemplateEngine:
    """Test OpenSpec template engine with comprehensive coverage."""

    @pytest.fixture
    def template_engine(self):
        """Create a template engine instance for testing."""
        return OpenSpecTemplateEngine()

    def test_template_engine_initialization(self, template_engine):
        """Test template engine initialization."""
        assert template_engine is not None
        assert len(template_engine.list_templates()) > 0

        # Check that built-in templates are loaded
        available_templates = template_engine.list_templates()
        assert "requirement" in available_templates
        assert "design" in available_templates
        assert "task" in available_templates

    def test_render_requirement_template(self, template_engine):
        """Test rendering requirement template."""
        data = {
            "name": "Test System",
            "version": "1.0.0",
            "overview": "Test system for template rendering",
            "requirements": [
                {
                    "id": "REQ-001",
                    "title": "Test Requirement",
                    "description": "This is a test requirement",
                    "priority": "high",
                    "acceptance_criteria": ["Criteria 1", "Criteria 2"],
                    "scenarios": [
                        {
                            "given": "test condition",
                            "when": "test action",
                            "then": "test result"
                        }
                    ]
                }
            ]
        }

        rendered = template_engine.render_template("requirement", data)
        
        assert rendered is not None
        assert isinstance(rendered, str)
        assert "Test System" in rendered
        assert "REQ-001" in rendered
        assert "Test Requirement" in rendered
        assert "test condition" in rendered

    def test_render_design_template(self, template_engine):
        """Test rendering design template."""
        data = {
            "name": "Test System Design",
            "version": "1.0.0",
            "design_overview": "System architecture for test application",
            "design_components": [
                {
                    "name": "Test Component",
                    "purpose": "Test component purpose",
                    "element_type": "service",
                    "technology": "Python/FastAPI"
                }
            ]
        }

        rendered = template_engine.render_template("design", data)
        
        assert rendered is not None
        assert "Test System Design" in rendered
        assert "Test Component" in rendered
        assert "Python/FastAPI" in rendered

    def test_render_task_template(self, template_engine):
        """Test rendering task template."""
        data = {
            "name": "Test System Tasks",
            "version": "1.0.0",
            "overview": "Implementation tasks for test system",
            "tasks": [
                {
                    "id": "TASK-001",
                    "title": "Test Task",
                    "description": "This is a test task",
                    "priority": "high",
                    "estimated_hours": 16,
                    "acceptance_criteria": ["Criterion 1", "Criterion 2"],
                    "deliverables": ["Deliverable 1", "Deliverable 2"]
                }
            ]
        }

        rendered = template_engine.render_template("task", data)
        
        assert rendered is not None
        assert "Test System Tasks" in rendered
        assert "TASK-001" in rendered
        assert "Test Task" in rendered

    def test_add_custom_template(self, template_engine):
        """Test adding custom template."""
        custom_template = """
# {{ title }}

{{ description }}

## Criteria
{% for criteria in criteria %}
- {{ criteria }}
{% endfor %}
        """.strip()

        template_engine.add_template("custom", custom_template)

        # Verify template was added
        available_templates = template_engine.list_templates()
        assert "custom" in available_templates

        # Render custom template
        data = {
            "title": "Custom Template Test",
            "description": "Testing custom template functionality",
            "criteria": ["Criteria 1", "Criteria 2", "Criteria 3"]
        }

        rendered = template_engine.render_template("custom", data)
        
        assert "Custom Template Test" in rendered
        assert "Testing custom template functionality" in rendered
        assert "- Criteria 1" in rendered
        assert "- Criteria 2" in rendered
        assert "- Criteria 3" in rendered

    def test_validate_template_valid(self, template_engine):
        """Test validating a valid template."""
        valid_template = "{{ title }} - {{ description }}"
        
        is_valid = template_engine.validate_template("valid_test", valid_template)
        assert is_valid

    def test_validate_template_invalid(self, template_engine):
        """Test validating an invalid template."""
        invalid_template = "{{ title"  # Missing closing brace
        
        is_valid = template_engine.validate_template("invalid_test", invalid_template)
        assert not is_valid

    def test_render_template_with_missing_data(self, template_engine):
        """Test rendering template with missing data."""
        data = {
            "title": "Test Title"
            # Missing 'description' field
        }

        # Should not raise error, but handle missing data gracefully
        rendered = template_engine.render_template("requirement", data)
        
        assert rendered is not None
        assert "Test Title" in rendered

    def test_render_nonexistent_template(self, template_engine):
        """Test rendering a non-existent template."""
        data = {"title": "Test"}
        
        with pytest.raises(ValueError):
            template_engine.render_template("nonexistent_template", data)

    def test_template_with_complex_data(self, template_engine):
        """Test rendering template with complex nested data."""
        data = {
            "name": "Complex System",
            "requirements": [
                {
                    "id": "REQ-001",
                    "title": "Complex Requirement",
                    "scenarios": [
                        {
                            "given": "complex condition",
                            "when": "complex action",
                            "then": "complex result",
                            "and_conditions": ["additional condition 1", "additional condition 2"],
                            "but_conditions": ["exception condition"]
                        }
                    ],
                    "metadata": {
                        "source": "stakeholder",
                        "priority_score": 9,
                        "tags": ["security", "performance"]
                    }
                }
            ]
        }

        rendered = template_engine.render_template("requirement", data)
        
        assert rendered is not None
        assert "Complex System" in rendered
        assert "complex condition" in rendered
        assert "additional condition 1" in rendered
        assert "exception condition" in rendered

    def test_template_performance(self, template_engine):
        """Test template rendering performance."""
        data = {
            "name": "Performance Test System",
            "requirements": [
                {
                    "id": f"REQ-{i:03d}",
                    "title": f"Requirement {i}",
                    "description": f"Description for requirement {i}",
                    "scenarios": [
                        {
                            "given": f"Condition {i}",
                            "when": f"Action {i}",
                            "then": f"Result {i}"
                        }
                    ]
                }
                for i in range(100)  # Large dataset
            ]
        }

        start_time = time.time()
        rendered = template_engine.render_template("requirement", data)
        end_time = time.time()

        duration = end_time - start_time
        
        assert rendered is not None
        assert len(rendered) > 0
        assert duration < 5.0  # Should complete within 5 seconds
        assert f"REQ-050" in rendered  # Check that middle requirement is included
        assert f"REQ-099" in rendered  # Check that last requirement is included


if __name__ == "__main__":
    pytest.main([__file__])