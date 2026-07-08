"""
Extractor registry for dynamic loader and site detection.
"""

from typing import Dict, Optional, Type, List
import logging
from urllib.parse import urlparse

from .base import BaseExtractor, ExtractorInfo

logger = logging.getLogger(__name__)


class ExtractorRegistry:
    """
    Registry for managing extractor plugins.
    Provides dynamic loading and URL-to-extractor mapping.
    """
    
    _extractors: Dict[str, Type[BaseExtractor]] = {}
    _domain_map: Dict[str, str] = {}  # Maps domain -> extractor_key
    
    @classmethod
    def register(cls, key: str, extractor_class: Type[BaseExtractor]) -> None:
        """
        Register an extractor.
        
        Args:
            key: Unique identifier for the extractor (e.g., "youtube")
            extractor_class: The extractor class to register
        """
        cls._extractors[key] = extractor_class
        
        # Extract domain mappings from extractor info
        try:
            instance = extractor_class()
            for domain in instance.info.domains:
                cls._domain_map[domain.lower()] = key
                logger.debug(f"Registered domain '{domain}' -> extractor '{key}'")
        except Exception as e:
            logger.warning(f"Could not instantiate {extractor_class.__name__} for registration: {e}")
    
    @classmethod
    def get_extractor(cls, key: str) -> Optional[BaseExtractor]:
        """
        Get an extractor instance by key.
        
        Args:
            key: The extractor identifier
        
        Returns:
            Extractor instance or None if not found
        """
        if key not in cls._extractors:
            logger.warning(f"Extractor '{key}' not found in registry")
            return None
        
        try:
            return cls._extractors[key]()
        except Exception as e:
            logger.error(f"Failed to instantiate extractor '{key}': {e}")
            return None
    
    @classmethod
    def find_extractor(cls, url: str) -> Optional[BaseExtractor]:
        """
        Find the appropriate extractor for a URL.
        
        Args:
            url: The video URL
        
        Returns:
            Extractor instance or None if no suitable extractor found
        """
        # Try domain-based lookup first
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        # Strip www. prefix
        if domain.startswith("www."):
            domain = domain[4:]
        
        if domain in cls._domain_map:
            extractor = cls.get_extractor(cls._domain_map[domain])
            if extractor and extractor.can_extract(url):
                return extractor
        
        # Fallback: try all registered extractors
        for key, extractor_class in cls._extractors.items():
            try:
                extractor = extractor_class()
                if extractor.can_extract(url):
                    return extractor
            except Exception as e:
                logger.debug(f"Extractor {key} failed: {e}")
                continue
        
        logger.warning(f"No suitable extractor found for URL: {url}")
        return None
    
    @classmethod
    def list_extractors(cls) -> Dict[str, ExtractorInfo]:
        """
        List all registered extractors with their info.
        
        Returns:
            Dictionary mapping extractor keys to their info
        """
        result = {}
        for key, extractor_class in cls._extractors.items():
            try:
                instance = extractor_class()
                result[key] = instance.info
            except Exception as e:
                logger.debug(f"Could not get info for {key}: {e}")
        return result
    
    @classmethod
    def get_supported_domains(cls) -> List[str]:
        """
        Get list of all supported domains.
        
        Returns:
            List of domain names
        """
        return list(cls._domain_map.keys())
