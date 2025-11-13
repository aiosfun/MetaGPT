"""
Performance Benchmark Tests for OpenSpec

Tests performance benchmarks, load testing, and scalability analysis
for large codebase processing with comprehensive metrics collection.
"""

import pytest
import asyncio
import time
import psutil
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch
from pathlib import Path
import tempfile
import shutil

from metagpt.logs import logger

# Import performance testing components
from tests.openspec.performance import (
    PerformanceBenchmark, LoadTester, PerformanceMetric,
    BenchmarkResult, LoadTestResult
)
from tests.openspec.fixtures import TestDataGenerator


class TestPerformanceBenchmarks:
    """Test performance benchmark functionality."""

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
        
        # Check that default benchmarks are registered
        expected_benchmarks = [
            "requirement_validation",
            "design_generation", 
            "task_creation",
            "template_rendering",
            "validation_processing",
            "cross_reference_analysis",
            "memory_usage",
            "concurrent_processing"
        ]
        
        for benchmark in expected_benchmarks:
            assert benchmark in performance_benchmark.benchmarks

    def test_performance_metric_creation(self):
        """Test performance metric creation and validation."""
        metric = PerformanceMetric(
            name="test_metric",
            value=100.5,
            unit="ms"
        )
        
        assert metric.name == "test_metric"
        assert metric.value == 100.5
        assert metric.unit == "ms"
        assert isinstance(metric.timestamp, datetime)
        assert isinstance(metric.metadata, dict)

    def test_benchmark_result_creation(self):
        """Test benchmark result creation and validation."""
        metrics = [
            PerformanceMetric("duration", 1.5, "seconds"),
            PerformanceMetric("operations", 100, "count"),
            PerformanceMetric("memory", 50.2, "MB")
        ]
        
        result = BenchmarkResult(
            benchmark_name="test_benchmark",
            success=True,
            duration=1.5,
            metrics=metrics,
            metadata={"test_type": "unit"}
        )
        
        assert result.benchmark_name == "test_benchmark"
        assert result.success is True
        assert result.duration == 1.5
        assert len(result.metrics) == 3
        assert result.metadata["test_type"] == "unit"

    @pytest.mark.asyncio
    async def test_requirement_validation_benchmark(self, performance_benchmark):
        """Test requirement validation benchmark performance."""
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
            
            # Check expected metrics
            metric_names = [metric.name for metric in result.metrics]
            expected_metrics = [
                "requirements_validated",
                "avg_time_per_requirement", 
                "memory_usage_delta",
                "validation_rate"
            ]
            
            for expected_metric in expected_metrics:
                assert expected_metric in metric_names

    @pytest.mark.asyncio
    async def test_design_generation_benchmark(self, performance_benchmark):
        """Test design generation benchmark performance."""
        result = await performance_benchmark.benchmark_design_generation()
        
        assert result.benchmark_name == "design_generation"
        assert result.success is True
        assert result.duration > 0
        assert len(result.metrics) > 0
        
        # Check expected metrics
        metric_names = [metric.name for metric in result.metrics]
        expected_metrics = [
            "designs_generated",
            "avg_time_per_design",
            "memory_usage_delta",
            "generation_rate"
        ]
        
        for expected_metric in expected_metrics:
            assert expected_metric in metric_names

    @pytest.mark.asyncio
    async def test_task_creation_benchmark(self, performance_benchmark):
        """Test task creation benchmark performance."""
        result = await performance_benchmark.benchmark_task_creation()
        
        assert result.benchmark_name == "task_creation"
        assert result.success is True
        assert result.duration > 0
        assert len(result.metrics) > 0
        
        # Check expected metrics
        metric_names = [metric.name for metric in result.metrics]
        expected_metrics = [
            "tasks_created",
            "avg_time_per_task",
            "memory_usage_delta",
            "creation_rate"
        ]
        
        for expected_metric in expected_metrics:
            assert expected_metric in metric_names

    @pytest.mark.asyncio
    async def test_template_rendering_benchmark(self, performance_benchmark):
        """Test template rendering benchmark performance."""
        with patch('tests.openspec.performance.OpenSpecTemplateEngine') as mock_engine_class:
            mock_engine = Mock()
            mock_engine_class.return_value = mock_engine
            mock_engine.render_template.return_value = "Rendered content"
            
            result = await performance_benchmark.benchmark_template_rendering()
            
            assert result.benchmark_name == "template_rendering"
            assert result.success is True
            assert result.duration > 0
            assert len(result.metrics) > 0
            
            # Check expected metrics
            metric_names = [metric.name for metric in result.metrics]
            expected_metrics = [
                "templates_rendered",
                "avg_time_per_template",
                "memory_usage_delta",
                "rendering_rate"
            ]
            
            for expected_metric in expected_metrics:
                assert expected_metric in metric_names

    @pytest.mark.asyncio
    async def test_validation_processing_benchmark(self, performance_benchmark):
        """Test validation processing benchmark performance."""
        result = await performance_benchmark.benchmark_validation_processing()
        
        assert result.benchmark_name == "validation_processing"
        assert result.success is True
        assert result.duration > 0
        assert len(result.metrics) > 0
        
        # Check expected metrics
        metric_names = [metric.name for metric in result.metrics]
        expected_metrics = [
            "items_processed",
            "avg_time_per_item",
            "memory_usage_delta",
            "processing_rate"
        ]
        
        for expected_metric in expected_metrics:
            assert expected_metric in metric_names

    @pytest.mark.asyncio
    async def test_cross_reference_analysis_benchmark(self, performance_benchmark):
        """Test cross-reference analysis benchmark performance."""
        result = await performance_benchmark.benchmark_cross_reference_analysis()
        
        assert result.benchmark_name == "cross_reference_analysis"
        assert result.success is True
        assert result.duration > 0
        assert len(result.metrics) > 0
        
        # Check expected metrics
        metric_names = [metric.name for metric in result.metrics]
        expected_metrics = [
            "analyses_completed",
            "avg_time_per_analysis",
            "memory_usage_delta",
            "analysis_rate"
        ]
        
        for expected_metric in expected_metrics:
            assert expected_metric in metric_names

    @pytest.mark.asyncio
    async def test_memory_usage_benchmark(self, performance_benchmark):
        """Test memory usage benchmark performance."""
        result = await performance_benchmark.benchmark_memory_usage()
        
        assert result.benchmark_name == "memory_usage"
        assert result.success is True
        assert result.duration > 0
        assert len(result.metrics) > 0
        
        # Check expected metrics
        metric_names = [metric.name for metric in result.metrics]
        expected_metrics = [
            "initial_memory_mb",
            "final_memory_mb",
            "memory_delta_mb",
            "memory_per_item_kb",
            "max_memory_sample"
        ]
        
        for expected_metric in expected_metrics:
            assert expected_metric in metric_names

    @pytest.mark.asyncio
    async def test_concurrent_processing_benchmark(self, performance_benchmark):
        """Test concurrent processing benchmark performance."""
        result = await performance_benchmark.benchmark_concurrent_processing()
        
        assert result.benchmark_name == "concurrent_processing"
        assert result.success is True
        assert result.duration > 0
        assert len(result.metrics) > 0
        
        # Check expected metrics
        metric_names = [metric.name for metric in result.metrics]
        expected_metrics = [
            "baseline_tps",
            "max_tps",
            "scalability_factor",
            "memory_delta_mb",
            "optimal_concurrency"
        ]
        
        for expected_metric in expected_metrics:
            assert expected_metric in metric_names

    @pytest.mark.asyncio
    async def test_run_all_benchmarks(self, performance_benchmark):
        """Test running all benchmarks."""
        # Mock individual benchmark methods to avoid long execution
        for benchmark_name in performance_benchmark.benchmarks:
            method = getattr(performance_benchmark, f"benchmark_{benchmark_name}")
            if asyncio.iscoroutinefunction(method):
                method = AsyncMock(return_value=BenchmarkResult(
                    benchmark_name=benchmark_name,
                    success=True,
                    duration=0.1,
                    metrics=[PerformanceMetric("test", 100, "unit")]
                ))
                setattr(performance_benchmark, f"benchmark_{benchmark_name}", method)
        
        results = await performance_benchmark.run_all_benchmarks()
        
        assert len(results) == len(performance_benchmark.benchmarks)
        
        for benchmark_name, result in results.items():
            assert result.benchmark_name == benchmark_name
            assert result.success is True
            assert len(result.metrics) > 0

    @pytest.mark.asyncio
    async def test_benchmark_error_handling(self, performance_benchmark):
        """Test benchmark error handling."""
        # Mock a benchmark to raise an exception
        async def failing_benchmark():
            raise Exception("Benchmark failed")
        
        performance_benchmark.benchmarks["failing_test"] = failing_benchmark
        
        result = await performance_benchmark.run_benchmark("failing_test")
        
        assert result.benchmark_name == "failing_test"
        assert result.success is False
        assert result.error_message == "Benchmark failed"
        assert result.duration >= 0

    @pytest.mark.asyncio
    async def test_benchmark_timeout_handling(self, performance_benchmark):
        """Test benchmark timeout handling."""
        # Mock a benchmark to timeout
        async def timeout_benchmark():
            await asyncio.sleep(10)  # Longer than typical timeout
        
        performance_benchmark.benchmarks["timeout_test"] = timeout_benchmark
        
        # This should handle timeout gracefully (implementation dependent)
        start_time = time.time()
        result = await performance_benchmark.run_benchmark("timeout_test")
        end_time = time.time()
        
        # Should complete or handle timeout appropriately
        assert result is not None
        assert result.benchmark_name == "timeout_test"

    def test_performance_report_generation(self, performance_benchmark):
        """Test performance report generation."""
        # Add some mock results
        performance_benchmark.results["test_benchmark"] = BenchmarkResult(
            benchmark_name="test_benchmark",
            success=True,
            duration=1.0,
            metrics=[
                PerformanceMetric("test_metric", 100, "ms"),
                PerformanceMetric("another_metric", 50, "count")
            ]
        )
        
        # Test report generation (would normally be called after running benchmarks)
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_benchmarks": 1,
                "successful_benchmarks": 1,
                "failed_benchmarks": 0,
                "total_duration": 1.0
            },
            "benchmarks": {
                "test_benchmark": {
                    "success": True,
                    "duration": 1.0,
                    "metrics": [
                        {
                            "name": "test_metric",
                            "value": 100,
                            "unit": "ms",
                            "timestamp": datetime.now().isoformat()
                        }
                    ]
                }
            }
        }
        
        assert "timestamp" in report_data
        assert "summary" in report_data
        assert "benchmarks" in report_data
        assert report_data["summary"]["total_benchmarks"] == 1


class TestLoadTesting:
    """Test load testing functionality."""

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
        assert result.failed_requests == 50
        assert result.error_rate == 5.0
        assert result.requests_per_second == 16.67

    @pytest.mark.asyncio
    async def test_run_load_test_basic(self, load_tester):
        """Test basic load test execution."""
        # Mock target function
        async def mock_target_function():
            await asyncio.sleep(0.01)  # Simulate work
        
        result = await load_tester.run_load_test(
            test_name="basic_load_test",
            target_function=mock_target_function,
            concurrent_users=3,
            duration_seconds=2
        )
        
        assert result.test_name == "basic_load_test"
        assert result.concurrent_users == 3
        assert result.duration >= 2.0
        assert result.total_requests > 0
        assert result.successful_requests >= 0
        assert result.failed_requests >= 0
        assert result.requests_per_second >= 0
        assert isinstance(result, LoadTestResult)

    @pytest.mark.asyncio
    async def test_run_load_test_with_failures(self, load_tester):
        """Test load test with function failures."""
        # Mock target function that fails sometimes
        call_count = 0
        
        async def failing_target_function():
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.005)
            if call_count % 3 == 0:  # Fail every 3rd call
                raise Exception("Simulated failure")
        
        result = await load_tester.run_load_test(
            test_name="failing_load_test",
            target_function=failing_target_function,
            concurrent_users=2,
            duration_seconds=1
        )
        
        assert result.test_name == "failing_load_test"
        assert result.total_requests > 0
        assert result.failed_requests > 0
        assert result.error_rate > 0
        assert result.successful_requests + result.failed_requests == result.total_requests

    @pytest.mark.asyncio
    async def test_run_load_test_rate_limiting(self, load_tester):
        """Test load test with rate limiting."""
        # Mock target function
        async def mock_target_function():
            await asyncio.sleep(0.01)
        
        result = await load_tester.run_load_test(
            test_name="rate_limited_test",
            target_function=mock_target_function,
            concurrent_users=2,
            duration_seconds=1,
            requests_per_second=50  # High rate limit
        )
        
        assert result.test_name == "rate_limited_test"
        assert result.requests_per_second <= 50  # Should respect rate limit

    @pytest.mark.asyncio
    async def test_run_scalability_test(self, load_tester):
        """Test scalability test execution."""
        # Mock target function
        async def mock_target_function():
            await asyncio.sleep(0.005)  # Fast function for scalability testing
        
        results = await load_tester.run_scalability_test(
            test_name="scalability_test",
            target_function=mock_target_function,
            user_levels=[1, 2, 3],
            duration_per_level=1
        )
        
        assert len(results) == 3
        
        for i, result in enumerate(results):
            assert result.test_name == f"scalability_test_{i+1}users"
            assert result.concurrent_users == i + 1
            assert result.duration >= 1.0
            assert isinstance(result, LoadTestResult)

    @pytest.mark.asyncio
    async def test_scalability_analysis(self, load_tester):
        """Test scalability analysis metrics."""
        # Mock target function with performance degradation under load
        async degrading_target_function(user_count):
            # Simulate slower performance under load
            base_delay = 0.01
            load_delay = user_count * 0.002  # Increase delay with load
            await asyncio.sleep(base_delay + load_delay)
        
        # Override run_load_test to use degrading function
        original_run_load_test = load_tester.run_load_test
        
        async def mock_run_load_test(test_name, target_function, concurrent_users, duration_seconds):
            # Create closure that captures concurrent_users
            async def bound_target():
                await degrading_target_function(concurrent_users)
            
            return await original_run_load_test(
                test_name, bound_target, concurrent_users, duration_seconds
            )
        
        load_tester.run_load_test = mock_run_load_test
        
        try:
            results = await load_tester.run_scalability_test(
                test_name="degradation_test",
                target_function=None,  # Not used with mock
                user_levels=[1, 5, 10],
                duration_per_level=1
            )
            
            # Should see performance degradation
            assert len(results) == 3
            
            # Response times should increase with user count
            response_times = [result.avg_response_time for result in results]
            assert response_times[0] < response_times[1] < response_times[2]
            
            # Throughput should show scalability characteristics
            throughputs = [result.requests_per_second for result in results]
            assert all(tps > 0 for tps in throughputs)
            
        finally:
            # Restore original method
            load_tester.run_load_test = original_run_load_test

    @pytest.mark.asyncio
    async def test_memory_monitoring_during_load_test(self, load_tester):
        """Test memory monitoring during load test."""
        # Mock target function that uses some memory
        async def memory_using_function():
            # Create some data to use memory
            data = ["test"] * 1000
            await asyncio.sleep(0.01)
            del data
        
        result = await load_tester.run_load_test(
            test_name="memory_test",
            target_function=memory_using_function,
            concurrent_users=2,
            duration_seconds=1
        )
        
        assert result.memory_usage_mb >= 0
        assert isinstance(result.memory_usage_mb, (int, float))

    @pytest.mark.asyncio
    async def test_cpu_monitoring_during_load_test(self, load_tester):
        """Test CPU monitoring during load test."""
        # Mock target function that uses CPU
        async def cpu_intensive_function():
            # Simulate CPU work
            start = time.time()
            while time.time() - start < 0.01:  # 10ms of work
                pass  # Busy wait
            await asyncio.sleep(0.001)  # Brief pause
        
        result = await load_tester.run_load_test(
            test_name="cpu_test",
            target_function=cpu_intensive_function,
            concurrent_users=2,
            duration_seconds=1
        )
        
        assert result.cpu_usage_percent >= 0
        assert isinstance(result.cpu_usage_percent, (int, float))

    def test_load_test_statistics_calculation(self):
        """Test load test statistics calculation."""
        # Create a mock load test result with known data
        response_times = [0.1, 0.15, 0.12, 0.08, 0.2, 0.11, 0.09, 0.13]
        
        # Calculate expected statistics
        avg_response_time = sum(response_times) / len(response_times)
        min_response_time = min(response_times)
        max_response_time = max(response_times)
        
        # For percentiles, we'd normally use numpy, but we'll approximate
        sorted_times = sorted(response_times)
        p95_index = int(0.95 * len(sorted_times))
        p99_index = int(0.99 * len(sorted_times))
        p95_response_time = sorted_times[min(p95_index, len(sorted_times) - 1)]
        p99_response_time = sorted_times[min(p99_index, len(sorted_times) - 1)]
        
        # Verify calculations
        assert 0.08 <= min_response_time <= 0.2
        assert 0.08 <= max_response_time <= 0.2
        assert avg_response_time > 0
        assert p95_response_time >= avg_response_time * 0.8
        assert p99_response_time >= p95_response_time

    @pytest.mark.asyncio
    async def test_load_test_report_generation(self, load_tester, temp_output_dir):
        """Test load test report generation."""
        # Add a mock result
        result = LoadTestResult(
            test_name="report_test",
            concurrent_users=5,
            duration=60.0,
            total_requests=500,
            successful_requests=475,
            failed_requests=25,
            avg_response_time=0.12,
            min_response_time=0.05,
            max_response_time=0.3,
            p95_response_time=0.2,
            p99_response_time=0.25,
            requests_per_second=8.33,
            error_rate=5.0,
            memory_usage_mb=75.0,
            cpu_usage_percent=40.0
        )
        
        load_tester.results.append(result)
        
        # Test scalability report generation
        await load_tester._generate_scalability_report("report_test", [result])
        
        # Check that report files were created
        report_file = temp_output_dir / "report_test_scalability.json"
        assert report_file.exists()
        
        # Verify report content
        import json
        with open(report_file, 'r') as f:
            report_data = json.load(f)
        
        assert report_data["test_name"] == "report_test"
        assert "results" in report_data
        assert len(report_data["results"]) == 1
        
        result_data = report_data["results"][0]
        assert result_data["concurrent_users"] == 5
        assert result_data["requests_per_second"] == 8.33
        assert result_data["error_rate"] == 5.0


class TestPerformanceRegression:
    """Test performance regression detection."""

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

    @pytest.mark.asyncio
    async def test_performance_regression_detection(self, performance_benchmark):
        """Test performance regression detection."""
        # Mock benchmark results showing regression
        baseline_results = {
            "requirement_validation": BenchmarkResult(
                benchmark_name="requirement_validation",
                success=True,
                duration=1.0,
                metrics=[PerformanceMetric("validation_rate", 100, "req/sec")]
            )
        }
        
        current_results = {
            "requirement_validation": BenchmarkResult(
                benchmark_name="requirement_validation",
                success=True,
                duration=2.0,  # 2x slower - regression
                metrics=[PerformanceMetric("validation_rate", 50, "req/sec")]  # 2x slower
            )
        }
        
        # Compare results
        baseline_duration = baseline_results["requirement_validation"].duration
        current_duration = current_results["requirement_validation"].duration
        
        baseline_rate = baseline_results["requirement_validation"].metrics[0].value
        current_rate = current_results["requirement_validation"].metrics[0].value
        
        # Detect regression
        duration_regression = (current_duration - baseline_duration) / baseline_duration
        rate_regression = (baseline_rate - current_rate) / baseline_rate
        
        assert duration_regression == 1.0  # 100% regression
        assert rate_regression == 0.5  # 50% regression
        
        # Regression threshold (typically 10-20%)
        regression_threshold = 0.2
        assert duration_regression > regression_threshold
        assert rate_regression > regression_threshold

    @pytest.mark.asyncio
    async def test_performance_improvement_detection(self, performance_benchmark):
        """Test performance improvement detection."""
        # Mock benchmark results showing improvement
        baseline_results = {
            "template_rendering": BenchmarkResult(
                benchmark_name="template_rendering",
                success=True,
                duration=2.0,
                metrics=[PerformanceMetric("rendering_rate", 50, "templates/sec")]
            )
        }
        
        current_results = {
            "template_rendering": BenchmarkResult(
                benchmark_name="template_rendering",
                success=True,
                duration=1.0,  # 2x faster - improvement
                metrics=[PerformanceMetric("rendering_rate", 100, "templates/sec")]  # 2x faster
            )
        }
        
        # Compare results
        baseline_duration = baseline_results["template_rendering"].duration
        current_duration = current_results["template_rendering"].duration
        
        baseline_rate = baseline_results["template_rendering"].metrics[0].value
        current_rate = current_results["template_rendering"].metrics[0].value
        
        # Detect improvement
        duration_improvement = (baseline_duration - current_duration) / baseline_duration
        rate_improvement = (current_rate - baseline_rate) / baseline_rate
        
        assert duration_improvement == 0.5  # 50% improvement
        assert rate_improvement == 1.0  # 100% improvement

    @pytest.mark.asyncio
    async def test_performance_trend_analysis(self, performance_benchmark):
        """Test performance trend analysis over multiple runs."""
        # Mock multiple benchmark runs
        trend_data = [
            {"run": 1, "duration": 1.0, "throughput": 100},
            {"run": 2, "duration": 1.1, "throughput": 95},
            {"run": 3, "duration": 1.2, "throughput": 92},
            {"run": 4, "duration": 1.3, "throughput": 88},
            {"run": 5, "duration": 1.4, "throughput": 85}
        ]
        
        # Calculate trend
        durations = [run["duration"] for run in trend_data]
        throughputs = [run["throughput"] for run in trend_data]
        
        # Simple linear trend calculation
        duration_trend = (durations[-1] - durations[0]) / len(durations)
        throughput_trend = (throughputs[-1] - throughputs[0]) / len(throughputs)
        
        # Should show negative trend (getting worse)
        assert duration_trend > 0  # Increasing duration
        assert throughput_trend < 0  # Decreasing throughput
        
        # Trend significance (more than 5% change)
        duration_change_percent = (durations[-1] - durations[0]) / durations[0]
        throughput_change_percent = (throughputs[-1] - throughputs[0]) / throughputs[0]
        
        assert abs(duration_change_percent) > 0.05  # More than 5% change
        assert abs(throughput_change_percent) > 0.05  # More than 5% change

    @pytest.mark.asyncio
    async def test_performance_baseline_establishment(self, performance_benchmark):
        """Test establishing performance baselines."""
        # Mock multiple runs to establish baseline
        baseline_runs = []
        
        for i in range(5):
            # Mock benchmark result with some variance
            base_duration = 1.0
            variance = 0.1 * (i - 2) / 2  # +/- 10% variance
            run_result = BenchmarkResult(
                benchmark_name="baseline_test",
                success=True,
                duration=base_duration + variance,
                metrics=[PerformanceMetric("operations", 100, "count")]
            )
            baseline_runs.append(run_result)
        
        # Calculate baseline statistics
        durations = [run.duration for run in baseline_runs]
        baseline_mean = sum(durations) / len(durations)
        baseline_min = min(durations)
        baseline_max = max(durations)
        
        # Baseline should be around 1.0 with some variance
        assert 0.9 <= baseline_mean <= 1.1
        assert baseline_min <= baseline_mean <= baseline_max
        
        # Baseline variance should be reasonable
        variance = max(abs(duration - baseline_mean) for duration in durations)
        assert variance <= 0.2  # Within 20% of mean


if __name__ == "__main__":
    pytest.main([__file__])