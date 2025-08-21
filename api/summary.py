from http.server import BaseHTTPRequestHandler
import json, os, urllib.request, ssl

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ALLOWED = os.getenv("ALLOWED_ORIGINS", "*")

SYSTEM = "Du bist ein knapper, sachlicher Analyst. Schreibe 3 kurze Bullet-Sätze (max 240 Zeichen), direkt, ohne Emojis, auf Deutsch."
USER_TMPL = "Fasse die aktuelle Kryptolage in 3 Bullet-Sätzen zusammen. Nutze diese Hinweise falls vorhanden: {hints}"

def respond(handler, code, data):
    handler.send_response(code)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Access-Control-Allow-Origin", ALLOWED)
    handler.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
    handler.send_header("Access-Control-Allow-Headers", "Content-Type")
    handler.send_header("Cache-Control", "no-store")
    handler.end_headers()
    handler.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))

def call_openai(hints):
    if not OPENAI_API_KEY:
        return None, "OPENAI_API_KEY not set"
    body = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": USER_TMPL.format(hints=hints or '')}
        ],
        "temperature": 0.2
    }
    req = urllib.request.Request("https://api.openai.com/v1/chat/completions",
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type":"application/json","Authorization":f"Bearer {OPENAI_API_KEY}"})
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, context=ctx, timeout=15) as r:
        j = json.load(r)
    try:
        return j["choices"][0]["message"]["content"], None
    except Exception as e:
        return None, f"parse_error: {e}"

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self): respond(self, 200, {})
    def do_POST(self):
        try:
            n = int(self.headers.get("Content-Length","0"))
            raw = self.rfile.read(n) if n>0 else b"{}"
            j = json.loads(raw.decode("utf-8"))
        except Exception:
            j = {}
        hints = j.get("hints") or ""
        text, err = call_openai(hints)
        if err:
            respond(self, 501, {"error": err}); return
        bullets = [s.strip(" •-") for s in text.splitlines() if s.strip()][:3]
        respond(self, 200, {"bullets": bullets})
    def do_GET(self):
        respond(self, 200, {"status":"ok","provider":"openai","needs_env":"OPENAI_API_KEY"})