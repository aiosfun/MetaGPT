"""
OpenSpec Test Framework

Provides comprehensive testing infrastructure for OpenSpec components including
unit tests, integration tests, performance benchmarks, and automated execution.
"""

import asyncio
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import json
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from enum import Enum

import pytest
import coverage
import concurrent.futures
from junit_xml import TestSuite, TestCase

from metagpt.logs import logger


class TestType(Enum):
    """Test type enumeration."""
    UNIT = "unit"
    INTEGRATION = "integration"
    PERFORMANCE = "performance"
    END_TO_END = "end_to_end"


class TestStatus(Enum):
    """Test status enumeration."""
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


@dataclass
class TestResult:
    """Test result data structure."""
    test_id: str
    test_name: str
    test_type: TestType
    status: TestStatus
    duration: float
    message: Optional[str] = None
    traceback: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class TestSuiteResult:
    """Test suite result data structure."""
    suite_name: str
    test_type: TestType
    results: List[TestResult] = field(default_factory=list)
    total_tests: int = 0
    passed_tests: int = 0
    failed_tests: int = 0
    skipped_tests: int = 0
    error_tests: int = 0
    total_duration: float = 0.0
    coverage_percentage: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)

    def add_result(self, result: TestResult):
        """Add a test result to the suite."""
        self.results.append(result)
        self.total_tests += 1
        self.total_duration += result.duration
        
        if result.status == TestStatus.PASSED:
            self.passed_tests += 1
        elif result.status == TestStatus.FAILED:
            self.failed_tests += 1
        elif result.status == TestStatus.SKIPPED:
            self.skipped_tests += 1
        elif result.status == TestStatus.ERROR:
            self.error_tests += 1


class OpenSpecTestFramework:
    """
    Main test framework for OpenSpec components.
    
    Provides comprehensive testing capabilities including:
    - Unit test execution with coverage reporting
    - Integration test orchestration
    - Performance benchmarking
    - Parallel test execution
    - Multiple output formats (JSON, XML, HTML)
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the test framework."""
        self.config = config or {}
        self.coverage = coverage.Coverage()
        self.test_results: Dict[TestType, TestSuiteResult] = {}
        self.parallel_workers = self.config.get("parallel_workers", 4)
        self.output_dir = Path(self.config.get("output_dir", "test_results"))
        self.output_dir.mkdir(exist_ok=True)
        
        # Initialize test suites
        for test_type in TestType:
            self.test_results[test_type] = TestSuiteResult(
                suite_name=f"OpenSpec {test_type.value.title()} Tests",
                test_type=test_type
            )

    async def run_unit_tests(self, test_paths: List[str] = None) -> TestSuiteResult:
        """Run unit tests with coverage reporting."""
        logger.info("Starting OpenSpec unit tests...")
        
        # Start coverage collection
        self.coverage.start()
        
        try:
            # Run pytest for unit tests
            test_paths = test_paths or ["tests/openspec/test_unit_*"]
            pytest_args = [
                *test_paths,
                "-v",
                "--tb=short",
                "--junit-xml=str",  # Capture XML output
                "--json-report", "--json-report-file=str",  # Capture JSON output
            ]
            
            # Execute pytest
            exit_code = pytest.main(pytest_args)
            
            # Stop coverage collection
            self.coverage.stop()
            self.coverage.save()
            
            # Generate coverage report
            coverage_report = self.coverage.report()
            
            # Parse results and create TestSuiteResult
            suite_result = self._parse_pytest_results(
                TestType.UNIT, 
                exit_code == 0,
                coverage_percentage=coverage_report
            )
            
            logger.info(f"Unit tests completed: {suite_result.passed_tests}/{suite_result.total_tests} passed")
            return suite_result
            
        except Exception as e:
            logger.error(f"Error running unit tests: {e}")
            # Create error result
            error_result = TestResult(
                test_id="unit_test_error",
                test_name="Unit Test Execution",
                test_type=TestType.UNIT,
                status=TestStatus.ERROR,
                duration=0.0,
                message=str(e),
                traceback=traceback.format_exc()
            )
            self.test_results[TestType.UNIT].add_result(error_result)
            return self.test_results[TestType.UNIT]

    async def run_integration_tests(self, test_paths: List[str] = None) -> TestSuiteResult:
        """Run integration tests."""
        logger.info("Starting OpenSpec integration tests...")
        
        try:
            test_paths = test_paths or ["tests/openspec/test_integration_*"]
            pytest_args = [
                *test_paths,
                "-v",
                "--tb=short",
                "-m", "integration",
            ]
            
            # Execute pytest
            exit_code = pytest.main(pytest_args)
            
            # Parse results
            suite_result = self._parse_pytest_results(TestType.INTEGRATION, exit_code == 0)
            
            logger.info(f"Integration tests completed: {suite_result.passed_tests}/{suite_result.total_tests} passed")
            return suite_result
            
        except Exception as e:
            logger.error(f"Error running integration tests: {e}")
            error_result = TestResult(
                test_id="integration_test_error",
                test_name="Integration Test Execution",
                test_type=TestType.INTEGRATION,
                status=TestStatus.ERROR,
                duration=0.0,
                message=str(e),
                traceback=traceback.format_exc()
            )
            self.test_results[TestType.INTEGRATION].add_result(error_result)
            return self.test_results[TestType.INTEGRATION]

    async def run_performance_tests(self, test_paths: List[str] = None) -> TestSuiteResult:
        """Run performance benchmarks."""
        logger.info("Starting OpenSpec performance tests...")
        
        try:
            from .performance import PerformanceBenchmark
            
            benchmark = PerformanceBenchmark()
            results = await benchmark.run_all_benchmarks()
            
            # Convert benchmark results to TestSuiteResult
            suite_result = self.test_results[TestType.PERFORMANCE]
            
            for benchmark_name, benchmark_result in results.items():
                status = TestStatus.PASSED if benchmark_result.get("success", False) else TestStatus.FAILED
                
                test_result = TestResult(
                    test_id=f"perf_{benchmark_name}",
                    test_name=benchmark_name,
                    test_type=TestType.PERFORMANCE,
                    status=status,
                    duration=benchmark_result.get("duration", 0.0),
                    message=benchmark_result.get("message"),
                    metadata=benchmark_result
                )
                suite_result.add_result(test_result)
            
            logger.info(f"Performance tests completed: {suite_result.passed_tests}/{suite_result.total_tests} passed")
            return suite_result
            
        except Exception as e:
            logger.error(f"Error running performance tests: {e}")
            error_result = TestResult(
                test_id="performance_test_error",
                test_name="Performance Test Execution",
                test_type=TestType.PERFORMANCE,
                status=TestStatus.ERROR,
                duration=0.0,
                message=str(e),
                traceback=traceback.format_exc()
            )
            self.test_results[TestType.PERFORMANCE].add_result(error_result)
            return self.test_results[TestType.PERFORMANCE]

    async def run_all_tests(self, parallel: bool = True) -> Dict[TestType, TestSuiteResult]:
        """Run all test suites."""
        logger.info("Starting comprehensive OpenSpec test suite...")
        
        if parallel:
            # Run tests in parallel
            tasks = [
                self.run_unit_tests(),
                self.run_integration_tests(),
                self.run_performance_tests()
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Handle exceptions
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    test_type = list(TestType)[i]
                    logger.error(f"Error in {test_type.value} tests: {result}")
                    # Create error result
                    error_result = TestResult(
                        test_id=f"{test_type.value}_suite_error",
                        test_name=f"{test_type.value.title()} Suite",
                        test_type=test_type,
                        status=TestStatus.ERROR,
                        duration=0.0,
                        message=str(result),
                        traceback=traceback.format_exc()
                    )
                    self.test_results[test_type].add_result(error_result)
        else:
            # Run tests sequentially
            await self.run_unit_tests()
            await self.run_integration_tests()
            await self.run_performance_tests()
        
        # Generate combined report
        await self.generate_combined_report()
        
        logger.info("Comprehensive test suite completed")
        return self.test_results

    def _parse_pytest_results(self, test_type: TestType, success: bool, coverage_percentage: float = 0.0) -> TestSuiteResult:
        """Parse pytest results into TestSuiteResult."""
        suite_result = self.test_results[test_type]
        suite_result.coverage_percentage = coverage_percentage
        
        # Create a summary result for now
        # In a real implementation, this would parse actual pytest output
        summary_result = TestResult(
            test_id=f"{test_type.value}_summary",
            test_name=f"{test_type.value.title()} Test Summary",
            test_type=test_type,
            status=TestStatus.PASSED if success else TestStatus.FAILED,
            duration=0.0,
            message=f"Overall {'PASS' if success else 'FAIL'} for {test_type.value} tests"
        )
        suite_result.add_result(summary_result)
        
        return suite_result

    async def generate_combined_report(self) -> str:
        """Generate combined test report in multiple formats."""
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "summary": self._generate_summary(),
            "suites": {}
        }
        
        # Add suite results
        for test_type, suite_result in self.test_results.items():
            report_data["suites"][test_type.value] = {
                "name": suite_result.suite_name,
                "total_tests": suite_result.total_tests,
                "passed": suite_result.passed_tests,
                "failed": suite_result.failed_tests,
                "skipped": suite_result.skipped_tests,
                "errors": suite_result.error_tests,
                "duration": suite_result.total_duration,
                "coverage": suite_result.coverage_percentage,
                "tests": [
                    {
                        "id": result.test_id,
                        "name": result.test_name,
                        "status": result.status.value,
                        "duration": result.duration,
                        "message": result.message,
                        "metadata": result.metadata
                    }
                    for result in suite_result.results
                ]
            }
        
        # Generate JSON report
        json_report_path = self.output_dir / "test_report.json"
        with open(json_report_path, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        # Generate HTML report
        html_report_path = await self._generate_html_report(report_data)
        
        # Generate JUnit XML report
        xml_report_path = self._generate_junit_xml_report()
        
        logger.info(f"Test reports generated:")
        logger.info(f"  JSON: {json_report_path}")
        logger.info(f"  HTML: {html_report_path}")
        logger.info(f"  XML: {xml_report_path}")
        
        return str(html_report_path)

    def _generate_summary(self) -> Dict[str, Any]:
        """Generate test summary statistics."""
        total_tests = sum(suite.total_tests for suite in self.test_results.values())
        total_passed = sum(suite.passed_tests for suite in self.test_results.values())
        total_failed = sum(suite.failed_tests for suite in self.test_results.values())
        total_skipped = sum(suite.skipped_tests for suite in self.test_results.values())
        total_errors = sum(suite.error_tests for suite in self.test_results.values())
        total_duration = sum(suite.total_duration for suite in self.test_results.values())
        avg_coverage = sum(suite.coverage_percentage for suite in self.test_results.values()) / len(self.test_results)
        
        return {
            "total_tests": total_tests,
            "passed": total_passed,
            "failed": total_failed,
            "skipped": total_skipped,
            "errors": total_errors,
            "success_rate": (total_passed / total_tests * 100) if total_tests > 0 else 0,
            "total_duration": total_duration,
            "average_coverage": avg_coverage
        }

    async def _generate_html_report(self, report_data: Dict[str, Any]) -> Path:
        """Generate HTML test report."""
        html_template = """
<!DOCTYPE html>
<html>
<head>
    <title>OpenSpec Test Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .summary { background: #f5f5f5; padding: 20px; border-radius: 5px; margin-bottom: 20px; }
        .suite { margin-bottom: 30px; }
        .test-passed { color: green; }
        .test-failed { color: red; }
        .test-skipped { color: orange; }
        .test-error { color: purple; }
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
    </style>
</head>
<body>
    <h1>OpenSpec Test Report</h1>
    <div class="summary">
        <h2>Summary</h2>
        <p>Total Tests: {total_tests}</p>
        <p>Passed: {passed} <span class="test-passed">({success_rate:.1f}%)</span></p>
        <p>Failed: {failed} <span class="test-failed"></span></p>
        <p>Skipped: {skipped} <span class="test-skipped"></span></p>
        <p>Errors: {errors} <span class="test-error"></span></p>
        <p>Total Duration: {total_duration:.2f}s</p>
        <p>Average Coverage: {average_coverage:.1f}%</p>
    </div>
    
    {suite_sections}
</body>
</html>
        """
        
        summary = report_data["summary"]
        suite_sections = ""
        
        for suite_name, suite_data in report_data["suites"].items():
            suite_sections += f"""
    <div class="suite">
        <h2>{suite_data['name']}</h2>
        <p>Tests: {suite_data['total_tests']}, Passed: {suite_data['passed']}, Failed: {suite_data['failed']}</p>
        <p>Coverage: {suite_data['coverage']:.1f}%, Duration: {suite_data['duration']:.2f}s</p>
        
        <table>
            <tr><th>Test</th><th>Status</th><th>Duration</th><th>Message</th></tr>
"""
            
            for test in suite_data['tests']:
                status_class = f"test-{test['status']}"
                suite_sections += f"""
            <tr>
                <td>{test['name']}</td>
                <td class="{status_class}">{test['status'].upper()}</td>
                <td>{test['duration']:.3f}s</td>
                <td>{test.get('message', '')}</td>
            </tr>
"""
            
            suite_sections += """
        </table>
    </div>
"""
        
        html_content = html_template.format(
            total_tests=summary["total_tests"],
            passed=summary["passed"],
            failed=summary["failed"],
            skipped=summary["skipped"],
            errors=summary["errors"],
            success_rate=summary["success_rate"],
            total_duration=summary["total_duration"],
            average_coverage=summary["average_coverage"],
            suite_sections=suite_sections
        )
        
        html_path = self.output_dir / "test_report.html"
        with open(html_path, 'w') as f:
            f.write(html_content)
        
        return html_path

    def _generate_junit_xml_report(self) -> Path:
        """Generate JUnit XML report for CI/CD integration."""
        test_suites = []
        
        for test_type, suite_result in self.test_results.items():
            test_cases = []
            
            for result in suite_result.results:
                test_case = TestCase(
                    name=result.test_name,
                    classname=f"OpenSpec.{test_type.value}",
                    elapsed_sec=result.duration,
                    status=result.status.value.upper()
                )
                
                if result.status in [TestStatus.FAILED, TestStatus.ERROR]:
                    if result.traceback:
                        test_case.add_failure_info(message=result.message or "", output=result.traceback)
                    else:
                        test_case.add_failure_info(message=result.message or "")
                
                test_cases.append(test_case)
            
            test_suite = TestSuite(
                name=suite_result.suite_name,
                test_cases=test_cases,
                failures=suite_result.failed_tests + suite_result.error_tests,
                tests=suite_result.total_tests,
                time=suite_result.total_duration
            )
            test_suites.append(test_suite)
        
        xml_path = self.output_dir / "junit_report.xml"
        with open(xml_path, 'w') as f:
            TestSuite.to_file(f, test_suites)
        
        return xml_path


class TestRunner:
    """Test runner for executing specific test types."""
    
    def __init__(self, framework: OpenSpecTestFramework):
        self.framework = framework
    
    async def run_tests_by_type(self, test_type: TestType, test_paths: List[str] = None) -> TestSuiteResult:
        """Run tests of a specific type."""
        if test_type == TestType.UNIT:
            return await self.framework.run_unit_tests(test_paths)
        elif test_type == TestType.INTEGRATION:
            return await self.framework.run_integration_tests(test_paths)
        elif test_type == TestType.PERFORMANCE:
            return await self.framework.run_performance_tests(test_paths)
        else:
            raise ValueError(f"Unsupported test type: {test_type}")


class TestReporter:
    """Test reporter for generating and managing test reports."""
    
    def __init__(self, output_dir: Path = None):
        self.output_dir = output_dir or Path("test_results")
        self.output_dir.mkdir(exist_ok=True)
    
    def generate_trend_report(self, historical_results: List[Dict[str, Any]]) -> str:
        """Generate trend analysis report from historical test results."""
        # Implementation for trend analysis
        pass
    
    def send_notification(self, results: Dict[TestType, TestSuiteResult], config: Dict[str, Any]):
        """Send test result notifications."""
        # Implementation for notifications (email, Slack, etc.)
        pass