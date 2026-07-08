"""
TikTok video extractor.
"""

from typing import Dict, Optional, Any
import re

from ..base import BaseExtractor, ExtractorInfo


class TikTokExtractor(BaseExtractor):
    """
    Extractor for TikTok videos.
    Supports single videos and user profiles.
    """
    
    info = ExtractorInfo(
        name="tiktok",
        domains=["tiktok.com", "www.tiktok.com", "m.tiktok.com", "vt.tiktok.com"],
        requires_auth=False,
        supports_playlists=False,
        description="TikTok video extractor"
    )
    
    def can_extract(self, url: str) -> bool:
        """Check if URL is a TikTok video URL."""
        return self.validate_url(url) and bool(re.search(r'/video/\d+', url))
    
    def extract_info(self, url: str, cookies_path: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """
        Extract TikTok video information.
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
            
            if cookies_path:
                ydl_opts["cookiefile"] = cookies_path
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
            
            return {
                "title": info.get("title", "TikTok Video"),
                "description": info.get("description", ""),
                "formats": self._normalize_formats(info.get("formats", [])),
                "uploader": info.get("creator", ""),
                "duration": info.get("duration", 0),
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
        """TikTok default: best quality."""
        return "best"
