"""
Design Cross-Reference Manager

Manages cross-references between design specifications and requirements.
"""

from __future__ import annotations

from typing import Dict, List, Set, Optional
from dataclasses import dataclass

from ..models.design import OpenSpecDesign, DesignComponent


class DesignCrossReferenceManager:
    """Manages cross-references for design specifications."""

    def __init__(self):
        """Initialize the design cross-reference manager."""
        self.designs: Dict[str, OpenSpecDesign] = {}
        self.requirement_mappings: Dict[str, Set[str]] = {}  # requirement_id -> design_names
        self.component_mappings: Dict[str, Set[str]] = {}   # component_name -> requirement_ids

    def add_design(self, design: OpenSpecDesign):
        """Add a design specification to manage.

        Args:
            design: The design specification to add
        """
        self.designs[design.name] = design

        # Process requirement mappings
        for mapping in design.requirements_mapping:
            self.add_requirement_mapping(
                requirement_id=mapping.requirement_id,
                design_name=design.name,
                design_elements=mapping.design_elements
            )

    def add_requirement_mapping(
        self,
        requirement_id: str,
        design_name: str,
        design_elements: List[str]
    ):
        """Add a requirement-to-design mapping.

        Args:
            requirement_id: ID of the requirement
            design_name: Name of the design
            design_elements: List of design elements that fulfill the requirement
        """
        # Add requirement to design mapping
        if requirement_id not in self.requirement_mappings:
            self.requirement_mappings[requirement_id] = set()
        self.requirement_mappings[requirement_id].add(design_name)

        # Add component to requirement mappings
        for element in design_elements:
            if element not in self.component_mappings:
                self.component_mappings[element] = set()
            self.component_mappings[element].add(requirement_id)

    def get_designs_for_requirement(self, requirement_id: str) -> List[str]:
        """Get all designs that fulfill a requirement.

        Args:
            requirement_id: ID of the requirement

        Returns:
            List of design names
        """
        return list(self.requirement_mappings.get(requirement_id, set()))

    def get_requirements_for_component(self, component_name: str) -> List[str]:
        """Get all requirements fulfilled by a component.

        Args:
            component_name: Name of the design component

        Returns:
            List of requirement IDs
        """
        return list(self.component_mappings.get(component_name, set()))

    def verify_traceability(self) -> List[str]:
        """Verify that all requirements have design coverage.

        Returns:
            List of requirements without design coverage
        """
        uncovered_requirements = []

        for requirement_id, design_names in self.requirement_mappings.items():
            if not design_names:
                uncovered_requirements.append(requirement_id)

        return uncovered_requirements

    def analyze_requirement_coverage(self, design_name: str) -> Dict[str, any]:
        """Analyze requirement coverage for a design.

        Args:
            design_name: Name of the design to analyze

        Returns:
            Coverage analysis dictionary
        """
        if design_name not in self.designs:
            return {"error": f"Design '{design_name}' not found"}

        design = self.designs[design_name]
        mapped_requirements = set()

        # Get requirements mapped in this design
        for mapping in design.requirements_mapping:
            mapped_requirements.add(mapping.requirement_id)

        # Analyze component coverage
        component_coverage = {}
        for component in design.design_components:
            component_reqs = self.get_requirements_for_component(component.name)
            component_coverage[component.name] = {
                "requirement_count": len(component_reqs),
                "requirements": component_reqs,
                "has_requirements": len(component_reqs) > 0
            }

        return {
            "design_name": design_name,
            "total_requirements": len(mapped_requirements),
            "mapped_requirements": list(mapped_requirements),
            "component_count": len(design.design_components),
            "components_with_requirements": len([
                c for c in component_coverage.values() if c["has_requirements"]
            ]),
            "component_coverage": component_coverage
        }

    def validate_design_references(self) -> List[str]:
        """Validate design cross-references.

        Returns:
            List of validation errors
        """
        errors = []

        for design_name, design in self.designs.items():
            # Validate requirement mappings
            for mapping in design.requirements_mapping:
                # Check if mapped components exist
                for element_name in mapping.design_elements:
                    component = design.find_component_by_name(element_name)
                    if component is None:
                        errors.append(
                            f"Design '{design_name}' maps requirement '{mapping.requirement_id}' "
                            f"to non-existent component '{element_name}'"
                        )

            # Validate component references
            for component in design.design_components:
                # Check dependencies
                for dep_name in component.dependencies:
                    dep_component = design.find_component_by_name(dep_name)
                    if dep_component is None:
                        errors.append(
                            f"Component '{component.name}' in design '{design_name}' "
                            f"has non-existent dependency '{dep_name}'"
                        )

        return errors

    def export_traceability_matrix(self) -> str:
        """Export a requirements traceability matrix.

        Returns:
            Markdown formatted traceability matrix
        """
        lines = ["# Requirements Traceability Matrix"]
        lines.append("")
        lines.append("| Requirement ID | Design | Components | Status |")
        lines.append("|----------------|--------|------------|--------|")

        # Get all unique requirements
        all_requirements = set(self.requirement_mappings.keys())

        for req_id in sorted(all_requirements):
            design_names = self.requirement_mappings.get(req_id, set())
            components = []

            # Get all components for this requirement
            for design_name in design_names:
                if design_name in self.designs:
                    design = self.designs[design_name]
                    for mapping in design.requirements_mapping:
                        if mapping.requirement_id == req_id:
                            components.extend(mapping.design_elements)

            status = "✅ Covered" if design_names else "❌ Uncovered"
            design_str = ", ".join(sorted(design_names)) if design_names else "None"
            component_str = ", ".join(sorted(set(components))) if components else "None"

            lines.append(f"| {req_id} | {design_str} | {component_str} | {status} |")

        return "\n".join(lines)