"""
OpenSpec Design Models

Pydantic models for OpenSpec design specifications.
"""

from __future__ import annotations

from enum import Enum
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, validator


class DesignElementType(str, Enum):
    """Types of design elements."""
    COMPONENT = "component"
    INTERFACE = "interface"
    DATA_STRUCTURE = "data_structure"
    API_ENDPOINT = "api_endpoint"
    WORKFLOW = "workflow"
    ARCHITECTURE = "architecture"


class CrossReferenceType(str, Enum):
    """Types of cross-references."""
    REQUIREMENT = "requirement"
    IMPLEMENTATION = "implementation"
    TEST = "test"
    DOCUMENTATION = "documentation"
    SPECIFICATION = "specification"


class Interface(BaseModel):
    """Represents an interface in a design component."""
    name: str = Field(..., description="Name of the interface")
    description: str = Field(..., description="Description of the interface")
    input_type: Optional[str] = Field(None, description="Input type specification")
    output_type: Optional[str] = Field(None, description="Output type specification")
    protocol: Optional[str] = Field(None, description="Communication protocol")
    endpoint: Optional[str] = Field(None, description="API endpoint if applicable")

    @validator('name')
    def validate_name(cls, v):
        """Validate interface name."""
        if not v or not v.strip():
            raise ValueError("Interface name cannot be empty")
        return v.strip()


class DesignComponent(BaseModel):
    """Represents a design component."""
    name: str = Field(..., description="Name of the component")
    purpose: str = Field(..., description="Purpose of the component")
    description: Optional[str] = Field(None, description="Detailed description")
    element_type: DesignElementType = Field(..., description="Type of design element")

    # Structure
    interfaces: List[Interface] = Field(default_factory=list, description="Interfaces exposed by the component")
    dependencies: List[str] = Field(default_factory=list, description="Dependencies on other components")
    sub_components: List[str] = Field(default_factory=list, description="Sub-components if any")

    # Behavior
    behavior: Optional[str] = Field(None, description="Component behavior description")
    data_flow: Optional[str] = Field(None, description="Data flow description")

    # Technical details
    technology: Optional[str] = Field(None, description="Technology stack")
    implementation_notes: Optional[str] = Field(None, description="Implementation guidance")

    # Quality attributes
    performance_requirements: Optional[str] = Field(None, description="Performance requirements")
    security_considerations: Optional[str] = Field(None, description="Security considerations")
    scalability_notes: Optional[str] = Field(None, description="Scalability considerations")

    @validator('name')
    def validate_name(cls, v):
        """Validate component name."""
        if not v or not v.strip():
            raise ValueError("Component name cannot be empty")
        return v.strip()

    @validator('purpose')
    def validate_purpose(cls, v):
        """Validate component purpose."""
        if not v or not v.strip():
            raise ValueError("Component purpose cannot be empty")
        return v.strip()


class RequirementMapping(BaseModel):
    """Maps a design element to a requirement."""
    requirement_id: str = Field(..., description="ID of the requirement")
    requirement_title: str = Field(..., description="Title of the requirement")
    design_elements: List[str] = Field(..., description="Design elements that fulfill this requirement")
    implementation_notes: Optional[str] = Field(None, description="Implementation notes for this mapping")
    verification_method: Optional[str] = Field(None, description="How to verify this requirement is met")

    @validator('requirement_id')
    def validate_requirement_id(cls, v):
        """Validate requirement ID."""
        if not v or not v.strip():
            raise ValueError("Requirement ID cannot be empty")
        return v.strip()

    @validator('requirement_title')
    def validate_requirement_title(cls, v):
        """Validate requirement title."""
        if not v or not v.strip():
            raise ValueError("Requirement title cannot be empty")
        return v.strip()


class CrossReference(BaseModel):
    """Represents a cross-reference to another specification."""
    target: str = Field(..., description="Target specification or element")
    reference_type: CrossReferenceType = Field(..., description="Type of reference")
    description: Optional[str] = Field(None, description="Description of the reference")
    bidirectional: bool = Field(default=False, description="Whether this is a bidirectional reference")

    @validator('target')
    def validate_target(cls, v):
        """Validate reference target."""
        if not v or not v.strip():
            raise ValueError("Reference target cannot be empty")
        return v.strip()


class OpenSpecDesign(BaseModel):
    """Complete OpenSpec design specification."""
    name: str = Field(..., description="Name of the design specification")
    version: str = Field(default="1.0", description="Specification version")
    design_overview: str = Field(..., description="High-level design overview")

    # Structure and components
    design_components: List[DesignComponent] = Field(default_factory=list, description="Design components")
    requirements_mapping: List[RequirementMapping] = Field(default_factory=list, description="Mapping to requirements")
    cross_references: List[CrossReference] = Field(default_factory=list, description="Cross-references")

    # Architecture and patterns
    architectural_patterns: List[str] = Field(default_factory=list, description="Architectural patterns used")
    design_principles: List[str] = Field(default_factory=list, description="Design principles followed")

    # Technical specifications
    technology_stack: Optional[str] = Field(None, description="Technology stack overview")
    data_model: Optional[str] = Field(None, description="Data model description")
    api_specifications: Optional[str] = Field(None, description="API specifications overview")

    # Quality and non-functional requirements
    quality_attributes: Dict[str, str] = Field(default_factory=dict, description="Quality attributes")
    constraints: List[str] = Field(default_factory=list, description="Design constraints")

    # Metadata
    created_at: Optional[str] = Field(None, description="Creation timestamp")
    updated_at: Optional[str] = Field(None, description="Last update timestamp")
    authors: List[str] = Field(default_factory=list, description="Authors of the design")
    reviewers: List[str] = Field(default_factory=list, description="Reviewers of the design")

    # Dependencies
    dependency_requirements: List[str] = Field(default_factory=list, description="Requirements this design depends on")
    dependent_designs: List[str] = Field(default_factory=list, description="Designs that depend on this one")

    @validator('name')
    def validate_name(cls, v):
        """Validate design name."""
        if not v or not v.strip():
            raise ValueError("Design name cannot be empty")
        return v.strip()

    @validator('design_overview')
    def validate_design_overview(cls, v):
        """Validate design overview."""
        if not v or not v.strip():
            raise ValueError("Design overview cannot be empty")
        return v.strip()

    def has_components(self) -> bool:
        """Check if design has any components."""
        return bool(self.design_components)

    def get_components_by_type(self, element_type: DesignElementType) -> List[DesignComponent]:
        """Get components by their type."""
        return [comp for comp in self.design_components if comp.element_type == element_type]

    def get_requirements_fulfillment(self) -> Dict[str, List[str]]:
        """Get mapping of requirements to design elements."""
        mapping = {}
        for req_map in self.requirements_mapping:
            mapping[req_map.requirement_id] = req_map.design_elements
        return mapping

    def find_component_by_name(self, name: str) -> Optional[DesignComponent]:
        """Find a component by its name."""
        for component in self.design_components:
            if component.name.lower() == name.lower():
                return component
        return None

    def get_interfaces(self) -> List[Interface]:
        """Get all interfaces from all components."""
        interfaces = []
        for component in self.design_components:
            interfaces.extend(component.interfaces)
        return interfaces

    def get_dependencies(self) -> Dict[str, List[str]]:
        """Get dependency graph."""
        dependencies = {}
        for component in self.design_components:
            dependencies[component.name] = component.dependencies
        return dependencies

    def to_markdown(self) -> str:
        """Convert design to OpenSpec markdown format."""
        lines = [f"# {self.name}"]

        if self.design_overview:
            lines.append(self.design_overview)
            lines.append("")

        # Requirements Mapping
        if self.requirements_mapping:
            lines.append("## Requirements Mapping")
            lines.append("")
            for mapping in self.requirements_mapping:
                lines.append(f"### {mapping.requirement_id}: {mapping.requirement_title}")
                lines.append(f"**Design Elements**: {', '.join(mapping.design_elements)}")
                if mapping.implementation_notes:
                    lines.append(f"**Implementation Notes**: {mapping.implementation_notes}")
                if mapping.verification_method:
                    lines.append(f"**Verification Method**: {mapping.verification_method}")
                lines.append("")

        # Design Components
        if self.design_components:
            lines.append("## Design Components")
            lines.append("")
            for component in self.design_components:
                lines.append(f"### {component.name}")
                lines.append(f"**Purpose**: {component.purpose}")
                lines.append(f"**Type**: {component.element_type.value}")

                if component.description:
                    lines.append(f"**Description**: {component.description}")

                if component.interfaces:
                    lines.append("**Interface**:")
                    for interface in component.interfaces:
                        interface_info = f"- {interface.name}: {interface.description}"
                        if interface.protocol:
                            interface_info += f" ({interface.protocol})"
                        lines.append(interface_info)

                if component.dependencies:
                    lines.append(f"**Dependencies**: {', '.join(component.dependencies)}")

                if component.technology:
                    lines.append(f"**Technology**: {component.technology}")

                if component.behavior:
                    lines.append(f"**Behavior**: {component.behavior}")

                if component.data_flow:
                    lines.append("**Data Flow**:")
                    lines.append(component.data_flow)

                lines.append("")

        # Cross-References
        if self.cross_references:
            lines.append("## Cross-References")
            lines.append("")
            for ref in self.cross_references:
                ref_info = f"- **{ref.reference_type.value.title()}**: {ref.target}"
                if ref.description:
                    ref_info += f" - {ref.description}"
                lines.append(ref_info)
            lines.append("")

        return "\n".join(lines).rstrip()

    def get_validation_errors(self) -> List[str]:
        """Get validation errors for this design."""
        errors = []

        if not self.has_components():
            errors.append("Design must have at least one component")

        # Validate requirement mappings
        for i, mapping in enumerate(self.requirements_mapping):
            try:
                mapping.dict()  # This will trigger Pydantic validation
                # Check if mapped design elements exist
                for element_name in mapping.design_elements:
                    if not self.find_component_by_name(element_name):
                        errors.append(
                            f"Requirement mapping {i+1} references non-existent component: {element_name}"
                        )
            except Exception as e:
                errors.append(f"Requirement mapping {i+1} validation error: {str(e)}")

        # Validate components
        for i, component in enumerate(self.design_components):
            try:
                component.dict()  # This will trigger Pydantic validation

                # Check if dependencies exist
                for dep_name in component.dependencies:
                    if not self.find_component_by_name(dep_name):
                        errors.append(
                            f"Component {component.name} has non-existent dependency: {dep_name}"
                        )

            except Exception as e:
                errors.append(f"Design component {i+1} validation error: {str(e)}")

        return errors