"""HTTP server helpers for dashboard hosting."""

from __future__ import annotations

import http.server
import signal
import socket
import socketserver
import sys
import webbrowser
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


class CORSRequestHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP request handler that injects CORS headers."""

    def end_headers(self) -> None:  # noqa: D401 - inherited docstring
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()

    def do_OPTIONS(self):  # type: ignore[override]
        self.send_response(200)
        self.end_headers()

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        message = format % args
        if "GET" in message and any(ext in message for ext in [".html", ".json", ".css", ".js"]):
            file_path = message.split('"')[1].split()[1]
            print(f"📁 Serving: {file_path}")
        else:
            print(f"{message}")

def serve_dashboard(port: int = 8083, *, auto_open: bool = True) -> None:
    """Serve the primary dashboard."""
    _serve_file("dashboard.html", port, auto_open=auto_open)


def _serve_file(
    html_filename: str,
    start_port: int,
    *,
    auto_open: bool = True,
) -> None:
    """Serve a static dashboard file with automatic CORS headers."""
    script_dir = Path.cwd()
    html_path = script_dir / html_filename
    if not html_path.exists():
        raise FileNotFoundError(f"{html_filename} not found in {script_dir}")

    port = _find_free_port(start_port)
    handler = CORSRequestHandler

    with _graceful_shutdown():
        with socketserver.TCPServer(("", port), handler) as httpd:
            url = f"http://localhost:{port}/{html_filename}"
            print(f"Server starting on port {port}")
            print(f"Dashboard URL: {url}")
            print(f"📁 Serving files from: {script_dir}")
            print("\n🔧 Server Features:")

            if auto_open:
                try:
                    print("\nOpening dashboard in your default browser...")
                    webbrowser.open(url)
                    print("   Browser opened successfully!")
                except Exception as exc:  # noqa: BLE001 - environment dependent
                    print(f"   ⚠️  Could not auto-open browser: {exc}")
                    print(f"   Please manually open: {url}")

            print("\n📈 Server Status: RUNNING")
            print("   Press Ctrl+C to stop the server")
            print("=" * 50)
            httpd.serve_forever()


def _find_free_port(start_port: int) -> int:
    port = start_port
    while port < start_port + 100:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.bind(("localhost", port))
                return port
            except OSError:
                port += 1
    raise RuntimeError(f"Could not find a free port starting from {start_port}")


@contextmanager
def _graceful_shutdown() -> Iterator[None]:
    def handler(sig, frame):  # noqa: ANN001 - signature required by signal
        print("\n\n🛑 Server shutting down...")
        print("👋 Thanks for using the dashboard!")
        sys.exit(0)

    previous_handler = signal.getsignal(signal.SIGINT)
    signal.signal(signal.SIGINT, handler)
    try:
        yield
    finally:
        signal.signal(signal.SIGINT, previous_handler)


__all__ = ["serve_dashboard", "CORSRequestHandler"]
