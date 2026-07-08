````markdown
# termux-video-tools

Lightweight Termux toolset to download videos from many websites using yt-dlp, with optional aria2 acceleration and a small web UI.

Features
- CLI wrapper (vidget)
- Flask web UI to enqueue downloads and upload cookies.txt
- aria2 RPC integration (aria2p) to accelerate downloads using aria2c
- cookies.txt support for authenticated sites
- Stores downloads in ~/storage/shared/Download by default

Prerequisites
- Termux on Android
- Termux storage permission: run `termux-setup-storage` once

Install
1. Place all files in `~/termux-video-tools`.
2. Make scripts executable:
   chmod +x ~/termux-video-tools/{installer.sh,vidget,video_server.py,start_aria2.sh}
3. Run the installer script to install packages:
   bash ~/termux-video-tools/installer.sh

Start aria2 (RPC)
- Start aria2 RPC to enable aria2 acceleration:
  ~/termux-video-tools/start_aria2.sh

Run the web UI
- Start server:
  vidget serve --port 8080
- Open http://localhost:8080 on the device or http://<device-ip>:8080 from a machine on same network.

CLI usage
- Download a URL:
  vidget download "https://example.com/..." --format best
- Use aria2 RPC for downloads:
  vidget download "..." --use-aria2
- Provide cookies file:
  vidget download "..." --cookies /path/to/cookies.txt

Notes
- For some sites, cookies (exported from your browser as cookies.txt) are required; upload via the web UI or pass the path via CLI.
- Some streams (DRM/protected) can't be downloaded.
- aria2c must be running with RPC enabled (start_aria2.sh does that).

Extending
- You can add authentication flags, more robust progress reporting, or a richer frontend later.

License
- MIT- Some sites use DRM or encrypted streams — those cannot be downloaded.
- Private sites requiring auth may need cookie files or login options; yt-dlp supports passing cookies and auth — you can extend the CLI to accept cookies.
- For long-running background use, run the serve command inside Termux:Boot or use termux-service wrappers.
- You may want to add aria2 integration for segmented downloading; this template uses yt-dlp direct download.

Want me to:
- Push these files to a GitHub repo for you?
- Add auth/cookie handling, aria2 acceleration, or a nicer web UI (React/tailwind)?
- Create a system to run the server automatically (Termux:Boot script or service)?

Tell me which next step you want and I will either push the repo (if you give me an owner/repo) or produce the extended code.
