"""
Generic/fallback video extractor for unsupported sites.
Uses yt-dlp as a base for maximum compatibility.
"""

from typing import Dict, Optional, Any

from ..base import BaseExtractor, ExtractorInfo


class GenericExtractor(BaseExtractor):
    """
    Generic extractor that works with any yt-dlp supported site.
    This is a fallback for sites without custom extractors.
    """
    
    info = ExtractorInfo(
        name="generic",
        domains=[],  # Matches any domain not specifically handled
        requires_auth=False,
        supports_playlists=True,
        supports_live=True,
        description="Generic extractor for any yt-dlp supported site"
    )
    
    def can_extract(self, url: str) -> bool:
        """Generic extractor can attempt to extract any URL."""
        try:
            import yt_dlp
            # Try to get supported extractors from yt-dlp
            return True
        except ImportError:
            return False
    
    def extract_info(self, url: str, cookies_path: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """
        Extract video information using yt-dlp as fallback.
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
                "title": info.get("title", "Video"),
                "description": info.get("description", ""),
                "formats": self._normalize_formats(info.get("formats", [])),
                "uploader": info.get("uploader", ""),
                "is_playlist": info.get("_type") == "playlist",
                "entries": len(info.get("entries", [])) if info.get("_type") == "playlist" else None,
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
                "width": fmt.get("width"),
                "filesize": fmt.get("filesize"),
            })
        return normalized
    
    def get_default_format(self) -> str:
        """Generic default: best quality."""
        return "best"
