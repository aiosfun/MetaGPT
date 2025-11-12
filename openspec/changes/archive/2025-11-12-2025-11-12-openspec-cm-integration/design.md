# OpenSpec Comprehensive Integration Design

## Architecture Overview

This design presents a comprehensive OpenSpec integration system that combines core OpenSpec workflow capabilities with advanced configuration management and interactive review systems. The architecture enables MetaGPT to function as a complete specification-driven development platform while maintaining full backward compatibility.

## System Components

### 1. Core OpenSpec Integration Layer
```python
class OpenSpecIntegrationManager:
    """Manages core OpenSpec workflow components"""

    def __init__(self, config: OpenSpecConfig)
    def generate_requirement(self, user_input: str) -> OpenSpecRequirement
    def create_design(self, requirements: OpenSpecRequirement) -> OpenSpecDesign
    def create_tasks(self, design: OpenSpecDesign) -> OpenSpecTaskSpecification
    def validate_spec(self, spec: Any) -> ValidationResult
```

### 2. Configuration Management Layer
```python
class OpenSpecConfigManager:
    """Centralized configuration system for all OpenSpec components"""

    def __init__(self, config_paths: List[str])
    def load_config(self) -> OpenSpecConfig
    def validate_config(self, config: Dict) -> ValidationResult
    def watch_config(self, callback: Callable) -> None
    def get_setting(self, key: str, default=None) -> Any
```

### 3. Review Workflow Layer
```python
class OpenSpecReviewManager:
    """Manages interactive review loops and feedback processing"""

    def __init__(self, config: OpenSpecConfig)
    def initiate_review(self, spec: Any, review_type: str) -> ReviewSession
    def process_feedback(self, feedback: str, spec: Any) -> Any
    def track_review_history(self, session_id: str) -> ReviewHistory
```

## Key Architectural Decisions

### 1. Single Configuration Interface
**The system uses ONE configuration structure in MetaGPT's config2.yaml:**

```yaml
openspec:
  enabled: true
  cli_path: "openspec"
  validation_mode: "strict"
  output_format: "openspec"
  change_tracking: true
  auto_validate: true
  review_mode: "interactive"
  workspace_path: "openspec"
```

**Rationale**: Simple, single interface minimizes user complexity while providing comprehensive control over all OpenSpec features. No additional configuration files needed.

### 2. Configuration Schema Validation
- **Pydantic Models**: Strong typing and validation for the OpenSpecConfig structure
- **JSON Schema**: Machine-readable schema for tool integration
- **Environment Variable Override**: Support for METAGPT_OPENSPEC_* environment variables
- **Default Values**: Sensible defaults for all optional settings

**Trade-off**: Strong validation ensures configuration integrity while maintaining simplicity. Benefits include error prevention and automatic defaults.

### 3. Simple Configuration Management
- **Single Source of Truth**: Only config2.yaml openspec section
- **Environment Variable Override**: METAGPT_OPENSPEC_* for temporary changes
- **Validation Pipeline**: Configuration validation before application
- **Default Values**: Sensible defaults for all settings

**Simplicity**: Minimal configuration overhead while maintaining flexibility.

### 4. Core OpenSpec Integration Architecture
```python
class OpenSpecWorkflowManager:
    """Orchestrates the complete OpenSpec workflow process"""

    def __init__(self, config: OpenSpecConfig):
        self.config_manager = OpenSpecConfigManager(config.config_paths)
        self.template_engine = OpenSpecTemplateEngine(config.templates)
        self.validator = OpenSpecValidator(config.validation)
        self.review_manager = OpenSpecReviewManager(config.review)

    async def complete_workflow(self, user_requirement: str) -> WorkflowResult:
        """Execute complete OpenSpec workflow from requirement to tasks"""
        requirements = await self.generate_requirements(user_requirement)
        approved_requirements = await self.review_requirements(requirements)
        design = await self.create_design(approved_requirements)
        approved_design = await self.review_design(design)
        tasks = await self.create_tasks(approved_design)
        return WorkflowResult(requirements, design, tasks)
```

### 6. Interactive Review System Design
```python
class ReviewSession:
    """Manages a single interactive review session"""

    def __init__(self, session_id: str, spec_type: str, content: Any):
        self.session_id = session_id
        self.spec_type = spec_type  # 'requirement', 'design', 'task'
        self.content = content
        self.feedback_history = []
        self.status = ReviewStatus.IN_PROGRESS

    async def process_human_feedback(self, feedback: str) -> ReviewResult:
        """Process human feedback and apply changes"""
        parsed_feedback = self.parse_feedback(feedback)
        updated_content = self.apply_changes(parsed_feedback)
        validation_result = self.validate_changes(updated_content)

        if validation_result.is_valid:
            self.feedback_history.append(parsed_feedback)
            return ReviewResult(updated_content, True)
        else:
            return ReviewResult(updated_content, False, validation_result.errors)
```

**Integration**: Review system seamlessly integrates with MetaGPT's existing AskReview framework while providing OpenSpec-specific functionality.

### 7. MetaGPT Role Integration Strategy
```python
# Enhanced ProductManager with OpenSpec support
class ProductManager(RoleZero):
    use_openspec: bool = Field(default=True, description="Enable OpenSpec requirement generation")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.use_openspec:
            self.set_actions([
                PrepareDocuments(send_to=any_to_str(self)),
                WritePRDWithOpenSpec(use_openspec=True)
            ])
        else:
            self.set_actions([
                PrepareDocuments(send_to=any_to_str(self)),
                WritePRD()
            ])

    def set_openspec_mode(self, use_openspec: bool):
        """Runtime switching between OpenSpec and legacy modes"""
        self.use_openspec = use_openspec
        write_prd_action = WritePRDWithOpenSpec if use_openspec else WritePRD
        if self.use_fixed_sop:
            self.set_actions([PrepareDocuments(send_to=any_to_str(self)), write_prd_action])
```

**Backward Compatibility**: Roles can switch between OpenSpec and legacy modes at runtime without breaking existing functionality.

## Component Design

### Configuration Manager
```python
class OpenSpecConfigManager:
    def __init__(self, config_paths: List[str])
    def load_config(self) -> OpenSpecConfig
    def validate_config(self, config: Dict) -> ValidationResult
    def watch_config(self, callback: Callable) -> None
    def get_setting(self, key: str, default=None) -> Any
    def set_setting(self, key: str, value: Any) -> bool
```

### Configuration Models
```python
class ValidationConfig(BaseModel):
    strict_mode: bool = False
    max_errors: int = 100
    custom_rules: List[CustomRule] = []
    exit_on_error: bool = True

class TemplateConfig(BaseModel):
    template_dir: Optional[str] = None
    custom_templates: Dict[str, str] = {}
    template_validation: bool = True

class WorkflowConfig(BaseModel):
    enable_review_loop: bool = True
    auto_approve_threshold: float = 0.9
    max_review_cycles: int = 3
    review_timeout: int = 300

class OpenSpecConfig(BaseModel):
    enabled: bool = True
    cli_path: str = "openspec"
    validation_mode: str = "strict"  # strict, lenient, permissive
    output_format: str = "openspec"  # openspec, legacy
    change_tracking: bool = True
    auto_validate: bool = True
    review_mode: str = "interactive"  # interactive, auto, skip
    workspace_path: str = "openspec"
    validation: ValidationConfig = ValidationConfig()
    templates: TemplateConfig = TemplateConfig()
    workflow: WorkflowConfig = WorkflowConfig()
    cli_tools: CLIToolConfig = CLIToolConfig()
```

### MetaGPT config2.yaml Integration
```python
# Addition to metagpt/config2.py
from metagpt.configs.openspec_config import OpenSpecConfig

class Config(CLIParams, YamlModel):
    # ... existing fields ...

    # OpenSpec Configuration
    openspec: OpenSpecConfig = Field(default_factory=OpenSpecConfig)
```

### Integration Points
- **MetaGPT Config Integration**: OpenSpec configuration loaded through standard MetaGPT config system
- **Role Integration**: Each role (ProductManager, Architect, ProjectManager) reads configuration during initialization
- **Action Integration**: OpenSpec actions check configuration before execution
- **Tool Integration**: CLI tools use configuration for command construction and error handling

## Security Considerations

### Configuration Access Control
- **File Permissions**: Proper file system permissions for configuration files
- **Environment Variables**: Support for secure credential storage
- **Validation**: Input validation to prevent injection attacks

### Sensitive Data Handling
- **Encryption**: Support for encrypted configuration values
- **Key Management**: Integration with existing key management systems
- **Audit Trail**: Logging of configuration changes for security auditing

## Performance Implications

### Configuration Loading
- **Lazy Loading**: Configuration loaded on-demand to reduce startup time
- **Caching**: In-memory caching with file change detection
- **Validation Caching**: Cached validation results for unchanged configurations

### Runtime Overhead
- **Minimal Impact**: Configuration checks add <1ms overhead to operations
- **Background Processes**: File watching and validation run in background threads
- **Memory Usage**: Configuration objects are lightweight and shared

## Migration Strategy

### Phase 1: Core Infrastructure
1. Implement configuration models and manager
2. Add basic file-based configuration support
3. Integrate with existing OpenSpec components

### Phase 2: Advanced Features
1. Add hot reloading capabilities
2. Implement plugin system
3. Add validation schema and tools

### Phase 3: Tool Integration
1. Integrate with CLI tools
2. Add environment-specific configurations
3. Implement configuration documentation and examples

## Risk Assessment

### Technical Risks
- **Configuration Complexity**: Risk of overly complex configuration system
  - **Mitigation**: Strong validation and sensible defaults
- **Performance Impact**: Risk of configuration overhead
  - **Mitigation**: Efficient caching and lazy loading
- **Compatibility Issues**: Risk of breaking existing functionality
  - **Mitigation**: Comprehensive testing and backward compatibility

### Operational Risks
- **Configuration Errors**: Risk of misconfiguration causing system failures
  - **Mitigation**: Strong validation and error reporting
- **Learning Curve**: Risk of users struggling with new configuration options
  - **Mitigation**: Clear documentation and examples
- **Maintenance Overhead**: Risk of increased maintenance burden
  - **Mitigation**: Automated testing and configuration validation tools