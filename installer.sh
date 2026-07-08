#!/data/data/com.termux/files/usr/bin/env bash
set -euo pipefail
PREFIX_DIR="${PREFIX:-/data/data/com.termux/files/usr}"
TOOLS_DIR="${HOME}/termux-video-tools"

echo "== Termux Video Tools installer =="
if [ ! -d "$PREFIX_DIR" ]; then
  echo "This doesn't look like Termux. Aborting."
  exit 1
fi

echo "Updating packages..."
pkg update -y

echo "Installing required packages: python, ffmpeg, aria2, git, build tools..."
pkg install -y python ffmpeg aria2 git clang make

echo "Creating tools directory at $TOOLS_DIR"
mkdir -p "$TOOLS_DIR"
cd "$TOOLS_DIR"

# Write minimal requirements if missing
if [ ! -f requirements.txt ]; then
cat > requirements.txt <<'PYREQ'
Flask>=2.0
yt-dlp>=2026.0.0
aria2p>=0.10.0
PYREQ
fi

echo "Upgrading pip and installing Python requirements..."
python3 -m pip install --upgrade pip setuptools wheel
python3 -m pip install -r requirements.txt

echo "Setting executable bits for scripts..."
chmod +x "$TOOLS_DIR"/vidget || true
chmod +x "$TOOLS_DIR"/video_server.py || true
chmod +x "$TOOLS_DIR"/start_aria2.sh || true
chmod +x "$TOOLS_DIR"/installer.sh || true

echo "Add $TOOLS_DIR to PATH if not already present."
SHELL_RC="$HOME/.profile"
if ! grep -q 'termux-video-tools' "$SHELL_RC" 2>/dev/null; then
  echo "export PATH=\"\$PATH:$TOOLS_DIR\"" >> "$SHELL_RC"
  echo "Added PATH entry to $SHELL_RC. Start a new session or run: source $SHELL_RC"
fi

echo
echo "Installer finished."
echo "Next steps:"
echo "  1) Allow storage: termux-setup-storage"
echo "  2) Start aria2 RPC: $TOOLS_DIR/start_aria2.sh"
echo "  3) Start web UI: vidget serve --port 8080"
echo "  4) Download from CLI: vidget download '<URL>' [--format best] [--use-aria2] [--cookies /path/to/cookies.txt]"if ! grep -q 'termux-video-tools' "$SHELL_RC" 2>/dev/null; then
  echo "export PATH=\"\$PATH:$TOOLS_DIR\"" >> "$SHELL_RC"
  echo "Added PATH entry to $SHELL_RC. Start a new session or run: source $SHELL_RC"
fi

echo "Make sure you allow storage access (one-time):"
echo "  termux-setup-storage"
echo
echo "To start the web UI:"
echo "  vidget serve --port 8080"
echo
echo "To download directly from CLI:"
echo "  vidget download '<URL>'"
echo
echo "Installer finished."
