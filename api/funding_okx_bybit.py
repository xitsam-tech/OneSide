from http.server import BaseHTTPRequestHandler
import json, ssl, urllib.request, urllib.error, os, time

ALLOWED = os.getenv("ALLOWED_ORIGINS", "*")

def get_json(url):
    ctx = ssl.create_default_context()
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, context=ctx, timeout=10) as r:
        return json.load(r)

def okx_rate(symbol):  # symbol: BTCUSDT or ETHUSDT
    inst = f"{symbol[:-4]}-USDT-SWAP"
    j = get_json(f"https://www.okx.com/api/v5/public/funding-rate?instId={inst}")
    data = (j.get("data") or [])
    if not data: 
        raise ValueError("OKX empty")
    d = data[0]
    # returns decimal (e.g. 0.0001). times are strings; provide best-effort epoch ms.
    cur = float(d.get("fundingRate") or 0.0)
    nxt = d.get("nextFundingRate")
    ts  = d.get("fundingTime") or d.get("nextFundingTime") or d.get("ts")
    try:
        ts = int(ts)
    except Exception:
        ts = 0
    return cur, nxt, ts

def bybit_rate(symbol):  # symbol: BTCUSDT or ETHUSDT
    j = get_json(f"https://api.bybit.com/v5/market/history-fund-rate?category=linear&symbol={symbol}&limit=1")
    res = (j.get("result") or {})
    lst = (res.get("list") or [])
    if not lst:
        raise ValueError("Bybit empty")
    d = lst[0]
    # fields: "fundingRate" (string), "fundingRateTimestamp" (ms)
    cur = float(d.get("fundingRate") or 0.0)
    ts  = int(d.get("fundingRateTimestamp") or 0)
    return cur, None, ts

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
            # 1) Try OKX (BTC/ETH)
            btc, _, t1 = okx_rate("BTCUSDT")
            eth, _, t2 = okx_rate("ETHUSDT")
            out = {"btc": btc, "eth": eth, "nextFundingTime": max(t1, t2), "src": "OKX"}
            self._hdr(); self.wfile.write(json.dumps(out).encode("utf-8")); return
        except Exception:
            pass
        try:
            # 2) Fallback: Bybit latest settled funding
            btc, _, t1 = bybit_rate("BTCUSDT")
            eth, _, t2 = bybit_rate("ETHUSDT")
            out = {"btc": btc, "eth": eth, "nextFundingTime": max(t1, t2), "src": "BYBIT"}
            self._hdr(); self.wfile.write(json.dumps(out).encode("utf-8")); return
        except Exception as e:
            self._hdr(502); self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))