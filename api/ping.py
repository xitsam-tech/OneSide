from http.server import BaseHTTPRequestHandler
import json, os
ALLOWED = os.getenv("ALLOWED_ORIGINS", "*")
class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", ALLOWED)
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type","application/json")
        self.send_header("Access-Control-Allow-Origin", ALLOWED)
        self.end_headers()
        self.wfile.write(json.dumps({"ok": True, "route": "/api/ping"}).encode("utf-8"))