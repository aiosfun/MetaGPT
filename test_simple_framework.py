#!/usr/bin/env python3
"""
Simple test script to validate the enhanced testing framework.
"""

import sys
import os
import asyncio
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "tests"))

def test_imports():
    """Test that all components can be imported."""
    print("Testing imports...")
    
    try:
        from tests.openspec.test_framework import OpenSpecTestFramework, TestType, TestStatus
        print("✓ Test framework imported successfully")
    except Exception as e:
        print(f"✗ Test framework import failed: {e}")
        return False
    
    try:
        from tests.openspec.fixtures import OpenSpecTestFixture, TestDataGenerator
        print("✓ Test fixtures imported successfully")
    except Exception as e:
        print(f"✗ Test fixtures import failed: {e}")
        return False
    
    try:
        from tests.openspec.performance import PerformanceBenchmark, LoadTester
        print("✓ Performance testing imported successfully")
    except Exception as e:
        print(f"✗ Performance testing import failed: {e}")
        return False
    
    try:
        from tests.openspec.integration import IntegrationTestSuite
        print("✓ Integration testing imported successfully")
    except Exception as e:
        print(f"✗ Integration testing import failed: {e}")
        return False
    
    return True

def test_basic_functionality():
    """Test basic functionality of the framework."""
    print("\nTesting basic functionality...")
    
    try:
        from tests.openspec.test_framework import OpenSpecTestFramework, TestResult, TestType, TestStatus
        
        # Create test framework
        framework = OpenSpecTestFramework()
        print("✓ Test framework created successfully")
        
        # Create test result
        result = TestResult(
            test_id="test_001",
            test_name="Sample Test",
            test_type=TestType.UNIT,
            status=TestStatus.PASSED,
            duration=0.123
        )
        print("✓ Test result created successfully")
        
        # Add result to suite
        suite_result = framework.test_results[TestType.UNIT]
        suite_result.add_result(result)
        print("✓ Test result added to suite successfully")
        
        # Verify suite statistics
        assert suite_result.total_tests == 1
        assert suite_result.passed_tests == 1
        assert suite_result.duration == 0.123
        print("✓ Suite statistics verified successfully")
        
    except Exception as e:
        print(f"✗ Basic functionality test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

def test_fixtures():
    """Test fixture functionality."""
    print("\nTesting fixtures...")
    
    try:
        from tests.openspec.fixtures import OpenSpecTestFixture, TestDataGenerator
        
        # Create test fixture
        fixture = OpenSpecTestFixture()
        print("✓ Test fixture created successfully")
        
        # Test getting requirements
        req = fixture.get_requirement_fixture()
        assert req is not None
        assert hasattr(req, 'id')
        assert hasattr(req, 'title')
        print("✓ Requirement fixture works successfully")
        
        # Test data generator
        generator = TestDataGenerator(seed=42)
        generated_req = generator.generate_requirement()
        assert generated_req is not None
        assert generated_req.id.startswith("REQ-")
        print("✓ Data generator works successfully")
        
    except Exception as e:
        print(f"✗ Fixtures test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

async def test_integration_suite():
    """Test integration suite functionality."""
    print("\nTesting integration suite...")
    
    try:
        from tests.openspec.integration import IntegrationTestSuite
        
        # Create integration suite
        suite = IntegrationTestSuite()
        print("✓ Integration suite created successfully")
        
        # Test component initialization
        await suite._initialize_openspec_components()
        assert "template_engine" in suite.test_data
        assert "validator" in suite.test_data
        assert "review_orchestrator" in suite.test_data
        print("✓ Component initialization works successfully")
        
    except Exception as e:
        print(f"✗ Integration suite test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

def test_performance_benchmark():
    """Test performance benchmark functionality."""
    print("\nTesting performance benchmark...")
    
    try:
        from tests.openspec.performance import PerformanceBenchmark, PerformanceMetric, BenchmarkResult
        import tempfile
        
        # Create performance benchmark
        with tempfile.TemporaryDirectory() as temp_dir:
            benchmark = PerformanceBenchmark(output_dir=Path(temp_dir))
            print("✓ Performance benchmark created successfully")
            
            # Test metric creation
            metric = PerformanceMetric(
                name="test_metric",
                value=100.5,
                unit="ms"
            )
            assert metric.name == "test_metric"
            assert metric.value == 100.5
            assert metric.unit == "ms"
            print("✓ Performance metric created successfully")
            
            # Test benchmark result creation
            result = BenchmarkResult(
                benchmark_name="test_benchmark",
                success=True,
                duration=1.0,
                metrics=[metric]
            )
            assert result.benchmark_name == "test_benchmark"
            assert result.success is True
            assert len(result.metrics) == 1
            print("✓ Benchmark result created successfully")
        
    except Exception as e:
        print(f"✗ Performance benchmark test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

async def main():
    """Main test function."""
    print("Testing Enhanced OpenSpec Testing Framework")
    print("=" * 50)
    
    # Add missing import for tempfile
    import tempfile
    
    tests = [
        ("Imports", test_imports),
        ("Basic Functionality", test_basic_functionality),
        ("Fixtures", test_fixtures),
        ("Integration Suite", test_integration_suite),
        ("Performance Benchmark", test_performance_benchmark),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\nRunning {test_name} Test...")
        print("-" * 30)
        
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            
            if result:
                print(f"✅ {test_name} Test PASSED")
                passed += 1
            else:
                print(f"❌ {test_name} Test FAILED")
        except Exception as e:
            print(f"❌ {test_name} Test ERROR: {e}")
    
    print("\n" + "=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("All tests passed! Enhanced testing framework is working correctly.")
        return 0
    else:
        print(f"{total - passed} tests failed. Please check the implementation.")
        return 1

if __name__ == "__main__":
    import tempfile
    exit_code = asyncio.run(main())
    sys.exit(exit_code)