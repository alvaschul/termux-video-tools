"""
YouTube video extractor.
"""

from typing import Dict, Optional, Any
import re

from ..base import BaseExtractor, ExtractorInfo


class YouTubeExtractor(BaseExtractor):
    """
    Extractor for YouTube videos.
    Supports single videos, playlists, and live streams.
    """
    
    info = ExtractorInfo(
        name="youtube",
        domains=["youtube.com", "youtu.be", "m.youtube.com"],
        supports_playlists=True,
        supports_live=True,
        description="YouTube video and playlist extractor"
    )
    
    def can_extract(self, url: str) -> bool:
        """Check if URL is a YouTube URL."""
        return self.validate_url(url) and self._extract_video_id(url) is not None
    
    def extract_info(self, url: str, cookies_path: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """
        Extract YouTube video information.
        Uses yt-dlp as the underlying extractor.
        """
        try:
            import yt_dlp
        except ImportError:
            return {
                "error": "yt-dlp not installed",
                "formats": []
            }
        
        video_id = self._extract_video_id(url)
        if not video_id:
            return {"error": "Could not extract video ID", "formats": []}
        
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
                "title": info.get("title", "Unknown"),
                "description": info.get("description", ""),
                "duration": info.get("duration", 0),
                "uploader": info.get("uploader", ""),
                "formats": self._normalize_formats(info.get("formats", [])),
                "is_playlist": info.get("_type") == "playlist",
                "entries": len(info.get("entries", [])) if info.get("_type") == "playlist" else None,
            }
        except Exception as e:
            return {"error": str(e), "formats": []}
    
    def _extract_video_id(self, url: str) -> Optional[str]:
        """Extract YouTube video ID from URL."""
        patterns = [
            r'youtube\.com/watch\?v=([\w-]{11})',
            r'youtu\.be/([\w-]{11})',
            r'youtube\.com/shorts/([\w-]{11})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None
    
    def _normalize_formats(self, formats: list) -> list:
        """Normalize format information."""
        normalized = []
        for fmt in formats:
            normalized.append({
                "format_id": fmt.get("format_id", ""),
                "ext": fmt.get("ext", "mp4"),
                "height": fmt.get("height"),
                "width": fmt.get("width"),
                "fps": fmt.get("fps"),
                "acodec": fmt.get("acodec"),
                "vcodec": fmt.get("vcodec"),
                "filesize": fmt.get("filesize"),
            })
        return normalized
    
    def get_default_format(self) -> str:
        """YouTube default: best quality with audio."""
        return "bestvideo+bestaudio/best"
