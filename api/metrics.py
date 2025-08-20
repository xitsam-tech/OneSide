
from http.server import BaseHTTPRequestHandler
import json, urllib.request, ssl, time

TIMEOUT = 5.0
ALLOWED = "*"

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0 (OneSideBot)"})
    with urllib.request.urlopen(req, timeout=TIMEOUT, context=ssl.create_default_context()) as r:
        return r.read()

def jget(url):
    try:
        return json.loads(fetch(url).decode("utf-8"))
    except Exception:
        return None

def btc_dominance():
    # CG global first, fallback to CoinLore
    j = jget("https://api.coingecko.com/api/v3/global")
    if j and j.get("data",{}).get("market_cap_percentage"):
        return float(j["data"]["market_cap_percentage"].get("btc",0.0))
    j = jget("https://api.coinlore.net/api/global/")
    if isinstance(j, list) and j:
        try: return float(j[0].get("btc_d",0.0))
        except Exception: pass
    return None

def eth_btc_ratio():
    j = jget("https://api.binance.com/api/v3/ticker/price?symbol=ETHBTC")
    try:
        return float(j.get("price",0.0)) if j else None
    except Exception:
        return None

def funding_rates():
    out = {}
    for sym in ("BTCUSDT","ETHUSDT"):
        j = jget(f"https://fapi.binance.com/fapi/v1/premiumIndex?symbol={sym}")
        try:
            out[sym.replace('USDT','')] = float(j.get("lastFundingRate",0.0))
        except Exception:
            out[sym.replace('USDT','')] = None
    return out

def fear_greed():
    j = jget("https://api.alternative.me/fng/?limit=1&format=json")
    try:
        v = int(j["data"][0]["value"])
        c = j["data"][0]["value_classification"]
        return {"value": v, "class": c}
    except Exception:
        return None

def mempool_fees():
    j = jget("https://mempool.space/api/v1/fees/recommended")
    if isinstance(j, dict):
        return {"fast": j.get("fastestFee"), "medium": j.get("halfHourFee"), "slow": j.get("hourFee")}
    return None

def respond(h, code, data):
    h.send_response(code)
    h.send_header("Content-Type","application/json; charset=utf-8")
    h.send_header("Access-Control-Allow-Origin", ALLOWED)
    h.send_header("Access-Control-Allow-Methods","GET,OPTIONS")
    h.send_header("Access-Control-Allow-Headers","Content-Type")
    h.end_headers()
    h.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self): respond(self, 200, {})
    def do_GET(self):
        t0=time.time()
        resp = {
            "btc_dominance": btc_dominance(),
            "eth_btc": eth_btc_ratio(),
            "funding": funding_rates(),
            "fear_greed": fear_greed(),
            "fees": mempool_fees(),
            "t_ms": int((time.time()-t0)*1000)
        }
        respond(self, 200, resp)
