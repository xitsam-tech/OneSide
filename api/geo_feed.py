from http.server import BaseHTTPRequestHandler
import json, urllib.parse, urllib.request, ssl, os

ALLOWED = os.getenv("ALLOWED_ORIGINS", "*")
GDELT = "https://api.gdeltproject.org/api/v2/doc/doc"
Q_GEO  = "(war OR conflict OR ceasefire OR sanctions OR nato OR russia OR china OR israel OR iran OR ukraine OR \"middle east\" OR election OR coup)"
Q_MACRO= "(inflation OR cpi OR ppi OR \"interest rate\" OR yields OR recession OR fomc OR \"federal reserve\" OR ecb OR boe OR nfp OR payrolls OR gdp)"

def get_json(url):
    ctx = ssl.create_default_context()
    req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
    with urllib.request.urlopen(req, context=ctx, timeout=12) as r:
        return json.load(r)

def fetch_docs(q):
    params = {"query": q, "timespan":"4h", "maxrecords":"30", "format":"json", "sort":"DateDesc"}
    url = GDELT + "?" + urllib.parse.urlencode(params)
    try:
        j = get_json(url)
        arts = (j.get("articles") or [])
        out = []
        for a in arts:
            url = a.get("url"); title = a.get("title") or ""
            domain = a.get("domain") or ""
            lang = a.get("language") or ""
            dt   = a.get("seendate") or ""
            if url and title: out.append({"url": url, "title": title, "domain": domain, "lang": lang, "ts": dt})
        return out
    except Exception:
        return []

def dedup(items, limit=12):
    seen = set(); out = []
    for it in items:
        key = (it.get("domain",""), (it.get("title") or "")[:60])
        if key in seen: continue
        seen.add(key); out.append(it)
        if len(out)>=limit: break
    return out

class handler(BaseHTTPRequestHandler):
    def _hdr(self, code=200, ctype="application/json"):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Access-Control-Allow-Origin", ALLOWED)
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Cache-Control", "public, max-age=300")
        self.end_headers()

    def do_OPTIONS(self): self._hdr()

    def do_GET(self):
        geo  = fetch_docs(Q_GEO)
        macro= fetch_docs(Q_MACRO)
        items = dedup(geo + macro, limit=12)
        self._hdr(); self.wfile.write(json.dumps({"items": items, "src": "GDELT Doc API"}).encode("utf-8"))