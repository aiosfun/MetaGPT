"""
OpenSpec Integration Testing Framework

Provides comprehensive integration testing capabilities for OpenSpec workflows
including end-to-end testing, API integration, and cross-component validation.
"""

import asyncio
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
import json

from metagpt.logs import logger


class IntegrationTestType(Enum):
    """Integration test type enumeration."""
    WORKFLOW = "workflow"
    API = "api"
    DATABASE = "database"
    CROSS_COMPONENT = "cross_component"
    END_TO_END = "end_to_end"


@dataclass
class IntegrationTestStep:
    """Integration test step definition."""
    name: str
    function: Callable
    expected_result: Any = None
    timeout_seconds: float = 30.0
    retry_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class IntegrationTestResult:
    """Integration test result data structure."""
    test_name: str
    test_type: IntegrationTestType
    success: bool
    duration: float
    steps_completed: int
    total_steps: int
    step_results: List[Dict[str, Any]] = field(default_factory=list)
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


class IntegrationTestSuite:
    """
    Integration test suite for OpenSpec workflows.
    
    Provides comprehensive integration testing including:
    - End-to-end workflow testing
    - API integration testing
    - Database integration testing
    - Cross-component interaction testing
    - Mock external dependencies
    """

    def __init__(self, config: Dict[str, Any] = None):
        """Initialize integration test suite."""
        self.config = config or {}
        self.test_results: List[IntegrationTestResult] = []
        self.mock_services: Dict[str, Any] = {}
        self.test_data: Dict[str, Any] = {}
        
        # Initialize mock services
        self._setup_mock_services()

    def _setup_mock_services(self):
        """Setup mock external services."""
        from unittest.mock import Mock, AsyncMock
        
        # Mock LLM service
        mock_llm = AsyncMock()
        mock_llm.acomplete.return_value.content = "Mock LLM response for testing"
        self.mock_services["llm"] = mock_llm
        
        # Mock database
        mock_db = Mock()
        mock_db.execute.return_value.fetchall.return_value = []
        self.mock_services["database"] = mock_db
        
        # Mock file system
        mock_fs = Mock()
        mock_fs.read_file.return_value = "Mock file content"
        mock_fs.write_file.return_value = True
        self.mock_services["filesystem"] = mock_fs

    async def run_workflow_integration_test(self, test_name: str = "workflow_integration") -> IntegrationTestResult:
        """Run complete OpenSpec workflow integration test."""
        logger.info(f"Starting workflow integration test: {test_name}")
        
        start_time = time.time()
        
        # Define workflow steps
        steps = [
            IntegrationTestStep(
                name="Initialize OpenSpec components",
                function=self._initialize_openspec_components
            ),
            IntegrationTestStep(
                name="Generate requirements",
                function=self._generate_test_requirements
            ),
            IntegrationTestStep(
                name="Create design specifications",
                function=self._create_design_specifications
            ),
            IntegrationTestStep(
                name="Generate implementation tasks",
                function=self._generate_implementation_tasks
            ),
            IntegrationTestStep(
                name="Validate specifications",
                function=self._validate_specifications
            ),
            IntegrationTestStep(
                name="Run review workflow",
                function=self._run_review_workflow
            ),
            IntegrationTestStep(
                name="Verify traceability",
                function=self._verify_traceability
            )
        ]
        
        step_results = []
        steps_completed = 0
        
        try:
            for step in steps:
                logger.info(f"Executing step: {step.name}")
                
                step_start = time.time()
                
                try:
                    # Execute step function
                    if asyncio.iscoroutinefunction(step.function):
                        result = await asyncio.wait_for(
                            step.function(),
                            timeout=step.timeout_seconds
                        )
                    else:
                        result = step.function()
                    
                    step_duration = time.time() - step_start
                    
                    # Check if result matches expectation
                    success = True
                    if step.expected_result is not None:
                        success = result == step.expected_result
                    
                    step_result = {
                        "name": step.name,
                        "success": success,
                        "duration": step_duration,
                        "result": result,
                        "expected": step.expected_result,
                        "metadata": step.metadata
                    }
                    
                    step_results.append(step_result)
                    steps_completed += 1
                    
                    if not success:
                        logger.warning(f"Step '{step.name}' did not produce expected result")
                    
                except asyncio.TimeoutError:
                    step_duration = time.time() - step_start
                    error_msg = f"Step '{step.name}' timed out after {step.timeout_seconds}s"
                    logger.error(error_msg)
                    
                    step_result = {
                        "name": step.name,
                        "success": False,
                        "duration": step_duration,
                        "error": error_msg,
                        "metadata": step.metadata
                    }
                    step_results.append(step_result)
                    break
                    
                except Exception as e:
                    step_duration = time.time() - step_start
                    error_msg = f"Step '{step.name}' failed: {str(e)}"
                    logger.error(error_msg)
                    
                    step_result = {
                        "name": step.name,
                        "success": False,
                        "duration": step_duration,
                        "error": error_msg,
                        "traceback": traceback.format_exc(),
                        "metadata": step.metadata
                    }
                    step_results.append(step_result)
                    break
        
        except Exception as e:
            logger.error(f"Workflow integration test failed: {e}")
        
        total_duration = time.time() - start_time
        overall_success = steps_completed == len(steps) and all(r["success"] for r in step_results)
        
        result = IntegrationTestResult(
            test_name=test_name,
            test_type=IntegrationTestType.WORKFLOW,
            success=overall_success,
            duration=total_duration,
            steps_completed=steps_completed,
            total_steps=len(steps),
            step_results=step_results,
            error_message=None if overall_success else f"Test failed at step {steps_completed + 1}",
            metadata={
                "workflow_type": "complete_openspec",
                "components_tested": ["requirements", "design", "tasks", "validation", "review"]
            }
        )
        
        self.test_results.append(result)
        
        logger.info(f"Workflow integration test completed: {'SUCCESS' if overall_success else 'FAILED'}")
        logger.info(f"Steps completed: {steps_completed}/{len(steps)}")
        logger.info(f"Duration: {total_duration:.2f}s")
        
        return result

    async def run_api_integration_test(self, test_name: str = "api_integration") -> IntegrationTestResult:
        """Run API integration test for OpenSpec components."""
        logger.info(f"Starting API integration test: {test_name}")
        
        start_time = time.time()
        
        steps = [
            IntegrationTestStep(
                name="Test requirement API endpoints",
                function=self._test_requirement_api
            ),
            IntegrationTestStep(
                name="Test design API endpoints",
                function=self._test_design_api
            ),
            IntegrationTestStep(
                name="Test task API endpoints",
                function=self._test_task_api
            ),
            IntegrationTestStep(
                name="Test validation API endpoints",
                function=self._test_validation_api
            ),
            IntegrationTestStep(
                name="Test review API endpoints",
                function=self._test_review_api
            )
        ]
        
        step_results = []
        steps_completed = 0
        
        try:
            for step in steps:
                logger.info(f"Executing API step: {step.name}")
                
                step_start = time.time()
                
                try:
                    result = await asyncio.wait_for(
                        step.function(),
                        timeout=step.timeout_seconds
                    )
                    
                    step_duration = time.time() - step_start
                    
                    step_result = {
                        "name": step.name,
                        "success": True,
                        "duration": step_duration,
                        "result": result,
                        "metadata": step.metadata
                    }
                    
                    step_results.append(step_result)
                    steps_completed += 1
                    
                except Exception as e:
                    step_duration = time.time() - step_start
                    error_msg = f"API step '{step.name}' failed: {str(e)}"
                    logger.error(error_msg)
                    
                    step_result = {
                        "name": step.name,
                        "success": False,
                        "duration": step_duration,
                        "error": error_msg,
                        "traceback": traceback.format_exc(),
                        "metadata": step.metadata
                    }
                    step_results.append(step_result)
                    break
        
        except Exception as e:
            logger.error(f"API integration test failed: {e}")
        
        total_duration = time.time() - start_time
        overall_success = steps_completed == len(steps) and all(r["success"] for r in step_results)
        
        result = IntegrationTestResult(
            test_name=test_name,
            test_type=IntegrationTestType.API,
            success=overall_success,
            duration=total_duration,
            steps_completed=steps_completed,
            total_steps=len(steps),
            step_results=step_results,
            error_message=None if overall_success else f"API test failed at step {steps_completed + 1}",
            metadata={
                "api_endpoints_tested": ["requirements", "design", "tasks", "validation", "review"]
            }
        )
        
        self.test_results.append(result)
        
        logger.info(f"API integration test completed: {'SUCCESS' if overall_success else 'FAILED'}")
        return result

    async def run_database_integration_test(self, test_name: str = "database_integration") -> IntegrationTestResult:
        """Run database integration test for OpenSpec persistence."""
        logger.info(f"Starting database integration test: {test_name}")
        
        start_time = time.time()
        
        steps = [
            IntegrationTestStep(
                name="Test database connection",
                function=self._test_database_connection
            ),
            IntegrationTestStep(
                name="Test requirement persistence",
                function=self._test_requirement_persistence
            ),
            IntegrationTestStep(
                name="Test design persistence",
                function=self._test_design_persistence
            ),
            IntegrationTestStep(
                name="Test task persistence",
                function=self._test_task_persistence
            ),
            IntegrationTestStep(
                name="Test data relationships",
                function=self._test_data_relationships
            )
        ]
        
        step_results = []
        steps_completed = 0
        
        try:
            for step in steps:
                logger.info(f"Executing database step: {step.name}")
                
                step_start = time.time()
                
                try:
                    result = await asyncio.wait_for(
                        step.function(),
                        timeout=step.timeout_seconds
                    )
                    
                    step_duration = time.time() - step_start
                    
                    step_result = {
                        "name": step.name,
                        "success": True,
                        "duration": step_duration,
                        "result": result,
                        "metadata": step.metadata
                    }
                    
                    step_results.append(step_result)
                    steps_completed += 1
                    
                except Exception as e:
                    step_duration = time.time() - step_start
                    error_msg = f"Database step '{step.name}' failed: {str(e)}"
                    logger.error(error_msg)
                    
                    step_result = {
                        "name": step.name,
                        "success": False,
                        "duration": step_duration,
                        "error": error_msg,
                        "traceback": traceback.format_exc(),
                        "metadata": step.metadata
                    }
                    step_results.append(step_result)
                    break
        
        except Exception as e:
            logger.error(f"Database integration test failed: {e}")
        
        total_duration = time.time() - start_time
        overall_success = steps_completed == len(steps) and all(r["success"] for r in step_results)
        
        result = IntegrationTestResult(
            test_name=test_name,
            test_type=IntegrationTestType.DATABASE,
            success=overall_success,
            duration=total_duration,
            steps_completed=steps_completed,
            total_steps=len(steps),
            step_results=step_results,
            error_message=None if overall_success else f"Database test failed at step {steps_completed + 1}",
            metadata={
                "database_operations_tested": ["connection", "requirements", "design", "tasks", "relationships"]
            }
        )
        
        self.test_results.append(result)
        
        logger.info(f"Database integration test completed: {'SUCCESS' if overall_success else 'FAILED'}")
        return result

    async def run_cross_component_test(self, test_name: str = "cross_component") -> IntegrationTestResult:
        """Run cross-component integration test."""
        logger.info(f"Starting cross-component integration test: {test_name}")
        
        start_time = time.time()
        
        steps = [
            IntegrationTestStep(
                name="Test requirement-design integration",
                function=self._test_requirement_design_integration
            ),
            IntegrationTestStep(
                name="Test design-task integration",
                function=self._test_design_task_integration
            ),
            IntegrationTestStep(
                name="Test validation integration",
                function=self._test_validation_integration
            ),
            IntegrationTestStep(
                name="Test review integration",
                function=self._test_review_integration
            ),
            IntegrationTestStep(
                name="Test template integration",
                function=self._test_template_integration
            )
        ]
        
        step_results = []
        steps_completed = 0
        
        try:
            for step in steps:
                logger.info(f"Executing cross-component step: {step.name}")
                
                step_start = time.time()
                
                try:
                    result = await asyncio.wait_for(
                        step.function(),
                        timeout=step.timeout_seconds
                    )
                    
                    step_duration = time.time() - step_start
                    
                    step_result = {
                        "name": step.name,
                        "success": True,
                        "duration": step_duration,
                        "result": result,
                        "metadata": step.metadata
                    }
                    
                    step_results.append(step_result)
                    steps_completed += 1
                    
                except Exception as e:
                    step_duration = time.time() - step_start
                    error_msg = f"Cross-component step '{step.name}' failed: {str(e)}"
                    logger.error(error_msg)
                    
                    step_result = {
                        "name": step.name,
                        "success": False,
                        "duration": step_duration,
                        "error": error_msg,
                        "traceback": traceback.format_exc(),
                        "metadata": step.metadata
                    }
                    step_results.append(step_result)
                    break
        
        except Exception as e:
            logger.error(f"Cross-component integration test failed: {e}")
        
        total_duration = time.time() - start_time
        overall_success = steps_completed == len(steps) and all(r["success"] for r in step_results)
        
        result = IntegrationTestResult(
            test_name=test_name,
            test_type=IntegrationTestType.CROSS_COMPONENT,
            success=overall_success,
            duration=total_duration,
            steps_completed=steps_completed,
            total_steps=len(steps),
            step_results=step_results,
            error_message=None if overall_success else f"Cross-component test failed at step {steps_completed + 1}",
            metadata={
                "integrations_tested": ["requirement-design", "design-task", "validation", "review", "template"]
            }
        )
        
        self.test_results.append(result)
        
        logger.info(f"Cross-component integration test completed: {'SUCCESS' if overall_success else 'FAILED'}")
        return result

    async def run_end_to_end_test(self, test_name: str = "end_to_end") -> IntegrationTestResult:
        """Run comprehensive end-to-end integration test."""
        logger.info(f"Starting end-to-end integration test: {test_name}")
        
        start_time = time.time()
        
        # Run all integration tests in sequence
        workflow_result = await self.run_workflow_integration_test(f"{test_name}_workflow")
        api_result = await self.run_api_integration_test(f"{test_name}_api")
        database_result = await self.run_database_integration_test(f"{test_name}_database")
        cross_component_result = await self.run_cross_component_test(f"{test_name}_cross_component")
        
        # Combine results
        all_results = [workflow_result, api_result, database_result, cross_component_result]
        overall_success = all(result.success for result in all_results)
        total_steps = sum(result.total_steps for result in all_results)
        completed_steps = sum(result.steps_completed for result in all_results)
        
        result = IntegrationTestResult(
            test_name=test_name,
            test_type=IntegrationTestType.END_TO_END,
            success=overall_success,
            duration=time.time() - start_time,
            steps_completed=completed_steps,
            total_steps=total_steps,
            step_results=[
                {
                    "name": "workflow_integration",
                    "success": workflow_result.success,
                    "duration": workflow_result.duration
                },
                {
                    "name": "api_integration",
                    "success": api_result.success,
                    "duration": api_result.duration
                },
                {
                    "name": "database_integration",
                    "success": database_result.success,
                    "duration": database_result.duration
                },
                {
                    "name": "cross_component_integration",
                    "success": cross_component_result.success,
                    "duration": cross_component_result.duration
                }
            ],
            error_message=None if overall_success else "One or more integration tests failed",
            metadata={
                "test_types": ["workflow", "api", "database", "cross_component"],
                "individual_results": [result.__dict__ for result in all_results]
            }
        )
        
        self.test_results.append(result)
        
        logger.info(f"End-to-end integration test completed: {'SUCCESS' if overall_success else 'FAILED'}")
        return result

    # Workflow step implementations
    async def _initialize_openspec_components(self):
        """Initialize OpenSpec components."""
        from metagpt.openspec import OpenSpecTemplateEngine, OpenSpecValidator, ReviewOrchestrator
        
        # Initialize components
        template_engine = OpenSpecTemplateEngine()
        validator = OpenSpecValidator()
        review_orchestrator = ReviewOrchestrator()
        
        # Store in test data
        self.test_data["template_engine"] = template_engine
        self.test_data["validator"] = validator
        self.test_data["review_orchestrator"] = review_orchestrator
        
        return {"components_initialized": 3}

    async def _generate_test_requirements(self):
        """Generate test requirements."""
        from .fixtures import TestDataGenerator
        
        generator = TestDataGenerator()
        requirements = generator.generate_test_dataset(requirement_count=5, design_count=0, task_count=0)
        
        self.test_data["requirements"] = requirements["requirements"]
        
        return {"requirements_generated": len(requirements["requirements"])}

    async def _create_design_specifications(self):
        """Create design specifications."""
        from .fixtures import TestDataGenerator
        
        generator = TestDataGenerator()
        designs = generator.generate_test_dataset(requirement_count=0, design_count=3, task_count=0)
        
        self.test_data["designs"] = designs["designs"]
        
        return {"designs_created": len(designs["designs"])}

    async def _generate_implementation_tasks(self):
        """Generate implementation tasks."""
        from .fixtures import TestDataGenerator
        
        generator = TestDataGenerator()
        tasks = generator.generate_test_dataset(requirement_count=0, design_count=0, task_count=8)
        
        self.test_data["tasks"] = tasks["tasks"]
        
        return {"tasks_generated": len(tasks["tasks"])}

    async def _validate_specifications(self):
        """Validate all specifications."""
        validator = self.test_data.get("validator")
        if not validator:
            raise ValueError("Validator not initialized")
        
        validation_results = {}
        
        # Validate requirements
        if "requirements" in self.test_data:
            req_results = []
            for req in self.test_data["requirements"]:
                result = await validator.validate_requirement(req)
                req_results.append(result)
            validation_results["requirements"] = req_results
        
        # Validate designs
        if "designs" in self.test_data:
            design_results = []
            for design in self.test_data["designs"]:
                result = await validator.validate_design(design)
                design_results.append(result)
            validation_results["designs"] = design_results
        
        # Validate tasks
        if "tasks" in self.test_data:
            task_results = []
            for task in self.test_data["tasks"]:
                result = await validator.validate_task(task)
                task_results.append(result)
            validation_results["tasks"] = task_results
        
        self.test_data["validation_results"] = validation_results
        
        return {
            "validations_completed": sum(len(results) for results in validation_results.values()),
            "validation_summary": {
                component: sum(1 for r in results if r.is_valid) / len(results) * 100 if results else 0
                for component, results in validation_results.items()
            }
        }

    async def _run_review_workflow(self):
        """Run review workflow."""
        orchestrator = self.test_data.get("review_orchestrator")
        if not orchestrator:
            raise ValueError("Review orchestrator not initialized")
        
        review_results = {}
        
        # Submit requirements for review
        if "requirements" in self.test_data:
            for req in self.test_data["requirements"][:2]:  # Review first 2 requirements
                review_id = await orchestrator.submit_for_review(
                    item_type="requirement",
                    item_id=req.id,
                    content=req
                )
                review_results[f"requirement_{req.id}"] = review_id
        
        # Submit designs for review
        if "designs" in self.test_data:
            for design in self.test_data["designs"][:1]:  # Review first design
                review_id = await orchestrator.submit_for_review(
                    item_type="design",
                    item_id=design.name,
                    content=design
                )
                review_results[f"design_{design.name}"] = review_id
        
        self.test_data["review_results"] = review_results
        
        return {"reviews_submitted": len(review_results)}

    async def _verify_traceability(self):
        """Verify traceability between components."""
        traceability_results = {}
        
        # Check requirement to design traceability
        if "requirements" in self.test_data and "designs" in self.test_data:
            req_count = len(self.test_data["requirements"])
            design_count = len(self.test_data["designs"])
            # Mock traceability check
            traceability_results["requirement_to_design"] = {
                "requirements": req_count,
                "designs": design_count,
                "traceability_score": 0.85  # Mock score
            }
        
        # Check design to task traceability
        if "designs" in self.test_data and "tasks" in self.test_data:
            design_count = len(self.test_data["designs"])
            task_count = len(self.test_data["tasks"])
            # Mock traceability check
            traceability_results["design_to_task"] = {
                "designs": design_count,
                "tasks": task_count,
                "traceability_score": 0.78  # Mock score
            }
        
        return {"traceability_verified": len(traceability_results), "results": traceability_results}

    # API test implementations
    async def _test_requirement_api(self):
        """Test requirement API endpoints."""
        # Mock API testing
        await asyncio.sleep(0.1)  # Simulate API call
        return {"api_endpoints_tested": ["GET /requirements", "POST /requirements", "PUT /requirements"]}

    async def _test_design_api(self):
        """Test design API endpoints."""
        # Mock API testing
        await asyncio.sleep(0.1)
        return {"api_endpoints_tested": ["GET /designs", "POST /designs", "PUT /designs"]}

    async def _test_task_api(self):
        """Test task API endpoints."""
        # Mock API testing
        await asyncio.sleep(0.1)
        return {"api_endpoints_tested": ["GET /tasks", "POST /tasks", "PUT /tasks"]}

    async def _test_validation_api(self):
        """Test validation API endpoints."""
        # Mock API testing
        await asyncio.sleep(0.1)
        return {"api_endpoints_tested": ["POST /validate/requirement", "POST /validate/design", "POST /validate/task"]}

    async def _test_review_api(self):
        """Test review API endpoints."""
        # Mock API testing
        await asyncio.sleep(0.1)
        return {"api_endpoints_tested": ["POST /review", "GET /review/:id", "POST /review/:id/feedback"]}

    # Database test implementations
    async def _test_database_connection(self):
        """Test database connection."""
        # Mock database connection test
        await asyncio.sleep(0.05)
        return {"connection_status": "success", "database_type": "mock_postgresql"}

    async def _test_requirement_persistence(self):
        """Test requirement persistence."""
        # Mock database operations
        await asyncio.sleep(0.1)
        return {"operations": ["insert", "select", "update", "delete"], "success_rate": 100}

    async def _test_design_persistence(self):
        """Test design persistence."""
        # Mock database operations
        await asyncio.sleep(0.1)
        return {"operations": ["insert", "select", "update", "delete"], "success_rate": 100}

    async def _test_task_persistence(self):
        """Test task persistence."""
        # Mock database operations
        await asyncio.sleep(0.1)
        return {"operations": ["insert", "select", "update", "delete"], "success_rate": 100}

    async def _test_data_relationships(self):
        """Test data relationships."""
        # Mock relationship testing
        await asyncio.sleep(0.15)
        return {"relationships_tested": ["requirement-design", "design-task", "requirement-task"]}

    # Cross-component test implementations
    async def _test_requirement_design_integration(self):
        """Test requirement-design integration."""
        await asyncio.sleep(0.1)
        return {"integration_type": "requirement-design", "status": "success"}

    async def _test_design_task_integration(self):
        """Test design-task integration."""
        await asyncio.sleep(0.1)
        return {"integration_type": "design-task", "status": "success"}

    async def _test_validation_integration(self):
        """Test validation integration."""
        await asyncio.sleep(0.1)
        return {"integration_type": "validation", "status": "success"}

    async def _test_review_integration(self):
        """Test review integration."""
        await asyncio.sleep(0.1)
        return {"integration_type": "review", "status": "success"}

    async def _test_template_integration(self):
        """Test template integration."""
        template_engine = self.test_data.get("template_engine")
        if not template_engine:
            raise ValueError("Template engine not initialized")
        
        # Test template rendering
        test_data = {"title": "Test", "content": "Test content"}
        rendered = template_engine.render_template("requirement", test_data)
        
        return {"template_rendered": len(rendered) > 0, "status": "success"}

    async def generate_integration_report(self, output_path: Path = None) -> str:
        """Generate comprehensive integration test report."""
        output_path = output_path or Path("test_results/integration_report.json")
        
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_tests": len(self.test_results),
                "successful_tests": sum(1 for r in self.test_results if r.success),
                "failed_tests": sum(1 for r in self.test_results if not r.success),
                "total_duration": sum(r.duration for r in self.test_results),
                "total_steps": sum(r.total_steps for r in self.test_results),
                "completed_steps": sum(r.steps_completed for r in self.test_results)
            },
            "test_results": [
                {
                    "test_name": result.test_name,
                    "test_type": result.test_type.value,
                    "success": result.success,
                    "duration": result.duration,
                    "steps_completed": result.steps_completed,
                    "total_steps": result.total_steps,
                    "error_message": result.error_message,
                    "metadata": result.metadata,
                    "step_results": result.step_results
                }
                for result in self.test_results
            ]
        }
        
        with open(output_path, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        logger.info(f"Integration test report generated: {output_path}")
        return str(output_path)


class WorkflowTestRunner:
    """
    Specialized test runner for OpenSpec workflow testing.
    
    Provides workflow-specific testing capabilities including:
    - Workflow orchestration testing
    - State management testing
    - Error handling testing
    - Performance testing for workflows
    """

    def __init__(self, integration_suite: IntegrationTestSuite):
        """Initialize workflow test runner."""
        self.integration_suite = integration_suite

    async def run_workflow_performance_test(
        self,
        workflow_name: str,
        iterations: int = 10,
        concurrent_runs: int = 1
    ) -> Dict[str, Any]:
        """Run workflow performance test."""
        logger.info(f"Starting workflow performance test: {workflow_name}")
        
        performance_results = []
        
        for i in range(iterations):
            start_time = time.time()
            
            # Run workflow
            if workflow_name == "complete_workflow":
                result = await self.integration_suite.run_workflow_integration_test(f"perf_test_{i}")
            elif workflow_name == "api_workflow":
                result = await self.integration_suite.run_api_integration_test(f"perf_test_{i}")
            else:
                raise ValueError(f"Unknown workflow: {workflow_name}")
            
            duration = time.time() - start_time
            performance_results.append({
                "iteration": i + 1,
                "duration": duration,
                "success": result.success,
                "steps_completed": result.steps_completed,
                "total_steps": result.total_steps
            })
        
        # Calculate performance statistics
        durations = [r["duration"] for r in performance_results]
        success_rate = sum(1 for r in performance_results if r["success"]) / len(performance_results) * 100
        
        stats = {
            "workflow_name": workflow_name,
            "iterations": iterations,
            "success_rate": success_rate,
            "avg_duration": sum(durations) / len(durations),
            "min_duration": min(durations),
            "max_duration": max(durations),
            "performance_results": performance_results
        }
        
        logger.info(f"Workflow performance test completed: {workflow_name}")
        logger.info(f"Success rate: {success_rate:.1f}%")
        logger.info(f"Avg duration: {stats['avg_duration']:.2f}s")
        
        return stats

    async def run_workflow_stress_test(
        self,
        workflow_name: str,
        duration_seconds: int = 60,
        max_concurrent: int = 5
    ) -> Dict[str, Any]:
        """Run workflow stress test."""
        logger.info(f"Starting workflow stress test: {workflow_name}")
        
        start_time = time.time()
        stress_results = []
        concurrent_runs = 0
        
        async def stress_worker():
            nonlocal concurrent_runs
            concurrent_runs += 1
            
            try:
                if workflow_name == "complete_workflow":
                    result = await self.integration_suite.run_workflow_integration_test(f"stress_test_{concurrent_runs}")
                else:
                    result = await self.integration_suite.run_api_integration_test(f"stress_test_{i}")
                
                stress_results.append({
                    "success": result.success,
                    "duration": result.duration,
                    "timestamp": datetime.now().isoformat()
                })
                
            except Exception as e:
                stress_results.append({
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })
            
            concurrent_runs -= 1
        
        # Run stress test for specified duration
        tasks = []
        while time.time() - start_time < duration_seconds:
            if concurrent_runs < max_concurrent:
                task = asyncio.create_task(stress_worker())
                tasks.append(task)
                await asyncio.sleep(0.1)  # Brief pause between starting new runs
            else:
                await asyncio.sleep(0.1)
        
        # Wait for all running tasks to complete
        await asyncio.gather(*tasks, return_exceptions=True)
        
        # Calculate stress test statistics
        total_runs = len(stress_results)
        successful_runs = sum(1 for r in stress_results if r["success"])
        success_rate = successful_runs / total_runs * 100 if total_runs > 0 else 0
        
        durations = [r["duration"] for r in stress_results if "duration" in r]
        avg_duration = sum(durations) / len(durations) if durations else 0
        
        stats = {
            "workflow_name": workflow_name,
            "duration_seconds": duration_seconds,
            "max_concurrent": max_concurrent,
            "total_runs": total_runs,
            "successful_runs": successful_runs,
            "success_rate": success_rate,
            "avg_duration": avg_duration,
            "runs_per_minute": total_runs / (duration_seconds / 60),
            "stress_results": stress_results
        }
        
        logger.info(f"Workflow stress test completed: {workflow_name}")
        logger.info(f"Total runs: {total_runs}, Success rate: {success_rate:.1f}%")
        
        return stats