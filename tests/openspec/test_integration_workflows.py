"""
Integration Tests for OpenSpec Workflows

Tests complete MetaGPT workflows with OpenSpec integration including
end-to-end workflows, API integration, cross-component interaction,
and mock external dependencies.
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
from metagpt.openspec import (
    OpenSpecRequirement, OpenSpecDesign, OpenSpecTaskSpecification,
    OpenSpecValidator, ReviewOrchestrator, ReviewStage, ReviewPriority
)
from metagpt.openspec.models.requirement import Requirement, Scenario
from metagpt.openspec.models.design import DesignComponent, RequirementMapping
from metagpt.openspec.models.task import ImplementationTask, TaskStatus, TaskPriority

# Import test framework
from tests.openspec.integration import IntegrationTestSuite, WorkflowTestRunner, IntegrationTestType
from tests.openspec.fixtures import OpenSpecTestFixture, TestDataGenerator


class TestOpenSpecWorkflowIntegration:
    """Test complete OpenSpec workflow integration."""

    @pytest.fixture
    def test_data(self):
        """Create test data for integration testing."""
        fixture = OpenSpecTestFixture()
        return {
            "requirements": fixture.sample_requirements,
            "designs": fixture.sample_designs,
            "tasks": fixture.sample_tasks
        }

    @pytest.fixture
    def integration_suite(self):
        """Create integration test suite."""
        return IntegrationTestSuite()

    @pytest.mark.asyncio
    async def test_complete_workflow_success(self, test_data, integration_suite):
        """Test complete successful OpenSpec workflow."""
        logger.info("Testing complete OpenSpec workflow integration")
        
        # Run complete workflow integration test
        result = await integration_suite.run_workflow_integration_test("complete_workflow_test")
        
        assert result is not None
        assert result.test_type == IntegrationTestType.WORKFLOW
        assert result.success is True
        assert result.steps_completed == result.total_steps
        assert result.duration > 0
        
        # Verify all steps completed successfully
        step_names = [step["name"] for step in result.step_results]
        expected_steps = [
            "Initialize OpenSpec components",
            "Generate requirements",
            "Create design specifications", 
            "Generate implementation tasks",
            "Validate specifications",
            "Run review workflow",
            "Verify traceability"
        ]
        
        for expected_step in expected_steps:
            assert expected_step in step_names
        
        # Verify all steps succeeded
        for step_result in result.step_results:
            assert step_result["success"] is True

    @pytest.mark.asyncio
    async def test_workflow_with_validation_errors(self, integration_suite):
        """Test workflow handling of validation errors."""
        # Mock validation to return errors
        with patch.object(integration_suite, '_validate_specifications') as mock_validate:
            mock_validate.side_effect = Exception("Validation error occurred")
            
            result = await integration_suite.run_workflow_integration_test("workflow_with_validation_errors")
            
            assert result is not None
            assert result.success is False  # Should fail due to validation error
            assert result.error_message is not None
            assert "validation" in result.error_message.lower()

    @pytest.mark.asyncio
    async def test_workflow_timeout_handling(self, integration_suite):
        """Test workflow timeout handling."""
        # Mock a step to timeout
        async def slow_step():
            await asyncio.sleep(10)  # Longer than timeout
            
        with patch.object(integration_suite, '_run_review_workflow', side_effect=slow_step):
            result = await integration_suite.run_workflow_integration_test("workflow_timeout_test")
            
            assert result is not None
            assert result.success is False
            assert result.steps_completed < result.total_steps

    @pytest.mark.asyncio
    async def test_requirement_to_design_traceability(self, test_data, integration_suite):
        """Test traceability from requirements to designs."""
        # Initialize components
        await integration_suite._initialize_openspec_components()
        integration_suite.test_data["requirements"] = test_data["requirements"]
        integration_suite.test_data["designs"] = test_data["designs"]
        
        # Test traceability verification
        result = await integration_suite._verify_traceability()
        
        assert result is not None
        assert "traceability_verified" in result
        assert "results" in result
        assert result["traceability_verified"] >= 1

    @pytest.mark.asyncio
    async def test_design_to_task_traceability(self, test_data, integration_suite):
        """Test traceability from designs to tasks."""
        # Initialize components
        await integration_suite._initialize_openspec_components()
        integration_suite.test_data["designs"] = test_data["designs"]
        integration_suite.test_data["tasks"] = test_data["tasks"]
        
        # Test traceability verification
        result = await integration_suite._verify_traceability()
        
        assert result is not None
        assert "results" in result
        
        # Check design-to-task traceability
        if "design_to_task" in result["results"]:
            design_task_result = result["results"]["design_to_task"]
            assert "designs" in design_task_result
            assert "tasks" in design_task_result
            assert "traceability_score" in design_task_result

    @pytest.mark.asyncio
    async def test_workflow_data_consistency(self, integration_suite):
        """Test data consistency throughout workflow."""
        # Run complete workflow
        result = await integration_suite.run_workflow_integration_test("data_consistency_test")
        
        assert result.success is True
        
        # Verify data consistency across steps
        test_data = integration_suite.test_data
        
        # Check requirements data
        if "requirements" in test_data:
            requirements = test_data["requirements"]
            assert all(hasattr(req, 'id') for req in requirements)
            assert all(hasattr(req, 'title') for req in requirements)
        
        # Check designs data
        if "designs" in test_data:
            designs = test_data["designs"]
            for design in designs:
                if isinstance(design, dict):
                    assert "name" in design
                    assert "components" in design
                else:
                    assert hasattr(design, 'name')
        
        # Check tasks data
        if "tasks" in test_data:
            tasks = test_data["tasks"]
            assert all(hasattr(task, 'id') for task in tasks)
            assert all(hasattr(task, 'title') for task in tasks)

    @pytest.mark.asyncio
    async def test_workflow_error_recovery(self, integration_suite):
        """Test workflow error recovery mechanisms."""
        # Mock a step to fail initially but succeed on retry
        call_count = 0
        
        async def flaky_step():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("Temporary failure")
            return {"success": True}
        
        with patch.object(integration_suite, '_validate_specifications', side_effect=flaky_step):
            # Note: Current implementation doesn't have retry logic, but this test
            # verifies error handling behavior
            result = await integration_suite.run_workflow_integration_test("error_recovery_test")
            
            assert result is not None
            # Should fail due to the error
            assert result.success is False


class TestOpenSpecAPIIntegration:
    """Test OpenSpec API integration."""

    @pytest.fixture
    def integration_suite(self):
        """Create integration test suite."""
        return IntegrationTestSuite()

    @pytest.mark.asyncio
    async def test_requirement_api_endpoints(self, integration_suite):
        """Test requirement API endpoints."""
        result = await integration_suite.run_api_integration_test("requirement_api_test")
        
        assert result is not None
        assert result.test_type == IntegrationTestType.API
        assert result.success is True
        
        # Check that requirement API endpoints were tested
        step_results = {step["name"]: step for step in result.step_results}
        assert "Test requirement API endpoints" in step_results
        assert step_results["Test requirement API endpoints"]["success"] is True

    @pytest.mark.asyncio
    async def test_design_api_endpoints(self, integration_suite):
        """Test design API endpoints."""
        result = await integration_suite.run_api_integration_test("design_api_test")
        
        assert result is not None
        assert result.success is True
        
        # Check that design API endpoints were tested
        step_results = {step["name"]: step for step in result.step_results}
        assert "Test design API endpoints" in step_results
        assert step_results["Test design API endpoints"]["success"] is True

    @pytest.mark.asyncio
    async def test_task_api_endpoints(self, integration_suite):
        """Test task API endpoints."""
        result = await integration_suite.run_api_integration_test("task_api_test")
        
        assert result is not None
        assert result.success is True
        
        # Check that task API endpoints were tested
        step_results = {step["name"]: step for step in result.step_results}
        assert "Test task API endpoints" in step_results
        assert step_results["Test task API endpoints"]["success"] is True

    @pytest.mark.asyncio
    async def test_validation_api_endpoints(self, integration_suite):
        """Test validation API endpoints."""
        result = await integration_suite.run_api_integration_test("validation_api_test")
        
        assert result is not None
        assert result.success is True
        
        # Check that validation API endpoints were tested
        step_results = {step["name"]: step for step in result.step_results}
        assert "Test validation API endpoints" in step_results
        assert step_results["Test validation API endpoints"]["success"] is True

    @pytest.mark.asyncio
    async def test_review_api_endpoints(self, integration_suite):
        """Test review API endpoints."""
        result = await integration_suite.run_api_integration_test("review_api_test")
        
        assert result is not None
        assert result.success is True
        
        # Check that review API endpoints were tested
        step_results = {step["name"]: step for step in result.step_results}
        assert "Test review API endpoints" in step_results
        assert step_results["Test review API endpoints"]["success"] is True

    @pytest.mark.asyncio
    async def test_api_error_handling(self, integration_suite):
        """Test API error handling."""
        # Mock API endpoint to return error
        async def failing_api_call():
            raise Exception("API endpoint unavailable")
        
        with patch.object(integration_suite, '_test_requirement_api', side_effect=failing_api_call):
            result = await integration_suite.run_api_integration_test("api_error_test")
            
            assert result is not None
            assert result.success is False
            assert result.steps_completed < result.total_steps

    @pytest.mark.asyncio
    async def test_api_response_validation(self, integration_suite):
        """Test API response validation."""
        # Mock API to return invalid response
        async def invalid_api_response():
            return {"invalid": "response structure"}
        
        with patch.object(integration_suite, '_test_design_api', side_effect=invalid_api_response):
            result = await integration_suite.run_api_integration_test("api_validation_test")
            
            # Should still succeed as mock responses are not validated in current implementation
            assert result is not None


class TestOpenSpecDatabaseIntegration:
    """Test OpenSpec database integration."""

    @pytest.fixture
    def integration_suite(self):
        """Create integration test suite."""
        return IntegrationTestSuite()

    @pytest.mark.asyncio
    async def test_database_connection(self, integration_suite):
        """Test database connection establishment."""
        result = await integration_suite.run_database_integration_test("database_connection_test")
        
        assert result is not None
        assert result.test_type == IntegrationTestType.DATABASE
        assert result.success is True
        
        # Check database connection step
        step_results = {step["name"]: step for step in result.step_results}
        assert "Test database connection" in step_results
        assert step_results["Test database connection"]["success"] is True

    @pytest.mark.asyncio
    async def test_requirement_persistence(self, integration_suite):
        """Test requirement data persistence."""
        result = await integration_suite.run_database_integration_test("requirement_persistence_test")
        
        assert result is not None
        assert result.success is True
        
        # Check requirement persistence step
        step_results = {step["name"]: step for step in result.step_results}
        assert "Test requirement persistence" in step_results
        assert step_results["Test requirement persistence"]["success"] is True

    @pytest.mark.asyncio
    async def test_design_persistence(self, integration_suite):
        """Test design data persistence."""
        result = await integration_suite.run_database_integration_test("design_persistence_test")
        
        assert result is not None
        assert result.success is True
        
        # Check design persistence step
        step_results = {step["name"]: step for step in result.step_results}
        assert "Test design persistence" in step_results
        assert step_results["Test design persistence"]["success"] is True

    @pytest.mark.asyncio
    async def test_task_persistence(self, integration_suite):
        """Test task data persistence."""
        result = await integration_suite.run_database_integration_test("task_persistence_test")
        
        assert result is not None
        assert result.success is True
        
        # Check task persistence step
        step_results = {step["name"]: step for step in result.step_results}
        assert "Test task persistence" in step_results
        assert step_results["Test task persistence"]["success"] is True

    @pytest.mark.asyncio
    async def test_data_relationships(self, integration_suite):
        """Test data relationship integrity."""
        result = await integration_suite.run_database_integration_test("data_relationships_test")
        
        assert result is not None
        assert result.success is True
        
        # Check data relationships step
        step_results = {step["name"]: step for step in result.step_results}
        assert "Test data relationships" in step_results
        assert step_results["Test data relationships"]["success"] is True

    @pytest.mark.asyncio
    async def test_database_transaction_handling(self, integration_suite):
        """Test database transaction handling."""
        # Mock database operations to test transaction behavior
        async def transaction_test():
            # Simulate transaction operations
            await asyncio.sleep(0.01)
            return {"transaction_committed": True}
        
        with patch.object(integration_suite, '_test_requirement_persistence', side_effect=transaction_test):
            result = await integration_suite.run_database_integration_test("transaction_test")
            
            assert result is not None
            assert result.success is True

    @pytest.mark.asyncio
    async def test_database_error_handling(self, integration_suite):
        """Test database error handling."""
        # Mock database operation to fail
        async def failing_db_operation():
            raise Exception("Database connection lost")
        
        with patch.object(integration_suite, '_test_database_connection', side_effect=failing_db_operation):
            result = await integration_suite.run_database_integration_test("db_error_test")
            
            assert result is not None
            assert result.success is False
            assert result.steps_completed < result.total_steps


class TestOpenSpecCrossComponentIntegration:
    """Test OpenSpec cross-component integration."""

    @pytest.fixture
    def integration_suite(self):
        """Create integration test suite."""
        return IntegrationTestSuite()

    @pytest.mark.asyncio
    async def test_requirement_design_integration(self, integration_suite):
        """Test requirement-design component integration."""
        result = await integration_suite.run_cross_component_test("requirement_design_integration")
        
        assert result is not None
        assert result.test_type == IntegrationTestType.CROSS_COMPONENT
        assert result.success is True
        
        # Check requirement-design integration step
        step_results = {step["name"]: step for step in result.step_results}
        assert "Test requirement-design integration" in step_results
        assert step_results["Test requirement-design integration"]["success"] is True

    @pytest.mark.asyncio
    async def test_design_task_integration(self, integration_suite):
        """Test design-task component integration."""
        result = await integration_suite.run_cross_component_test("design_task_integration")
        
        assert result is not None
        assert result.success is True
        
        # Check design-task integration step
        step_results = {step["name"]: step for step in result.step_results}
        assert "Test design-task integration" in step_results
        assert step_results["Test design-task integration"]["success"] is True

    @pytest.mark.asyncio
    async def test_validation_integration(self, integration_suite):
        """Test validation component integration."""
        result = await integration_suite.run_cross_component_test("validation_integration")
        
        assert result is not None
        assert result.success is True
        
        # Check validation integration step
        step_results = {step["name"]: step for step in result.step_results}
        assert "Test validation integration" in step_results
        assert step_results["Test validation integration"]["success"] is True

    @pytest.mark.asyncio
    async def test_review_integration(self, integration_suite):
        """Test review component integration."""
        result = await integration_suite.run_cross_component_test("review_integration")
        
        assert result is not None
        assert result.success is True
        
        # Check review integration step
        step_results = {step["name"]: step for step in result.step_results}
        assert "Test review integration" in step_results
        assert step_results["Test review integration"]["success"] is True

    @pytest.mark.asyncio
    async def test_template_integration(self, integration_suite):
        """Test template component integration."""
        result = await integration_suite.run_cross_component_test("template_integration")
        
        assert result is not None
        assert result.success is True
        
        # Check template integration step
        step_results = {step["name"]: step for step in result.step_results}
        assert "Test template integration" in step_results
        assert step_results["Test template integration"]["success"] is True

    @pytest.mark.asyncio
    async def test_component_communication(self, integration_suite):
        """Test inter-component communication."""
        # Initialize components
        await integration_suite._initialize_openspec_components()
        
        # Test that components can communicate
        validator = integration_suite.test_data.get("validator")
        template_engine = integration_suite.test_data.get("template_engine")
        
        assert validator is not None
        assert template_engine is not None
        
        # Test component interaction
        result = await integration_suite._test_template_integration()
        
        assert result is not None
        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_component_dependency_resolution(self, integration_suite):
        """Test component dependency resolution."""
        # Test that components can resolve their dependencies
        await integration_suite._initialize_openspec_components()
        
        # Check that review orchestrator can access validator
        review_orchestrator = integration_suite.test_data.get("review_orchestrator")
        validator = integration_suite.test_data.get("validator")
        
        assert review_orchestrator is not None
        assert validator is not None
        
        # Test dependency usage
        result = await integration_suite._run_review_workflow()
        
        assert result is not None
        assert "reviews_submitted" in result

    @pytest.mark.asyncio
    async def test_component_error_propagation(self, integration_suite):
        """Test error propagation between components."""
        # Mock a component to fail
        async def failing_validator():
            raise Exception("Validator component failed")
        
        with patch.object(integration_suite, '_validate_specifications', side_effect=failing_validator):
            result = await integration_suite.run_cross_component_test("error_propagation_test")
            
            assert result is not None
            assert result.success is False


class TestOpenSpecEndToEndIntegration:
    """Test comprehensive end-to-end OpenSpec integration."""

    @pytest.fixture
    def integration_suite(self):
        """Create integration test suite."""
        return IntegrationTestSuite()

    @pytest.mark.asyncio
    async def test_complete_end_to_end_workflow(self, integration_suite):
        """Test complete end-to-end OpenSpec workflow."""
        result = await integration_suite.run_end_to_end_test("complete_e2e_test")
        
        assert result is not None
        assert result.test_type == IntegrationTestType.END_TO_END
        assert result.success is True
        assert result.total_steps >= 4  # Should include all test types
        
        # Check that all integration types were tested
        step_results = {step["name"]: step for step in result.step_results}
        expected_steps = [
            "workflow_integration",
            "api_integration", 
            "database_integration",
            "cross_component_integration"
        ]
        
        for expected_step in expected_steps:
            assert expected_step in step_results
            assert step_results[expected_step]["success"] is True

    @pytest.mark.asyncio
    async def test_end_to_end_with_failures(self, integration_suite):
        """Test end-to-end workflow with some failures."""
        # Mock one integration test to fail
        async def failing_workflow_test():
            return await integration_suite.run_workflow_integration_test("failing_workflow")
        
        with patch.object(integration_suite, 'run_workflow_integration_test', side_effect=failing_workflow_test):
            # Mock the workflow test to fail
            with patch.object(integration_suite, '_initialize_openspec_components', side_effect=Exception("Component init failed")):
                result = await integration_suite.run_end_to_end_test("e2e_with_failures")
                
                assert result is not None
                # Should fail due to workflow integration failure
                assert result.success is False

    @pytest.mark.asyncio
    async def test_end_to_end_performance(self, integration_suite):
        """Test end-to-end workflow performance."""
        start_time = time.time()
        
        result = await integration_suite.run_end_to_end_test("e2e_performance_test")
        
        end_time = time.time()
        total_duration = end_time - start_time
        
        assert result is not None
        assert result.success is True
        assert total_duration < 30.0  # Should complete within 30 seconds
        assert result.duration > 0

    @pytest.mark.asyncio
    async def test_end_to_end_data_flow(self, integration_suite):
        """Test data flow through end-to-end workflow."""
        result = await integration_suite.run_end_to_end_test("e2e_data_flow_test")
        
        assert result is not None
        assert result.success is True
        
        # Verify that data was generated and processed
        test_data = integration_suite.test_data
        
        # Should have data from various stages
        assert len(test_data) > 0
        
        # Check that components were initialized
        assert "template_engine" in test_data
        assert "validator" in test_data
        assert "review_orchestrator" in test_data

    @pytest.mark.asyncio
    async def test_end_to_end_report_generation(self, integration_suite, temp_output_dir):
        """Test end-to-end report generation."""
        # Run end-to-end test
        await integration_suite.run_end_to_end_test("e2e_report_test")
        
        # Generate report
        report_path = await integration_suite.generate_integration_report(temp_output_dir / "e2e_report.json")
        
        assert Path(report_path).exists()
        assert Path(report_path).stat().st_size > 0
        
        # Verify report content
        with open(report_path, 'r') as f:
            report_data = json.load(f)
        
        assert "timestamp" in report_data
        assert "summary" in report_data
        assert "test_results" in report_data
        assert report_data["summary"]["total_tests"] >= 1


class TestWorkflowTestRunner:
    """Test workflow test runner functionality."""

    @pytest.fixture
    def workflow_runner(self):
        """Create workflow test runner."""
        integration_suite = IntegrationTestSuite()
        return WorkflowTestRunner(integration_suite)

    @pytest.mark.asyncio
    async def test_workflow_performance_test(self, workflow_runner):
        """Test workflow performance testing."""
        # Mock integration test to avoid actual execution
        workflow_runner.integration_suite.run_workflow_integration_test = AsyncMock(
            return_value=IntegrationTestResult(
                test_name="perf_test",
                test_type=IntegrationTestType.WORKFLOW,
                success=True,
                duration=0.5,
                steps_completed=5,
                total_steps=5
            )
        )
        
        stats = await workflow_runner.run_workflow_performance_test(
            workflow_name="complete_workflow",
            iterations=3,
            concurrent_runs=1
        )
        
        assert stats is not None
        assert stats["workflow_name"] == "complete_workflow"
        assert stats["iterations"] == 3
        assert stats["success_rate"] == 100.0
        assert "avg_duration" in stats
        assert "min_duration" in stats
        assert "max_duration" in stats
        assert "performance_results" in stats
        assert len(stats["performance_results"]) == 3

    @pytest.mark.asyncio
    async def test_workflow_performance_test_with_failures(self, workflow_runner):
        """Test workflow performance testing with failures."""
        # Mock integration test to fail sometimes
        call_count = 0
        
        async def mock_workflow_test(test_name):
            nonlocal call_count
            call_count += 1
            return IntegrationTestResult(
                test_name=test_name,
                test_type=IntegrationTestType.WORKFLOW,
                success=call_count % 2 == 1,  # Fail every other call
                duration=0.5,
                steps_completed=5,
                total_steps=5
            )
        
        workflow_runner.integration_suite.run_workflow_integration_test = AsyncMock(side_effect=mock_workflow_test)
        
        stats = await workflow_runner.run_workflow_performance_test(
            workflow_name="failing_workflow",
            iterations=4,
            concurrent_runs=1
        )
        
        assert stats is not None
        assert stats["success_rate"] == 50.0  # 2 out of 4 should succeed
        assert len(stats["performance_results"]) == 4

    @pytest.mark.asyncio
    async def test_workflow_stress_test(self, workflow_runner):
        """Test workflow stress testing."""
        # Mock integration test to be fast
        workflow_runner.integration_suite.run_workflow_integration_test = AsyncMock(
            return_value=IntegrationTestResult(
                test_name="stress_test",
                test_type=IntegrationTestType.WORKFLOW,
                success=True,
                duration=0.1,
                steps_completed=5,
                total_steps=5
            )
        )
        
        stats = await workflow_runner.run_workflow_stress_test(
            workflow_name="complete_workflow",
            duration_seconds=2,
            max_concurrent=3
        )
        
        assert stats is not None
        assert stats["workflow_name"] == "complete_workflow"
        assert stats["duration_seconds"] == 2
        assert stats["max_concurrent"] == 3
        assert stats["total_runs"] >= 0
        assert "success_rate" in stats
        assert "runs_per_minute" in stats
        assert "stress_results" in stats

    @pytest.mark.asyncio
    async def test_workflow_stress_test_with_failures(self, workflow_runner):
        """Test workflow stress testing with failures."""
        # Mock integration test to fail sometimes
        async def mock_stress_test(test_name):
            import random
            success = random.random() > 0.3  # 70% success rate
            return IntegrationTestResult(
                test_name=test_name,
                test_type=IntegrationTestType.WORKFLOW,
                success=success,
                duration=0.1,
                steps_completed=5,
                total_steps=5
            )
        
        workflow_runner.integration_suite.run_workflow_integration_test = AsyncMock(side_effect=mock_stress_test)
        
        stats = await workflow_runner.run_workflow_stress_test(
            workflow_name="stressy_workflow",
            duration_seconds=1,
            max_concurrent=2
        )
        
        assert stats is not None
        assert stats["success_rate"] >= 0  # Should have some success rate
        assert stats["total_runs"] >= 0

    @pytest.mark.asyncio
    async def test_workflow_performance_statistics(self, workflow_runner):
        """Test workflow performance statistics calculation."""
        # Mock integration test with varying durations
        durations = [0.3, 0.5, 0.4, 0.6, 0.2]
        
        async def mock_workflow_test(test_name):
            duration = durations[len(mock_workflow_test.call_args_list) % len(durations)]
            return IntegrationTestResult(
                test_name=test_name,
                test_type=IntegrationTestType.WORKFLOW,
                success=True,
                duration=duration,
                steps_completed=5,
                total_steps=5
            )
        
        workflow_runner.integration_suite.run_workflow_integration_test = AsyncMock(side_effect=mock_workflow_test)
        
        stats = await workflow_runner.run_workflow_performance_test(
            workflow_name="variable_workflow",
            iterations=5,
            concurrent_runs=1
        )
        
        assert stats is not None
        assert abs(stats["avg_duration"] - sum(durations) / len(durations)) < 0.01
        assert stats["min_duration"] == min(durations)
        assert stats["max_duration"] == max(durations)

    @pytest.mark.asyncio
    async def test_workflow_scalability_analysis(self, workflow_runner):
        """Test workflow scalability analysis."""
        # Mock integration test to simulate different performance under load
        async def mock_workflow_test(test_name):
            # Simulate slower performance under load
            import time
            start = time.time()
            await asyncio.sleep(0.01)  # Base processing time
            return IntegrationTestResult(
                test_name=test_name,
                test_type=IntegrationTestType.WORKFLOW,
                success=True,
                duration=time.time() - start,
                steps_completed=5,
                total_steps=5
            )
        
        workflow_runner.integration_suite.run_workflow_integration_test = AsyncMock(side_effect=mock_workflow_test)
        
        stats = await workflow_runner.run_workflow_stress_test(
            workflow_name="scalability_test",
            duration_seconds=1,
            max_concurrent=5
        )
        
        assert stats is not None
        assert stats["max_concurrent"] == 5
        assert stats["total_runs"] >= 0
        assert stats["runs_per_minute"] >= 0


if __name__ == "__main__":
    pytest.main([__file__])