"""
Instagram video/reel extractor.
"""

from typing import Dict, Optional, Any
import re

from ..base import BaseExtractor, ExtractorInfo


class InstagramExtractor(BaseExtractor):
    """
    Extractor for Instagram videos, reels, and posts.
    Requires authentication (cookies) for most content.
    """
    
    info = ExtractorInfo(
        name="instagram",
        domains=["instagram.com", "www.instagram.com"],
        requires_auth=True,
        supports_playlists=False,
        description="Instagram video and reel extractor"
    )
    
    def can_extract(self, url: str) -> bool:
        """Check if URL is an Instagram media URL."""
        return self.validate_url(url) and bool(re.search(r'/(?:p|reel|tv)/', url))
    
    def extract_info(self, url: str, cookies_path: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """
        Extract Instagram video information.
        Requires cookies for authentication.
        """
        if not cookies_path:
            return {
                "error": "Instagram requires authentication. Please provide cookies.txt",
                "formats": []
            }
        
        try:
            import yt_dlp
        except ImportError:
            return {
                "error": "yt-dlp not installed",
                "formats": []
            }
        
        try:
            ydl_opts = {
                "skip_download": True,
                "quiet": True,
                "no_warnings": True,
                "cookiefile": cookies_path,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
            
            return {
                "title": info.get("title", "Instagram Video"),
                "description": info.get("description", ""),
                "formats": self._normalize_formats(info.get("formats", [])),
                "uploader": info.get("uploader", ""),
            }
        except Exception as e:
            return {"error": str(e), "formats": []}
    
    def _normalize_formats(self, formats: list) -> list:
        """Normalize format information."""
        normalized = []
        for fmt in formats:
            normalized.append({
                "format_id": fmt.get("format_id", ""),
                "ext": fmt.get("ext", "mp4"),
                "height": fmt.get("height"),
                "filesize": fmt.get("filesize"),
            })
        return normalized
    
    def get_default_format(self) -> str:
        """Instagram default: best available format."""
        return "best"
    
    def requires_cookies(self) -> bool:
        """Instagram always requires cookies."""
        return True
