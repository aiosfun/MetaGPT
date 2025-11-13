"""
Unit tests for OpenSpec Enhanced Testing Framework

Tests individual components of the enhanced testing framework including
test framework, fixtures, performance testing, and integration testing.
"""

import pytest
import asyncio
import time
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
import tempfile
import shutil

from metagpt.logs import logger

# Import the enhanced testing framework components
from tests.openspec.test_framework import (
    OpenSpecTestFramework, TestRunner, TestReporter,
    TestType, TestStatus, TestResult, TestSuiteResult
)
from tests.openspec.fixtures import (
    OpenSpecTestFixture, TestDataGenerator, MockDataFactory,
    TestConfiguration
)
from tests.openspec.performance import (
    PerformanceBenchmark, LoadTester, PerformanceMetric,
    BenchmarkResult, LoadTestResult
)
from tests.openspec.integration import (
    IntegrationTestSuite, WorkflowTestRunner, IntegrationTestType,
    IntegrationTestStep, IntegrationTestResult
)


class TestOpenSpecTestFramework:
    """Test the main test framework functionality."""

    @pytest.fixture
    def temp_output_dir(self):
        """Create a temporary output directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def test_framework(self, temp_output_dir):
        """Create a test framework instance for testing."""
        config = {
            "output_dir": str(temp_output_dir),
            "parallel_workers": 2
        }
        return OpenSpecTestFramework(config)

    def test_framework_initialization(self, test_framework):
        """Test test framework initialization."""
        assert test_framework is not None
        assert test_framework.parallel_workers == 2
        assert test_framework.output_dir.exists()
        assert len(test_framework.test_results) == len(TestType)
        assert test_framework.coverage is not None

    def test_test_result_creation(self):
        """Test test result data structure."""
        result = TestResult(
            test_id="test_001",
            test_name="Test Case 1",
            test_type=TestType.UNIT,
            status=TestStatus.PASSED,
            duration=0.123,
            message="Test passed successfully"
        )

        assert result.test_id == "test_001"
        assert result.test_name == "Test Case 1"
        assert result.test_type == TestType.UNIT
        assert result.status == TestStatus.PASSED
        assert result.duration == 0.123
        assert result.message == "Test passed successfully"
        assert isinstance(result.timestamp, datetime)

    def test_test_suite_result_add_result(self, test_framework):
        """Test adding results to test suite."""
        suite_result = test_framework.test_results[TestType.UNIT]
        
        # Add a passed test
        passed_result = TestResult(
            test_id="test_001",
            test_name="Passed Test",
            test_type=TestType.UNIT,
            status=TestStatus.PASSED,
            duration=0.1
        )
        suite_result.add_result(passed_result)
        
        # Add a failed test
        failed_result = TestResult(
            test_id="test_002",
            test_name="Failed Test",
            test_type=TestType.UNIT,
            status=TestStatus.FAILED,
            duration=0.2,
            message="Test failed"
        )
        suite_result.add_result(failed_result)
        
        # Verify suite results
        assert suite_result.total_tests == 2
        assert suite_result.passed_tests == 1
        assert suite_result.failed_tests == 1
        assert suite_result.total_duration == 0.3
        assert len(suite_result.results) == 2

    @pytest.mark.asyncio
    async def test_run_unit_tests_mock(self, test_framework):
        """Test running unit tests with mocked pytest."""
        with patch('pytest.main') as mock_pytest:
            mock_pytest.return_value = 0  # Success exit code
            
            with patch.object(test_framework.coverage, 'report', return_value=85.0):
                result = await test_framework.run_unit_tests()
            
            assert result.test_type == TestType.UNIT
            assert result.total_tests >= 1
            assert result.coverage_percentage == 85.0
            mock_pytest.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_integration_tests_mock(self, test_framework):
        """Test running integration tests with mocked pytest."""
        with patch('pytest.main') as mock_pytest:
            mock_pytest.return_value = 0  # Success exit code
            
            result = await test_framework.run_integration_tests()
            
            assert result.test_type == TestType.INTEGRATION
            assert result.total_tests >= 1
            mock_pytest.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_performance_tests_mock(self, test_framework):
        """Test running performance tests with mocked benchmark."""
        with patch('tests.openspec.performance.PerformanceBenchmark') as mock_benchmark_class:
            mock_benchmark = AsyncMock()
            mock_benchmark_class.return_value = mock_benchmark
            
            # Mock benchmark results
            mock_results = {
                "test_benchmark": BenchmarkResult(
                    benchmark_name="test_benchmark",
                    success=True,
                    duration=0.5,
                    metrics=[PerformanceMetric("test_metric", 100, "ms")]
                )
            }
            mock_benchmark.run_all_benchmarks.return_value = mock_results
            
            result = await test_framework.run_performance_tests()
            
            assert result.test_type == TestType.PERFORMANCE
            assert result.total_tests >= 1
            mock_benchmark.run_all_benchmarks.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_combined_report(self, test_framework):
        """Test generating combined test report."""
        # Add some test results
        suite_result = test_framework.test_results[TestType.UNIT]
        suite_result.add_result(TestResult(
            test_id="test_001",
            test_name="Test 1",
            test_type=TestType.UNIT,
            status=TestStatus.PASSED,
            duration=0.1
        ))
        
        report_path = await test_framework.generate_combined_report()
        
        assert Path(report_path).exists()
        assert (test_framework.output_dir / "test_report.json").exists()
        assert (test_framework.output_dir / "junit_report.xml").exists()

    def test_generate_summary(self, test_framework):
        """Test generating test summary statistics."""
        # Add test results to different suites
        for test_type in TestType:
            suite_result = test_framework.test_results[test_type]
            suite_result.add_result(TestResult(
                test_id=f"{test_type.value}_test",
                test_name=f"{test_type.value} Test",
                test_type=test_type,
                status=TestStatus.PASSED,
                duration=0.1
            ))
        
        summary = test_framework._generate_summary()
        
        assert summary["total_tests"] == len(TestType)
        assert summary["passed"] == len(TestType)
        assert summary["failed"] == 0
        assert summary["success_rate"] == 100.0


class TestTestFixture:
    """Test the test fixtures functionality."""

    @pytest.fixture
    def test_fixture(self):
        """Create a test fixture instance."""
        return OpenSpecTestFixture()

    def test_fixture_initialization(self, test_fixture):
        """Test fixture initialization."""
        assert test_fixture is not None
        assert len(test_fixture.sample_requirements) > 0
        assert len(test_fixture.sample_designs) > 0
        assert len(test_fixture.sample_tasks) > 0
        assert len(test_fixture.test_configurations) > 0

    def test_get_requirement_fixture(self, test_fixture):
        """Test getting requirement fixtures."""
        # Get default requirement
        req = test_fixture.get_requirement_fixture()
        assert req is not None
        assert hasattr(req, 'id')
        assert hasattr(req, 'title')
        
        # Get specific requirement
        specific_req = test_fixture.get_requirement_fixture("REQ-001")
        assert specific_req is not None
        assert specific_req.id == "REQ-001"

    def test_get_design_fixture(self, test_fixture):
        """Test getting design fixtures."""
        # Get default design
        design = test_fixture.get_design_fixture()
        assert design is not None
        assert "name" in design
        assert "components" in design
        
        # Get specific design
        specific_design = test_fixture.get_design_fixture("Authentication Service")
        assert specific_design is not None
        assert specific_design["name"] == "Authentication Service"

    def test_get_task_fixture(self, test_fixture):
        """Test getting task fixtures."""
        # Get default task
        task = test_fixture.get_task_fixture()
        assert task is not None
        assert hasattr(task, 'id')
        assert hasattr(task, 'title')
        
        # Get specific task
        specific_task = test_fixture.get_task_fixture("TASK-001")
        assert specific_task is not None
        assert specific_task.id == "TASK-001"

    def test_get_test_configuration(self, test_fixture):
        """Test getting test configurations."""
        # Get default configuration
        config = test_fixture.get_test_configuration()
        assert config is not None
        assert hasattr(config, 'test_name')
        assert hasattr(config, 'test_type')
        
        # Get specific configuration
        specific_config = test_fixture.get_test_configuration("requirement_validation")
        assert specific_config is not None
        assert specific_config.test_name == "requirement_validation"


class TestDataGenerator:
    """Test the test data generator functionality."""

    @pytest.fixture
    def data_generator(self):
        """Create a data generator instance."""
        return TestDataGenerator(seed=42)  # Fixed seed for reproducible tests

    def test_generator_initialization(self, data_generator):
        """Test data generator initialization."""
        assert data_generator is not None
        assert data_generator.random is not None

    def test_generate_requirement(self, data_generator):
        """Test requirement generation."""
        req = data_generator.generate_requirement()
        
        assert req is not None
        assert req.id.startswith("REQ-")
        assert req.title is not None
        assert req.priority in ["low", "medium", "high", "critical"]
        assert len(req.scenarios) >= 1
        assert len(req.acceptance_criteria) >= 2

    def test_generate_requirement_with_params(self, data_generator):
        """Test requirement generation with parameters."""
        req = data_generator.generate_requirement(
            requirement_id="CUSTOM-001",
            title="Custom Requirement",
            priority="high",
            scenario_count=3
        )
        
        assert req.id == "CUSTOM-001"
        assert req.title == "Custom Requirement"
        assert req.priority == "high"
        assert len(req.scenarios) == 3

    def test_generate_design_component(self, data_generator):
        """Test design component generation."""
        component = data_generator.generate_design_component()
        
        assert component is not None
        assert component.name is not None
        assert component.element_type in ["service", "component", "module", "data_store", "interface"]
        assert len(component.interfaces) >= 1
        assert component.technology is not None

    def test_generate_design_component_with_params(self, data_generator):
        """Test design component generation with parameters."""
        component = data_generator.generate_design_component(
            name="Custom Service",
            element_type="service",
            dependency_count=2
        )
        
        assert component.name == "Custom Service"
        assert component.element_type == "service"
        assert len(component.dependencies) == 2

    def test_generate_implementation_task(self, data_generator):
        """Test implementation task generation."""
        task = data_generator.generate_implementation_task()
        
        assert task is not None
        assert task.id.startswith("TASK-")
        assert task.title is not None
        assert task.status.value == "pending"
        assert len(task.requirement_ids) >= 1
        assert len(task.acceptance_criteria) >= 3
        assert len(task.deliverables) >= 2

    def test_generate_implementation_task_with_params(self, data_generator):
        """Test implementation task generation with parameters."""
        task = data_generator.generate_implementation_task(
            task_id="CUSTOM-TASK-001",
            title="Custom Task",
            requirement_count=2
        )
        
        assert task.id == "CUSTOM-TASK-001"
        assert task.title == "Custom Task"
        assert len(task.requirement_ids) == 2

    def test_generate_test_dataset(self, data_generator):
        """Test complete test dataset generation."""
        dataset = data_generator.generate_test_dataset(
            requirement_count=5,
            design_count=3,
            task_count=8
        )
        
        assert "requirements" in dataset
        assert "designs" in dataset
        assert "tasks" in dataset
        assert len(dataset["requirements"]) == 5
        assert len(dataset["designs"]) == 3
        assert len(dataset["tasks"]) == 8


class TestMockDataFactory:
    """Test the mock data factory functionality."""

    def test_create_mock_llm_response(self):
        """Test creating mock LLM response."""
        mock_response = MockDataFactory.create_mock_llm_response("Test response")
        
        assert mock_response is not None
        assert mock_response.content == "Test response"
        assert hasattr(mock_response, 'choices')

    def test_create_mock_database_connection(self):
        """Test creating mock database connection."""
        mock_conn = MockDataFactory.create_mock_database_connection()
        
        assert mock_conn is not None
        assert hasattr(mock_conn, 'execute')
        assert hasattr(mock_conn, 'commit')
        assert hasattr(mock_conn, 'rollback')

    def test_create_mock_file_system(self):
        """Test creating mock file system."""
        mock_fs = MockDataFactory.create_mock_file_system()
        
        assert mock_fs is not None
        assert "/project" in mock_fs
        assert mock_fs["/project"]["type"] == "directory"

    def test_create_mock_git_repository(self):
        """Test creating mock Git repository."""
        mock_repo = MockDataFactory.create_mock_git_repository()
        
        assert mock_repo is not None
        assert hasattr(mock_repo, 'active_branch')
        assert hasattr(mock_repo, 'remotes')


class TestPerformanceBenchmark:
    """Test the performance benchmark functionality."""

    @pytest.fixture
    def temp_output_dir(self):
        """Create a temporary output directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def performance_benchmark(self, temp_output_dir):
        """Create a performance benchmark instance."""
        return PerformanceBenchmark(output_dir=temp_output_dir)

    def test_benchmark_initialization(self, performance_benchmark):
        """Test performance benchmark initialization."""
        assert performance_benchmark is not None
        assert performance_benchmark.output_dir.exists()
        assert len(performance_benchmark.benchmarks) > 0
        assert "requirement_validation" in performance_benchmark.benchmarks

    def test_performance_metric_creation(self):
        """Test performance metric creation."""
        metric = PerformanceMetric(
            name="test_metric",
            value=100.5,
            unit="ms"
        )
        
        assert metric.name == "test_metric"
        assert metric.value == 100.5
        assert metric.unit == "ms"
        assert isinstance(metric.timestamp, datetime)

    def test_benchmark_result_creation(self):
        """Test benchmark result creation."""
        metrics = [
            PerformanceMetric("metric1", 100, "ms"),
            PerformanceMetric("metric2", 50, "count")
        ]
        
        result = BenchmarkResult(
            benchmark_name="test_benchmark",
            success=True,
            duration=1.5,
            metrics=metrics
        )
        
        assert result.benchmark_name == "test_benchmark"
        assert result.success is True
        assert result.duration == 1.5
        assert len(result.metrics) == 2

    @pytest.mark.asyncio
    async def test_run_requirement_validation_benchmark(self, performance_benchmark):
        """Test running requirement validation benchmark."""
        with patch('tests.openspec.performance.OpenSpecValidator') as mock_validator_class:
            mock_validator = AsyncMock()
            mock_validator_class.return_value = mock_validator
            
            # Mock validation result
            mock_validation_result = Mock()
            mock_validation_result.is_valid = True
            mock_validator.validate_requirement.return_value = mock_validation_result
            
            result = await performance_benchmark.benchmark_requirement_validation()
            
            assert result.benchmark_name == "requirement_validation"
            assert result.success is True
            assert result.duration > 0
            assert len(result.metrics) > 0

    @pytest.mark.asyncio
    async def test_run_design_generation_benchmark(self, performance_benchmark):
        """Test running design generation benchmark."""
        result = await performance_benchmark.benchmark_design_generation()
        
        assert result.benchmark_name == "design_generation"
        assert result.success is True
        assert result.duration > 0
        assert len(result.metrics) > 0

    @pytest.mark.asyncio
    async def test_run_task_creation_benchmark(self, performance_benchmark):
        """Test running task creation benchmark."""
        result = await performance_benchmark.benchmark_task_creation()
        
        assert result.benchmark_name == "task_creation"
        assert result.success is True
        assert result.duration > 0
        assert len(result.metrics) > 0

    @pytest.mark.asyncio
    async def test_run_template_rendering_benchmark(self, performance_benchmark):
        """Test running template rendering benchmark."""
        with patch('tests.openspec.performance.OpenSpecTemplateEngine') as mock_engine_class:
            mock_engine = Mock()
            mock_engine_class.return_value = mock_engine
            mock_engine.render_template.return_value = "Rendered content"
            
            result = await performance_benchmark.benchmark_template_rendering()
            
            assert result.benchmark_name == "template_rendering"
            assert result.success is True
            assert result.duration > 0

    @pytest.mark.asyncio
    async def test_run_all_benchmarks(self, performance_benchmark):
        """Test running all benchmarks."""
        # Mock all benchmark methods to avoid actual execution
        for benchmark_name in performance_benchmark.benchmarks:
            method = getattr(performance_benchmark, f"benchmark_{benchmark_name}")
            if asyncio.iscoroutinefunction(method):
                method = AsyncMock(return_value=BenchmarkResult(
                    benchmark_name=benchmark_name,
                    success=True,
                    duration=0.1
                ))
                setattr(performance_benchmark, f"benchmark_{benchmark_name}", method)
        
        results = await performance_benchmark.run_all_benchmarks()
        
        assert len(results) == len(performance_benchmark.benchmarks)
        for benchmark_name, result in results.items():
            assert result.benchmark_name == benchmark_name
            assert result.success is True


class TestLoadTester:
    """Test the load testing functionality."""

    @pytest.fixture
    def temp_output_dir(self):
        """Create a temporary output directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def load_tester(self, temp_output_dir):
        """Create a load tester instance."""
        return LoadTester(output_dir=temp_output_dir)

    def test_load_tester_initialization(self, load_tester):
        """Test load tester initialization."""
        assert load_tester is not None
        assert load_tester.output_dir.exists()
        assert len(load_tester.results) == 0

    def test_load_test_result_creation(self):
        """Test load test result creation."""
        result = LoadTestResult(
            test_name="test_load",
            concurrent_users=10,
            duration=60.0,
            total_requests=1000,
            successful_requests=950,
            failed_requests=50,
            avg_response_time=0.1,
            min_response_time=0.05,
            max_response_time=0.2,
            p95_response_time=0.15,
            p99_response_time=0.18,
            requests_per_second=16.67,
            error_rate=5.0,
            memory_usage_mb=50.0,
            cpu_usage_percent=25.0
        )
        
        assert result.test_name == "test_load"
        assert result.concurrent_users == 10
        assert result.successful_requests == 950
        assert result.error_rate == 5.0

    @pytest.mark.asyncio
    async def test_run_load_test(self, load_tester):
        """Test running a load test."""
        # Mock target function
        async def mock_target_function():
            await asyncio.sleep(0.01)  # Simulate work
        
        result = await load_tester.run_load_test(
            test_name="test_load",
            target_function=mock_target_function,
            concurrent_users=3,
            duration_seconds=2
        )
        
        assert result.test_name == "test_load"
        assert result.concurrent_users == 3
        assert result.duration >= 2.0
        assert result.total_requests > 0
        assert isinstance(result, LoadTestResult)

    @pytest.mark.asyncio
    async def test_run_scalability_test(self, load_tester):
        """Test running a scalability test."""
        # Mock target function
        async def mock_target_function():
            await asyncio.sleep(0.005)  # Simulate work
        
        results = await load_tester.run_scalability_test(
            test_name="test_scalability",
            target_function=mock_target_function,
            user_levels=[1, 2, 3],
            duration_per_level=1
        )
        
        assert len(results) == 3
        for result in results:
            assert result.test_name.startswith("test_scalability_")
            assert result.concurrent_users in [1, 2, 3]


class TestIntegrationTestSuite:
    """Test the integration test suite functionality."""

    @pytest.fixture
    def integration_suite(self):
        """Create an integration test suite instance."""
        return IntegrationTestSuite()

    def test_integration_suite_initialization(self, integration_suite):
        """Test integration suite initialization."""
        assert integration_suite is not None
        assert len(integration_suite.mock_services) > 0
        assert "llm" in integration_suite.mock_services
        assert "database" in integration_suite.mock_services
        assert "filesystem" in integration_suite.mock_services

    def test_integration_test_step_creation(self):
        """Test integration test step creation."""
        async def mock_function():
            return "test_result"
        
        step = IntegrationTestStep(
            name="test_step",
            function=mock_function,
            expected_result="test_result",
            timeout_seconds=10.0
        )
        
        assert step.name == "test_step"
        assert step.function == mock_function
        assert step.expected_result == "test_result"
        assert step.timeout_seconds == 10.0

    def test_integration_test_result_creation(self):
        """Test integration test result creation."""
        result = IntegrationTestResult(
            test_name="test_integration",
            test_type=IntegrationTestType.WORKFLOW,
            success=True,
            duration=5.0,
            steps_completed=3,
            total_steps=5
        )
        
        assert result.test_name == "test_integration"
        assert result.test_type == IntegrationTestType.WORKFLOW
        assert result.success is True
        assert result.steps_completed == 3
        assert result.total_steps == 5

    @pytest.mark.asyncio
    async def test_initialize_openspec_components(self, integration_suite):
        """Test initializing OpenSpec components."""
        result = await integration_suite._initialize_openspec_components()
        
        assert result is not None
        assert "components_initialized" in result
        assert result["components_initialized"] == 3
        assert "template_engine" in integration_suite.test_data
        assert "validator" in integration_suite.test_data
        assert "review_orchestrator" in integration_suite.test_data

    @pytest.mark.asyncio
    async def test_generate_test_requirements(self, integration_suite):
        """Test generating test requirements."""
        result = await integration_suite._generate_test_requirements()
        
        assert result is not None
        assert "requirements_generated" in result
        assert result["requirements_generated"] > 0
        assert "requirements" in integration_suite.test_data

    @pytest.mark.asyncio
    async def test_create_design_specifications(self, integration_suite):
        """Test creating design specifications."""
        result = await integration_suite._create_design_specifications()
        
        assert result is not None
        assert "designs_created" in result
        assert result["designs_created"] > 0
        assert "designs" in integration_suite.test_data

    @pytest.mark.asyncio
    async def test_generate_implementation_tasks(self, integration_suite):
        """Test generating implementation tasks."""
        result = await integration_suite._generate_implementation_tasks()
        
        assert result is not None
        assert "tasks_generated" in result
        assert result["tasks_generated"] > 0
        assert "tasks" in integration_suite.test_data

    @pytest.mark.asyncio
    async def test_run_workflow_integration_test(self, integration_suite):
        """Test running workflow integration test."""
        result = await integration_suite.run_workflow_integration_test()
        
        assert result is not None
        assert result.test_type == IntegrationTestType.WORKFLOW
        assert result.total_steps > 0
        assert isinstance(result, IntegrationTestResult)

    @pytest.mark.asyncio
    async def test_run_api_integration_test(self, integration_suite):
        """Test running API integration test."""
        result = await integration_suite.run_api_integration_test()
        
        assert result is not None
        assert result.test_type == IntegrationTestType.API
        assert result.total_steps > 0
        assert isinstance(result, IntegrationTestResult)

    @pytest.mark.asyncio
    async def test_run_database_integration_test(self, integration_suite):
        """Test running database integration test."""
        result = await integration_suite.run_database_integration_test()
        
        assert result is not None
        assert result.test_type == IntegrationTestType.DATABASE
        assert result.total_steps > 0
        assert isinstance(result, IntegrationTestResult)

    @pytest.mark.asyncio
    async def test_run_cross_component_test(self, integration_suite):
        """Test running cross-component test."""
        result = await integration_suite.run_cross_component_test()
        
        assert result is not None
        assert result.test_type == IntegrationTestType.CROSS_COMPONENT
        assert result.total_steps > 0
        assert isinstance(result, IntegrationTestResult)

    @pytest.mark.asyncio
    async def test_generate_integration_report(self, integration_suite, temp_output_dir):
        """Test generating integration test report."""
        # Add a test result
        result = IntegrationTestResult(
            test_name="test_report",
            test_type=IntegrationTestType.WORKFLOW,
            success=True,
            duration=1.0,
            steps_completed=1,
            total_steps=1
        )
        integration_suite.test_results.append(result)
        
        report_path = await integration_suite.generate_integration_report(temp_output_dir / "integration_report.json")
        
        assert Path(report_path).exists()
        assert Path(report_path).stat().st_size > 0


class TestWorkflowTestRunner:
    """Test the workflow test runner functionality."""

    @pytest.fixture
    def workflow_runner(self):
        """Create a workflow test runner instance."""
        integration_suite = IntegrationTestSuite()
        return WorkflowTestRunner(integration_suite)

    def test_workflow_runner_initialization(self, workflow_runner):
        """Test workflow test runner initialization."""
        assert workflow_runner is not None
        assert workflow_runner.integration_suite is not None

    @pytest.mark.asyncio
    async def test_run_workflow_performance_test(self, workflow_runner):
        """Test running workflow performance test."""
        # Mock the integration test to avoid actual execution
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
        
        assert stats["workflow_name"] == "complete_workflow"
        assert stats["iterations"] == 3
        assert stats["success_rate"] == 100.0
        assert "avg_duration" in stats
        assert "performance_results" in stats

    @pytest.mark.asyncio
    async def test_run_workflow_stress_test(self, workflow_runner):
        """Test running workflow stress test."""
        # Mock the integration test to avoid actual execution
        workflow_runner.integration_suite.run_workflow_integration_test = AsyncMock(
            return_value=IntegrationTestResult(
                test_name="stress_test",
                test_type=IntegrationTestType.WORKFLOW,
                success=True,
                duration=0.3,
                steps_completed=5,
                total_steps=5
            )
        )
        
        stats = await workflow_runner.run_workflow_stress_test(
            workflow_name="complete_workflow",
            duration_seconds=2,
            max_concurrent=2
        )
        
        assert stats["workflow_name"] == "complete_workflow"
        assert stats["duration_seconds"] == 2
        assert stats["max_concurrent"] == 2
        assert "total_runs" in stats
        assert "success_rate" in stats


if __name__ == "__main__":
    pytest.main([__file__])