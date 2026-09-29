"""Core package exports."""

from image_toolbox.core.base import BaseOperation
from image_toolbox.core.context import ImageContext
from image_toolbox.core.exceptions import (
    CorruptImageError,
    OperationError,
    TargetSizeUnreachableError,
    ToolboxError,
    ValidationError,
)
from image_toolbox.core.i18n import _, i18n
from image_toolbox.core.pipeline import PipelineEngine
from image_toolbox.core.registry import OperationRegistry, register_operation, registry

__all__ = [
    "BaseOperation",
    "ImageContext",
    "PipelineEngine",
    "OperationRegistry",
    "registry",
    "register_operation",
    "ToolboxError",
    "ValidationError",
    "OperationError",
    "TargetSizeUnreachableError",
    "CorruptImageError",
    "i18n",
    "_",
]
