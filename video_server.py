#!/data/data/com.termux/files/usr/bin/env python3
"""
Termux Video Tools - server and CLI
Features:
- Extensible extractor plugin system for site-specific handling
- yt-dlp downloads (via Python API or subprocess)
- aria2 integration via aria2p RPC (extract direct URLs via yt-dlp then add to aria2)
- cookies.txt support (upload or path)
- simple Flask web UI with AJAX polling
"""
import os
import sys
import uuid
import json
import threading
import queue
import argparse
import time
import logging
from datetime import datetime
from pathlib import Path
from shutil import which

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Flask import (optional if running CLI-only)
try:
    from flask import Flask, request, redirect, url_for, jsonify, render_template, send_from_directory
    FLASK_AVAILABLE = True
except Exception:
    FLASK_AVAILABLE = False

# External libs
try:
    import yt_dlp as ytdlp_pkg
except Exception:
    ytdlp_pkg = None

try:
    import aria2p
except Exception:
    aria2p = None

# Extractor system
try:
    from extractors.registry import ExtractorRegistry
    import extractors.sites  # Auto-registers extractors
    EXTRACTORS_AVAILABLE = True
    logger.info("Extractor system loaded successfully")
except Exception as e:
    EXTRACTORS_AVAILABLE = False
    logger.warning(f"Extractor system not available: {e}")

HOME = Path.home()
TOOLS_DIR = HOME / "termux-video-tools"
OUT_DIR = HOME / "storage" / "shared" / "Download"
COOKIES_DIR = TOOLS_DIR / "cookies"
JOBS_FILE = TOOLS_DIR / "jobs.json"
STATIC_DIR = TOOLS_DIR / "static"

TOOLS_DIR.mkdir(parents=True, exist_ok=True)
COOKIES_DIR.mkdir(parents=True, exist_ok=True)
OUT_DIR.mkdir(parents=True, exist_ok=True)
STATIC_DIR.mkdir(parents=True, exist_ok=True)

# In-memory job store + persistence lock
JOBS = {}
JOBS_LOCK = threading.Lock()
TASK_QUEUE = queue.Queue()

# aria2 RPC defaults
ARIA2_HOST = "http://localhost"
ARIA2_PORT = 6800

def save_jobs():
    try:
        with JOBS_LOCK:
            with open(JOBS_FILE, "w") as f:
                json.dump(JOBS, f, indent=2, default=str)
    except Exception as e:
        logger.error(f"Failed to save jobs: {e}")

def load_jobs():
    if JOBS_FILE.exists():
        try:
            with open(JOBS_FILE, "r") as f:
                data = json.load(f)
            with JOBS_LOCK:
                JOBS.update(data)
            logger.info(f"Loaded {len(JOBS)} jobs from persistent storage")
        except Exception as e:
            logger.error(f"Failed to load jobs: {e}")

def enqueue_download(url, fmt="best", use_aria2=False, cookies_path=None, outdir=None):
    jobid = str(uuid.uuid4())
    
    # Detect extractor
    extractor_key = "generic"
    if EXTRACTORS_AVAILABLE:
        try:
            extractor = ExtractorRegistry.find_extractor(url)
            if extractor:
                extractor_key = extractor.info.name
                logger.info(f"Selected extractor '{extractor_key}' for URL: {url[:60]}...")
        except Exception as e:
            logger.warning(f"Failed to detect extractor: {e}")
    
    job = {
        "id": jobid,
        "url": url,
        "format": fmt or "best",
        "use_aria2": bool(use_aria2),
        "cookies": str(cookies_path) if cookies_path else None,
        "outdir": str(outdir or OUT_DIR),
        "extractor": extractor_key,
        "status": "queued",
        "progress": 0.0,
        "message": "",
        "created_at": str(datetime.utcnow())
    }
    with JOBS_LOCK:
        JOBS[jobid] = job
        save_jobs()
    TASK_QUEUE.put(jobid)
    return jobid

def run_yt_dlp_download(url, outdir, fmt, cookies_path=None):
    outtpl = str(Path(outdir) / "%(title)s.%(ext)s")
    # Try Python API first
    try:
        if ytdlp_pkg is None:
            raise RuntimeError("yt-dlp Python package not available")
        opts = {
            "outtmpl": outtpl,
            "format": fmt or "best",
            "noplaylist": False,
            "merge_output_format": None,
        }
        if cookies_path:
            opts["cookiefile"] = str(cookies_path)
        with ytdlp_pkg.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
        return True, f"Downloaded via yt-dlp: {info.get('title', '')}"
    except Exception as e:
        # Fallback to subprocess call if Python API failed
        import subprocess
        cmd = ["yt-dlp", "-o", outtpl, "-f", fmt or "best"]
        if cookies_path:
            cmd += ["--cookies", str(cookies_path)]
        cmd += [url]
        try:
            subprocess.run(cmd, check=True)
            return True, "Downloaded via yt-dlp (subprocess)"
        except Exception as e2:
            return False, f"yt-dlp failed: {e} | {e2}"

def aria2_add_and_wait(uris, outdir, filename=None, max_wait=3600):
    """
    Add URIs to aria2 via aria2p and wait until finished (simple polling).
    Returns (success, message)
    """
    if aria2p is None:
        return False, "aria2p not installed"
    try:
        client = aria2p.Client(host=ARIA2_HOST, port=ARIA2_PORT)
        api = aria2p.API(client)
    except Exception as e:
        return False, f"Failed to connect to aria2 RPC: {e}"

    try:
        options = {"dir": str(outdir)}
        if filename:
            options["out"] = filename
        # add uris
        download = api.add_uris(uris, options=options)
        # Poll download status
        waited = 0
        while True:
            download.update()
            if download.is_complete:
                return True, f"aria2 download complete: gid={download.gid}"
            if download.is_error:
                return False, f"aria2 download error: {download.error_message}"
            time.sleep(1)
            waited += 1
            if waited >= max_wait:
                return False, "aria2 download timeout"
    except Exception as e:
        return False, f"aria2 add failed: {e}"

def run_via_aria2_with_extraction(url, outdir, fmt, cookies_path=None):
    """
    Use yt-dlp to extract direct file URIs and hand them to aria2.
    If extraction can't produce direct URIs suitable for aria2 (or multiple parts need merging),
    fall back to calling yt-dlp with --external-downloader aria2c.
    """
    # Ensure yt-dlp extraction works
    try:
        if ytdlp_pkg is None:
            raise RuntimeError("yt-dlp Python package not available")
        ydl_opts = {"format": fmt or "best", "noplaylist": False, "skip_download": True}
        if cookies_path:
            ydl_opts["cookiefile"] = str(cookies_path)
        with ytdlp_pkg.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
    except Exception as e:
        # Extraction failed -> fallback to external-downloader call
        return run_yt_dlp_download_using_external_aria2(url, outdir, fmt, cookies_path)

    # Normalize to a list of entries
    entries = []
    if isinstance(info, dict) and info.get("_type") == "playlist":
        entries = info.get("entries", [])
    else:
        entries = [info]

    # For each entry, try to collect a single direct URL (or list) for aria2
    for entry in entries:
        uris = []
        # Prefer 'url' top-level (direct URL)
        if entry.get("url") and entry.get("acodec") != "none" or entry.get("ext"):
            # In some cases 'url' is a direct resource
            if entry.get("protocol", "") not in ("m3u8", "dash"):
                uris.append(entry.get("url"))
        # fallback to formats array with direct urls
        if not uris and entry.get("formats"):
            # choose best matching format
            formats = entry.get("formats")
            # pick the requested format (fmt) if present
            if formats:
                # pick the first format that has a direct 'url'
                for f in reversed(formats):
                    if f.get("url") and f.get("protocol") not in ("m3u8", "dash"):
                        uris.append(f.get("url"))
                        break
        if not uris:
            # Cannot hand a single direct URL to aria2 for this entry; fallback
            return run_yt_dlp_download_using_external_aria2(url, outdir, fmt, cookies_path)

        # Try adding the found URIs to aria2
        filename = None
        if entry.get("title") and entry.get("ext"):
            filename = f"{entry.get('title')}.{entry.get('ext')}"
        success, msg = aria2_add_and_wait(uris, outdir, filename)
        if not success:
            return False, msg
    return True, "aria2 downloads finished"

def run_yt_dlp_download_using_external_aria2(url, outdir, fmt, cookies_path=None):
    outtpl = str(Path(outdir) / "%(title)s.%(ext)s")
    import subprocess
    cmd = ["yt-dlp", "-o", outtpl, "-f", fmt or "best", "--external-downloader", "aria2c", "--external-downloader-args", "-x 4 -s 4 -k 1M"]
    if cookies_path:
        cmd += ["--cookies", str(cookies_path)]
    cmd += [url]
    try:
        subprocess.run(cmd, check=True)
        return True, "Downloaded via yt-dlp using external aria2c"
    except Exception as e:
        return False, f"external aria2c download failed: {e}"

def process_job(jobid):
    with JOBS_LOCK:
        job = JOBS.get(jobid)
        if not job:
            return
        job["status"] = "running"
        job["started_at"] = str(datetime.utcnow())
        save_jobs()

    url = job.get("url")
    fmt = job.get("format", "best")
    use_aria2 = job.get("use_aria2", False)
    cookies = job.get("cookies")
    outdir = Path(job.get("outdir") or OUT_DIR)
    outdir.mkdir(parents=True, exist_ok=True)

    try:
        if use_aria2:
            success, message = run_via_aria2_with_extraction(url, outdir, fmt, cookies)
        else:
            success, message = run_yt_dlp_download(url, outdir, fmt, cookies)
    except Exception as e:
        success = False
        message = f"Unexpected error: {e}"

    with JOBS_LOCK:
        job["status"] = "done" if success else "error"
        job["finished_at"] = str(datetime.utcnow())
        job["message"] = message
        job["progress"] = 100.0 if success else job.get("progress", 0.0)
        save_jobs()

def worker():
    while True:
        jobid = TASK_QUEUE.get()
        if jobid is None:
            break
        try:
            process_job(jobid)
        except Exception as e:
            with JOBS_LOCK:
                if jobid in JOBS:
                    JOBS[jobid]["status"] = "error"
                    JOBS[jobid]["message"] = f"Worker failed: {e}"
                    save_jobs()
        TASK_QUEUE.task_done()

# Start background worker thread
_worker_thread = threading.Thread(target=worker, daemon=True)
_worker_thread.start()
load_jobs()

# Flask routes and simple static site
if FLASK_AVAILABLE:
    app = Flask(__name__, static_folder=str(STATIC_DIR), template_folder=str(STATIC_DIR))

    @app.route("/")
    def index():
        # Serves static/index.html
        return send_from_directory(str(STATIC_DIR), "index.html")

    @app.route("/api/download", methods=["POST"])
    def api_download():
        use_aria2 = request.form.get("use_aria2", "false").lower() in ("1", "true", "yes", "on")
        fmt = request.form.get("format", "best")
        url = request.form.get("url")
        if not url:
            return jsonify({"error": "missing url"}), 400

        cookies_file = None
        if "cookies_file" in request.files and request.files["cookies_file"].filename:
            f = request.files["cookies_file"]
            jobid_tmp = str(uuid.uuid4())
            cookies_path = COOKIES_DIR / f"{jobid_tmp}-cookies.txt"
            f.save(str(cookies_path))
            cookies_file = str(cookies_path)
        else:
            # optionally accept a path string
            cookies_path_field = request.form.get("cookies")
            if cookies_path_field:
                cookies_file = cookies_path_field

        jid = enqueue_download(url, fmt=fmt, use_aria2=use_aria2, cookies_path=cookies_file, outdir=OUT_DIR)
        return jsonify({"job_id": jid})

    @app.route("/api/jobs", methods=["GET"])
    def api_jobs():
        with JOBS_LOCK:
            return jsonify(JOBS)

    @app.route("/api/status/<jobid>", methods=["GET"])
    def api_status(jobid):
        with JOBS_LOCK:
            job = JOBS.get(jobid)
            if not job:
                return jsonify({"error": "job not found"}), 404
            return jsonify(job)

    @app.route("/api/retry/<jobid>", methods=["POST"])
    def api_retry(jobid):
        with JOBS_LOCK:
            job = JOBS.get(jobid)
            if not job:
                return jsonify({"error": "job not found"}), 404
            # enqueue a fresh job with same parameters
            newjid = enqueue_download(job["url"], fmt=job.get("format"), use_aria2=job.get("use_aria2"), cookies_path=job.get("cookies"), outdir=job.get("outdir"))
            return jsonify({"new_job_id": newjid})

    @app.route("/api/extractors", methods=["GET"])
    def api_extractors():
        """List all available extractors and supported sites."""
        if not EXTRACTORS_AVAILABLE:
            return jsonify({
                "error": "Extractor system not available",
                "extractors": {}
            })
        
        try:
            extractors_info = ExtractorRegistry.list_extractors()
            supported_domains = ExtractorRegistry.get_supported_domains()
            
            result = {
                "total_extractors": len(extractors_info),
                "total_domains": len(supported_domains),
                "extractors": {}
            }
            
            for key, info in extractors_info.items():
                result["extractors"][key] = {
                    "name": info.name,
                    "domains": info.domains,
                    "requires_auth": info.requires_auth,
                    "supports_playlists": info.supports_playlists,
                    "supports_live": info.supports_live,
                    "description": info.description,
                }
            
            result["supported_domains"] = sorted(supported_domains)
            return jsonify(result)
        except Exception as e:
            logger.error(f"Error listing extractors: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route("/api/detect", methods=["POST"])
    def api_detect():
        """Detect which extractor will handle a given URL."""
        url = request.json.get("url") if request.is_json else request.form.get("url")
        
        if not url:
            return jsonify({"error": "missing url"}), 400
        
        if not EXTRACTORS_AVAILABLE:
            return jsonify({
                "error": "Extractor system not available",
                "extractor": None
            })
        
        try:
            extractor = ExtractorRegistry.find_extractor(url)
            if extractor:
                return jsonify({
                    "extractor": extractor.info.name,
                    "requires_auth": extractor.info.requires_auth,
                    "supports_playlists": extractor.info.supports_playlists,
                    "supports_live": extractor.info.supports_live,
                    "description": extractor.info.description,
                    "default_format": extractor.get_default_format(),
                })
            else:
                return jsonify({
                    "error": "No suitable extractor found",
                    "extractor": None
                }), 404
        except Exception as e:
            logger.error(f"Error detecting extractor: {e}")
            return jsonify({"error": str(e)}), 500

# CLI entrypoint
def cli_main():
    parser = argparse.ArgumentParser(prog="video_server.py")
    parser.add_argument("--serve", action="store_true", help="Run web UI")
    parser.add_argument("--port", type=int, default=8080, help="Port for web UI")
    parser.add_argument("--download", nargs="+", help="Download URL (CLI mode)")
    parser.add_argument("--format", default="best", help="Format for yt-dlp")
    parser.add_argument("--use-aria2", action="store_true", help="Use aria2 RPC (requires aria2c running with RPC)")
    parser.add_argument("--cookies", help="Path to cookies.txt file")
    parser.add_argument("--status", help="Query status for job id")
    parser.add_argument("--list-extractors", action="store_true", help="List all available extractors")
    parser.add_argument("--detect", help="Detect extractor for a URL")
    args = parser.parse_args()

    if args.serve:
        if not FLASK_AVAILABLE:
            print("Flask is not installed. Please pip install Flask and try again.")
            sys.exit(1)
        print(f"Starting web UI on http://0.0.0.0:{args.port}")
        print(f"Extractor system: {'ENABLED' if EXTRACTORS_AVAILABLE else 'DISABLED'}")
        app.run(host="0.0.0.0", port=args.port, threaded=True)
    elif args.download:
        url = " ".join(args.download)
        jid = enqueue_download(url, fmt=args.format, use_aria2=args.use_aria2, cookies_path=args.cookies, outdir=OUT_DIR)
        print("Enqueued job:", jid)
        # Wait for completion (optional)
        print("Waiting for job to finish (polling)...")
        while True:
            with JOBS_LOCK:
                status = JOBS.get(jid, {}).get("status")
                message = JOBS.get(jid, {}).get("message", "")
            print("status:", status, "message:", message)
            if status in ("done", "error"):
                break
            time.sleep(1)
    elif args.status:
        jid = args.status
        with JOBS_LOCK:
            job = JOBS.get(jid)
        if not job:
            print("Job not found.")
            sys.exit(1)
        print(json.dumps(job, indent=2))
    elif args.list_extractors:
        if not EXTRACTORS_AVAILABLE:
            print("Extractor system not available")
            sys.exit(1)
        
        try:
            extractors_info = ExtractorRegistry.list_extractors()
            print("\n=== Available Extractors ===\n")
            for key, info in extractors_info.items():
                print(f"Name: {info.name}")
                print(f"  Domains: {', '.join(info.domains) if info.domains else 'Any (fallback)'}")
                print(f"  Auth Required: {info.requires_auth}")
                print(f"  Playlists: {info.supports_playlists}")
                print(f"  Live Streams: {info.supports_live}")
                print(f"  Description: {info.description}")
                print()
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)
    elif args.detect:
        if not EXTRACTORS_AVAILABLE:
            print("Extractor system not available")
            sys.exit(1)
        
        try:
            extractor = ExtractorRegistry.find_extractor(args.detect)
            if extractor:
                print(f"Detected Extractor: {extractor.info.name}")
                print(f"  Description: {extractor.info.description}")
                print(f"  Requires Auth: {extractor.info.requires_auth}")
                print(f"  Default Format: {extractor.get_default_format()}")
            else:
                print("No suitable extractor found for this URL")
                sys.exit(1)
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)
    else:
        parser.print_help()

if __name__ == "__main__":
    cli_main()
