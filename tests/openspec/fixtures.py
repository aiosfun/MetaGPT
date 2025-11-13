"""
OpenSpec Test Fixtures and Data Generators

Provides comprehensive test fixtures, data generators, and mock objects
for testing OpenSpec components.
"""

import random
import string
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
import json
import yaml

from metagpt.openspec.models.requirement import Requirement, Scenario
from metagpt.openspec.models.design import DesignComponent, RequirementMapping, CrossReference
from metagpt.openspec.models.task import ImplementationTask, TaskStatus, TaskPriority


@dataclass
class TestConfiguration:
    """Test configuration data structure."""
    test_name: str
    test_type: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    expected_results: Dict[str, Any] = field(default_factory=dict)
    mock_data: Dict[str, Any] = field(default_factory=dict)


class OpenSpecTestFixture:
    """
    Provides test fixtures for OpenSpec components.
    
    Includes sample requirements, designs, tasks, and other test data
    that can be used across different test suites.
    """
    
    def __init__(self):
        """Initialize test fixture with default data."""
        self.sample_requirements = self._create_sample_requirements()
        self.sample_designs = self._create_sample_designs()
        self.sample_tasks = self._create_sample_tasks()
        self.test_configurations = self._create_test_configurations()
    
    def _create_sample_requirements(self) -> List[Requirement]:
        """Create sample requirement fixtures."""
        return [
            Requirement(
                id="REQ-001",
                title="User Authentication",
                description="The system SHALL authenticate users before granting access to protected resources",
                priority="high",
                acceptance_criteria=[
                    "Users can register with email and password",
                    "Users can login with valid credentials",
                    "Invalid login attempts are rejected with appropriate error messages",
                    "Sessions expire after inactivity timeout",
                    "Password reset functionality is available"
                ],
                scenarios=[
                    Scenario(
                        given="a new user wants to register",
                        when="the user provides valid email and password",
                        then="the system creates a new account and sends confirmation email"
                    ),
                    Scenario(
                        given="a registered user wants to login",
                        when="the user provides valid credentials",
                        then="the system authenticates the user and creates a session"
                    ),
                    Scenario(
                        given="a user provides invalid credentials",
                        when="the user attempts to login",
                        then="the system rejects the attempt with appropriate error message"
                    )
                ]
            ),
            Requirement(
                id="REQ-002",
                title="Data Storage",
                description="The system SHALL store user data securely and maintain data integrity",
                priority="high",
                acceptance_criteria=[
                    "User data is encrypted at rest",
                    "Data backups are performed daily",
                    "Personal information is protected according to privacy regulations",
                    "Data retention policies are enforced",
                    "Audit logs are maintained for data access"
                ],
                scenarios=[
                    Scenario(
                        given="user data needs to be stored",
                        when="the system processes user information",
                        then="the data is encrypted and stored in the database"
                    )
                ]
            ),
            Requirement(
                id="REQ-003",
                title="API Access",
                description="The system SHALL provide RESTful API for external integrations",
                priority="medium",
                acceptance_criteria=[
                    "API endpoints follow REST conventions",
                    "API documentation is available and up-to-date",
                    "Rate limiting is implemented to prevent abuse",
                    "API authentication is required for protected endpoints",
                    "API responses include appropriate status codes and error messages"
                ],
                scenarios=[
                    Scenario(
                        given="an external service needs to access system data",
                        when="the service makes an authenticated API request",
                        then="the system returns the requested data in JSON format"
                    )
                ]
            )
        ]
    
    def _create_sample_designs(self) -> List[Dict[str, Any]]:
        """Create sample design fixtures."""
        return [
            {
                "name": "Authentication Service",
                "components": [
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
                            },
                            {
                                "name": "register_api",
                                "description": "REST API for user registration",
                                "input_type": "RegisterRequest",
                                "output_type": "UserResponse",
                                "protocol": "HTTP/REST",
                                "endpoint": "/api/auth/register"
                            }
                        ],
                        dependencies=["Database", "Email Service", "Cache Service"],
                        sub_components=["Login Handler", "Registration Handler", "Session Manager"],
                        technology="Python/FastAPI",
                        behavior="Processes authentication requests and manages user sessions",
                        performance_requirements="< 200ms response time for 95% of requests",
                        security_considerations="Input validation, rate limiting, secure password storage"
                    ),
                    DesignComponent(
                        name="Database",
                        purpose="Store persistent application data",
                        element_type="data_store",
                        description="PostgreSQL database for user data and application state",
                        interfaces=[
                            {
                                "name": "data_access",
                                "description": "Database connection interface",
                                "input_type": "Query",
                                "output_type": "ResultSet",
                                "protocol": "SQL"
                            }
                        ],
                        dependencies=["Backup Service"],
                        technology="PostgreSQL",
                        behavior="Stores and retrieves application data",
                        performance_requirements="< 100ms query response time",
                        security_considerations="Connection encryption, access controls"
                    )
                ],
                "mappings": [
                    RequirementMapping(
                        requirement_id="REQ-001",
                        requirement_title="User Authentication",
                        design_elements=["Authentication Service", "Database"],
                        implementation_notes="Use JWT tokens for session management, bcrypt for password hashing",
                        verification_method="Unit tests, integration tests, security audits"
                    ),
                    RequirementMapping(
                        requirement_id="REQ-002",
                        requirement_title="Data Storage",
                        design_elements=["Database"],
                        implementation_notes="Implement field-level encryption for sensitive data",
                        verification_method="Data encryption tests, backup verification tests"
                    )
                ]
            }
        ]
    
    def _create_sample_tasks(self) -> List[ImplementationTask]:
        """Create sample task fixtures."""
        return [
            ImplementationTask(
                id="TASK-001",
                title="Implement Authentication Service",
                description="Create the authentication service with login and registration endpoints",
                requirement_ids=["REQ-001"],
                status=TaskStatus.PENDING,
                priority=TaskPriority.HIGH,
                estimated_hours=24,
                dependencies=["TASK-002"],  # Database setup
                assignee="backend_developer_1",
                acceptance_criteria=[
                    "Authentication service is created using FastAPI",
                    "Login endpoint is implemented with proper validation",
                    "Registration endpoint is implemented with email verification",
                    "JWT token management is working correctly",
                    "Error handling is implemented for all edge cases",
                    "Unit tests achieve >90% coverage"
                ],
                deliverables=[
                    "Authentication service source code",
                    "API documentation",
                    "Unit and integration tests",
                    "Deployment configuration"
                ],
                progress_percentage=0,
                notes="Waiting for database schema to be finalized"
            ),
            ImplementationTask(
                id="TASK-002",
                title="Setup Database Schema",
                description="Configure PostgreSQL database and create user tables with proper indexes",
                requirement_ids=["REQ-002"],
                status=TaskStatus.PENDING,
                priority=TaskPriority.HIGH,
                estimated_hours=16,
                dependencies=[],
                assignee="database_admin",
                acceptance_criteria=[
                    "PostgreSQL database is created and configured",
                    "User tables are created with proper constraints",
                    "Indexes are created for performance optimization",
                    "Database migration scripts are prepared",
                    "Backup procedures are documented and tested"
                ],
                deliverables=[
                    "Database schema definition",
                    "Migration scripts",
                    "Backup and restore procedures",
                    "Database documentation"
                ],
                progress_percentage=0,
                notes="Database server is ready for configuration"
            ),
            ImplementationTask(
                id="TASK-003",
                title="Implement API Documentation",
                description="Create comprehensive API documentation using OpenAPI specification",
                requirement_ids=["REQ-003"],
                status=TaskStatus.PENDING,
                priority=TaskPriority.MEDIUM,
                estimated_hours=12,
                dependencies=["TASK-001"],
                assignee="technical_writer",
                acceptance_criteria=[
                    "OpenAPI 3.0 specification is created",
                    "Interactive API documentation is available",
                    "Code examples are provided for all endpoints",
                    "Authentication documentation is clear",
                    "Error response documentation is complete"
                ],
                deliverables=[
                    "OpenAPI specification file",
                    "Interactive documentation portal",
                    "API usage examples",
                    "Postman collection"
                ],
                progress_percentage=0,
                notes="Will start after authentication service is implemented"
            )
        ]
    
    def _create_test_configurations(self) -> List[TestConfiguration]:
        """Create test configuration fixtures."""
        return [
            TestConfiguration(
                test_name="requirement_validation",
                test_type="unit",
                parameters={
                    "validate_scenarios": True,
                    "validate_acceptance_criteria": True,
                    "require_unique_ids": True
                },
                expected_results={
                    "valid_requirements": 3,
                    "validation_errors": 0
                }
            ),
            TestConfiguration(
                test_name="design_traceability",
                test_type="integration",
                parameters={
                    "check_requirement_coverage": True,
                    "validate_component_dependencies": True
                },
                expected_results={
                    "coverage_percentage": 100,
                    "traceability_errors": 0
                }
            ),
            TestConfiguration(
                test_name="performance_benchmark",
                test_type="performance",
                parameters={
                    "concurrent_users": 100,
                    "duration_seconds": 60,
                    "response_time_threshold": 500
                },
                expected_results={
                    "avg_response_time": "< 500ms",
                    "success_rate": "> 99%"
                }
            )
        ]
    
    def get_requirement_fixture(self, requirement_id: str = None) -> Optional[Requirement]:
        """Get a specific requirement fixture by ID."""
        if requirement_id:
            for req in self.sample_requirements:
                if req.id == requirement_id:
                    return req
        return self.sample_requirements[0] if self.sample_requirements else None
    
    def get_design_fixture(self, design_name: str = None) -> Optional[Dict[str, Any]]:
        """Get a specific design fixture by name."""
        if design_name:
            for design in self.sample_designs:
                if design.get("name") == design_name:
                    return design
        return self.sample_designs[0] if self.sample_designs else None
    
    def get_task_fixture(self, task_id: str = None) -> Optional[ImplementationTask]:
        """Get a specific task fixture by ID."""
        if task_id:
            for task in self.sample_tasks:
                if task.id == task_id:
                    return task
        return self.sample_tasks[0] if self.sample_tasks else None
    
    def get_test_configuration(self, test_name: str = None) -> Optional[TestConfiguration]:
        """Get a specific test configuration by name."""
        if test_name:
            for config in self.test_configurations:
                if config.test_name == test_name:
                    return config
        return self.test_configurations[0] if self.test_configurations else None


class TestDataGenerator:
    """
    Generates test data for OpenSpec components.
    
    Provides methods to create realistic test data including requirements,
    designs, tasks, and various edge cases for comprehensive testing.
    """
    
    def __init__(self, seed: int = None):
        """Initialize data generator with optional seed for reproducibility."""
        self.random = random.Random(seed)
    
    def generate_requirement(
        self,
        requirement_id: str = None,
        title: str = None,
        priority: str = None,
        scenario_count: int = None
    ) -> Requirement:
        """Generate a random requirement for testing."""
        requirement_id = requirement_id or f"REQ-{self.random.randint(1000, 9999)}"
        
        titles = [
            "User Management", "Data Processing", "API Integration", "Security Features",
            "Performance Optimization", "Reporting System", "Notification Service",
            "File Upload", "Search Functionality", "Dashboard Analytics"
        ]
        title = title or self.random.choice(titles)
        
        priorities = ["low", "medium", "high", "critical"]
        priority = priority or self.random.choice(priorities)
        
        scenario_count = scenario_count or self.random.randint(1, 4)
        scenarios = [
            self._generate_scenario() for _ in range(scenario_count)
        ]
        
        acceptance_criteria_count = self.random.randint(2, 6)
        acceptance_criteria = [
            f"Criterion {i+1}: {self._generate_sentence()}"
            for i in range(acceptance_criteria_count)
        ]
        
        return Requirement(
            id=requirement_id,
            title=title,
            description=f"The system SHALL {title.lower()} with proper functionality and security",
            priority=priority,
            acceptance_criteria=acceptance_criteria,
            scenarios=scenarios
        )
    
    def generate_design_component(
        self,
        name: str = None,
        element_type: str = None,
        dependency_count: int = None
    ) -> DesignComponent:
        """Generate a random design component for testing."""
        name = name or f"{self._generate_component_name()} Service"
        
        element_types = ["service", "component", "module", "data_store", "interface"]
        element_type = element_type or self.random.choice(element_types)
        
        dependency_count = dependency_count or self.random.randint(0, 3)
        dependencies = [
            self._generate_component_name() for _ in range(dependency_count)
        ]
        
        interface_count = self.random.randint(1, 3)
        interfaces = [
            {
                "name": f"{name.lower().replace(' ', '_')}_api_{i+1}",
                "description": f"API interface {i+1} for {name}",
                "input_type": f"Request{i+1}",
                "output_type": f"Response{i+1}",
                "protocol": "HTTP/REST"
            }
            for i in range(interface_count)
        ]
        
        technologies = ["Python/FastAPI", "Node.js/Express", "Java/Spring", "Go", "Python/Django"]
        technology = self.random.choice(technologies)
        
        return DesignComponent(
            name=name,
            purpose=f"Handle {name.lower()} functionality",
            element_type=element_type,
            description=f"Component responsible for {name.lower()} operations",
            interfaces=interfaces,
            dependencies=dependencies,
            technology=technology,
            behavior=f"Processes {name.lower()} requests and returns appropriate responses",
            performance_requirements=f"< {self.random.randint(50, 500)}ms response time",
            security_considerations="Input validation, authentication, authorization"
        )
    
    def generate_implementation_task(
        self,
        task_id: str = None,
        title: str = None,
        priority: TaskPriority = None,
        requirement_count: int = None
    ) -> ImplementationTask:
        """Generate a random implementation task for testing."""
        task_id = task_id or f"TASK-{self.random.randint(1000, 9999)}"
        
        titles = [
            "Implement User Authentication", "Create Database Schema", "Build API Endpoints",
            "Design User Interface", "Setup Testing Framework", "Configure Deployment",
            "Optimize Performance", "Add Security Features", "Create Documentation"
        ]
        title = title or self.random.choice(titles)
        
        priorities = list(TaskPriority)
        priority = priority or self.random.choice(priorities)
        
        requirement_count = requirement_count or self.random.randint(1, 3)
        requirement_ids = [f"REQ-{self.random.randint(1000, 9999)}" for _ in range(requirement_count)]
        
        estimated_hours = self.random.randint(8, 40)
        
        acceptance_criteria_count = self.random.randint(3, 7)
        acceptance_criteria = [
            f"Task requirement {i+1} is completed and tested"
            for i in range(acceptance_criteria_count)
        ]
        
        deliverable_count = self.random.randint(2, 5)
        deliverables = [
            f"Deliverable {i+1}: {self._generate_deliverable_type()}"
            for i in range(deliverable_count)
        ]
        
        return ImplementationTask(
            id=task_id,
            title=title,
            description=f"Complete implementation of {title.lower()} with all required functionality",
            requirement_ids=requirement_ids,
            status=TaskStatus.PENDING,
            priority=priority,
            estimated_hours=estimated_hours,
            dependencies=[f"TASK-{self.random.randint(1000, 9999)}" for _ in range(self.random.randint(0, 2))],
            assignee=f"developer_{self.random.randint(1, 5)}",
            acceptance_criteria=acceptance_criteria,
            deliverables=deliverables,
            progress_percentage=0
        )
    
    def generate_test_dataset(
        self,
        requirement_count: int = 10,
        design_count: int = 5,
        task_count: int = 15
    ) -> Dict[str, List[Any]]:
        """Generate a complete test dataset."""
        requirements = [
            self.generate_requirement() for _ in range(requirement_count)
        ]
        
        designs = [
            self.generate_design_component() for _ in range(design_count)
        ]
        
        tasks = [
            self.generate_implementation_task() for _ in range(task_count)
        ]
        
        return {
            "requirements": requirements,
            "designs": designs,
            "tasks": tasks
        }
    
    def _generate_scenario(self) -> Scenario:
        """Generate a random scenario."""
        givens = [
            "a user wants to perform an action",
            "the system receives a request",
            "data needs to be processed",
            "an error condition occurs",
            "a resource is not available"
        ]
        
        whens = [
            "the user provides valid input",
            "the system processes the request",
            "the operation is executed",
            "validation is performed",
            "the resource is accessed"
        ]
        
        thens = [
            "the system returns the expected result",
            "the operation completes successfully",
            "an appropriate response is generated",
            "the user is notified of the outcome",
            "the system state is updated"
        ]
        
        return Scenario(
            given=self.random.choice(givens),
            when=self.random.choice(whens),
            then=self.random.choice(thens)
        )
    
    def _generate_sentence(self) -> str:
        """Generate a random sentence for test data."""
        subjects = ["The system", "Users", "Administrators", "The application", "Data"]
        verbs = ["must", "should", "will", "shall", "can"]
        objects = [
            "process requests efficiently",
            "maintain data integrity",
            "provide secure access",
            "ensure performance standards",
            "handle error conditions"
        ]
        
        return f"{self.random.choice(subjects)} {self.random.choice(verbs)} {self.random.choice(objects)}."
    
    def _generate_component_name(self) -> str:
        """Generate a random component name."""
        prefixes = ["User", "Auth", "Data", "Payment", "Notification", "Search", "Report", "File"]
        suffixes = ["Service", "Manager", "Handler", "Processor", "Controller", "Engine"]
        
        return f"{self.random.choice(prefixes)}{self.random.choice(suffixes)}"
    
    def _generate_deliverable_type(self) -> str:
        """Generate a random deliverable type."""
        deliverables = [
            "Source code implementation",
            "Unit tests",
            "Integration tests",
            "API documentation",
            "User manual",
            "Deployment scripts",
            "Configuration files",
            "Performance benchmarks"
        ]
        
        return self.random.choice(deliverables)


class MockDataFactory:
    """
    Factory for creating mock objects and test doubles.
    
    Provides various mock objects for testing OpenSpec components
    without requiring actual dependencies.
    """
    
    @staticmethod
    def create_mock_llm_response(text: str = "Mock response") -> Any:
        """Create a mock LLM response object."""
        from unittest.mock import Mock
        
        mock_response = Mock()
        mock_response.content = text
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = text
        return mock_response
    
    @staticmethod
    def create_mock_database_connection() -> Any:
        """Create a mock database connection."""
        from unittest.mock import Mock, AsyncMock
        
        mock_conn = Mock()
        mock_conn.execute = AsyncMock(return_value=Mock(fetchall=AsyncMock(return_value=[])))
        mock_conn.commit = AsyncMock()
        mock_conn.rollback = AsyncMock()
        return mock_conn
    
    @staticmethod
    def create_mock_file_system() -> Dict[str, Any]:
        """Create a mock file system structure."""
        return {
            "/project": {
                "type": "directory",
                "children": {
                    "src": {
                        "type": "directory",
                        "children": {
                            "main.py": {"type": "file", "content": "print('Hello World')"},
                            "utils.py": {"type": "file", "content": "def helper(): pass"}
                        }
                    },
                    "tests": {
                        "type": "directory",
                        "children": {
                            "test_main.py": {"type": "file", "content": "def test_main(): pass"}
                        }
                    },
                    "README.md": {"type": "file", "content": "# Test Project"}
                }
            }
        }
    
    @staticmethod
    def create_mock_git_repository() -> Any:
        """Create a mock Git repository object."""
        from unittest.mock import Mock
        
        mock_repo = Mock()
        mock_repo.active_branch.name = "main"
        mock_repo.remotes.origin.url = "https://github.com/test/repo.git"
        mock_repo.head.commit.hexsha = "abc123"
        mock_repo.untracked_files = []
        mock_repo.is_dirty.return_value = False
        return mock_repo