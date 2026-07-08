"""
Twitch stream and VOD extractor.
"""

from typing import Dict, Optional, Any
import re

from ..base import BaseExtractor, ExtractorInfo


class TwitchExtractor(BaseExtractor):
    """
    Extractor for Twitch streams and VODs.
    Supports live streams and recorded videos.
    """
    
    info = ExtractorInfo(
        name="twitch",
        domains=["twitch.tv", "www.twitch.tv", "m.twitch.tv"],
        requires_auth=False,
        supports_live=True,
        description="Twitch stream and VOD extractor"
    )
    
    def can_extract(self, url: str) -> bool:
        """Check if URL is a Twitch URL."""
        return self.validate_url(url) and bool(
            re.search(r'/(\w+)(?:/videos|/(?!video))?$', url) or 
            re.search(r'/videos/\d+', url)
        )
    
    def extract_info(self, url: str, cookies_path: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """
        Extract Twitch stream/VOD information.
        """
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
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
            
            is_live = info.get("is_live", False)
            
            return {
                "title": info.get("title", "Twitch Stream"),
                "description": info.get("description", ""),
                "formats": self._normalize_formats(info.get("formats", [])),
                "uploader": info.get("uploader", ""),
                "is_live": is_live,
                "duration": info.get("duration") if not is_live else None,
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
                "fps": fmt.get("fps"),
            })
        return normalized
    
    def get_default_format(self) -> str:
        """Twitch default: best available quality."""
        return "best"
