"""
Requirement Cross-Reference Manager

Manages cross-references between requirements and other specifications.
"""

from __future__ import annotations

from typing import Dict, List, Set, Optional
from dataclasses import dataclass, field

from ..models.requirement import OpenSpecRequirement, Requirement


@dataclass
class ReferenceLink:
    """Represents a cross-reference link."""
    source_id: str
    target_id: str
    target_type: str  # requirement, design, implementation, test
    description: Optional[str] = None
    bidirectional: bool = False


class RequirementCrossReferenceManager:
    """Manages cross-references for requirement specifications."""

    def __init__(self):
        """Initialize the cross-reference manager."""
        self.requirements: Dict[str, OpenSpecRequirement] = {}
        self.references: Dict[str, List[ReferenceLink]] = {}
        self.reverse_references: Dict[str, List[ReferenceLink]] = {}

    def add_requirement(self, requirement: OpenSpecRequirement):
        """Add a requirement specification to manage.

        Args:
            requirement: The requirement specification to add
        """
        self.requirements[requirement.name] = requirement

        # Process explicit cross-references in the requirement
        for dep in requirement.dependencies:
            self.add_reference(
                source_id=requirement.name,
                target_id=dep,
                target_type="specification",
                description="Dependency on specification"
            )

    def add_reference(
        self,
        source_id: str,
        target_id: str,
        target_type: str,
        description: Optional[str] = None,
        bidirectional: bool = False
    ):
        """Add a cross-reference link.

        Args:
            source_id: Source requirement ID
            target_id: Target specification/element ID
            target_type: Type of target (requirement, design, implementation, test)
            description: Description of the relationship
            bidirectional: Whether this is a bidirectional reference
        """
        link = ReferenceLink(
            source_id=source_id,
            target_id=target_id,
            target_type=target_type,
            description=description,
            bidirectional=bidirectional
        )

        # Add forward reference
        if source_id not in self.references:
            self.references[source_id] = []
        self.references[source_id].append(link)

        # Add reverse reference
        if target_id not in self.reverse_references:
            self.reverse_references[target_id] = []
        self.reverse_references[target_id].append(link)

    def get_references_from(self, source_id: str) -> List[ReferenceLink]:
        """Get all references from a source requirement.

        Args:
            source_id: Source requirement ID

        Returns:
            List of reference links
        """
        return self.references.get(source_id, [])

    def get_references_to(self, target_id: str) -> List[ReferenceLink]:
        """Get all references to a target.

        Args:
            target_id: Target ID

        Returns:
            List of reference links
        """
        return self.reverse_references.get(target_id, [])

    def analyze_impact(
        self,
        requirement_id: str,
        change_type: str = "modification"
    ) -> Dict[str, List[str]]:
        """Analyze the impact of changing a requirement.

        Args:
            requirement_id: ID of the requirement being changed
            change_type: Type of change (modification, removal, addition)

        Returns:
            Dictionary with impact analysis
        """
        impact = {
            "direct_dependencies": [],
            "dependents": [],
            "affected_designs": [],
            "affected_tests": [],
            "implementation_impacts": []
        }

        # Get direct dependencies
        for ref in self.get_references_from(requirement_id):
            if ref.target_type == "specification":
                impact["direct_dependencies"].append(ref.target_id)
            elif ref.target_type == "design":
                impact["affected_designs"].append(ref.target_id)
            elif ref.target_type == "implementation":
                impact["implementation_impacts"].append(ref.target_id)
            elif ref.target_type == "test":
                impact["affected_tests"].append(ref.target_id)

        # Get dependents (things that reference this requirement)
        for ref in self.get_references_to(requirement_id):
            if ref.source_id != requirement_id:  # Avoid self-references
                impact["dependents"].append(ref.source_id)

        return impact

    def validate_references(self) -> List[str]:
        """Validate all cross-references.

        Returns:
            List of validation errors
        """
        errors = []

        # Check for missing target requirements
        for source_id, refs in self.references.items():
            for ref in refs:
                if ref.target_type == "requirement" and ref.target_id not in self.requirements:
                    errors.append(
                        f"Requirement '{source_id}' references non-existent requirement '{ref.target_id}'"
                    )

        # Check for circular dependencies
        circular_deps = self._find_circular_dependencies()
        for cycle in circular_deps:
            errors.append(f"Circular dependency detected: {' -> '.join(cycle)}")

        return errors

    def _find_circular_dependencies(self) -> List[List[str]]:
        """Find circular dependencies in requirements.

        Returns:
            List of cycles found
        """
        visited = set()
        rec_stack = set()
        cycles = []

        def dfs(node: str, path: List[str]) -> bool:
            if node in rec_stack:
                cycle_start = path.index(node)
                cycles.append(path[cycle_start:] + [node])
                return True

            if node in visited:
                return False

            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for ref in self.references.get(node, []):
                if ref.target_type == "requirement":
                    if dfs(ref.target_id, path.copy()):
                        return True

            rec_stack.remove(node)
            return False

        for req_id in self.requirements:
            if req_id not in visited:
                dfs(req_id, [])

        return cycles

    def get_dependency_graph(self) -> Dict[str, List[str]]:
        """Get the dependency graph.

        Returns:
            Dictionary mapping requirements to their dependencies
        """
        graph = {}
        for req_id in self.requirements:
            dependencies = []
            for ref in self.references.get(req_id, []):
                if ref.target_type == "requirement":
                    dependencies.append(ref.target_id)
            graph[req_id] = dependencies
        return graph

    def export_references_markdown(self, requirement_id: str) -> str:
        """Export cross-references for a requirement in markdown format.

        Args:
            requirement_id: ID of the requirement

        Returns:
            Markdown formatted cross-references
        """
        lines = [f"## Cross-References for {requirement_id}"]
        lines.append("")

        # References from this requirement
        forward_refs = self.get_references_from(requirement_id)
        if forward_refs:
            lines.append("### References From")
            for ref in forward_refs:
                ref_info = f"- **{ref.target_type.title()}**: {ref.target_id}"
                if ref.description:
                    ref_info += f" - {ref.description}"
                lines.append(ref_info)
            lines.append("")

        # References to this requirement
        reverse_refs = self.get_references_to(requirement_id)
        if reverse_refs:
            lines.append("### References To")
            for ref in reverse_refs:
                if ref.source_id != requirement_id:
                    ref_info = f"- **{ref.source_id}** ({ref.target_type})"
                    if ref.description:
                        ref_info += f" - {ref.description}"
                    lines.append(ref_info)
            lines.append("")

        # Impact analysis
        impact = self.analyze_impact(requirement_id)
        if any(impact.values()):
            lines.append("### Impact Analysis")
            for category, items in impact.items():
                if items:
                    category_name = category.replace("_", " ").title()
                    lines.append(f"**{category_name}**:")
                    for item in items:
                        lines.append(f"- {item}")
            lines.append("")

        return "\n".join(lines)