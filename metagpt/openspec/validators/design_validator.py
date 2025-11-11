"""
OpenSpec Design Validator

Specialized validator for OpenSpec design specifications.
"""

from __future__ import annotations

import re
from typing import List, Dict, Any, Optional, Set

from .base_validator import BaseValidator, ValidationResult, ValidationLevel
from ..models.design import OpenSpecDesign, DesignComponent, RequirementMapping


class DesignValidator(BaseValidator):
    """Validator for OpenSpec design specifications."""

    def validate(self, spec: OpenSpecDesign) -> ValidationResult:
        """Validate an OpenSpec design specification.

        Args:
            spec: The design specification to validate

        Returns:
            ValidationResult with validation issues
        """
        result = ValidationResult()

        # Basic structure validation
        self._validate_basic_structure(spec, result)

        # Content validation
        self._validate_design_content(spec, result)

        # Component validation
        self._validate_design_components(spec, result)

        # Requirements mapping validation
        self._validate_requirements_mapping(spec, result)

        # Cross-reference validation
        self._validate_cross_references(spec, result)

        # Architectural validation
        self._validate_architecture(spec, result)

        # Completeness validation
        self._validate_completeness(spec, result)

        result.is_valid = not result.has_errors() or (self.strict_mode and result.has_warnings())
        result.summary = result.get_summary()
        return result

    def _validate_design_content(self, spec: OpenSpecDesign, result: ValidationResult):
        """Validate design content and overview."""
        # Design overview validation
        if not spec.design_overview or not spec.design_overview.strip():
            result.add_error(
                "Design must have an overview",
                location="design_overview",
                suggestion="Add a comprehensive design overview explaining the solution approach"
            )
        elif len(spec.design_overview.strip()) < 50:
            result.add_warning(
                "Design overview is too brief",
                location="design_overview",
                suggestion="Provide a more detailed design overview"
            )

        # Check if design has any substance
        if not spec.has_components() and not spec.requirements_mapping:
            result.add_error(
                "Design must have either components or requirements mapping",
                location="root",
                suggestion="Add design components or requirements mapping to make this a meaningful design"
            )

    def _validate_design_components(self, spec: OpenSpecDesign, result: ValidationResult):
        """Validate design components."""
        if not spec.design_components:
            result.add_warning(
                "Design has no components defined",
                location="design_components",
                suggestion="Add design components to describe the solution structure"
            )
            return

        component_names: Set[str] = set()
        interface_names: Set[str] = set()

        for comp_idx, component in enumerate(spec.design_components):
            location = f"design_components[{comp_idx}]"

            # Check for unique component names
            if component.name in component_names:
                result.add_error(
                    f"Duplicate component name: '{component.name}'",
                    location=location,
                    suggestion="Use unique names for design components"
                )
            component_names.add(component.name)

            # Validate component content
            if not component.purpose or not component.purpose.strip():
                result.add_error(
                    f"Component '{component.name}' must have a purpose",
                    location=location,
                    suggestion="Add a clear purpose for this component"
                )

            # Validate component interfaces
            for interface_idx, interface in enumerate(component.interfaces):
                interface_location = f"{location}, interfaces[{interface_idx}]"

                if interface.name in interface_names:
                    result.add_warning(
                        f"Duplicate interface name: '{interface.name}'",
                        location=interface_location,
                        suggestion="Use unique names for interfaces across components"
                    )
                interface_names.add(interface.name)

                if not interface.description or not interface.description.strip():
                    result.add_error(
                        f"Interface '{interface.name}' must have a description",
                        location=interface_location,
                        suggestion="Add a description for this interface"
                    )

            # Validate dependencies
            for dep_name in component.dependencies:
                dep_component = spec.find_component_by_name(dep_name)
                if not dep_component:
                    result.add_error(
                        f"Component '{component.name}' depends on non-existent component '{dep_name}'",
                        location=location,
                        suggestion=f"Remove the dependency or add component '{dep_name}'"
                    )
                else:
                    # Check for circular dependencies (simple check)
                    if component.name in dep_component.dependencies:
                        result.add_error(
                            f"Circular dependency detected between '{component.name}' and '{dep_name}'",
                            location=location,
                            suggestion="Redesign to eliminate circular dependencies"
                        )

            # Validate component quality attributes
            if component.element_type.value == "component" and not component.interfaces:
                result.add_warning(
                    f"Component '{component.name}' has no interfaces defined",
                    location=location,
                    suggestion="Add interfaces to define how this component interacts with others"
                )

    def _validate_requirements_mapping(self, spec: OpenSpecDesign, result: ValidationResult):
        """Validate requirements mapping."""
        if not spec.requirements_mapping:
            if spec.design_components:
                result.add_warning(
                    "Design has components but no requirements mapping",
                    location="requirements_mapping",
                    suggestion="Add requirements mapping to show how components fulfill requirements"
                )
            return

        requirement_ids: Set[str] = set()

        for map_idx, mapping in enumerate(spec.requirements_mapping):
            location = f"requirements_mapping[{map_idx}]"

            # Check for unique requirement IDs
            if mapping.requirement_id in requirement_ids:
                result.add_error(
                    f"Duplicate requirement mapping for ID: '{mapping.requirement_id}'",
                    location=location,
                    suggestion="Each requirement should only be mapped once"
                )
            requirement_ids.add(mapping.requirement_id)

            # Validate mapping content
            if not mapping.design_elements:
                result.add_error(
                    f"Requirements mapping for '{mapping.requirement_id}' has no design elements",
                    location=location,
                    suggestion="Add design elements that fulfill this requirement"
                )

            # Check if mapped design elements exist
            for element_name in mapping.design_elements:
                if not spec.find_component_by_name(element_name):
                    result.add_error(
                        f"Requirements mapping references non-existent component: '{element_name}'",
                        location=location,
                        suggestion=f"Remove the reference or add component '{element_name}'"
                    )

            # Validate requirement title
            if not mapping.requirement_title or not mapping.requirement_title.strip():
                result.add_warning(
                    f"Requirements mapping should include the requirement title",
                    location=location,
                    suggestion="Add the requirement title for better traceability"
                )

    def _validate_cross_references(self, spec: OpenSpecDesign, result: ValidationResult):
        """Validate cross-references."""
        for ref_idx, ref in enumerate(spec.cross_references):
            location = f"cross_references[{ref_idx}]"

            if not ref.target or not ref.target.strip():
                result.add_error(
                    "Cross-reference target cannot be empty",
                    location=location,
                    suggestion="Provide a valid target for the cross-reference"
                )

            # Validate reference format
            if not re.match(r'^[a-zA-Z0-9_\-/]+$', ref.target):
                result.add_warning(
                    f"Cross-reference target '{ref.target}' may not follow OpenSpec conventions",
                    location=location,
                    suggestion="Use format like 'spec-name' or 'capability-name/sub-section'"
                )

    def _validate_architecture(self, spec: OpenSpecDesign, result: ValidationResult):
        """Validate architectural aspects."""
        # Check for architectural consistency
        if spec.design_components:
            # Identify components without clear purpose or interfaces
            isolated_components = []
            for component in spec.design_components:
                if not component.interfaces and not component.dependencies:
                    isolated_components.append(component.name)

            if isolated_components:
                result.add_warning(
                    f"Components appear isolated: {', '.join(isolated_components)}",
                    location="architecture",
                    suggestion="Consider adding interfaces or dependencies to integrate these components"
                )

        # Validate technology consistency
        technologies_used = set()
        for component in spec.design_components:
            if component.technology:
                technologies_used.add(component.technology)

        if len(technologies_used) > 5:
            result.add_info(
                f"Design uses many different technologies ({len(technologies_used)}): {', '.join(technologies_used)}",
                location="technology_stack",
                suggestion="Consider if technology diversity is justified or could be simplified"
            )

        # Check for quality attributes consideration
        quality_attrs_missing = []
        for component in spec.design_components:
            if not component.performance_requirements and component.element_type.value == "component":
                quality_attrs_missing.append(component.name)

        if quality_attrs_missing:
            result.add_warning(
                f"Components missing quality attribute considerations: {', '.join(quality_attrs_missing)}",
                location="quality_attributes",
                suggestion="Add performance, security, or scalability considerations"
            )

    def _validate_completeness(self, spec: OpenSpecDesign, result: ValidationResult):
        """Validate design completeness."""
        # Check for metadata
        if not spec.authors:
            result.add_warning(
                "Design should have authors",
                location="metadata",
                suggestion="Add author information to track responsibility"
            )

        if not spec.created_at:
            result.add_info(
                "Design should have creation timestamp",
                location="metadata",
                suggestion="Add creation timestamp for version tracking"
            )

        # Check for essential design information
        if not spec.technology_stack:
            result.add_info(
                "Design should specify the technology stack",
                location="technology_stack",
                suggestion="Add technology stack information to guide implementation"
            )

        if spec.design_components and not spec.design_overview:
            result.add_error(
                "Design with components must have an overview",
                location="design_overview",
                suggestion="Add a design overview to explain the overall architecture"
            )

        # Validate design quality
        total_interfaces = sum(len(comp.interfaces) for comp in spec.design_components)
        if spec.design_components and total_interfaces == 0:
            result.add_warning(
                "Design has components but no defined interfaces",
                location="interfaces",
                suggestion="Add interfaces to define component interactions"
            )

        # Check for implementation guidance
        components_without_implementation = [
            comp.name for comp in spec.design_components
            if not comp.implementation_notes and comp.element_type.value == "component"
        ]

        if components_without_implementation:
            result.add_info(
                f"Components lack implementation notes: {', '.join(components_without_implementation)}",
                location="implementation",
                suggestion="Add implementation notes to guide developers"
            )