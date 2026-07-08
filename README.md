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
- **Site Detection**: Automatic extractor detection with `/api/detect` endpoint
- **Extractor API**: Query `/api/extractors` to see all supported sites

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

**Web UI Features:**
- 🎬 Real-time site detection when pasting URLs
- 📋 Live download queue with status tracking
- 🌐 Full list of supported extractors with capabilities
- 📥 Drag-and-drop cookies file upload
- 🔄 Automatic job refresh every 2 seconds
- ♻️ Retry failed downloads

### CLI Usage

**List all available extractors:**
```bash
python3 video_server.py --list-extractors
```

**Detect extractor for a URL:**
```bash
python3 video_server.py --detect "https://youtube.com/watch?v=..."
```

**Download a URL:**
```bash
vidget download "https://example.com/video"
```

**Download with specific format:**
```bash
vidget download "https://youtube.com/watch?v=..." --format "bestvideo+bestaudio/best"
```

**Use aria2 RPC for faster downloads:**
```bash
vidget download "https://example.com/video" --use-aria2
```

**Provide cookies for authenticated sites:**
```bash
vidget download "https://instagram.com/p/..." --cookies /path/to/cookies.txt
```

**Get job status:**
```bash
vidget status <JOB_ID>
```

## Supported Sites

### Built-in Extractors (Optimized)
- **YouTube** - Videos, playlists, shorts, live streams
- **Instagram** - Videos, reels, posts (requires cookies)
- **TikTok** - Individual videos
- **Twitch** - Streams and VODs
- **Twitter/X** - Tweets with video

### Generic Fallback (1000+ sites via yt-dlp)
Including: Vimeo, Facebook, Dailymotion, Reddit, Bilibili, Niconico, Pinterest, Spotify, SoundCloud, and many more...

## Architecture

### Extractor Plugin System

The refactored engine uses an extensible extractor architecture:

```
extractors/
  __init__.py         - Package exports
  base.py             - BaseExtractor abstract class
  registry.py         - ExtractorRegistry for dynamic loading
  sites/
    __init__.py       - Auto-registers all built-in extractors
    youtube.py        - YouTube-specific extractor
    instagram.py      - Instagram-specific extractor
    tiktok.py         - TikTok-specific extractor
    twitch.py         - Twitch-specific extractor
    twitter.py        - Twitter/X-specific extractor
    generic.py        - Fallback for all other sites
```

### API Endpoints

#### GET `/api/extractors`
List all available extractors and supported domains.

**Response:**
```json
{
  "total_extractors": 6,
  "total_domains": 5,
  "extractors": {
    "youtube": {
      "name": "youtube",
      "domains": ["youtube.com", "youtu.be"],
      "requires_auth": false,
      "supports_playlists": true,
      "supports_live": true,
      "description": "YouTube video and playlist extractor"
    }
  },
  "supported_domains": ["instagram.com", "tiktok.com"]
}
```

#### POST `/api/detect`
Detect which extractor will handle a given URL.

**Request:**
```json
{"url": "https://youtube.com/watch?v=..."}
```

**Response:**
```json
{
  "extractor": "youtube",
  "requires_auth": false,
  "supports_playlists": true,
  "supports_live": true,
  "description": "YouTube video and playlist extractor",
  "default_format": "bestvideo+bestaudio/best"
}
```

#### POST `/api/download`
Enqueue a video download.

**Request (Form data):**
```
url: https://example.com/video
format: best
use_aria2: false
cookies_file: (optional file)
```

**Response:**
```json
{"job_id": "abc-123-def"}
```

#### GET `/api/jobs`
List all download jobs.

#### GET `/api/status/<job_id>`
Get status of a specific job.

#### POST `/api/retry/<job_id>`
Retry a failed download.

## Adding a New Site Extractor

1. Create a new file in `extractors/sites/mysite.py`:

```python
from extractors.base import BaseExtractor, ExtractorInfo

class MySiteExtractor(BaseExtractor):
    info = ExtractorInfo(
        name="mysite",
        domains=["mysite.com", "www.mysite.com"],
        requires_auth=False,
        supports_playlists=True,
        supports_live=False,
        description="Extractor for mysite"
    )
    
    def can_extract(self, url: str) -> bool:
        """Check if URL matches this site."""
        return self.validate_url(url)
    
    def extract_info(self, url: str, cookies_path=None, **kwargs):
        """Extract video info and return normalized data."""
        try:
            import yt_dlp
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
                "formats": self._normalize_formats(info.get("formats", [])),
            }
        except Exception as e:
            return {"error": str(e), "formats": []}
    
    def _normalize_formats(self, formats: list) -> list:
        """Normalize format info for consistency."""
        return [
            {
                "format_id": fmt.get("format_id", ""),
                "ext": fmt.get("ext", "mp4"),
                "height": fmt.get("height"),
            }
            for fmt in formats
        ]
    
    def get_default_format(self) -> str:
        """Return site-specific default format."""
        return "best"
```

2. Register it in `extractors/sites/__init__.py`:

```python
from .mysite import MySiteExtractor

ExtractorRegistry.register("mysite", MySiteExtractor)
```

3. Done! The extractor will be auto-loaded and automatically used for URLs matching `mysite.com`.

## How It Works

1. **URL Detection**: When a URL is submitted (web UI or CLI), `ExtractorRegistry.find_extractor()` determines the appropriate handler
2. **Site-Specific Extraction**: The selected extractor retrieves format info, metadata, and direct URLs
3. **Download Processing**: Extracted info is passed to yt-dlp or aria2 for actual download
4. **Job Tracking**: All downloads are queued and tracked with persistent storage (`jobs.json`)
5. **Real-time Updates**: Web UI polls `/api/jobs` every 2 seconds for live status

## Troubleshooting

### "No suitable extractor found"
The URL's site may not be supported. Try checking if yt-dlp supports it:
```bash
yt-dlp --dump-json "https://..." | head -50
```

### Instagram/Private content downloads fail
Make sure to provide valid cookies exported from your browser:
```bash
vidget download "https://instagram.com/..." --cookies ~/.cookies.txt
```

### aria2 connection fails
Ensure aria2 is running with RPC enabled:
```bash
~/termux-video-tools/start_aria2.sh
```

### Extractor detection not working
Check that the extractor system loaded:
```bash
python3 video_server.py --list-extractors
```

If no extractors show, verify the `extractors/` directory exists and contains the modules.

## Notes
- Some streams (DRM/protected) cannot be downloaded
- Live streams may require specific handling depending on the platform
- Private content usually requires cookies from an authenticated session
- aria2c must be running with RPC enabled for aria2 acceleration
- The web UI automatically refreshes jobs every 2 seconds

## Performance Tips

1. **Use aria2 acceleration** for large files (enable `--use-aria2`)
2. **Use cached cookies** instead of uploading each time
3. **Batch downloads** using playlists where supported
4. **Run on device** for best speeds (local network downloads to phone storage)

## License
MIT
