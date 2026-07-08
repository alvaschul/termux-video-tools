Termux Video Tools
==================

What it is
- A small Termux toolset to download videos from (almost) any website using yt-dlp + ffmpeg.
- CLI + a basic web UI to enqueue downloads from a browser on the device.
- Runs without root; stores downloads in ~/storage/shared/Videos by default.

Install (quick)
1. Open Termux.
2. Run:
   termux-setup-storage
   mkdir -p ~/termux-video-tools
   # Save the provided files into ~/termux-video-tools (installer.sh, vidget, video_server.py, requirements.txt)
   bash ~/termux-video-tools/installer.sh

Usage
- Start the web UI:
  vidget serve --port 8080
  Then open http://localhost:8080 in Termux's browser or a browser on the same network.

- Download a URL from CLI:
  vidget download "https://example.com/watch?v=abc123"

Notes & limitations
- Some sites use DRM or encrypted streams — those cannot be downloaded.
- Private sites requiring auth may need cookie files or login options; yt-dlp supports passing cookies and auth — you can extend the CLI to accept cookies.
- For long-running background use, run the serve command inside Termux:Boot or use termux-service wrappers.
- You may want to add aria2 integration for segmented downloading; this template uses yt-dlp direct download.

Want me to:
- Push these files to a GitHub repo for you?
- Add auth/cookie handling, aria2 acceleration, or a nicer web UI (React/tailwind)?
- Create a system to run the server automatically (Termux:Boot script or service)?

Tell me which next step you want and I will either push the repo (if you give me an owner/repo) or produce the extended code.
