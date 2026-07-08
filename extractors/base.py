"""
Base extractor class defining the plugin interface.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
import re


@dataclass
class ExtractorInfo:
    """Metadata for an extractor."""
    name: str                           # e.g., "youtube"
    domains: List[str]                  # e.g., ["youtube.com", "youtu.be"]
    requires_auth: bool = False         # Whether cookies/auth tokens are needed
    supports_playlists: bool = False    # Whether the site supports playlists
    supports_live: bool = False         # Whether live streams are supported
    description: str = ""


class BaseExtractor(ABC):
    """
    Abstract base class for site-specific video extractors.
    
    Each extractor handles extraction logic for a specific website or group of sites.
    Extractors can override methods to provide site-specific behavior (auth, format selection, etc.)
    """
    
    info: ExtractorInfo
    
    def __init__(self):
        """Initialize the extractor."""
        if not hasattr(self, 'info') or self.info is None:
            raise NotImplementedError(f"{self.__class__.__name__} must define 'info' attribute")
    
    @abstractmethod
    def can_extract(self, url: str) -> bool:
        """
        Check if this extractor can handle the given URL.
        
        Args:
            url: The video URL to check
        
        Returns:
            True if this extractor can handle the URL, False otherwise
        """
        pass
    
    @abstractmethod
    def extract_info(self, url: str, cookies_path: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """
        Extract video metadata and format information from the URL.
        
        Args:
            url: The video URL
            cookies_path: Optional path to cookies.txt file for authentication
            **kwargs: Additional extractor-specific arguments
        
        Returns:
            Dictionary with keys:
                - title: str - video title
                - formats: List[Dict] - available formats with keys:
                    - format_id: str
                    - url: str - direct URL if available
                    - ext: str - file extension
                    - height: int - video height (if applicable)
                    - bitrate: int - audio bitrate (if applicable)
                - direct_url: Optional[str] - direct download URL if available
                - is_playlist: bool - whether this is a playlist
                - entries: Optional[List[Dict]] - playlist entries if applicable
        """
        pass
    
    def get_default_format(self) -> str:
        """
        Get the default format for this site.
        Override in subclasses for site-specific defaults.
        """
        return "best"
    
    def get_custom_headers(self) -> Dict[str, str]:
        """
        Get custom headers needed for requests to this site.
        Override in subclasses to add site-specific headers.
        """
        return {}
    
    def requires_cookies(self) -> bool:
        """
        Check if this extractor requires cookies for extraction.
        """
        return self.info.requires_auth
    
    def validate_url(self, url: str) -> bool:
        """
        Validate URL format for this site.
        Override in subclasses for stricter validation.
        """
        for domain in self.info.domains:
            if domain.lower() in url.lower():
                return True
        return False
