"""
Integration tests for OpenSpec workflow.

Tests the complete OpenSpec integration including requirement generation,
design generation, task generation, and review orchestration.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from metagpt.openspec import (
    OpenSpecRequirement,
    OpenSpecDesign,
    OpenSpecTaskSpecification,
    OpenSpecValidator,
    ReviewOrchestrator,
    ReviewStage,
    ReviewPriority,
    Requirement,
    Scenario,
    ImplementationTask,
    TaskStatus,
    TaskPriority
)
from metagpt.openspec.models.requirement import Requirement
from metagpt.openspec.models.design import DesignComponent, RequirementMapping
from metagpt.openspec.models.task import ImplementationTask


class TestOpenSpecIntegration:
    """Test OpenSpec integration functionality."""

    @pytest.fixture
    def sample_requirement(self):
        """Create a sample OpenSpec requirement for testing."""
        return OpenSpecRequirement(
            name="Test System",
            version="1.0.0",
            overview="A test system for OpenSpec integration",
            requirements=[
                Requirement(
                    id="REQ-001",
                    title="User Authentication",
                    description="The system SHALL authenticate users before access",
                    priority="high",
                    acceptance_criteria=[
                        "Users can register with email and password",
                        "Users can login with valid credentials",
                        "Invalid login attempts are rejected"
                    ],
                    scenarios=[
                        Scenario(
                            given="a new user wants to register",
                            when="the user provides valid email and password",
                            then="the system creates a new account"
                        )
                    ]
                ),
                Requirement(
                    id="REQ-002",
                    title="Data Storage",
                    description="The system SHALL store user data securely",
                    priority="medium",
                    acceptance_criteria=[
                        "User data is encrypted at rest",
                        "Data backups are performed daily",
                        "Personal information is protected"
                    ]
                )
            ]
        )

    @pytest.fixture
    def sample_design(self):
        """Create a sample OpenSpec design for testing."""
        return OpenSpecDesign(
            name="Test System Design",
            version="1.0.0",
            design_overview="System architecture for the test application",
            design_components=[
                DesignComponent(
                    name="Authentication Service",
                    purpose="Handle user authentication and authorization",
                    element_type="service",
                    description="Microservice responsible for user login, registration, and session management",
                    interfaces=[
                        {
                            "name": "login_api",
                            "description": "REST API for user login",
                            "input_type": "LoginRequest",
                            "output_type": "AuthResponse",
                            "protocol": "HTTP/REST",
                            "endpoint": "/api/auth/login"
                        }
                    ],
                    dependencies=["Database", "Email Service"],
                    technology="Python/FastAPI"
                ),
                DesignComponent(
                    name="Database",
                    purpose="Store application data",
                    element_type="data_store",
                    description="PostgreSQL database for persistent data storage",
                    technology="PostgreSQL"
                )
            ],
            requirements_mapping=[
                RequirementMapping(
                    requirement_id="REQ-001",
                    requirement_title="User Authentication",
                    design_elements=["Authentication Service"],
                    implementation_notes="Use JWT tokens for session management",
                    verification_method="Unit tests and integration tests"
                )
            ]
        )

    @pytest.fixture
    def sample_task_spec(self):
        """Create a sample OpenSpec task specification for testing."""
        return OpenSpecTaskSpecification(
            name="Test System Tasks",
            version="1.0.0",
            overview="Implementation tasks for the test system",
            tasks=[
                ImplementationTask(
                    id="TASK-001",
                    title="Setup Authentication Service",
                    description="Implement the authentication service with login and registration endpoints",
                    requirement_ids=["REQ-001"],
                    status=TaskStatus.PENDING,
                    priority=TaskPriority.HIGH,
                    estimated_hours=16,
                    dependencies=["TASK-002"],  # Database setup
                    acceptance_criteria=[
                        "Authentication service is created",
                        "Login endpoint is implemented",
                        "Registration endpoint is implemented",
                        "JWT token management is working"
                    ],
                    deliverables=[
                        "Authentication service code",
                        "API documentation",
                        "Unit tests"
                    ]
                ),
                ImplementationTask(
                    id="TASK-002",
                    title="Setup Database",
                    description="Configure PostgreSQL database and create user tables",
                    requirement_ids=["REQ-002"],
                    status=TaskStatus.PENDING,
                    priority=TaskPriority.HIGH,
                    estimated_hours=8,
                    acceptance_criteria=[
                        "Database is created",
                        "User tables are created",
                        "Database connection is configured"
                    ],
                    deliverables=[
                        "Database schema",
                        "Migration scripts",
                        "Connection configuration"
                    ]
                )
            ]
        )

    def test_openspec_requirement_creation(self, sample_requirement):
        """Test OpenSpec requirement creation and validation."""
        assert sample_requirement.name == "Test System"
        assert len(sample_requirement.requirements) == 2
        assert sample_requirement.requirements[0].id == "REQ-001"
        assert len(sample_requirement.requirements[0].scenarios) == 1

    def test_openspec_design_creation(self, sample_design):
        """Test OpenSpec design creation and validation."""
        assert sample_design.name == "Test System Design"
        assert len(sample_design.design_components) == 2
        assert len(sample_design.requirements_mapping) == 1
        assert sample_design.design_components[0].name == "Authentication Service"

    def test_openspec_task_creation(self, sample_task_spec):
        """Test OpenSpec task specification creation and validation."""
        assert sample_task_spec.name == "Test System Tasks"
        assert len(sample_task_spec.tasks) == 2
        assert sample_task_spec.tasks[0].requirement_ids == ["REQ-001"]
        assert sample_task_spec.tasks[0].priority == TaskPriority.HIGH

    def test_requirement_to_design_traceability(self, sample_requirement, sample_design):
        """Test traceability from requirements to design."""
        # Check that REQ-001 is mapped in the design
        mapped_requirements = set()
        for mapping in sample_design.requirements_mapping:
            mapped_requirements.add(mapping.requirement_id)

        assert "REQ-001" in mapped_requirements
        assert len(sample_design.requirements_mapping) > 0

    def test_design_to_task_traceability(self, sample_design, sample_task_spec):
        """Test traceability from design to tasks."""
        # Check that tasks reference requirements that are mapped in design
        task_requirements = set()
        for task in sample_task_spec.tasks:
            task_requirements.update(task.requirement_ids)

        # At least one task should reference a mapped requirement
        design_requirements = set(mapping.requirement_id for mapping in sample_design.requirements_mapping)
        assert len(task_requirements.intersection(design_requirements)) > 0

    @pytest.mark.asyncio
    async def test_requirement_validation(self, sample_requirement):
        """Test requirement validation."""
        validator = OpenSpecValidator()
        result = await validator.validate_requirement(sample_requirement)

        # Should pass basic validation
        assert result.is_valid
        assert len(result.issues) == 0

    @pytest.mark.asyncio
    async def test_design_validation(self, sample_design):
        """Test design validation."""
        validator = OpenSpecValidator()
        result = await validator.validate_design(sample_design)

        # Should pass basic validation
        assert result.is_valid
        assert len(result.issues) == 0

    @pytest.mark.asyncio
    async def test_task_validation(self, sample_task_spec):
        """Test task specification validation."""
        validator = OpenSpecValidator()
        result = await validator.validate_task(sample_task_spec)

        # Should pass basic validation
        assert result.is_valid
        assert len(result.issues) == 0

    @pytest.mark.asyncio
    async def test_review_orchestrator_workflow(self, sample_requirement):
        """Test the complete review orchestrator workflow."""
        orchestrator = ReviewOrchestrator()

        # Submit requirement for review
        review_id = await orchestrator.submit_for_review(
            item_type="requirement",
            item_id="REQ-001",
            content=sample_requirement,
            priority=ReviewPriority.HIGH
        )

        assert review_id is not None

        # Wait for review to complete (simulate async processing)
        await asyncio.sleep(0.1)

        # Check review status
        status = orchestrator.get_review_status(review_id)
        assert status is not None
        assert status["item_type"] == "requirement"
        assert status["item_id"] == "REQ-001"
        assert status["priority"] == "high"

        # Check that review progressed through stages
        assert status["stage"] in [stage.value for stage in ReviewStage]

    @pytest.mark.asyncio
    async def test_stakeholder_feedback(self, sample_design):
        """Test adding stakeholder feedback to reviews."""
        orchestrator = ReviewOrchestrator()

        # Submit design for review
        review_id = await orchestrator.submit_for_review(
            item_type="design",
            item_id="DESIGN-001",
            content=sample_design
        )

        # Add stakeholder feedback
        await orchestrator.add_stakeholder_feedback(
            review_id=review_id,
            stakeholder_id="product_manager",
            feedback_type="suggestion",
            category="usability",
            severity="medium",
            message="Consider adding user interface components for better UX",
            suggestions=["Add UI component specifications", "Include user workflow diagrams"]
        )

        # Check feedback was added
        feedback = orchestrator.get_review_feedback(review_id)
        assert len(feedback) > 0

        stakeholder_feedback = [f for f in feedback if f.reviewer_id == "product_manager"]
        assert len(stakeholder_feedback) == 1
        assert stakeholder_feedback[0].category == "usability"

    @pytest.mark.asyncio
    async def test_quality_gates(self, sample_requirement):
        """Test quality gate evaluation."""
        orchestrator = ReviewOrchestrator()

        # Submit requirement for review
        review_id = await orchestrator.submit_for_review(
            item_type="requirement",
            item_id="REQ-001",
            content=sample_requirement
        )

        # Wait for review to complete
        await asyncio.sleep(0.1)

        # Check feedback for quality gate results
        feedback = orchestrator.get_review_feedback(review_id)
        quality_gate_feedback = [f for f in feedback if f.feedback_type == "quality_gate"]
        assert len(quality_gate_feedback) > 0

        # Check that quality gates were evaluated
        gate_names = set(f.category for f in quality_gate_feedback)
        expected_gates = {"Format Compliance", "Content Completeness", "Validation Pass Rate"}
        assert gate_names.intersection(expected_gates)

    def test_cross_reference_management(self, sample_design):
        """Test cross-reference management functionality."""
        from metagpt.openspec.cross_ref.design_manager import DesignCrossReferenceManager

        manager = DesignCrossReferenceManager()

        # Add design to manager
        manager.add_design(sample_design)

        # Test requirement to design mapping
        designs_for_req = manager.get_designs_for_requirement("REQ-001")
        assert len(designs_for_req) > 0

        # Test component to requirement mapping
        reqs_for_component = manager.get_requirements_for_component("Authentication Service")
        assert len(reqs_for_component) > 0

        # Test traceability verification
        uncovered = manager.verify_traceability()
        assert isinstance(uncovered, list)

        # Test design reference validation
        errors = manager.validate_design_references()
        assert isinstance(errors, list)

    def test_template_engine_rendering(self):
        """Test template engine functionality."""
        from metagpt.openspec.template_engine import OpenSpecTemplateEngine

        engine = OpenSpecTemplateEngine()

        # Test requirement template rendering
        requirement_data = {
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

        rendered = engine.render_template("requirement", requirement_data)
        assert rendered is not None
        assert "Test System" in rendered
        assert "REQ-001" in rendered
        assert "Test Requirement" in rendered

    @pytest.mark.asyncio
    async def test_end_to_end_workflow(self, sample_requirement, sample_design, sample_task_spec):
        """Test complete end-to-end OpenSpec workflow."""
        validator = OpenSpecValidator()
        orchestrator = ReviewOrchestrator()

        # Step 1: Validate all specifications
        req_validation = await validator.validate_requirement(sample_requirement)
        design_validation = await validator.validate_design(sample_design)
        task_validation = await validator.validate_task(sample_task_spec)

        assert req_validation.is_valid
        assert design_validation.is_valid
        assert task_validation.is_valid

        # Step 2: Submit all for review
        req_review_id = await orchestrator.submit_for_review(
            "requirement", "REQ-001", sample_requirement, ReviewPriority.HIGH
        )
        design_review_id = await orchestrator.submit_for_review(
            "design", "DESIGN-001", sample_design, ReviewPriority.MEDIUM
        )
        task_review_id = await orchestrator.submit_for_review(
            "task", "TASK-001", sample_task_spec, ReviewPriority.MEDIUM
        )

        # Wait for reviews to complete
        await asyncio.sleep(0.1)

        # Step 3: Check all review statuses
        req_status = orchestrator.get_review_status(req_review_id)
        design_status = orchestrator.get_review_status(design_review_id)
        task_status = orchestrator.get_review_status(task_review_id)

        assert req_status is not None
        assert design_status is not None
        assert task_status is not None

        # Step 4: Verify traceability chain
        assert sample_requirement.requirements[0].id == "REQ-001"
        assert sample_design.requirements_mapping[0].requirement_id == "REQ-001"
        assert sample_task_spec.tasks[0].requirement_ids == ["REQ-001"]

        # Complete workflow should be successful
        assert all([
            req_status["stage"] != "failed",
            design_status["stage"] != "failed",
            task_status["stage"] != "failed"
        ])


class TestOpenSpecErrorHandling:
    """Test error handling in OpenSpec components."""

    @pytest.mark.asyncio
    async def test_validation_error_handling(self):
        """Test validation with invalid input."""
        validator = OpenSpecValidator()

        # Test with None input
        result = await validator.validate_requirement(None)
        assert not result.is_valid
        assert len(result.issues) > 0

    def test_template_error_handling(self):
        """Test template engine error handling."""
        from metagpt.openspec.template_engine import OpenSpecTemplateEngine

        engine = OpenSpecTemplateEngine()

        # Test with invalid template
        with pytest.raises(Exception):
            engine.render_template("invalid_template", {})

    @pytest.mark.asyncio
    async def test_review_orchestrator_error_handling(self):
        """Test review orchestrator error handling."""
        orchestrator = ReviewOrchestrator()

        # Test getting status for non-existent review
        status = orchestrator.get_review_status("non_existent")
        assert status is None

        # Test getting feedback for non-existent review
        feedback = orchestrator.get_review_feedback("non_existent")
        assert feedback == []

    def test_cross_reference_error_handling(self):
        """Test cross-reference manager error handling."""
        from metagpt.openspec.cross_ref.design_manager import DesignCrossReferenceManager

        manager = DesignCrossReferenceManager()

        # Test with empty manager
        designs = manager.get_designs_for_requirement("non_existent")
        assert designs == []

        requirements = manager.get_requirements_for_component("non_existent")
        assert requirements == []


if __name__ == "__main__":
    pytest.main([__file__])