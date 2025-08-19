from http.server import BaseHTTPRequestHandler
import json, ssl, urllib.request, os

ALLOWED = os.getenv("ALLOWED_ORIGINS", "*")

class handler(BaseHTTPRequestHandler):
    def _hdr(self, code=200, ctype="application/json"):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Access-Control-Allow-Origin", ALLOWED)
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Cache-Control", "public, max-age=60")
        self.end_headers()

    def do_OPTIONS(self): 
        self._hdr()

    def do_GET(self):
        try:
            ctx = ssl.create_default_context()
            with urllib.request.urlopen("https://mempool.space/api/v1/fees/recommended", context=ctx) as rf:
                j = json.load(rf)
            out = {
                "fast": j.get("fastestFee") or j.get("high_priority"),
                "hour": j.get("hourFee") or j.get("economyFee")
            }
            self._hdr(); self.wfile.write(json.dumps(out).encode("utf-8"))
        except Exception as e:
            self._hdr(502); self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))