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
            u = "https://fapi.binance.com/fapi/v1/premiumIndex?symbol="
            with urllib.request.urlopen(u+"BTCUSDT", context=ctx) as rb:
                btc = json.load(rb)
            with urllib.request.urlopen(u+"ETHUSDT", context=ctx) as reth:
                eth = json.load(reth)

            out = {
                "btc": float(btc.get("lastFundingRate") or btc.get("fundingRate") or 0.0),
                "eth": float(eth.get("lastFundingRate") or eth.get("fundingRate") or 0.0),
                "nextFundingTime": max(int(btc.get("nextFundingTime") or 0),
                                       int(eth.get("nextFundingTime") or 0))
            }
            self._hdr(); self.wfile.write(json.dumps(out).encode("utf-8"))
        except Exception as e:
            self._hdr(502); self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))