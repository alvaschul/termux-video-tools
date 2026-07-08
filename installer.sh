#!/data/data/com.termux/files/usr/bin/env bash
set -euo pipefail
PREFIX_DIR="${PREFIX:-/data/data/com.termux/files/usr}"
TOOLS_DIR="$HOME/termux-video-tools"

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

echo "Writing helper files..."
# User should create the rest of files manually or via git clone of a repo.
cat > "$TOOLS_DIR/requirements.txt" <<'PYREQ'
Flask>=2.0
yt-dlp>=2024.0.0
PYREQ

echo "Installing Python requirements..."
python3 -m pip install --upgrade pip
python3 -m pip install -r "$TOOLS_DIR/requirements.txt" || true

echo "Installing scripts into $TOOLS_DIR..."
chmod +x "$TOOLS_DIR/vidget" || true
chmod +x "$TOOLS_DIR/video_server.py" || true

echo "Add $TOOLS_DIR to PATH if not already present."
SHELL_RC="$HOME/.profile"
if ! grep -q 'termux-video-tools' "$SHELL_RC" 2>/dev/null; then
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
