"""
Site-specific extractors for video tools engine.
Provides a plugin system to support custom extraction logic per site.
"""

from .base import BaseExtractor, ExtractorInfo
from .registry import ExtractorRegistry

__all__ = ["BaseExtractor", "ExtractorInfo", "ExtractorRegistry"]
