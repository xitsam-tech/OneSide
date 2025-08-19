from http.server import BaseHTTPRequestHandler
import json, os, urllib.request, ssl

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ALLOWED = os.getenv("ALLOWED_ORIGINS", "*")

def respond(handler, code, data):
    handler.send_response(code)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Access-Control-Allow-Origin", ALLOWED)
    handler.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
    handler.send_header("Access-Control-Allow-Headers", "Content-Type")
    handler.send_header("Cache-Control", "no-store")
    handler.end_headers()
    handler.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))

def call_openai_list(titles):
    if not OPENAI_API_KEY: return None, "OPENAI_API_KEY not set"
    prompt = "Paraphrasiere jede Schlagzeile in GENAU EINEN knappen Bullet-Satz (max 120 Zeichen), ohne Anführungszeichen & Emojis, Reihenfolge beibehalten.\n\n" + "\n".join([f"- {t}" for t in titles])
    body = {"model":"gpt-4o-mini","messages":[{"role":"user","content":prompt}],"temperature":0.2}
    req = urllib.request.Request("https://api.openai.com/v1/chat/completions",
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type":"application/json","Authorization":f"Bearer {OPENAI_API_KEY}"})
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, context=ctx, timeout=15) as r:
        j = json.load(r)
    try:
        text = j["choices"][0]["message"]["content"]
        lines = [l.strip(" -•") for l in text.splitlines() if l.strip()]
        return lines, None
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
        titles = j.get("titles") or []
        if titles:
            lines, err = call_openai_list(titles[:8])
            if err: respond(self, 501, {"error": err}); return
            respond(self, 200, {"bullets": lines}); return
        respond(self, 400, {"error":"missing titles"})
    def do_GET(self):
        respond(self, 200, {"status":"ok","provider":"openai","needs_env":"OPENAI_API_KEY"})