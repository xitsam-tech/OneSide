
from http.server import BaseHTTPRequestHandler
import json, urllib.request, urllib.error, socket, time, re
from xml.etree import ElementTree as ET

RSS_EN = [
    ("Reuters Markets", "https://feeds.reuters.com/reuters/marketsNews"),
    ("Reuters Crypto", "https://www.reuters.com/markets/cryptocurrency/rss"),
    ("AP Business", "https://apnews.com/hub/apf-business?utm_source=apnews.com&utm_medium=referral&utm_campaign=rss"),
    ("BBC Business", "http://feeds.bbci.co.uk/news/business/rss.xml"),
    ("Yahoo Finance", "https://feeds.finance.yahoo.com/rss/2.0/headline?s=BTC-USD,ETH-USD&region=US&lang=en-US"),
]

TIMEOUT = 5.5
PAT = re.compile(r"(bitcoin|crypto|blockchain|mining|btc|eth|ethereum|stablecoin|altcoin|defi|etf|sec|spot\s*etf|futures|exchange|binance|coinbase|kraken|okx|wallet|liquidity|onchain|token|staking|airdrop|halving|hashrate|gas fee|mempool|treasury|bond|yield|interest|rate|fed|ecb|cpi|ppi|inflation|gdp|tariff|sanction|fx|forex|currency|usd|eur|gbp|jpy|yuan|yen|oil|gold|nasdaq|s&p|dow|volatility|market cap|marketcap)", re.I)

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0 (OneSideBot)"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return r.read()

def parse_rss(content, source):
    out=[]
    try:
        root = ET.fromstring(content)
    except Exception:
        return out
    for item in root.findall('.//item'):
        t = (item.findtext('title') or '').strip()
        l = (item.findtext('link') or '').strip()
        if t and l and PAT.search(t):
            out.append({"title": t, "url": l, "domain": source})
    for entry in root.findall('.//{http://www.w3.org/2005/Atom}entry'):
        t = (entry.findtext('{http://www.w3.org/2005/Atom}title') or '').strip()
        l = ""
        for ln in entry.findall('{http://www.w3.org/2005/Atom}link'):
            href = ln.attrib.get('href')
            if href: l = href
        if t and l and PAT.search(t):
            out.append({"title": t, "url": l, "domain": source})
    return out

def dedupe(items, limit=24):
    seen=set(); out=[]
    for it in items:
        key=(it.get("title","")[:80].lower(), it.get("domain",""))
        if key in seen: continue
        seen.add(key); out.append(it)
        if len(out)>=limit: break
    return out

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin","*")
        self.send_header("Access-Control-Allow-Methods","GET,OPTIONS")
        self.send_header("Access-Control-Allow-Headers","Content-Type")
        self.end_headers()
    def do_GET(self):
        t0=time.time()
        items=[]
        for name, url in RSS_EN:
            try:
                raw = fetch(url)
                items += parse_rss(raw, name)
            except Exception:
                continue
        items = dedupe(items, 36)[:12]
        resp = {"items": items, "src":"rss-finance-en", "t_ms": int((time.time()-t0)*1000), "count": len(items)}
        self.send_response(200)
        self.send_header("Content-Type","application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin","*")
        self.end_headers()
        self.wfile.write(json.dumps(resp, ensure_ascii=False).encode("utf-8"))
