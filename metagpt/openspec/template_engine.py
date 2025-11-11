"""
OpenSpec Template Engine

Provides template-based generation of OpenSpec-compliant specifications.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Optional, Any

from jinja2 import Environment, FileSystemLoader, Template, TemplateNotFound


class OpenSpecTemplateEngine:
    """Template engine for generating OpenSpec-compliant specifications."""

    def __init__(self, template_dir: Optional[str] = None):
        """Initialize the template engine.

        Args:
            template_dir: Directory containing OpenSpec templates.
                        Defaults to built-in templates.
        """
        if template_dir is None:
            template_dir = Path(__file__).parent / "templates"

        self.template_dir = Path(template_dir)
        self.template_dir.mkdir(exist_ok=True)

        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            trim_blocks=True,
            lstrip_blocks=True
        )

        # Register custom filters
        self.env.filters["kebab_case"] = self._kebab_case
        self.env.filters["snake_case"] = self._snake_case

        # Load built-in templates
        self._ensure_builtin_templates()

    def _kebab_case(self, text: str) -> str:
        """Convert text to kebab-case."""
        return re.sub(r'[\s_]+', '-', text.strip().lower())

    def _snake_case(self, text: str) -> str:
        """Convert text to snake_case."""
        return re.sub(r'[\s-]+', '_', text.strip().lower())

    def _ensure_builtin_templates(self):
        """Ensure built-in templates exist."""
        requirement_template = '''# {{ requirement_name }}

## ADDED Requirements

{% for req in requirements %}
### Requirement: {{ req.title }}
{{ req.description }}

{% for scenario in req.scenarios %}
#### Scenario: {{ scenario.name }}
{% if scenario.given %}**Given** {{ scenario.given }}{% endif %}
{% if scenario.when %}**When** {{ scenario.when }}{% endif %}
{% if scenario.then %}**Then** {{ scenario.then }}{% endif %}
{% endfor %}
{% endfor %}

{% if modified_requirements %}
## MODIFIED Requirements

{% for req in modified_requirements %}
### Requirement: {{ req.title }}
{{ req.description }}

{% for scenario in req.scenarios %}
#### Scenario: {{ scenario.name }}
{% if scenario.given %}**Given** {{ scenario.given }}{% endif %}
{% if scenario.when %}**When** {{ scenario.when }}{% endif %}
{% if scenario.then %}**Then** {{ scenario.then }}{% endif %}
{% endfor %}
{% endfor %}
{% endif %}

{% if removed_requirements %}
## REMOVED Requirements

{% for req in removed_requirements %}
### Requirement: {{ req.title }}
**Reason**: {{ req.reason }}
**Migration**: {{ req.migration }}
{% endfor %}
{% endif %}
'''

        design_template = '''# {{ design_name }}

## Design Overview

{{ design_overview }}

{% if requirements_mapping %}
## Requirements Mapping

{% for mapping in requirements_mapping %}
### {{ mapping.requirement_id }}: {{ mapping.requirement_title }}
- **Design Elements**: {{ mapping.design_elements | join(', ') }}
- **Implementation Notes**: {{ mapping.implementation_notes }}
{% endfor %}
{% endif %}

{% if design_components %}
## Design Components

{% for component in design_components %}
### {{ component.name }}

**Purpose**: {{ component.purpose }}

**Interface**:
{% for interface in component.interfaces %}
- {{ interface.name }}: {{ interface.description }}
{% endfor %}

**Dependencies**: {{ component.dependencies | join(', ') if component.dependencies else 'None' }}

{% if component.data_flow %}
**Data Flow**:
{{ component.data_flow }}
{% endif %}
{% endfor %}
{% endif %}

{% if cross_references %}
## Cross-References

{% for ref in cross_references %}
- **{{ ref.type }}**: {{ ref.target }}
{% endfor %}
{% endif %}
'''

        # Write templates if they don't exist
        requirement_path = self.template_dir / "requirement.j2"
        design_path = self.template_dir / "design.j2"

        if not requirement_path.exists():
            requirement_path.write_text(requirement_template)

        if not design_path.exists():
            design_path.write_text(design_template)

    def render_requirement(self, **kwargs) -> str:
        """Render an OpenSpec requirement specification.

        Args:
            **kwargs: Template variables including:
                - requirement_name: Name of the requirement
                - requirements: List of new requirements
                - modified_requirements: List of modified requirements
                - removed_requirements: List of removed requirements

        Returns:
            Rendered OpenSpec requirement specification
        """
        template = self.env.get_template("requirement.j2")
        return template.render(**kwargs)

    def render_design(self, **kwargs) -> str:
        """Render an OpenSpec design specification.

        Args:
            **kwargs: Template variables including:
                - design_name: Name of the design
                - design_overview: Design description
                - requirements_mapping: List of requirement mappings
                - design_components: List of design components
                - cross_references: List of cross-references

        Returns:
            Rendered OpenSpec design specification
        """
        template = self.env.get_template("design.j2")
        return template.render(**kwargs)

    async def render_requirement_template(self, requirement_data: Dict[str, Any]) -> str:
        """Render requirement template with provided data.

        Args:
            requirement_data: Dictionary containing requirement data

        Returns:
            Rendered requirement specification
        """
        return self.render_requirement(
            requirement_name=requirement_data.get("title", "Unnamed Requirement"),
            requirements=[requirement_data],
            modified_requirements=[],
            removed_requirements=[]
        )

    def render_custom_template(self, template_name: str, **kwargs) -> str:
        """Render a custom template.

        Args:
            template_name: Name of the custom template
            **kwargs: Template variables

        Returns:
            Rendered template content

        Raises:
            TemplateNotFound: If template doesn't exist
        """
        template = self.env.get_template(template_name)
        return template.render(**kwargs)

    def add_template(self, template_name: str, content: str):
        """Add a custom template.

        Args:
            template_name: Name of the template file (should end with .j2)
            content: Template content
        """
        if not template_name.endswith('.j2'):
            template_name += '.j2'

        template_path = self.template_dir / template_name
        template_path.write_text(content)

    def list_templates(self) -> List[str]:
        """List all available templates.

        Returns:
            List of template names
        """
        templates = []
        for template_file in self.template_dir.glob("*.j2"):
            templates.append(template_file.stem)
        return templates