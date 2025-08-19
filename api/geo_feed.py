
from http.server import BaseHTTPRequestHandler
import json, urllib.parse, urllib.request, ssl, os, time, xml.etree.ElementTree as ET

ALLOWED = os.getenv("ALLOWED_ORIGINS", "*")

# --- Primary: GDELT (Geo + Macro) ---
GDELT = "https://api.gdeltproject.org/api/v2/doc/doc"
Q_GEO  = "(war OR conflict OR ceasefire OR sanctions OR nato OR russia OR china OR israel OR iran OR ukraine OR \"middle east\" OR election OR coup)"
Q_MACRO= "(inflation OR cpi OR ppi OR \"interest rate\" OR yields OR recession OR fomc OR \"federal reserve\" OR ecb OR boe OR nfp OR payrolls OR gdp)"

# --- RSS fallbacks (no key) ---
RSS_SOURCES = [
    ("Reuters World", "https://feeds.reuters.com/reuters/worldNews"),
    ("Reuters Business", "https://feeds.reuters.com/reuters/businessNews"),
    ("BBC World", "https://feeds.bbci.co.uk/news/world/rss.xml"),
    ("Al Jazeera", "https://www.aljazeera.com/xml/rss/all.xml"),
]

UA = {"User-Agent":"Mozilla/5.0 (OneSide/1.0; +https://one-side.vercel.app)"}

def get_json(url, timeout=5):
    ctx = ssl.create_default_context()
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, context=ctx, timeout=timeout) as r:
        return json.load(r)

def fetch_docs(q, timeout=5, maxrecords=24):
    url = GDELT + "?" + urllib.parse.urlencode({
        "query": q, "timespan":"4h", "maxrecords": str(maxrecords), "format":"json", "sort":"DateDesc"
    })
    try:
        j = get_json(url, timeout=timeout)
        arts = (j.get("articles") or [])
        out = []
        for a in arts:
            url = a.get("url"); title = a.get("title") or ""
            if not (url and title): continue
            out.append({
                "url": url,
                "title": title,
                "domain": (a.get("domain") or urllib.parse.urlparse(url).netloc).replace("www.",""),
                "lang": a.get("language") or "",
                "ts": a.get("seendate") or ""
            })
        return out, None
    except Exception as e:
        return [], f"gdelt_error:{type(e).__name__}:{e}"

def fetch_rss(url, timeout=5, limit=30):
    try:
        ctx = ssl.create_default_context()
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, context=ctx, timeout=timeout) as r:
            data = r.read()
        root = ET.fromstring(data)
        out = []
        for item in root.findall('.//item')[:limit]:
            title = (item.findtext('title') or "").strip()
            link  = (item.findtext('link') or "").strip()
            if not (title and link): continue
            d = urllib.parse.urlparse(link).netloc.replace("www.","")
            out.append({"url": link, "title": title, "domain": d, "lang":"", "ts": ""})
        return out, None
    except Exception as e:
        return [], f"rss_error:{type(e).__name__}:{e}"

def dedup(items, limit=12):
    seen = set(); out = []
    for it in items:
        key = (it.get("domain",""), (it.get("title") or "")[:64])
        if key in seen: continue
        seen.add(key); out.append(it)
        if len(out) >= limit: break
    return out

class handler(BaseHTTPRequestHandler):
    def _hdr(self, code=200):
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", ALLOWED)
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Cache-Control", "public, max-age=180")
        self.end_headers()

    def do_OPTIONS(self): self._hdr()

    def do_GET(self):
        t0 = time.time()
        items = []
        errors = []

        # Try GDELT fast (short timeouts)
        geo, err = fetch_docs(Q_GEO, timeout=5, maxrecords=24)
        if err: errors.append(err)
        mac, err2 = fetch_docs(Q_MACRO, timeout=5, maxrecords=24)
        if err2: errors.append(err2)
        items = dedup(geo + mac, limit=12)

        # Fallback to RSS if needed
        if not items:
            for name, url in RSS_SOURCES:
                rss, er = fetch_rss(url, timeout=5, limit=30)
                if er: errors.append(f"{name}:{er}")
                items = dedup(items + rss, limit=12)
                if len(items) >= 6: break  # good enough

        self._hdr(200)
        payload = {"items": items, "src": "GDELT+RSS", "t_ms": int((time.time()-t0)*1000)}
        if errors: payload["errors"] = errors
        self.wfile.write(json.dumps(payload, ensure_ascii=False).encode("utf-8"))
