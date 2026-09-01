"""Minimal test — hosting par Python chal raha hai ya nahi."""

from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os

port = int(os.environ.get("HTTP_PLATFORM_PORT") or os.environ.get("PORT") or "8010")


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        body = json.dumps({"ok": True, "message": "Python is running", "port": port}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    HTTPServer(("127.0.0.1", port), Handler).serve_forever()
