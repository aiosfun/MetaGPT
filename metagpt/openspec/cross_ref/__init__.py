"""
OpenSpec Cross-Reference Management

Manages cross-references between specifications, requirements, and implementations.
"""

from .requirement_manager import RequirementCrossReferenceManager
from .design_manager import DesignCrossReferenceManager

__all__ = [
    "RequirementCrossReferenceManager",
    "DesignCrossReferenceManager",
]