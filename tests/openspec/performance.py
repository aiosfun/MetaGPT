"""
OpenSpec Performance Testing Framework

Provides comprehensive performance benchmarking and load testing
capabilities for OpenSpec components.
"""

import asyncio
import time
import statistics
import psutil
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable, Union
import json
import csv
import matplotlib.pyplot as plt
import numpy as np

from metagpt.logs import logger


@dataclass
class PerformanceMetric:
    """Performance metric data structure."""
    name: str
    value: float
    unit: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BenchmarkResult:
    """Benchmark result data structure."""
    benchmark_name: str
    success: bool
    duration: float
    metrics: List[PerformanceMetric] = field(default_factory=list)
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LoadTestResult:
    """Load test result data structure."""
    test_name: str
    concurrent_users: int
    duration: float
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_response_time: float
    min_response_time: float
    max_response_time: float
    p95_response_time: float
    p99_response_time: float
    requests_per_second: float
    error_rate: float
    memory_usage_mb: float
    cpu_usage_percent: float
    timestamp: datetime = field(default_factory=datetime.now)


class PerformanceBenchmark:
    """
    Performance benchmarking suite for OpenSpec components.
    
    Provides comprehensive benchmarking capabilities including:
    - Response time measurement
    - Memory usage profiling
    - CPU usage monitoring
    - Throughput testing
    - Scalability analysis
    """

    def __init__(self, output_dir: Path = None):
        """Initialize performance benchmark suite."""
        self.output_dir = output_dir or Path("test_results/performance")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.results: Dict[str, BenchmarkResult] = {}
        self.benchmarks: Dict[str, Callable] = {}
        
        # Register default benchmarks
        self._register_default_benchmarks()

    def _register_default_benchmarks(self):
        """Register default benchmark functions."""
        self.benchmarks.update({
            "requirement_validation": self.benchmark_requirement_validation,
            "design_generation": self.benchmark_design_generation,
            "task_creation": self.benchmark_task_creation,
            "template_rendering": self.benchmark_template_rendering,
            "validation_processing": self.benchmark_validation_processing,
            "cross_reference_analysis": self.benchmark_cross_reference_analysis,
            "memory_usage": self.benchmark_memory_usage,
            "concurrent_processing": self.benchmark_concurrent_processing
        })

    async def run_all_benchmarks(self) -> Dict[str, BenchmarkResult]:
        """Run all registered benchmarks."""
        logger.info("Starting comprehensive performance benchmarking...")
        
        results = {}
        
        for benchmark_name, benchmark_func in self.benchmarks.items():
            logger.info(f"Running benchmark: {benchmark_name}")
            try:
                result = await benchmark_func()
                results[benchmark_name] = result
                self.results[benchmark_name] = result
                
                if result.success:
                    logger.info(f"✓ {benchmark_name}: {result.duration:.3f}s")
                else:
                    logger.error(f"✗ {benchmark_name}: {result.error_message}")
                    
            except Exception as e:
                logger.error(f"Error in benchmark {benchmark_name}: {e}")
                error_result = BenchmarkResult(
                    benchmark_name=benchmark_name,
                    success=False,
                    duration=0.0,
                    error_message=str(e)
                )
                results[benchmark_name] = error_result
                self.results[benchmark_name] = error_result
        
        # Generate performance report
        await self._generate_performance_report(results)
        
        logger.info("Performance benchmarking completed")
        return results

    async def run_benchmark(self, benchmark_name: str) -> BenchmarkResult:
        """Run a specific benchmark."""
        if benchmark_name not in self.benchmarks:
            raise ValueError(f"Benchmark '{benchmark_name}' not found")
        
        logger.info(f"Running benchmark: {benchmark_name}")
        result = await self.benchmarks[benchmark_name]()
        self.results[benchmark_name] = result
        
        if result.success:
            logger.info(f"✓ {benchmark_name}: {result.duration:.3f}s")
        else:
            logger.error(f"✗ {benchmark_name}: {result.error_message}")
        
        return result

    async def benchmark_requirement_validation(self) -> BenchmarkResult:
        """Benchmark requirement validation performance."""
        from .fixtures import TestDataGenerator
        
        generator = TestDataGenerator()
        requirements = [generator.generate_requirement() for _ in range(100)]
        
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        try:
            from metagpt.openspec.validators.base_validator import OpenSpecValidator
            validator = OpenSpecValidator()
            
            # Validate all requirements
            validation_results = []
            for req in requirements:
                result = await validator.validate_requirement(req)
                validation_results.append(result)
            
            end_time = time.time()
            end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
            
            duration = end_time - start_time
            memory_delta = end_memory - start_memory
            
            metrics = [
                PerformanceMetric("requirements_validated", len(requirements), "count"),
                PerformanceMetric("avg_time_per_requirement", duration / len(requirements), "seconds"),
                PerformanceMetric("memory_usage_delta", memory_delta, "MB"),
                PerformanceMetric("validation_rate", len(requirements) / duration, "req/sec")
            ]
            
            return BenchmarkResult(
                benchmark_name="requirement_validation",
                success=True,
                duration=duration,
                metrics=metrics,
                metadata={
                    "requirements_count": len(requirements),
                    "successful_validations": sum(1 for r in validation_results if r.is_valid)
                }
            )
            
        except Exception as e:
            return BenchmarkResult(
                benchmark_name="requirement_validation",
                success=False,
                duration=time.time() - start_time,
                error_message=str(e)
            )

    async def benchmark_design_generation(self) -> BenchmarkResult:
        """Benchmark design generation performance."""
        from .fixtures import TestDataGenerator
        
        generator = TestDataGenerator()
        requirements = [generator.generate_requirement() for _ in range(50)]
        
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        try:
            # Mock design generation (in real implementation, this would use actual design generator)
            designs = []
            for req in requirements:
                # Simulate design generation work
                await asyncio.sleep(0.001)  # Simulate processing time
                design = generator.generate_design_component()
                designs.append(design)
            
            end_time = time.time()
            end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
            
            duration = end_time - start_time
            memory_delta = end_memory - start_memory
            
            metrics = [
                PerformanceMetric("designs_generated", len(designs), "count"),
                PerformanceMetric("avg_time_per_design", duration / len(designs), "seconds"),
                PerformanceMetric("memory_usage_delta", memory_delta, "MB"),
                PerformanceMetric("generation_rate", len(designs) / duration, "designs/sec")
            ]
            
            return BenchmarkResult(
                benchmark_name="design_generation",
                success=True,
                duration=duration,
                metrics=metrics,
                metadata={
                    "requirements_count": len(requirements),
                    "designs_generated": len(designs)
                }
            )
            
        except Exception as e:
            return BenchmarkResult(
                benchmark_name="design_generation",
                success=False,
                duration=time.time() - start_time,
                error_message=str(e)
            )

    async def benchmark_task_creation(self) -> BenchmarkResult:
        """Benchmark task creation performance."""
        from .fixtures import TestDataGenerator
        
        generator = TestDataGenerator()
        requirements = [generator.generate_requirement() for _ in range(30)]
        
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        try:
            # Generate tasks for requirements
            tasks = []
            for req in requirements:
                # Simulate task creation work
                await asyncio.sleep(0.002)  # Simulate processing time
                task = generator.generate_implementation_task(requirement_count=1)
                task.requirement_ids = [req.id]
                tasks.append(task)
            
            end_time = time.time()
            end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
            
            duration = end_time - start_time
            memory_delta = end_memory - start_memory
            
            metrics = [
                PerformanceMetric("tasks_created", len(tasks), "count"),
                PerformanceMetric("avg_time_per_task", duration / len(tasks), "seconds"),
                PerformanceMetric("memory_usage_delta", memory_delta, "MB"),
                PerformanceMetric("creation_rate", len(tasks) / duration, "tasks/sec")
            ]
            
            return BenchmarkResult(
                benchmark_name="task_creation",
                success=True,
                duration=duration,
                metrics=metrics,
                metadata={
                    "requirements_count": len(requirements),
                    "tasks_created": len(tasks)
                }
            )
            
        except Exception as e:
            return BenchmarkResult(
                benchmark_name="task_creation",
                success=False,
                duration=time.time() - start_time,
                error_message=str(e)
            )

    async def benchmark_template_rendering(self) -> BenchmarkResult:
        """Benchmark template rendering performance."""
        from metagpt.openspec.template_engine import OpenSpecTemplateEngine
        from .fixtures import TestDataGenerator
        
        generator = TestDataGenerator()
        engine = OpenSpecTemplateEngine()
        requirements = [generator.generate_requirement() for _ in range(200)]
        
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        try:
            # Render templates for all requirements
            rendered_count = 0
            for req in requirements:
                data = {
                    "name": "Test System",
                    "version": "1.0.0",
                    "overview": "Test system for benchmarking",
                    "requirements": [req.__dict__]
                }
                rendered = engine.render_template("requirement", data)
                if rendered:
                    rendered_count += 1
            
            end_time = time.time()
            end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
            
            duration = end_time - start_time
            memory_delta = end_memory - start_memory
            
            metrics = [
                PerformanceMetric("templates_rendered", rendered_count, "count"),
                PerformanceMetric("avg_time_per_template", duration / rendered_count, "seconds"),
                PerformanceMetric("memory_usage_delta", memory_delta, "MB"),
                PerformanceMetric("rendering_rate", rendered_count / duration, "templates/sec")
            ]
            
            return BenchmarkResult(
                benchmark_name="template_rendering",
                success=True,
                duration=duration,
                metrics=metrics,
                metadata={
                    "requirements_count": len(requirements),
                    "successful_renders": rendered_count
                }
            )
            
        except Exception as e:
            return BenchmarkResult(
                benchmark_name="template_rendering",
                success=False,
                duration=time.time() - start_time,
                error_message=str(e)
            )

    async def benchmark_validation_processing(self) -> BenchmarkResult:
        """Benchmark validation processing performance."""
        from .fixtures import TestDataGenerator
        
        generator = TestDataGenerator()
        test_data = generator.generate_test_dataset(
            requirement_count=100,
            design_count=50,
            task_count=75
        )
        
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        try:
            # Simulate validation processing
            processed_items = 0
            
            # Process requirements
            for req in test_data["requirements"]:
                await asyncio.sleep(0.001)  # Simulate validation work
                processed_items += 1
            
            # Process designs
            for design in test_data["designs"]:
                await asyncio.sleep(0.0015)  # Simulate validation work
                processed_items += 1
            
            # Process tasks
            for task in test_data["tasks"]:
                await asyncio.sleep(0.0008)  # Simulate validation work
                processed_items += 1
            
            end_time = time.time()
            end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
            
            duration = end_time - start_time
            memory_delta = end_memory - start_memory
            
            metrics = [
                PerformanceMetric("items_processed", processed_items, "count"),
                PerformanceMetric("avg_time_per_item", duration / processed_items, "seconds"),
                PerformanceMetric("memory_usage_delta", memory_delta, "MB"),
                PerformanceMetric("processing_rate", processed_items / duration, "items/sec")
            ]
            
            return BenchmarkResult(
                benchmark_name="validation_processing",
                success=True,
                duration=duration,
                metrics=metrics,
                metadata={
                    "requirements_processed": len(test_data["requirements"]),
                    "designs_processed": len(test_data["designs"]),
                    "tasks_processed": len(test_data["tasks"]),
                    "total_items": processed_items
                }
            )
            
        except Exception as e:
            return BenchmarkResult(
                benchmark_name="validation_processing",
                success=False,
                duration=time.time() - start_time,
                error_message=str(e)
            )

    async def benchmark_cross_reference_analysis(self) -> BenchmarkResult:
        """Benchmark cross-reference analysis performance."""
        from .fixtures import TestDataGenerator
        
        generator = TestDataGenerator()
        test_data = generator.generate_test_dataset(
            requirement_count=150,
            design_count=75,
            task_count=100
        )
        
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        try:
            # Simulate cross-reference analysis
            analysis_results = []
            
            # Analyze requirement to design mappings
            for req in test_data["requirements"]:
                await asyncio.sleep(0.002)  # Simulate analysis work
                # Mock analysis result
                analysis_results.append({
                    "requirement_id": req.id,
                    "mapped_designs": 2,
                    "traceability_score": 0.95
                })
            
            # Analyze design to task mappings
            for design in test_data["designs"]:
                await asyncio.sleep(0.0015)  # Simulate analysis work
                # Mock analysis result
                analysis_results.append({
                    "design_name": design.name,
                    "mapped_tasks": 3,
                    "implementation_coverage": 0.88
                })
            
            end_time = time.time()
            end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
            
            duration = end_time - start_time
            memory_delta = end_memory - start_memory
            
            metrics = [
                PerformanceMetric("analyses_completed", len(analysis_results), "count"),
                PerformanceMetric("avg_time_per_analysis", duration / len(analysis_results), "seconds"),
                PerformanceMetric("memory_usage_delta", memory_delta, "MB"),
                PerformanceMetric("analysis_rate", len(analysis_results) / duration, "analyses/sec")
            ]
            
            return BenchmarkResult(
                benchmark_name="cross_reference_analysis",
                success=True,
                duration=duration,
                metrics=metrics,
                metadata={
                    "requirements_analyzed": len(test_data["requirements"]),
                    "designs_analyzed": len(test_data["designs"]),
                    "total_analyses": len(analysis_results)
                }
            )
            
        except Exception as e:
            return BenchmarkResult(
                benchmark_name="cross_reference_analysis",
                success=False,
                duration=time.time() - start_time,
                error_message=str(e)
            )

    async def benchmark_memory_usage(self) -> BenchmarkResult:
        """Benchmark memory usage patterns."""
        from .fixtures import TestDataGenerator
        
        generator = TestDataGenerator()
        
        start_time = time.time()
        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        try:
            memory_samples = []
            
            # Generate increasing amounts of data and measure memory
            for batch_size in [100, 500, 1000, 2000]:
                # Generate data batch
                test_data = generator.generate_test_dataset(
                    requirement_count=batch_size,
                    design_count=batch_size // 2,
                    task_count=batch_size // 1.5
                )
                
                # Measure memory after generation
                current_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
                memory_samples.append({
                    "batch_size": batch_size,
                    "memory_mb": current_memory,
                    "memory_delta": current_memory - initial_memory
                })
                
                # Simulate some processing
                await asyncio.sleep(0.1)
            
            end_time = time.time()
            final_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
            
            duration = end_time - start_time
            total_memory_delta = final_memory - initial_memory
            
            # Calculate memory efficiency metrics
            total_items = sum(sample["batch_size"] * 2.5 for sample in memory_samples)  # Approximate
            memory_per_item = total_memory_delta / total_items if total_items > 0 else 0
            
            metrics = [
                PerformanceMetric("initial_memory_mb", initial_memory, "MB"),
                PerformanceMetric("final_memory_mb", final_memory, "MB"),
                PerformanceMetric("memory_delta_mb", total_memory_delta, "MB"),
                PerformanceMetric("memory_per_item_kb", memory_per_item * 1024, "KB"),
                PerformanceMetric("max_memory_sample", max(sample["memory_delta"] for sample in memory_samples), "MB")
            ]
            
            return BenchmarkResult(
                benchmark_name="memory_usage",
                success=True,
                duration=duration,
                metrics=metrics,
                metadata={
                    "memory_samples": memory_samples,
                    "total_items_processed": total_items
                }
            )
            
        except Exception as e:
            return BenchmarkResult(
                benchmark_name="memory_usage",
                success=False,
                duration=time.time() - start_time,
                error_message=str(e)
            )

    async def benchmark_concurrent_processing(self) -> BenchmarkResult:
        """Benchmark concurrent processing capabilities."""
        from .fixtures import TestDataGenerator
        
        generator = TestDataGenerator()
        
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        try:
            # Test different concurrency levels
            concurrency_levels = [1, 2, 4, 8, 16]
            results = {}
            
            for concurrency in concurrency_levels:
                # Create concurrent tasks
                async def process_item(item_id):
                    await asyncio.sleep(0.01)  # Simulate work
                    return f"processed_{item_id}"
                
                # Run concurrent tasks
                tasks = [process_item(i) for i in range(concurrency * 10)]
                concurrent_start = time.time()
                
                completed_tasks = await asyncio.gather(*tasks)
                
                concurrent_end = time.time()
                concurrent_duration = concurrent_end - concurrent_start
                
                results[concurrency] = {
                    "duration": concurrent_duration,
                    "tasks_completed": len(completed_tasks),
                    "tasks_per_second": len(completed_tasks) / concurrent_duration
                }
            
            end_time = time.time()
            end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
            
            duration = end_time - start_time
            memory_delta = end_memory - start_memory
            
            # Calculate scalability metrics
            baseline_tps = results[1]["tasks_per_second"]
            max_tps = max(result["tasks_per_second"] for result in results.values())
            scalability_factor = max_tps / baseline_tps if baseline_tps > 0 else 0
            
            metrics = [
                PerformanceMetric("baseline_tps", baseline_tps, "tasks/sec"),
                PerformanceMetric("max_tps", max_tps, "tasks/sec"),
                PerformanceMetric("scalability_factor", scalability_factor, "x"),
                PerformanceMetric("memory_delta_mb", memory_delta, "MB"),
                PerformanceMetric("optimal_concurrency", max(results.keys(), key=lambda k: results[k]["tasks_per_second"]), "workers")
            ]
            
            return BenchmarkResult(
                benchmark_name="concurrent_processing",
                success=True,
                duration=duration,
                metrics=metrics,
                metadata={
                    "concurrency_results": results,
                    "total_tasks_processed": sum(result["tasks_completed"] for result in results.values())
                }
            )
            
        except Exception as e:
            return BenchmarkResult(
                benchmark_name="concurrent_processing",
                success=False,
                duration=time.time() - start_time,
                error_message=str(e)
            )

    async def _generate_performance_report(self, results: Dict[str, BenchmarkResult]):
        """Generate comprehensive performance report."""
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_benchmarks": len(results),
                "successful_benchmarks": sum(1 for r in results.values() if r.success),
                "failed_benchmarks": sum(1 for r in results.values() if not r.success),
                "total_duration": sum(r.duration for r in results.values())
            },
            "benchmarks": {}
        }
        
        for name, result in results.items():
            report_data["benchmarks"][name] = {
                "success": result.success,
                "duration": result.duration,
                "error_message": result.error_message,
                "metrics": [
                    {
                        "name": metric.name,
                        "value": metric.value,
                        "unit": metric.unit,
                        "timestamp": metric.timestamp.isoformat()
                    }
                    for metric in result.metrics
                ],
                "metadata": result.metadata
            }
        
        # Save JSON report
        json_path = self.output_dir / "performance_report.json"
        with open(json_path, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        # Generate CSV report for metrics
        csv_path = self.output_dir / "performance_metrics.csv"
        with open(csv_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Benchmark', 'Metric', 'Value', 'Unit', 'Timestamp'])
            
            for benchmark_name, result in results.items():
                for metric in result.metrics:
                    writer.writerow([
                        benchmark_name,
                        metric.name,
                        metric.value,
                        metric.unit,
                        metric.timestamp.isoformat()
                    ])
        
        # Generate performance charts
        await self._generate_performance_charts(results)
        
        logger.info(f"Performance report generated: {json_path}")
        logger.info(f"Performance metrics CSV: {csv_path}")

    async def _generate_performance_charts(self, results: Dict[str, BenchmarkResult]):
        """Generate performance visualization charts."""
        try:
            # Prepare data for charts
            benchmark_names = []
            durations = []
            success_rates = []
            
            for name, result in results.items():
                benchmark_names.append(name.replace('_', ' ').title())
                durations.append(result.duration)
                success_rates.append(100 if result.success else 0)
            
            # Create performance comparison chart
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
            
            # Duration chart
            bars1 = ax1.bar(benchmark_names, durations, color='skyblue')
            ax1.set_title('Benchmark Duration Comparison')
            ax1.set_ylabel('Duration (seconds)')
            ax1.tick_params(axis='x', rotation=45)
            
            # Add value labels on bars
            for bar in bars1:
                height = bar.get_height()
                ax1.text(bar.get_x() + bar.get_width()/2., height,
                        f'{height:.3f}s', ha='center', va='bottom')
            
            # Success rate chart
            bars2 = ax2.bar(benchmark_names, success_rates, color='lightgreen')
            ax2.set_title('Benchmark Success Rate')
            ax2.set_ylabel('Success Rate (%)')
            ax2.set_ylim(0, 100)
            ax2.tick_params(axis='x', rotation=45)
            
            # Add value labels on bars
            for bar in bars2:
                height = bar.get_height()
                ax2.text(bar.get_x() + bar.get_width()/2., height,
                        f'{height:.0f}%', ha='center', va='bottom')
            
            plt.tight_layout()
            
            # Save chart
            chart_path = self.output_dir / "performance_charts.png"
            plt.savefig(chart_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info(f"Performance charts generated: {chart_path}")
            
        except Exception as e:
            logger.warning(f"Failed to generate performance charts: {e}")


class LoadTester:
    """
    Load testing framework for OpenSpec components.
    
    Provides comprehensive load testing capabilities including:
    - Concurrent user simulation
    - Request rate testing
    - Stress testing
    - Scalability analysis
    """

    def __init__(self, output_dir: Path = None):
        """Initialize load tester."""
        self.output_dir = output_dir or Path("test_results/load_testing")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.results: List[LoadTestResult] = []

    async def run_load_test(
        self,
        test_name: str,
        target_function: Callable,
        concurrent_users: int = 10,
        duration_seconds: int = 60,
        requests_per_second: int = None
    ) -> LoadTestResult:
        """Run a load test with specified parameters."""
        logger.info(f"Starting load test: {test_name}")
        logger.info(f"Concurrent users: {concurrent_users}, Duration: {duration_seconds}s")
        
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        start_cpu = psutil.cpu_percent()
        
        # Track response times and results
        response_times = []
        successful_requests = 0
        failed_requests = 0
        total_requests = 0
        
        async def user_session():
            """Simulate a single user session."""
            nonlocal successful_requests, failed_requests, total_requests, response_times
            
            session_start = time.time()
            
            while time.time() - session_start < duration_seconds:
                try:
                    request_start = time.time()
                    
                    # Execute target function
                    if asyncio.iscoroutinefunction(target_function):
                        await target_function()
                    else:
                        target_function()
                    
                    request_end = time.time()
                    response_time = request_end - request_start
                    response_times.append(response_time)
                    successful_requests += 1
                    
                except Exception as e:
                    failed_requests += 1
                    logger.warning(f"Request failed: {e}")
                
                total_requests += 1
                
                # Rate limiting if specified
                if requests_per_second:
                    delay = 1.0 / requests_per_second
                    await asyncio.sleep(delay)
        
        # Run concurrent user sessions
        tasks = [user_session() for _ in range(concurrent_users)]
        await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.time()
        end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        end_cpu = psutil.cpu_percent()
        
        total_duration = end_time - start_time
        memory_usage = end_memory - start_memory
        cpu_usage = end_cpu - start_cpu
        
        # Calculate statistics
        if response_times:
            avg_response_time = statistics.mean(response_times)
            min_response_time = min(response_times)
            max_response_time = max(response_times)
            p95_response_time = np.percentile(response_times, 95)
            p99_response_time = np.percentile(response_times, 99)
        else:
            avg_response_time = min_response_time = max_response_time = 0
            p95_response_time = p99_response_time = 0
        
        requests_per_second_actual = total_requests / total_duration if total_duration > 0 else 0
        error_rate = (failed_requests / total_requests * 100) if total_requests > 0 else 0
        
        result = LoadTestResult(
            test_name=test_name,
            concurrent_users=concurrent_users,
            duration=total_duration,
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            avg_response_time=avg_response_time,
            min_response_time=min_response_time,
            max_response_time=max_response_time,
            p95_response_time=p95_response_time,
            p99_response_time=p99_response_time,
            requests_per_second=requests_per_second_actual,
            error_rate=error_rate,
            memory_usage_mb=memory_usage,
            cpu_usage_percent=cpu_usage
        )
        
        self.results.append(result)
        
        logger.info(f"Load test completed: {test_name}")
        logger.info(f"  Total requests: {total_requests}")
        logger.info(f"  Success rate: {100 - error_rate:.1f}%")
        logger.info(f"  Avg response time: {avg_response_time:.3f}s")
        logger.info(f"  Requests/sec: {requests_per_second_actual:.1f}")
        
        return result

    async def run_scalability_test(
        self,
        test_name: str,
        target_function: Callable,
        user_levels: List[int] = None,
        duration_per_level: int = 30
    ) -> List[LoadTestResult]:
        """Run scalability test across different user levels."""
        user_levels = user_levels or [1, 5, 10, 25, 50, 100]
        results = []
        
        for users in user_levels:
            level_test_name = f"{test_name}_{users}users"
            result = await self.run_load_test(
                level_test_name,
                target_function,
                concurrent_users=users,
                duration_seconds=duration_per_level
            )
            results.append(result)
            
            # Brief pause between levels
            await asyncio.sleep(2)
        
        # Generate scalability report
        await self._generate_scalability_report(test_name, results)
        
        return results

    async def _generate_scalability_report(self, test_name: str, results: List[LoadTestResult]):
        """Generate scalability analysis report."""
        report_data = {
            "test_name": test_name,
            "timestamp": datetime.now().isoformat(),
            "results": [
                {
                    "concurrent_users": result.concurrent_users,
                    "requests_per_second": result.requests_per_second,
                    "avg_response_time": result.avg_response_time,
                    "p95_response_time": result.p95_response_time,
                    "error_rate": result.error_rate,
                    "memory_usage_mb": result.memory_usage_mb
                }
                for result in results
            ]
        }
        
        # Save scalability report
        report_path = self.output_dir / f"{test_name}_scalability.json"
        with open(report_path, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        # Generate scalability chart
        try:
            users = [result.concurrent_users for result in results]
            rps = [result.requests_per_second for result in results]
            response_times = [result.avg_response_time * 1000 for result in results]  # Convert to ms
            
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
            
            # Throughput chart
            ax1.plot(users, rps, 'b-o', label='Requests/sec')
            ax1.set_xlabel('Concurrent Users')
            ax1.set_ylabel('Requests per Second')
            ax1.set_title('Throughput Scalability')
            ax1.grid(True)
            ax1.legend()
            
            # Response time chart
            ax2.plot(users, response_times, 'r-o', label='Avg Response Time')
            ax2.set_xlabel('Concurrent Users')
            ax2.set_ylabel('Response Time (ms)')
            ax2.set_title('Response Time Scalability')
            ax2.grid(True)
            ax2.legend()
            
            plt.tight_layout()
            
            chart_path = self.output_dir / f"{test_name}_scalability.png"
            plt.savefig(chart_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info(f"Scalability report generated: {report_path}")
            logger.info(f"Scalability chart generated: {chart_path}")
            
        except Exception as e:
            logger.warning(f"Failed to generate scalability chart: {e}")