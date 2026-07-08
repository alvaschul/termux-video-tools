"""
Built-in site extractors.
Automatically registered when imported.
"""

from .youtube import YouTubeExtractor
from .instagram import InstagramExtractor
from .tiktok import TikTokExtractor
from .twitch import TwitchExtractor
from .twitter import TwitterExtractor
from .generic import GenericExtractor

from ..registry import ExtractorRegistry

# Auto-register all built-in extractors
ExtractorRegistry.register("youtube", YouTubeExtractor)
ExtractorRegistry.register("instagram", InstagramExtractor)
ExtractorRegistry.register("tiktok", TikTokExtractor)
ExtractorRegistry.register("twitch", TwitchExtractor)
ExtractorRegistry.register("twitter", TwitterExtractor)
ExtractorRegistry.register("generic", GenericExtractor)

__all__ = [
    "YouTubeExtractor",
    "InstagramExtractor",
    "TikTokExtractor",
    "TwitchExtractor",
    "TwitterExtractor",
    "GenericExtractor",
]
