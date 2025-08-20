
from http.server import BaseHTTPRequestHandler
import json, urllib.request, urllib.error, ssl, time

TIMEOUT = 6.0
ALLOWED = "*"

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0 (OneSideBot)"})
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, timeout=TIMEOUT, context=ctx) as r:
        ctype = r.headers.get("Content-Type","")
        return r.read(), ctype

def to_json(b):
    try: return json.loads(b.decode("utf-8"))
    except Exception: return None

def get_rates(base="USD", symbols=("EUR","USD","GBP","JPY")):
    try:
        raw, _ = fetch(f"https://api.exchangerate.host/latest?base={base}&symbols={','.join(symbols)}")
        j = to_json(raw) or {}
        return j.get("rates") or {}
    except Exception:
        return {}

def from_coingecko(vs="USD", limit=10):
    url = f"https://api.coingecko.com/api/v3/coins/markets?vs_currency={vs.lower()}&order=market_cap_desc&per_page={max(10,limit)}&page=1&sparkline=false&locale=en"
    raw, _ = fetch(url)
    j = to_json(raw) or []
    out = []
    for x in j[:limit]:
        out.append({
            "rank": x.get("market_cap_rank"),
            "symbol": (x.get("symbol") or "").upper(),
            "name": x.get("name"),
            "price": x.get("current_price"),
            "ch24": x.get("price_change_percentage_24h"),
            "vol24": x.get("total_volume"),
            "mcap": x.get("market_cap"),
            "src": "coingecko"
        })
    return out

def from_coinlore(vs="USD", limit=10):
    raw, _ = fetch("https://api.coinlore.net/api/tickers/?start=0&limit=100")
    j = to_json(raw) or {}
    data = j.get("data") or []
    # CoinLore is USD; convert if needed
    rates = get_rates("USD", ("EUR","USD","GBP","JPY"))
    fx = rates.get(vs.upper(), 1.0) if vs.upper()!="USD" else 1.0
    out = []
    for x in data[:max(limit,20)]:
        price_usd = float(x.get("price_usd") or 0.0)
        out.append({
            "rank": int(x.get("rank") or 0),
            "symbol": (x.get("symbol") or "").upper(),
            "name": x.get("name"),
            "price": price_usd * (fx or 1.0),
            "ch24": float(x.get("percent_change_24h") or 0.0),
            "vol24": float(x.get("volume24") or 0.0) * (fx or 1.0),
            "mcap": float(x.get("market_cap_usd") or 0.0) * (fx or 1.0),
            "src": "coinlore+fx" if vs.upper()!="USD" else "coinlore"
        })
    out.sort(key=lambda x: (x["rank"] if x["rank"] else 1e9))
    return out[:limit]

def from_binance_fallback(vs="USD", limit=10):
    # Use BTC, ETH, and big caps via USDT, approximate USD=USDT, convert via FX if needed.
    raw, _ = fetch("https://api.binance.com/api/v3/ticker/24hr")
    j = to_json(raw) or []
    want = {"BTCUSDT":"BTC","ETHUSDT":"ETH","BNBUSDT":"BNB","SOLUSDT":"SOL","XRPUSDT":"XRP","ADAUSDT":"ADA","DOGEUSDT":"DOGE","TONUSDT":"TON","DOTUSDT":"DOT","TRXUSDT":"TRX"}
    m = {x["symbol"]:x for x in j if x.get("symbol") in want}
    rates = get_rates("USD", ("EUR","USD","GBP","JPY"))
    fx = rates.get(vs.upper(), 1.0) if vs.upper()!="USD" else 1.0
    out=[]
    for sym, coin in want.items():
        x = m.get(sym) or {}
        last = float(x.get("lastPrice") or 0.0)
        chp  = float(x.get("priceChangePercent") or 0.0)
        vol  = float(x.get("quoteVolume") or 0.0)  # USDT ≈ USD
        out.append({
            "rank": None,
            "symbol": coin,
            "name": coin,
            "price": last * (fx or 1.0),
            "ch24": chp,
            "vol24": vol * (fx or 1.0),
            "mcap": None,
            "src": "binance+fx" if vs.upper()!="USD" else "binance"
        })
    return out[:limit]

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
        import urllib.parse as up
        qs = up.parse_qs(up.urlparse(self.path).query)
        vs = (qs.get("vs") or ["EUR"])[0].upper()
        limit = int((qs.get("limit") or ["10"])[0])
        t0 = time.time()
        try:
            data = from_coingecko(vs, limit)
        except Exception:
            data = []
        if not data:
            try: data = from_coinlore(vs, limit)
            except Exception: data = []
        if not data:
            try: data = from_binance_fallback(vs, limit)
            except Exception: data = []
        resp = {"vs":vs, "limit":limit, "items":data, "t_ms": int((time.time()-t0)*1000)}
        respond(self, 200, resp)
