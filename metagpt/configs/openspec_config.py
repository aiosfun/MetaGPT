#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2025/11/12
@Author  : OpenSpec Integration
@File    : openspec_config.py
"""

from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, validator


class ValidationMode(str, Enum):
    """OpenSpec validation modes"""
    STRICT = "strict"
    LENIENT = "lenient"
    PERMISSIVE = "permissive"


class OutputFormat(str, Enum):
    """OpenSpec output formats"""
    OPENSPEC = "openspec"
    LEGACY = "legacy"


class ReviewMode(str, Enum):
    """OpenSpec review modes"""
    INTERACTIVE = "interactive"
    AUTO = "auto"
    SKIP = "skip"


class ValidationConfig(BaseModel):
    """Configuration for OpenSpec validation"""
    strict_mode: bool = Field(default=True, description="Enable strict validation mode")
    max_errors: int = Field(default=100, description="Maximum number of errors to report")
    custom_rules: List[Dict[str, str]] = Field(default_factory=list, description="Custom validation rules")
    exit_on_error: bool = Field(default=True, description="Exit on validation error")

    @validator('max_errors')
    def validate_max_errors(cls, v):
        if v < 1:
            raise ValueError("max_errors must be at least 1")
        return v


class TemplateConfig(BaseModel):
    """Configuration for OpenSpec templates"""
    template_dir: Optional[str] = Field(default=None, description="Custom template directory")
    custom_templates: Dict[str, str] = Field(default_factory=dict, description="Custom template definitions")
    template_validation: bool = Field(default=True, description="Validate template syntax")

    @validator('template_dir')
    def validate_template_dir(cls, v):
        if v and not v.strip():
            return None
        return v


class WorkflowConfig(BaseModel):
    """Configuration for OpenSpec workflows"""
    enable_review_loop: bool = Field(default=True, description="Enable review loop")
    auto_approve_threshold: float = Field(default=0.9, description="Auto-approval threshold")
    max_review_cycles: int = Field(default=3, description="Maximum review cycles")
    review_timeout: int = Field(default=300, description="Review timeout in seconds")

    @validator('auto_approve_threshold')
    def validate_threshold(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError("auto_approve_threshold must be between 0.0 and 1.0")
        return v

    @validator('max_review_cycles')
    def validate_review_cycles(cls, v):
        if v < 1:
            raise ValueError("max_review_cycles must be at least 1")
        return v

    @validator('review_timeout')
    def validate_review_timeout(cls, v):
        if v < 30:
            raise ValueError("review_timeout must be at least 30 seconds")
        return v


class CLIToolConfig(BaseModel):
    """Configuration for CLI tools"""
    tool_path: str = Field(default="openspec", description="Path to OpenSpec CLI executable")
    fallback_enabled: bool = Field(default=True, description="Enable fallback mechanisms")
    timeout: int = Field(default=60, description="CLI execution timeout in seconds")
    retry_attempts: int = Field(default=3, description="Number of retry attempts")

    @validator('timeout')
    def validate_timeout(cls, v):
        if v < 10:
            raise ValueError("timeout must be at least 10 seconds")
        return v

    @validator('retry_attempts')
    def validate_retry_attempts(cls, v):
        if v < 0:
            raise ValueError("retry_attempts must be non-negative")
        return v


class OpenSpecConfig(BaseModel):
    """Comprehensive OpenSpec configuration"""

    # Core OpenSpec settings
    enabled: bool = Field(default=True, description="Enable OpenSpec integration")
    cli_path: str = Field(default="openspec", description="Path to OpenSpec CLI executable")
    validation_mode: ValidationMode = Field(default=ValidationMode.STRICT, description="Validation mode")
    output_format: OutputFormat = Field(default=OutputFormat.OPENSPEC, description="Output format")
    change_tracking: bool = Field(default=True, description="Enable change tracking")
    auto_validate: bool = Field(default=True, description="Automatically validate generated content")
    review_mode: ReviewMode = Field(default=ReviewMode.INTERACTIVE, description="Review mode")
    workspace_path: str = Field(default="~/.metagpt/openspec", description="OpenSpec workspace directory")

    # Sub-configurations
    validation: ValidationConfig = Field(default_factory=ValidationConfig, description="Validation configuration")
    templates: TemplateConfig = Field(default_factory=TemplateConfig, description="Template configuration")
    workflow: WorkflowConfig = Field(default_factory=WorkflowConfig, description="Workflow configuration")
    cli_tools: CLIToolConfig = Field(default_factory=CLIToolConfig, description="CLI tools configuration")

    @validator('workspace_path')
    def validate_workspace_path(cls, v):
        if not v or not v.strip():
            raise ValueError("workspace_path cannot be empty")
        return v.strip()

    @validator('cli_path')
    def validate_cli_path(cls, v):
        if not v or not v.strip():
            raise ValueError("cli_path cannot be empty")
        return v.strip()

    def is_enabled(self) -> bool:
        """Check if OpenSpec is enabled"""
        return self.enabled

    def is_validation_strict(self) -> bool:
        """Check if validation is in strict mode"""
        return self.validation_mode == ValidationMode.STRICT

    def is_interactive_review(self) -> bool:
        """Check if interactive review is enabled"""
        return self.review_mode == ReviewMode.INTERACTIVE

    def should_track_changes(self) -> bool:
        """Check if change tracking is enabled"""
        return self.change_tracking

    def get_workspace_path(self) -> str:
        """Get the workspace path"""
        return self.workspace_path

    def get_cli_path(self) -> str:
        """Get the CLI path"""
        return self.cli_path

    class Config:
        """Pydantic configuration"""
        use_enum_values = True
        extra = "forbid"  # Prevent additional fields
        validate_assignment = True