"""Image Utility Toolbox - Modular Headless Image Processing Engine."""

from image_toolbox.core.context import ImageContext
from image_toolbox.core.base import BaseOperation
from image_toolbox.core.pipeline import PipelineEngine
from image_toolbox.core.registry import registry, register_operation
from image_toolbox.core.i18n import i18n, _
from image_toolbox.core.exceptions import (
    ToolboxError,
    ValidationError,
    OperationError,
    TargetSizeUnreachableError,
    CorruptImageError,
)
from image_toolbox.services.compressor_service import TargetSizeCompressorService
from image_toolbox.services.batch_runner import BatchProcessingRunner, BatchItemResult

# 22 operasyonu deftere yükle
import image_toolbox.operations

__version__ = "0.1.0"

__all__ = [
    "ImageContext",
    "BaseOperation",
    "PipelineEngine",
    "registry",
    "register_operation",
    "TargetSizeCompressorService",
    "BatchProcessingRunner",
    "BatchItemResult",
    "ToolboxError",
    "ValidationError",
    "OperationError",
    "TargetSizeUnreachableError",
    "CorruptImageError",
    "i18n",
    "_",
    "__version__",
]
