#!/data/data/com.termux/files/usr/bin/env python3
import os
import sys
import uuid
import json
import threading
import queue
import argparse
from datetime import datetime
from pathlib import Path

try:
    from flask import Flask, request, redirect, url_for, jsonify, render_template_string
except Exception:
    Flask = None

# Local storage paths
HOME = Path.home()
TOOLS_DIR = HOME / "termux-video-tools"
OUT_DIR = HOME / "storage" / "shared" / "Videos"
OUT_DIR.mkdir(parents=True, exist_ok=True)
JOBS_FILE = TOOLS_DIR / "jobs.json"
TASK_QUEUE = queue.Queue()
JOBS = {}
JOBS_LOCK = threading.Lock()

# Minimal HTML template for the web UI
HTML = """
<!doctype html>
<title>Termux Video Downloader</title>
<h1>Termux Video Downloader</h1>
<form method=post action="/download">
  URL: <input name=url size=80>
  Format: <input name=format value="best">
  <input type=submit value=Download>
</form>
<hr>
<h2>Queue / Jobs</h2>
<ul>
{% for jobid, j in jobs.items() %}
  <li><b>{{jobid}}</b> - {{j.get('url')}} - {{j.get('status')}} - {{j.get('message','')}}</li>
{% endfor %}
</ul>
"""

def save_jobs():
    try:
        with JOBS_LOCK:
            (TOOLS_DIR).mkdir(parents=True, exist_ok=True)
            with open(JOBS_FILE, "w") as f:
                json.dump(JOBS, f, default=str, indent=2)
    except Exception:
        pass

def load_jobs():
    if JOBS_FILE.exists():
        try:
            with open(JOBS_FILE, "r") as f:
                data = json.load(f)
            with JOBS_LOCK:
                JOBS.update(data)
        except Exception:
            pass

def run_yt_dlp(url, outdir, fmt):
    """Try to use yt_dlp Python API; fallback to calling yt-dlp subprocess."""
    outtpl = str(outdir / "%(title)s.%(ext)s")
    try:
        import yt_dlp
        opts = {
            "outtmpl": outtpl,
            "format": fmt or "best",
            "noplaylist": False,
        }
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
        return True, str(info.get("title", ""))
    except Exception as e:
        # fallback to subprocess
        import subprocess
        cmd = ["yt-dlp", "-o", outtpl, "-f", fmt or "best", url]
        try:
            subprocess.run(cmd, check=True)
            return True, "downloaded (subprocess)"
        except Exception as e2:
            return False, f"yt-dlp failed: {e} | {e2}"

def worker():
    while True:
        jobid = TASK_QUEUE.get()
        if jobid is None:
            break
        with JOBS_LOCK:
            job = JOBS.get(jobid, {})
            job["status"] = "running"
            job["started_at"] = str(datetime.utcnow())
            save_jobs()
        url = job.get("url")
        fmt = job.get("format", "best")
        outdir = Path(job.get("outdir", str(OUT_DIR)))
        outdir.mkdir(parents=True, exist_ok=True)
        success, msg = run_yt_dlp(url, outdir, fmt)
        with JOBS_LOCK:
            job["status"] = "done" if success else "error"
            job["finished_at"] = str(datetime.utcnow())
            job["message"] = msg
            save_jobs()
        TASK_QUEUE.task_done()

def enqueue_download(url, fmt="best", outdir=None):
    jobid = str(uuid.uuid4())
    job = {
        "id": jobid,
        "url": url,
        "format": fmt,
        "outdir": str(outdir or OUT_DIR),
        "status": "queued",
        "created_at": str(datetime.utcnow())
    }
    with JOBS_LOCK:
        JOBS[jobid] = job
        save_jobs()
    TASK_QUEUE.put(jobid)
    return jobid

# Start background worker thread
_worker_thread = threading.Thread(target=worker, daemon=True)
_worker_thread.start()
load_jobs()

# Flask app section
if Flask:
    app = Flask(__name__)

    @app.route("/", methods=["GET"])
    def index():
        with JOBS_LOCK:
            jobs_view = dict(JOBS)
        return render_template_string(HTML, jobs=jobs_view)

    @app.route("/download", methods=["POST"])
    def download_route():
        url = request.form.get("url") or request.json.get("url")
        fmt = request.form.get("format") or request.json.get("format") or "best"
        if not url:
            return "Missing url", 400
        jobid = enqueue_download(url, fmt)
        return redirect(url_for("status_route", jobid=jobid))

    @app.route("/status/<jobid>", methods=["GET"])
    def status_route(jobid):
        with JOBS_LOCK:
            job = JOBS.get(jobid)
        if not job:
            return jsonify({"error": "job not found"}), 404
        return jsonify(job)

    @app.route("/jobs", methods=["GET"])
    def jobs_route():
        with JOBS_LOCK:
            return jsonify(JOBS)

def cli_main():
    parser = argparse.ArgumentParser(prog="video_server.py")
    parser.add_argument("--serve", action="store_true", help="Run web UI")
    parser.add_argument("--port", type=int, default=8080, help="Port for web UI")
    parser.add_argument("--download", nargs="+", help="Download URL (CLI mode)")
    parser.add_argument("--format", default="best", help="Format for yt-dlp")
    parser.add_argument("--status", help="Query status for job id")
    args = parser.parse_args()

    if args.serve:
        if not Flask:
            print("Flask not installed. Please run: pip install Flask")
            sys.exit(1)
        print(f"Starting web UI on http://0.0.0.0:{args.port}")
        app.run(host="0.0.0.0", port=args.port, threaded=True)
    elif args.download:
        url = " ".join(args.download)
        jobid = enqueue_download(url, args.format)
        print("Enqueued job:", jobid)
        # Optionally wait for completion:
        print("Waiting for job to finish...")
        while True:
            with JOBS_LOCK:
                status = JOBS.get(jobid, {}).get("status")
            if status in ("done", "error"):
                print("Job finished:", status)
                with JOBS_LOCK:
                    print(json.dumps(JOBS[jobid], indent=2))
                break
            else:
                import time
                time.sleep(1)
    elif args.status:
        jid = args.status
        with JOBS_LOCK:
            job = JOBS.get(jid)
        if not job:
            print("Job not found.")
            sys.exit(1)
        print(json.dumps(job, indent=2))
    else:
        parser.print_help()

if __name__ == "__main__":
    cli_main()
