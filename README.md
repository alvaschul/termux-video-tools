# termux-video-tools

Lightweight Termux toolset to download videos from many websites using yt-dlp, with optional aria2 acceleration and a small web UI.

## Features
- **Extensible Extractor System**: Plugin-based architecture for site-specific extraction
- **Multi-Site Support**: Built-in extractors for YouTube, Instagram, TikTok, Twitch, Twitter/X and fallback for 1000+ other sites
- **CLI wrapper (vidget)**: Command-line interface for quick downloads
- **Flask web UI**: Enqueue downloads and upload cookies.txt via browser
- **aria2 RPC integration**: Optional aria2 acceleration using aria2p
- **Cookie Support**: Per-site authentication for protected content
- **Smart Format Selection**: Site-specific format defaults and auto-selection
- **Live Stream Support**: Download live streams from supported platforms
- **Playlist Support**: Batch download playlists where supported

## Prerequisites
- Termux on Android
- Termux storage permission: run `termux-setup-storage` once

## Install
1. Place all files in `~/termux-video-tools`.
2. Make scripts executable:
   ```bash
   chmod +x ~/termux-video-tools/{installer.sh,vidget,video_server.py,start_aria2.sh}
   ```
3. Run the installer script to install packages:
   ```bash
   bash ~/termux-video-tools/installer.sh
   ```

## Usage

### Start aria2 (RPC) - Optional
```bash
~/termux-video-tools/start_aria2.sh
```

### Web UI
Start the web server:
```bash
vidget serve --port 8080
```
Open http://localhost:8080 on the device or http://<device-ip>:8080 from a machine on the same network.

### CLI Usage

Download a URL:
```bash
vidget download "https://example.com/video"
```

Download with specific format:
```bash
vidget download "https://youtube.com/watch?v=..." --format "bestvideo+bestaudio/best"
```

Use aria2 RPC for faster downloads:
```bash
vidget download "https://example.com/video" --use-aria2
```

Provide cookies for authenticated sites:
```bash
vidget download "https://instagram.com/..." --cookies /path/to/cookies.txt
```

Get job status:
```bash
vidget status <JOB_ID>
```

## Supported Sites

The engine includes built-in extractors for:
- **YouTube**: Videos, playlists, shorts, live streams
- **Instagram**: Videos, reels, posts (requires cookies)
- **TikTok**: Individual videos
- **Twitch**: Streams and VODs
- **Twitter/X**: Tweets with video

Additionally supports **1000+ sites** via yt-dlp fallback including:
- Vimeo
- Facebook
- Dailymotion
- Reddit
- Bilibili
- Niconico
- And many more...

## Architecture

### Extractor Plugin System

The refactored engine uses an extensible extractor architecture:

```
extractors/
  base.py           - BaseExtractor abstract class
  registry.py       - ExtractorRegistry for dynamic loading
  sites/
    youtube.py      - YouTube-specific extractor
    instagram.py    - Instagram-specific extractor
    tiktok.py       - TikTok-specific extractor
    twitch.py       - Twitch-specific extractor
    twitter.py      - Twitter/X-specific extractor
    generic.py      - Fallback for all other sites
```

### Adding a New Site Extractor

1. Create a new file in `extractors/sites/`:
   ```python
   from extractors.base import BaseExtractor, ExtractorInfo
   
   class MyExtractor(BaseExtractor):
       info = ExtractorInfo(
           name="mysite",
           domains=["mysite.com", "www.mysite.com"],
           requires_auth=False,
           supports_playlists=True,
           description="Extractor for mysite"
       )
       
       def can_extract(self, url: str) -> bool:
           return self.validate_url(url)
       
       def extract_info(self, url: str, cookies_path=None, **kwargs):
           # Your extraction logic here
           return {"formats": [], "title": "..."}
   ```

2. Register it in `extractors/sites/__init__.py`:
   ```python
   from .mysite import MyExtractor
   ExtractorRegistry.register("mysite", MyExtractor)
   ```

### How It Works

1. **URL Detection**: When a URL is submitted, `ExtractorRegistry.find_extractor()` determines the appropriate handler
2. **Site-Specific Extraction**: The selected extractor retrieves format info, metadata, and direct URLs
3. **Download Processing**: Extracted info is passed to yt-dlp or aria2 for actual download
4. **Job Tracking**: All downloads are queued and tracked with persistent storage

## Notes
- For some sites, cookies (exported from your browser as cookies.txt) are required
- Some streams (DRM/protected) cannot be downloaded
- aria2c must be running with RPC enabled (start_aria2.sh does that)
- Live streams may require specific handling depending on the platform

## Troubleshooting

### "No suitable extractor found"
The URL's site may not be supported. Try the generic extractor with yt-dlp directly:
```bash
yt-dlp "<URL>" --dump-json | head -50
```

### Instagram/Private content downloads fail
Make sure to provide valid cookies:
```bash
vidget download "<URL>" --cookies ~/.netrc
```

### aria2 connection fails
Ensure aria2 is running:
```bash
~/termux-video-tools/start_aria2.sh
```

## License
MIT
