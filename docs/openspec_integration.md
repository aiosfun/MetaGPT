# OpenSpec Integration for MetaGPT

This document describes the comprehensive OpenSpec integration that has been added to MetaGPT to support structured specification generation, validation, and management across the entire software development lifecycle.

## Overview

The OpenSpec integration enables MetaGPT's multi-agent workflow to generate OpenSpec-compliant specifications with:

- **Structured requirement generation** using OpenSpec templates with Gherkin scenarios
- **Comprehensive validation** with multi-level feedback and improvement suggestions
- **End-to-end traceability** linking requirements through design to implementation
- **Review orchestration** with quality gates and stakeholder feedback collection
- **Template-based rendering** ensuring consistent specification formatting
- **Cross-reference management** between specifications, designs, and tasks
- **Quality assurance** through automated validation and quality gates

## Key Components

### 1. Template Engine (`metagpt/openspec/template_engine.py`)

Jinja2-based template system for generating OpenSpec-compliant specifications:

```python
from metagpt.openspec import OpenSpecTemplateEngine

template_engine = OpenSpecTemplateEngine()
result = template_engine.render_requirement(
    requirement_name="My Requirements",
    requirements=[...]
)
```

### 2. Data Models (`metagpt/openspec/models/`)

Pydantic models for OpenSpec specification structure:

- `OpenSpecRequirement`: Complete requirement specification
- `Requirement`: Individual requirement with scenarios
- `Scenario`: Gherkin-style scenario definition
- `OpenSpecDesign`: Design specification with component mappings

### 3. Validation Framework (`metagpt/openspec/validators/`)

Multi-level validation system:

```python
from metagpt.openspec import OpenSpecValidator, OpenSpecRequirement

validator = OpenSpecValidator(strict_mode=False)
result = validator.validate(requirement_spec)
print(result.get_summary())
```

### 4. Enhanced WritePRD (`metagpt/actions/write_prd_openspec.py`)

OpenSpec-enhanced PRD generation:

- Automatic requirement extraction and structuring
- LLM-powered scenario generation
- Built-in validation
- Fallback to original WritePRD behavior

### 5. Updated Product Manager (`metagpt/roles/product_manager.py`)

Enhanced Product Manager with OpenSpec support:

- `use_openspec` flag to enable/disable OpenSpec mode
- Automatic action selection based on mode
- `set_openspec_mode()` method for runtime configuration

### 6. Cross-Reference Management (`metagpt/openspec/cross_ref/`)

Systems for managing relationships between specifications:

- `RequirementCrossReferenceManager`: Requirements and their relationships
- `DesignCrossReferenceManager`: Design-to-requirement traceability
- `TaskTraceabilityManager`: End-to-end requirement-to-task traceability
- Impact analysis and dependency tracking

### 7. Review Orchestration (`metagpt/openspec/review/`)

Comprehensive review workflow management:

- `ReviewOrchestrator`: Automated review workflow coordination
- Multi-stage validation with quality gates
- Stakeholder feedback collection and processing
- Improvement suggestion generation
- Quality gate enforcement with configurable criteria

### 8. Enhanced Role Integration

All core MetaGPT roles now support OpenSpec:

- **ProductManager**: `WritePRDWithOpenSpec` with OpenSpec mode toggle
- **Architect**: `WriteDesignWithOpenSpec` with requirement traceability
- **ProjectManager**: `WriteTasksWithOpenSpec` with task-to-requirement mapping

## Usage

### Basic Usage

```python
from metagpt.roles.product_manager import ProductManager

# Create Product Manager with OpenSpec enabled
pm = ProductManager(use_openspec=True)

# Or toggle OpenSpec mode at runtime
pm.set_openspec_mode(True)
```

### OpenSpec Task Generation

```python
from metagpt.actions.write_tasks_openspec import WriteTasksWithOpenSpec
from metagpt.openspec import OpenSpecTaskSpecification, ImplementationTask, TaskPriority

# Create OpenSpec-enabled task generator
task_writer = WriteTasksWithOpenSpec(use_openspec=True)

# Generate tasks from design
task_spec = await task_writer.generate_openspec_tasks(
    design_content="System design content here",
    requirements=[{"id": "REQ_001", "title": "User Authentication"}]
)

# Task specification follows OpenSpec format
print(f"Generated {task_spec.total_tasks} tasks")
print(f"Overall progress: {task_spec.overall_progress}%")
```

### OpenSpec Design Generation

```python
from metagpt.actions.design_api_openspec import WriteDesignWithOpenSpec
from metagpt.openspec import OpenSpecDesign, DesignComponent, RequirementMapping

# Create OpenSpec-enabled design generator
design_writer = WriteDesignWithOpenSpec(use_openspec=True)

# Generate design from requirements
design_spec = await design_writer.run(
    prd=openspec_requirement_spec
)

# Design specification includes requirement mappings
print(f"Generated {len(design_spec.design_components)} components")
print(f"Requirements mapped: {len(design_spec.requirements_mapping)}")
```

### Review Orchestration

```python
from metagpt.openspec import ReviewOrchestrator, ReviewPriority

# Create review orchestrator
orchestrator = ReviewOrchestrator()

# Submit specification for review
review_id = await orchestrator.submit_for_review(
    item_type="requirement",
    item_id="REQ_001",
    content=requirement_spec,
    priority=ReviewPriority.HIGH
)

# Wait for review completion and get status
status = orchestrator.get_review_status(review_id)
print(f"Review stage: {status['stage']}")
print(f"Quality gates passed: {status['stage'] == 'completed'}")

# Add stakeholder feedback
await orchestrator.add_stakeholder_feedback(
    review_id=review_id,
    stakeholder_id="product_manager",
    feedback_type="suggestion",
    category="clarity",
    severity="medium",
    message="Make requirement more specific",
    suggestions=["Add measurable criteria"]
)
```

### Direct OpenSpec Usage

```python
from metagpt.openspec import OpenSpecRequirement, Requirement, Scenario, OpenSpecValidator

# Create a requirement specification
spec = OpenSpecRequirement(
    name="User Authentication",
    description="Requirements for user authentication system",
    added_requirements=[
        Requirement(
            title="User Login",
            description="Users must be able to log in with credentials",
            scenarios=[
                Scenario(
                    name="Successful Login",
                    given="User has valid credentials",
                    when="User submits login form",
                    then="User is authenticated and redirected to dashboard"
                )
            ]
        )
    ]
)

# Validate the specification
validator = OpenSpecValidator()
result = validator.validate(spec)
print(f"Valid: {result.is_valid}")
print(f"Issues: {result.get_summary()}")

# Export to markdown
markdown = spec.to_markdown()
print(markdown)
```

### Template Customization

```python
from metagpt.openspec import OpenSpecTemplateEngine

# Create custom template
template_engine = OpenSpecTemplateEngine()
template_engine.add_template("custom_requirement.j2", """
# {{ requirement_name }}

{{ description }}

{% for req in requirements %}
## {{ req.title }}
{{ req.description }}
{% endfor %}
""")

# Render with custom template
result = template_engine.render_custom_template("custom_requirement.j2", ...)
```

## OpenSpec Format

The integration supports the OpenSpec specification format:

```markdown
# Requirement Specification Name

## ADDED Requirements

### Requirement: Requirement Title
Requirement description here.

#### Scenario: Scenario Name
**Given** Precondition
**When** Action occurs
**Then** Expected outcome

## MODIFIED Requirements

### Requirement: Modified Requirement Title
Complete modified requirement description with scenarios.

## REMOVED Requirements

### Requirement: Removed Requirement Title
**Reason**: Reason for removal
**Migration**: Migration guidance
```

## Validation Features

The validator checks for:

- **Format Compliance**: Proper OpenSpec markdown structure
- **Scenario Completeness**: Gherkin elements (Given/When/Then)
- **Requirement Quality**: Descriptive titles and adequate descriptions
- **Cross-Reference Consistency**: Valid dependencies and mappings
- **Architecture Validation**: Component relationships and dependencies

Validation results include:

- **Errors**: Critical issues that must be fixed
- **Warnings**: Issues that should be reviewed
- **Info**: Informational messages

## Integration Points

### Product Manager Integration

The Product Manager role now supports OpenSpec through:

1. **Automatic Action Selection**: Uses `WritePRDWithOpenSpec` when OpenSpec is enabled
2. **Mode Configuration**: `use_openspec` flag and `set_openspec_mode()` method
3. **Backward Compatibility**: Falls back to original WritePRD if needed

### File Structure

```
metagpt/openspec/
├── __init__.py
├── template_engine.py
├── models/
│   ├── __init__.py
│   ├── requirement.py
│   ├── design.py
│   └── task.py
├── validators/
│   ├── __init__.py
│   └── base_validator.py
├── cross_ref/
│   ├── __init__.py
│   ├── requirement_manager.py
│   ├── design_manager.py
│   └── task_manager.py
├── review/
│   ├── __init__.py
│   └── orchestrator.py
├── templates/
│   ├── requirement.j2
│   ├── design.j2
│   └── task.j2
└── tests/
    ├── test_openspec_integration.py
    └── test_openspec_components.py

# Enhanced Actions
metagpt/actions/
├── write_prd_openspec.py
├── design_api_openspec.py
└── write_tasks_openspec.py

# Enhanced Roles
metagpt/roles/
├── product_manager.py      # Enhanced with OpenSpec support
├── architect.py            # Enhanced with OpenSpec support
└── project_manager.py      # Enhanced with OpenSpec support
```

### Task Traceability Management

```python
from metagpt.openspec.cross_ref.task_manager import TaskTraceabilityManager

# Task traceability management
traceability_manager = TaskTraceabilityManager()
traceability_manager.add_task_specification(task_spec)

# Get requirement coverage
coverage = traceability_manager.get_requirement_to_task_coverage()
print(f"Requirements covered: {sum(1 for c in coverage.values() if c['fully_covered'])}")

# Get end-to-end traceability
e2e_trace = traceability_manager.get_end_to_end_traceability("REQ_001")
print(f"Tasks for REQ_001: {len(e2e_trace['tasks'])}")

# Generate traceability report
report = traceability_manager.generate_traceability_report("markdown")
```

## Benefits

1. **Improved Quality**: Structured specifications with validation reduce ambiguity
2. **End-to-End Traceability**: Clear links from requirements through design to tasks and implementation
3. **Comprehensive Review Process**: Automated review orchestration with quality gates and stakeholder feedback
4. **Task Management**: Structured task generation with requirement traceability and progress tracking
5. **Change Management**: Proper tracking of specification evolution with impact analysis
6. **Quality Assurance**: Multi-level validation with detailed error reporting and improvement suggestions
7. **Cross-Reference Management**: Sophisticated dependency tracking and coverage analysis
8. **Industry Alignment**: Follows established specification management best practices (OpenSpec, Gherkin)
9. **Workflow Integration**: Seamless integration with MetaGPT's multi-agent architecture
10. **Backward Compatibility**: Existing workflows remain functional with optional OpenSpec enhancement

## Implementation Status

The current implementation covers comprehensive OpenSpec integration across all phases:

- ✅ **Phase 1**: Foundation and Template System
- ✅ **Phase 2**: Requirement Generation Integration
- ✅ **Phase 3**: Design Integration (WriteDesignWithOpenSpec)
- ✅ **Phase 4**: Task Generation Enhancement (WriteTasksWithOpenSpec)
- ✅ **Phase 5**: Cross-Reference Management (All specification types)
- ✅ **Phase 6**: Review and Validation Workflow (ReviewOrchestrator)
- ✅ **Phase 7**: Quality Gates and Feedback Processing
- ✅ **Phase 8**: Integration Testing and Documentation

## Current Capabilities

The OpenSpec integration now provides:

1. **Complete Specification Generation**: Requirements, designs, and tasks all follow OpenSpec format
2. **End-to-End Traceability**: From requirements through design to task implementation
3. **Automated Review Workflow**: Multi-stage validation with quality gates
4. **Stakeholder Feedback Management**: Structured feedback collection and processing
5. **Quality Assurance**: Comprehensive validation with detailed reporting
6. **Role Integration**: All MetaGPT roles enhanced with OpenSpec capabilities
7. **Backward Compatibility**: Existing workflows remain functional

## Examples

See the `examples/openspec_workflow/` directory for complete examples of OpenSpec integration usage.