"""
Task Implementation Traceability Manager

Manages single-path traceability following requirement→design→task→implementation chain.
"""

from __future__ import annotations

from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path
import json

from ..models.task import OpenSpecTaskSpecification, ImplementationTask, TaskStatus
from ..models.requirement import OpenSpecRequirement
from ..models.design import OpenSpecDesign


@dataclass
class ImplementationArtifact:
    """Represents an implementation artifact (file, code, test, etc.)."""
    artifact_id: str
    artifact_type: str  # source_code, test, documentation, config
    file_path: str
    task_ids: List[str]
    description: Optional[str] = None
    created_at: Optional[str] = None
    checksum: Optional[str] = None


@dataclass
class TraceLink:
    """Represents a traceability link between elements."""
    source_id: str
    source_type: str  # requirement, task, artifact
    target_id: str
    target_type: str
    link_type: str  # implements, tests, documents, depends_on
    description: Optional[str] = None
    strength: str = "strong"  # strong, weak, indirect


class TaskTraceabilityManager:
    """Manages single-path traceability following requirement→design→task chain."""

    def __init__(self):
        """Initialize the traceability manager."""
        self.design_specifications: Dict[str, OpenSpecDesign] = {}
        self.task_specifications: Dict[str, OpenSpecTaskSpecification] = {}
        self.requirement_specifications: Dict[str, OpenSpecRequirement] = {}
        self.implementation_artifacts: Dict[str, ImplementationArtifact] = {}
        self.trace_links: List[TraceLink] = []

        # Single-path traceability mappings
        self.requirement_to_design_mappings: Dict[str, List[str]] = {}
        self.design_to_task_mappings: Dict[str, List[str]] = {}

    def add_design_specification(self, design_spec: OpenSpecDesign):
        """Add a design specification to manage.

        Args:
            design_spec: The design specification to add
        """
        self.design_specifications[design_spec.name] = design_spec

        # Initialize design to task mapping
        self.design_to_task_mappings[design_spec.name] = []

    def add_task_specification(self, task_spec: OpenSpecTaskSpecification):
        """Add a task specification to manage.

        Args:
            task_spec: The task specification to add
        """
        self.task_specifications[task_spec.name] = task_spec

        # Create automatic trace links from design components to tasks
        for task in task_spec.implementation_tasks:
            self.add_trace_link(
                source_id=task.design_id if hasattr(task, 'design_id') else "unknown_design",
                source_type="design",
                target_id=task.task_id,
                target_type="task",
                link_type="implements",
                description=f"Task '{task.title}' implements design component"
            )

    def add_requirement_specification(self, req_spec: OpenSpecRequirement):
        """Add a requirement specification to manage.

        Args:
            req_spec: The requirement specification to add
        """
        self.requirement_specifications[req_spec.name] = req_spec

    def add_implementation_artifact(self, artifact: ImplementationArtifact):
        """Add an implementation artifact to manage.

        Args:
            artifact: The implementation artifact to add
        """
        self.implementation_artifacts[artifact.artifact_id] = artifact

        # Create automatic trace links from tasks to artifacts
        for task_id in artifact.task_ids:
            self.add_trace_link(
                source_id=task_id,
                source_type="task",
                target_id=artifact.artifact_id,
                target_type="artifact",
                link_type="implemented_in",
                description=f"Task implemented in {artifact.file_path}"
            )

    def add_requirement_to_design_mapping(self, requirement_id: str, design_id: str):
        """Add requirement→design mapping following the single traceability path.

        Args:
            requirement_id: ID of the requirement
            design_id: ID of the design component that covers this requirement
        """
        if requirement_id not in self.requirement_to_design_mappings:
            self.requirement_to_design_mappings[requirement_id] = []
        if design_id not in self.requirement_to_design_mappings[requirement_id]:
            self.requirement_to_design_mappings[requirement_id].append(design_id)

        self.add_trace_link(
            source_id=requirement_id,
            source_type="requirement",
            target_id=design_id,
            target_type="design",
            link_type="covered_by",
            description=f"Requirement covered by design component"
        )

    def add_design_to_task_mapping(self, design_id: str, task_id: str):
        """Add design→task mapping following the single traceability path.

        Args:
            design_id: ID of the design component
            task_id: ID of the implementation task
        """
        if design_id not in self.design_to_task_mappings:
            self.design_to_task_mappings[design_id] = []
        if task_id not in self.design_to_task_mappings[design_id]:
            self.design_to_task_mappings[design_id].append(task_id)

        self.add_trace_link(
            source_id=design_id,
            source_type="design",
            target_id=task_id,
            target_type="task",
            link_type="implemented_by",
            description=f"Design component implemented by task"
        )

    def add_trace_link(
        self,
        source_id: str,
        source_type: str,
        target_id: str,
        target_type: str,
        link_type: str,
        description: Optional[str] = None,
        strength: str = "strong"
    ):
        """Add a traceability link.

        Args:
            source_id: Source element ID
            source_type: Source element type
            target_id: Target element ID
            target_type: Target element type
            link_type: Type of link
            description: Link description
            strength: Link strength
        """
        link = TraceLink(
            source_id=source_id,
            source_type=source_type,
            target_id=target_id,
            target_type=target_type,
            link_type=link_type,
            description=description,
            strength=strength
        )
        self.trace_links.append(link)

    def get_requirement_to_design_traceability(self, requirement_id: str) -> Dict[str, any]:
        """Get design components that cover this requirement.

        Args:
            requirement_id: ID of the requirement

        Returns:
            Dictionary with requirement→design mapping and coverage analysis
        """
        design_components = self.requirement_to_design_mappings.get(requirement_id, [])

        return {
            "requirement_id": requirement_id,
            "covering_designs": design_components,
            "design_count": len(design_components),
            "has_design_coverage": len(design_components) > 0,
            "design_details": []
        }

    def get_design_to_task_traceability(self, design_id: str) -> Dict[str, any]:
        """Get implementation tasks derived from this design component.

        Args:
            design_id: ID of the design component

        Returns:
            Dictionary with design→task mapping and progress tracking
        """
        tasks = self.design_to_task_mappings.get(design_id, [])

        # Get task completion status
        completed_tasks = 0
        total_tasks = len(tasks)
        task_details = []

        for task_id in tasks:
            task_info = {"task_id": task_id, "status": "unknown"}
            for task_spec in self.task_specifications.values():
                for task in task_spec.implementation_tasks:
                    if task.task_id == task_id:
                        task_info.update({
                            "title": task.title,
                            "status": task.status.value,
                            "description": task.description
                        })
                        if task.status == TaskStatus.COMPLETED:
                            completed_tasks += 1
                        break
            task_details.append(task_info)

        return {
            "design_id": design_id,
            "implementation_tasks": tasks,
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "task_completion_percentage": (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0,
            "has_task_coverage": len(tasks) > 0,
            "task_details": task_details
        }

    def get_requirement_to_task_coverage(self) -> Dict[str, Dict[str, any]]:
        """Get coverage analysis following requirement→design→task chain.

        Returns:
            Dictionary with requirement coverage information derived through design components
        """
        coverage = {}

        # Get all requirements from all specifications
        all_requirements = {}
        for req_spec in self.requirement_specifications.values():
            for req in req_spec.get_all_requirements():
                # Create a simple ID for the requirement
                req_id = f"{req_spec.name}_{req.title.lower().replace(' ', '_')}"
                all_requirements[req_id] = req

        # Analyze each requirement through the design→task chain
        for req_id, req in all_requirements.items():
            req_trace = self.get_requirement_to_design_traceability(req_id)

            total_tasks = 0
            completed_tasks = 0
            all_task_details = []

            # Get tasks through design components
            for design_id in req_trace["covering_designs"]:
                design_trace = self.get_design_to_task_traceability(design_id)
                total_tasks += design_trace["total_tasks"]
                completed_tasks += design_trace["completed_tasks"]
                all_task_details.extend(design_trace["task_details"])

            coverage[req_id] = {
                "requirement_title": req.title,
                "covering_designs": req_trace["covering_designs"],
                "design_count": req_trace["design_count"],
                "total_tasks": total_tasks,
                "completed_tasks": completed_tasks,
                "coverage_percentage": (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0,
                "fully_covered": req_trace["has_design_coverage"] and total_tasks > 0,
                "has_design_coverage": req_trace["has_design_coverage"],
                "task_details": all_task_details
            }

        return coverage

    def get_task_to_artifact_traceability(self, task_id: str) -> List[ImplementationArtifact]:
        """Get implementation artifacts for a specific task.

        Args:
            task_id: ID of the task

        Returns:
            List of implementation artifacts
        """
        artifacts = []
        for link in self.trace_links:
            if link.source_id == task_id and link.source_type == "task" and link.target_type == "artifact":
                artifact = self.implementation_artifacts.get(link.target_id)
                if artifact:
                    artifacts.append(artifact)
        return artifacts

    def get_end_to_end_traceability(self, requirement_id: str) -> Dict[str, any]:
        """Get end-to-end traceability following requirement→design→task→implementation chain.

        Args:
            requirement_id: ID of the requirement

        Returns:
            End-to-end traceability information following the single path
        """
        traceability = {
            "requirement_id": requirement_id,
            "designs": [],
            "total_tasks": 0,
            "completed_tasks": 0,
            "total_artifacts": 0,
            "traceability_chain_complete": False
        }

        # Step 1: Get design components that cover this requirement
        req_to_design = self.get_requirement_to_design_traceability(requirement_id)
        if not req_to_design["has_design_coverage"]:
            return traceability  # No design coverage, chain broken

        # Step 2: For each design component, get implementation tasks
        all_tasks = []
        for design_id in req_to_design["covering_designs"]:
            design_to_task = self.get_design_to_task_traceability(design_id)

            design_info = {
                "design_id": design_id,
                "tasks": design_to_task["task_details"],
                "task_count": design_to_task["total_tasks"],
                "completed_tasks": design_to_task["completed_tasks"],
                "artifacts": []
            }

            # Step 3: For each task, get implementation artifacts
            for task_detail in design_to_task["task_details"]:
                task_id = task_detail["task_id"]
                task_artifacts = self.get_task_to_artifact_traceability(task_id)

                task_info = {
                    **task_detail,
                    "artifacts": [{
                        "artifact_id": artifact.artifact_id,
                        "file_path": artifact.file_path,
                        "type": artifact.artifact_type,
                        "description": artifact.description
                    } for artifact in task_artifacts]
                }

                design_info["artifacts"].extend(task_info["artifacts"])

            traceability["designs"].append(design_info)
            traceability["total_tasks"] += design_info["task_count"]
            traceability["completed_tasks"] += design_info["completed_tasks"]
            traceability["total_artifacts"] += len(design_info["artifacts"])

        # Check if traceability chain is complete
        traceability["traceability_chain_complete"] = (
            req_to_design["has_design_coverage"] and
            traceability["total_tasks"] > 0
        )

        return traceability

    def analyze_implementation_gaps(self) -> Dict[str, List[str]]:
        """Analyze gaps in the requirement→design→task traceability chain.

        Returns:
            Dictionary of gaps by category
        """
        gaps = {
            "requirements_without_design_coverage": [],
            "designs_without_task_coverage": [],
            "incomplete_tasks": [],
            "untested_code": [],
            "undocumented_features": []
        }

        # Find requirements without design coverage (break in traceability chain)
        coverage = self.get_requirement_to_task_coverage()
        for req_id, coverage_info in coverage.items():
            if not coverage_info["has_design_coverage"]:
                gaps["requirements_without_design_coverage"].append(req_id)

        # Find design components without task coverage
        for design_id in self.design_to_task_mappings:
            if not self.design_to_task_mappings[design_id]:
                gaps["designs_without_task_coverage"].append(design_id)

        # Find incomplete tasks
        for task_spec in self.task_specifications.values():
            for task in task_spec.implementation_tasks:
                if task.status not in [TaskStatus.COMPLETED, TaskStatus.CANCELLED]:
                    gaps["incomplete_tasks"].append(task.task_id)

        # Find code without tests
        for artifact in self.implementation_artifacts.values():
            if artifact.artifact_type == "source_code":
                # Check if there are test artifacts for this code
                has_tests = False
                for task_id in artifact.task_ids:
                    task_artifacts = self.get_task_to_artifact_traceability(task_id)
                    for task_artifact in task_artifacts:
                        if task_artifact.artifact_type == "test":
                            has_tests = True
                            break
                    if has_tests:
                        break

                if not has_tests:
                    gaps["untested_code"].append(artifact.artifact_id)

        return gaps

    def generate_traceability_report(self, format: str = "markdown") -> str:
        """Generate a comprehensive traceability report.

        Args:
            format: Output format (markdown, html, json)

        Returns:
            Formatted traceability report
        """
        if format == "markdown":
            return self._generate_markdown_report()
        elif format == "json":
            return self._generate_json_report()
        else:
            raise ValueError(f"Unsupported format: {format}")

    def _generate_markdown_report(self) -> str:
        """Generate markdown traceability report following requirement→design→task chain."""
        lines = ["# Traceability Report (Requirement → Design → Task Chain)"]
        lines.append("")

        # Requirements coverage
        lines.append("## Requirements Coverage")
        lines.append("")
        coverage = self.get_requirement_to_task_coverage()

        for req_id, coverage_info in coverage.items():
            lines.append(f"### {req_id}")
            lines.append(f"**Requirement**: {coverage_info['requirement_title']}")
            lines.append(f"**Design Coverage**: {'✅' if coverage_info['has_design_coverage'] else '❌'} ({coverage_info['design_count']} design components)")
            lines.append(f"**Tasks**: {coverage_info['completed_tasks']}/{coverage_info['total_tasks']} completed")
            lines.append(f"**Overall Coverage**: {coverage_info['coverage_percentage']:.1f}%")
            lines.append("")

            if coverage_info["covering_designs"]:
                lines.append("**Covering Design Components**:")
                for design_id in coverage_info["covering_designs"]:
                    lines.append(f"- {design_id}")
                lines.append("")

        # Traceability chain gaps
        lines.append("## Traceability Chain Gaps")
        lines.append("")
        gaps = self.analyze_implementation_gaps()

        for gap_type, items in gaps.items():
            if items:
                lines.append(f"### {gap_type.replace('_', ' ').title()}")
                for item in items:
                    lines.append(f"- {item}")
                lines.append("")

        # Statistics
        lines.append("## Statistics")
        lines.append("")
        fully_covered_requirements = sum(1 for c in coverage.values() if c['fully_covered'])
        requirements_with_design_coverage = sum(1 for c in coverage.values() if c['has_design_coverage'])

        lines.append(f"- **Total Requirements**: {len(coverage)}")
        lines.append(f"- **Requirements with Design Coverage**: {requirements_with_design_coverage}/{len(coverage)}")
        lines.append(f"- **Fully Covered Requirements (Design + Tasks)**: {fully_covered_requirements}/{len(coverage)}")
        lines.append(f"- **Total Design Components**: {len(self.design_specifications)}")
        lines.append(f"- **Total Tasks**: {sum(len(spec.implementation_tasks) for spec in self.task_specifications.values())}")
        lines.append(f"- **Completed Tasks**: {sum(1 for spec in self.task_specifications.values() for task in spec.implementation_tasks if task.status == TaskStatus.COMPLETED)}")
        lines.append(f"- **Implementation Artifacts**: {len(self.implementation_artifacts)}")
        lines.append("")

        return "\n".join(lines)

    def _generate_json_report(self) -> str:
        """Generate JSON traceability report."""
        report = {
            "coverage": self.get_requirement_to_task_coverage(),
            "gaps": self.analyze_implementation_gaps(),
            "statistics": {
                "total_requirements": len(self.requirement_specifications),
                "total_tasks": sum(len(spec.implementation_tasks) for spec in self.task_specifications.values()),
                "completed_tasks": sum(1 for spec in self.task_specifications.values() for task in spec.implementation_tasks if task.status == TaskStatus.COMPLETED),
                "total_artifacts": len(self.implementation_artifacts)
            },
            "trace_links_count": len(self.trace_links)
        }
        return json.dumps(report, indent=2)

    def save_traceability_data(self, file_path: str):
        """Save traceability data to file.

        Args:
            file_path: Path to save the data
        """
        data = {
            "task_specifications": {name: spec.dict() for name, spec in self.task_specifications.items()},
            "requirement_specifications": {name: spec.dict() for name, spec in self.requirement_specifications.items()},
            "implementation_artifacts": {aid: artifact.__dict__ for aid, artifact in self.implementation_artifacts.items()},
            "trace_links": [link.__dict__ for link in self.trace_links]
        }

        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)

    def load_traceability_data(self, file_path: str):
        """Load traceability data from file.

        Args:
            file_path: Path to load the data from
        """
        with open(file_path, 'r') as f:
            data = json.load(f)

        # Restore data structures
        # Note: In a full implementation, you'd reconstruct the objects properly
        self.trace_links = [TraceLink(**link) for link in data.get("trace_links", [])]