"""
OpenSpec Task Models

Pydantic models for OpenSpec task specifications that bridge requirements to implementation.
"""

from __future__ import annotations

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator

from .requirement import Requirement, Scenario


class TaskStatus(str, Enum):
    """Status of implementation tasks."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


class TaskPriority(str, Enum):
    """Priority levels for tasks."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ImplementationTask(BaseModel):
    """Represents an implementation task derived from requirements."""

    # Core identification
    task_id: str = Field(..., description="Unique task identifier")
    title: str = Field(..., description="Task title")
    description: str = Field(..., description="Detailed task description")

    # Requirement traceability
    requirement_id: str = Field(..., description="ID of the requirement this task fulfills")
    requirement_title: str = Field(..., description="Title of the related requirement")
    scenario_id: Optional[str] = Field(None, description="ID of specific scenario this addresses")

    # Task details
    file_path: Optional[str] = Field(None, description="Target file for implementation")
    implementation_type: str = Field(..., description="Type of implementation (class, function, API, etc.)")

    # Implementation guidance
    acceptance_criteria: List[str] = Field(default_factory=list, description="Acceptance criteria for this task")
    implementation_notes: Optional[str] = Field(None, description="Specific implementation guidance")
    dependencies: List[str] = Field(default_factory=list, description="Task dependencies")

    # Task management
    status: TaskStatus = Field(default=TaskStatus.PENDING, description="Current task status")
    priority: TaskPriority = Field(default=TaskPriority.MEDIUM, description="Task priority")
    estimated_effort: Optional[str] = Field(None, description="Estimated effort (e.g., '2 days', '4 hours')")

    # Technical specifications
    language: Optional[str] = Field(None, description="Programming language")
    framework: Optional[str] = Field(None, description="Framework or technology")
    test_requirements: List[str] = Field(default_factory=list, description="Testing requirements")

    @validator('task_id')
    def validate_task_id(cls, v):
        """Validate task ID format."""
        if not v or not v.strip():
            raise ValueError("Task ID cannot be empty")
        return v.strip()

    @validator('title')
    def validate_title(cls, v):
        """Validate task title."""
        if not v or not v.strip():
            raise ValueError("Task title cannot be empty")
        return v.strip()

    @validator('description')
    def validate_description(cls, v):
        """Validate task description."""
        if not v or not v.strip():
            raise ValueError("Task description cannot be empty")
        return v.strip()

    def to_markdown(self) -> str:
        """Convert task to OpenSpec markdown format."""
        lines = [
            f"### Task: {self.title}",
            f"**Task ID**: {self.task_id}",
            f"**Implementation Type**: {self.implementation_type}",
            f"**Status**: {self.status.value}",
            f"**Priority**: {self.priority.value}",
            ""
        ]

        if self.file_path:
            lines.append(f"**File**: `{self.file_path}`")
            lines.append("")

        lines.append("**Description**:")
        lines.append(self.description)
        lines.append("")

        lines.append(f"**Fulfills Requirement**: {self.requirement_id} - {self.requirement_title}")
        if self.scenario_id:
            lines.append(f"**Addresses Scenario**: {self.scenario_id}")
        lines.append("")

        if self.acceptance_criteria:
            lines.append("**Acceptance Criteria**:")
            for criteria in self.acceptance_criteria:
                lines.append(f"- {criteria}")
            lines.append("")

        if self.dependencies:
            lines.append("**Dependencies**:")
            for dep in self.dependencies:
                lines.append(f"- {dep}")
            lines.append("")

        if self.estimated_effort:
            lines.append(f"**Estimated Effort**: {self.estimated_effort}")
            lines.append("")

        tech_details = []
        if self.language:
            tech_details.append(self.language)
        if self.framework:
            tech_details.append(self.framework)
        if tech_details:
            lines.append(f"**Technology**: {', '.join(tech_details)}")
            lines.append("")

        if self.implementation_notes:
            lines.append("**Implementation Notes**:")
            lines.append(self.implementation_notes)
            lines.append("")

        if self.test_requirements:
            lines.append("**Testing Requirements**:")
            for test_req in self.test_requirements:
                lines.append(f"- {test_req}")
            lines.append("")

        return "\n".join(lines)


class TaskMapping(BaseModel):
    """Maps a requirement to its implementation tasks."""

    requirement_id: str = Field(..., description="ID of the requirement")
    requirement_title: str = Field(..., description="Title of the requirement")
    tasks: List[str] = Field(..., description="List of task IDs that implement this requirement")
    completion_percentage: float = Field(default=0.0, description="Percentage of completion (0-100)")

    @validator('completion_percentage')
    def validate_completion_percentage(cls, v):
        """Validate completion percentage range."""
        if not 0 <= v <= 100:
            raise ValueError("Completion percentage must be between 0 and 100")
        return v


class OpenSpecTaskSpecification(BaseModel):
    """Complete OpenSpec task specification for implementation phase."""

    name: str = Field(..., description="Name of the task specification")
    version: str = Field(default="1.0", description="Specification version")
    description: str = Field(..., description="Description of the implementation work")

    # Implementation tasks
    implementation_tasks: List[ImplementationTask] = Field(default_factory=list, description="List of implementation tasks")

    # Requirement mappings
    requirement_mappings: List[TaskMapping] = Field(default_factory=list, description="Mappings from requirements to tasks")

    # Development specifications
    package_dependencies: List[str] = Field(default_factory=list, description="Required packages")
    api_specifications: Optional[str] = Field(None, description="API specifications")
    shared_knowledge: Optional[str] = Field(None, description="Shared development knowledge")

    # Progress tracking
    total_tasks: int = Field(default=0, description="Total number of tasks")
    completed_tasks: int = Field(default=0, description="Number of completed tasks")
    overall_progress: float = Field(default=0.0, description="Overall progress percentage")

    # Metadata
    created_at: Optional[str] = Field(None, description="Creation timestamp")
    updated_at: Optional[str] = Field(None, description="Last update timestamp")
    authors: List[str] = Field(default_factory=list, description="Authors of the specification")

    # Dependencies
    prerequisite_tasks: List[str] = Field(default_factory=list, description="Prerequisite tasks")
    blocked_tasks: List[str] = Field(default_factory=list, description="Blocked tasks")

    @validator('name')
    def validate_name(cls, v):
        """Validate specification name."""
        if not v or not v.strip():
            raise ValueError("Specification name cannot be empty")
        return v.strip()

    def add_task(self, task: ImplementationTask):
        """Add a task to the specification."""
        self.implementation_tasks.append(task)
        self._update_progress()

    def _update_progress(self):
        """Update progress tracking."""
        self.total_tasks = len(self.implementation_tasks)
        self.completed_tasks = len([t for t in self.implementation_tasks if t.status == TaskStatus.COMPLETED])

        if self.total_tasks > 0:
            self.overall_progress = (self.completed_tasks / self.total_tasks) * 100

    def get_tasks_by_requirement(self, requirement_id: str) -> List[ImplementationTask]:
        """Get all tasks for a specific requirement."""
        return [task for task in self.implementation_tasks if task.requirement_id == requirement_id]

    def get_tasks_by_status(self, status: TaskStatus) -> List[ImplementationTask]:
        """Get tasks by their status."""
        return [task for task in self.implementation_tasks if task.status == status]

    def get_next_tasks(self, limit: int = 5) -> List[ImplementationTask]:
        """Get next tasks to work on (pending tasks sorted by priority)."""
        pending_tasks = self.get_tasks_by_status(TaskStatus.PENDING)
        # Sort by priority (critical > high > medium > low)
        priority_order = {TaskPriority.CRITICAL: 0, TaskPriority.HIGH: 1, TaskPriority.MEDIUM: 2, TaskPriority.LOW: 3}
        pending_tasks.sort(key=lambda t: priority_order.get(t.priority, 3))
        return pending_tasks[:limit]

    def update_requirement_mappings(self):
        """Update requirement mappings based on current tasks."""
        # Group tasks by requirement
        req_tasks = {}
        for task in self.implementation_tasks:
            if task.requirement_id not in req_tasks:
                req_tasks[task.requirement_id] = {
                    'title': task.requirement_title,
                    'tasks': [],
                    'completed': 0
                }
            req_tasks[task.requirement_id]['tasks'].append(task.task_id)
            if task.status == TaskStatus.COMPLETED:
                req_tasks[task.requirement_id]['completed'] += 1

        # Create mappings
        self.requirement_mappings = []
        for req_id, info in req_tasks.items():
            completion = (info['completed'] / len(info['tasks'])) * 100 if info['tasks'] else 0
            self.requirement_mappings.append(TaskMapping(
                requirement_id=req_id,
                requirement_title=info['title'],
                tasks=info['tasks'],
                completion_percentage=completion
            ))

    def validate_task_dependencies(self) -> List[str]:
        """Validate that task dependencies are valid."""
        errors = []
        task_ids = {task.task_id for task in self.implementation_tasks}

        for task in self.implementation_tasks:
            for dep_id in task.dependencies:
                if dep_id not in task_ids:
                    errors.append(f"Task '{task.task_id}' depends on non-existent task '{dep_id}'")

        return errors

    def to_markdown(self) -> str:
        """Convert task specification to OpenSpec markdown format."""
        lines = [f"# {self.name}"]

        if self.description:
            lines.append(self.description)
            lines.append("")

        # Progress overview
        lines.append("## Implementation Progress")
        lines.append(f"- **Total Tasks**: {self.total_tasks}")
        lines.append(f"- **Completed**: {self.completed_tasks}")
        lines.append(f"- **Overall Progress**: {self.overall_progress:.1f}%")
        lines.append("")

        # Implementation Tasks
        if self.implementation_tasks:
            lines.append("## Implementation Tasks")
            lines.append("")

            # Group by requirement
            tasks_by_req = {}
            for task in self.implementation_tasks:
                if task.requirement_id not in tasks_by_req:
                    tasks_by_req[task.requirement_id] = []
                tasks_by_req[task.requirement_id].append(task)

            for req_id, tasks in tasks_by_req.items():
                lines.append(f"### For Requirement: {req_id}")
                lines.append("")
                for task in tasks:
                    lines.append(task.to_markdown())
                    lines.append("")

        # Requirement Mappings
        if self.requirement_mappings:
            lines.append("## Requirement to Task Mappings")
            lines.append("")
            for mapping in self.requirement_mappings:
                lines.append(f"### {mapping.requirement_id}")
                lines.append(f"**Tasks**: {', '.join(mapping.tasks)}")
                lines.append(f"**Completion**: {mapping.completion_percentage:.1f}%")
                lines.append("")

        # Development Specifications
        if self.package_dependencies or self.api_specifications or self.shared_knowledge:
            lines.append("## Development Specifications")
            lines.append("")

            if self.package_dependencies:
                lines.append("### Package Dependencies")
                for dep in self.package_dependencies:
                    lines.append(f"- {dep}")
                lines.append("")

            if self.api_specifications:
                lines.append("### API Specifications")
                lines.append("```yaml")
                lines.append(self.api_specifications)
                lines.append("```")
                lines.append("")

            if self.shared_knowledge:
                lines.append("### Shared Knowledge")
                lines.append(self.shared_knowledge)
                lines.append("")

        return "\n".join(lines).rstrip()

    def get_validation_errors(self) -> List[str]:
        """Get validation errors for this task specification."""
        errors = []

        if not self.implementation_tasks:
            errors.append("Task specification must have at least one implementation task")

        # Validate task dependencies
        errors.extend(self.validate_task_dependencies())

        # Validate each task
        for i, task in enumerate(self.implementation_tasks):
            try:
                task.dict()  # This will trigger Pydantic validation
            except Exception as e:
                errors.append(f"Implementation task {i+1} validation error: {str(e)}")

        # Check for circular dependencies
        errors.extend(self._check_circular_dependencies())

        return errors

    def _check_circular_dependencies(self) -> List[str]:
        """Check for circular dependencies between tasks."""
        visited = set()
        rec_stack = set()
        cycles = []

        def dfs(task_id: str, path: List[str]) -> bool:
            if task_id in rec_stack:
                cycle_start = path.index(task_id)
                cycles.append(path[cycle_start:] + [task_id])
                return True

            if task_id in visited:
                return False

            visited.add(task_id)
            rec_stack.add(task_id)
            path.append(task_id)

            # Find task and check its dependencies
            task = next((t for t in self.implementation_tasks if t.task_id == task_id), None)
            if task:
                for dep_id in task.dependencies:
                    if dfs(dep_id, path.copy()):
                        return True

            rec_stack.remove(task_id)
            return False

        for task in self.implementation_tasks:
            if task.task_id not in visited:
                dfs(task.task_id, [])

        return [f"Circular dependency detected: {' -> '.join(cycle)}" for cycle in cycles]