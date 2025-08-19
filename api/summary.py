
from http.server import BaseHTTPRequestHandler
import json, os, urllib.request, urllib.error, ssl

API_KEY = (os.getenv("OPENAI_API_KEY") or os.getenv("AI_GATEWAY_API_KEY") or os.getenv("AI_API_KEY"))
BASE_URL = os.getenv("AI_API_URL", "https://api.openai.com/v1/chat/completions")
MODEL    = os.getenv("AI_MODEL", "openai/gpt-4o-mini")
INCLUDE_MODEL = os.getenv("AI_INCLUDE_MODEL", "1").lower() not in ("0","false","no")
AUTH_HDR = os.getenv("AI_AUTH_HEADER", "Authorization")
AUTH_VAL = os.getenv("AI_AUTH_VALUE") or (("Bearer " + API_KEY) if AUTH_HDR.lower()=="authorization" else (API_KEY or ""))
ALLOWED  = os.getenv("ALLOWED_ORIGINS", "*")

def respond(h, code, data):
    h.send_response(code)
    h.send_header("Content-Type", "application/json; charset=utf-8")
    h.send_header("Access-Control-Allow-Origin", ALLOWED)
    h.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
    h.send_header("Access-Control-Allow-Headers", "Content-Type")
    h.end_headers()
    h.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))

def chat(messages):
    if not API_KEY:
        return None, {"error":"missing_api_key","hint":"Set AI_GATEWAY_API_KEY (or OPENAI_API_KEY)."} 
    body = {"messages": messages, "temperature": 0.2}
    if INCLUDE_MODEL: body["model"] = MODEL
    req = urllib.request.Request(
        BASE_URL,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type":"application/json", AUTH_HDR: AUTH_VAL}
    )
    try:
        with urllib.request.urlopen(req, context=ssl.create_default_context(), timeout=25) as r:
            j = json.load(r)
        return j["choices"][0]["message"]["content"], None
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8","replace")
        try: payload = json.loads(raw)
        except Exception: payload = {"message": raw[:300]}
        return None, {"http_status": e.code, "provider_error": payload}
    except urllib.error.URLError as e:
        return None, {"network_error": str(e.reason)}
    except Exception as e:
        return None, {"exception": str(e)}

def bullets_from_titles(titles, lang="en"):
    # Enforce translation to target lang for any non-English headlines
    lang = (lang or "en").lower()
    if lang.startswith("de"):
        sys = "Antworte immer auf Deutsch. Paraphrasiere/übersetze JEDE Schlagzeile in GENAU EINEN knappen Bullet-Satz (max 120 Zeichen), sachlich, ohne Emojis/Anführungszeichen. Bewahre die Reihenfolge."
    else:
        sys = "Answer in concise English. For each headline, translate if needed and write EXACTLY ONE compact bullet sentence (max 120 chars), no emojis/quotes. Keep order."
    user = "\\n".join([f"- {t}" for t in titles])
    text, err = chat([{"role":"system","content":sys},{"role":"user","content":user}])
    if err: return None, err
    lines = [l.strip(" -•") for l in text.splitlines() if l.strip()]
    return lines, None

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self): respond(self, 200, {})
    def do_GET(self):
        respond(self, 200, {"status":"ok","base_url":BASE_URL,"model":(MODEL if INCLUDE_MODEL else None),"auth_header":AUTH_HDR})
    def do_POST(self):
        try:
            n = int(self.headers.get("Content-Length","0")); raw = self.rfile.read(n) if n>0 else b"{}"
            data = json.loads(raw.decode("utf-8"))
        except Exception:
            data = {}
        lang = data.get("lang") or "en"
        titles = (data.get("titles") or [])[:4]  # hard limit 4
        if titles:
            lines, err = bullets_from_titles(titles, lang=lang)
            if err: respond(self, 502, {"error": err}); return
            respond(self, 200, {"bullets": lines}); return
        respond(self, 400, {"error":"missing titles"})
