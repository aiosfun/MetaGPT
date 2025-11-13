"""
Enhanced OpenSpec testing framework.

This package provides comprehensive testing capabilities for OpenSpec components
including unit tests, integration tests, performance benchmarks, and automated
test execution with CI/CD integration.
"""

from .test_framework import OpenSpecTestFramework, TestRunner, TestReporter
from .fixtures import OpenSpecTestFixture, TestDataGenerator
from .performance import PerformanceBenchmark, LoadTester
from .integration import IntegrationTestSuite, WorkflowTestRunner

__all__ = [
    "OpenSpecTestFramework",
    "TestRunner", 
    "TestReporter",
    "OpenSpecTestFixture",
    "TestDataGenerator",
    "PerformanceBenchmark",
    "LoadTester",
    "IntegrationTestSuite",
    "WorkflowTestRunner",
]