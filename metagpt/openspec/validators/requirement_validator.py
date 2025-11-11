"""
OpenSpec Requirement Validator

Specialized validator for OpenSpec requirement specifications.
"""

from __future__ import annotations

import re
from typing import List, Dict, Any, Optional, Set

from .base_validator import BaseValidator, ValidationResult, ValidationIssue, ValidationLevel
from ..models.requirement import OpenSpecRequirement, Requirement, Scenario


class RequirementValidator(BaseValidator):
    """Validator for OpenSpec requirement specifications."""

    def validate(self, spec: OpenSpecRequirement) -> ValidationResult:
        """Validate an OpenSpec requirement specification.

        Args:
            spec: The requirement specification to validate

        Returns:
            ValidationResult with validation issues
        """
        result = ValidationResult()

        # Basic structure validation
        self._validate_basic_structure(spec, result)

        # Content validation
        self._validate_requirement_content(spec, result)

        # Scenario validation
        self._validate_scenarios(spec, result)

        # Cross-reference validation
        self._validate_cross_references(spec, result)

        # Format validation
        self._validate_format_conventions(spec, result)

        # Completeness validation
        self._validate_completeness(spec, result)

        result.is_valid = not result.has_errors() or (self.strict_mode and result.has_warnings())
        result.summary = result.get_summary()
        return result

    def _validate_requirement_content(self, spec: OpenSpecRequirement, result: ValidationResult):
        """Validate requirement content and structure."""
        if not spec.has_requirements():
            result.add_error(
                "Specification must have at least one requirement",
                location="root",
                suggestion="Add requirements using ADDED, MODIFIED, or REMOVED sections"
            )

        # Validate each requirement
        for req_idx, req in enumerate(spec.added_requirements):
            self._validate_individual_requirement(req, req_idx, "ADDED", result)

        for req_idx, req in enumerate(spec.modified_requirements):
            self._validate_individual_requirement(req, req_idx, "MODIFIED", result)
            # Additional checks for modified requirements
            if not req.scenarios:
                result.add_error(
                    f"Modified requirement {req_idx + 1} must have scenarios",
                    location=f"modified_requirements[{req_idx}]",
                    suggestion="Add scenarios to describe the modified behavior"
                )

        # Validate removed requirements
        for req_idx, removed_req in enumerate(spec.removed_requirements):
            if not removed_req.reason:
                result.add_error(
                    f"Removed requirement {req_idx + 1} must have a reason",
                    location=f"removed_requirements[{req_idx}]",
                    suggestion="Add a reason for removing this requirement"
                )

    def _validate_individual_requirement(self, req: Requirement, req_idx: int, section: str, result: ValidationResult):
        """Validate an individual requirement."""
        location = f"{section.lower()}_requirements[{req_idx}]"

        # Title validation
        if not req.title or not req.title.strip():
            result.add_error(
                f"Requirement {req_idx + 1} must have a title",
                location=location,
                suggestion="Add a descriptive title for the requirement"
            )
        elif len(req.title.strip()) < 5:
            result.add_warning(
                f"Requirement title is too short (less than 5 characters)",
                location=location,
                suggestion="Use a more descriptive title"
            )

        # Description validation
        if not req.description or not req.description.strip():
            result.add_error(
                f"Requirement {req_idx + 1} must have a description",
                location=location,
                suggestion="Add a detailed description of the requirement"
            )
        elif len(req.description.strip()) < 20:
            result.add_warning(
                f"Requirement description is too brief (less than 20 characters)",
                location=location,
                suggestion="Provide a more comprehensive description"
            )

        # Scenarios validation
        if not req.scenarios:
            result.add_error(
                f"Requirement {req_idx + 1} must have at least one scenario",
                location=location,
                suggestion="Add scenarios to describe the requirement behavior"
            )

        # Acceptance criteria validation
        if not req.acceptance_criteria:
            result.add_warning(
                f"Requirement {req_idx + 1} should have acceptance criteria",
                location=location,
                suggestion="Add acceptance criteria to define when the requirement is met"
            )

    def _validate_scenarios(self, spec: OpenSpecRequirement, result: ValidationResult):
        """Validate scenario structure and content."""
        scenario_names: Set[str] = set()

        for req_idx, req in enumerate(spec.get_all_requirements()):
            for scenario_idx, scenario in enumerate(req.scenarios):
                location = f"requirement {req_idx + 1}, scenario {scenario_idx + 1}"

                # Check for unique scenario names
                if scenario.name in scenario_names:
                    result.add_warning(
                        f"Duplicate scenario name: '{scenario.name}'",
                        location=location,
                        suggestion="Use unique names for scenarios"
                    )
                scenario_names.add(scenario.name)

                # Validate scenario name
                if not scenario.name or not scenario.name.strip():
                    result.add_error(
                        "Scenario name cannot be empty",
                        location=location,
                        suggestion="Provide a meaningful name for the scenario"
                    )
                elif len(scenario.name.strip()) < 3:
                    result.add_warning(
                        "Scenario name is too short",
                        location=location,
                        suggestion="Use a more descriptive scenario name"
                    )

                # Validate Gherkin structure
                gherkin_elements = [bool(scenario.given), bool(scenario.when), bool(scenario.then)]
                if sum(gherkin_elements) < 1:
                    result.add_error(
                        "Scenario must have at least one Gherkin element (Given, When, Then)",
                        location=location,
                        suggestion="Add at least one of: Given, When, Then"
                    )
                elif not gherkin_elements[2]:  # No 'Then' element
                    result.add_warning(
                        "Scenario should have a 'Then' element to describe expected outcome",
                        location=location,
                        suggestion="Add a 'Then' clause to specify the expected result"
                    )

                # Validate Gherkin content
                if scenario.given and not scenario.given.strip():
                    result.add_error(
                        "Given clause cannot be empty",
                        location=location,
                        suggestion="Provide context in the Given clause"
                    )

                if scenario.when and not scenario.when.strip():
                    result.add_error(
                        "When clause cannot be empty",
                        location=location,
                        suggestion="Provide the action in the When clause"
                    )

                if scenario.then and not scenario.then.strip():
                    result.add_error(
                        "Then clause cannot be empty",
                        location=location,
                        suggestion="Provide the expected outcome in the Then clause"
                    )

        self._check_scenario_structure(spec, result)

    def _validate_cross_references(self, spec: OpenSpecRequirement, result: ValidationResult):
        """Validate cross-references and dependencies."""
        # Check for circular dependencies (basic check)
        for dep in spec.dependencies:
            if not dep or not dep.strip():
                result.add_error(
                    "Dependency reference cannot be empty",
                    location="dependencies",
                    suggestion="Provide valid dependency references or remove empty entries"
                )

        # Validate format of references (should follow OpenSpec conventions)
        reference_pattern = r'^[a-zA-Z0-9_-]+(/[a-zA-Z0-9_-]+)*$'
        for ref in spec.dependencies + spec.dependents:
            if ref and not re.match(reference_pattern, ref):
                result.add_warning(
                    f"Reference '{ref}' may not follow OpenSpec naming conventions",
                    location="cross_references",
                    suggestion="Use format like 'spec-name/sub-section' or 'capability-name'"
                )

    def _validate_format_conventions(self, spec: OpenSpecRequirement, result: ValidationResult):
        """Validate OpenSpec format conventions."""
        # Check requirement title format
        for req_idx, req in enumerate(spec.get_all_requirements()):
            # Requirement titles should be concise but descriptive
            if len(req.title.split()) > 15:
                result.add_warning(
                    f"Requirement title is very long ({len(req.title.split())} words)",
                    location=f"requirement {req_idx + 1}",
                    suggestion="Consider shortening the requirement title"
                )

            # Check for common formatting issues
            if req.title.endswith('.'):
                result.add_info(
                    "Requirement titles typically don't end with periods",
                    location=f"requirement {req_idx + 1}"
                )

    def _validate_completeness(self, spec: OpenSpecRequirement, result: ValidationResult):
        """Validate specification completeness."""
        # Check for metadata
        if not spec.authors:
            result.add_warning(
                "Specification should have authors",
                location="metadata",
                suggestion="Add author information to track responsibility"
            )

        if not spec.created_at:
            result.add_info(
                "Specification should have creation timestamp",
                location="metadata",
                suggestion="Add creation timestamp for version tracking"
            )

        # Check if this is a delta specification (has operations)
        if not (spec.added_requirements or spec.modified_requirements or
                spec.removed_requirements or spec.renamed_requirements):
            result.add_warning(
                "Specification appears to be a base spec, but OpenSpec typically uses delta format",
                location="root",
                suggestion="Consider using delta format with ADDED/MODIFIED/REMOVED sections"
            )

        # Check for adequate requirement coverage
        total_scenarios = sum(len(req.scenarios) for req in spec.get_all_requirements())
        if total_scenarios == 0:
            result.add_error(
                "Specification has no scenarios defined",
                location="root",
                suggestion="Add scenarios to each requirement to describe expected behavior"
            )
        elif total_scenarios < len(spec.get_all_requirements()):
            result.add_warning(
                "Some requirements may have insufficient scenario coverage",
                location="root",
                suggestion="Add more scenarios to fully cover requirement behavior"
            )