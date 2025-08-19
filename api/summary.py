from http.server import BaseHTTPRequestHandler
import json, os, urllib.request, urllib.error, ssl

# --- Flexible env configuration ---
API_KEY = (
    os.getenv("OPENAI_API_KEY") or
    os.getenv("AI_GATEWAY_API_KEY") or
    os.getenv("AI_API_KEY")
)
BASE_URL = os.getenv("AI_API_URL", "https://api.openai.com/v1/chat/completions")
MODEL    = os.getenv("AI_MODEL", "gpt-4o-mini")
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
    h.send_header("Cache-Control", "no-store")
    h.end_headers()
    h.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))

def call_chat(messages):
    if not API_KEY:
        return None, {"error":"missing_api_key","hint":"Set OPENAI_API_KEY or AI_GATEWAY_API_KEY."}
    body = {"messages": messages, "temperature": 0.2}
    if INCLUDE_MODEL:
        body["model"] = MODEL
    req = urllib.request.Request(
        BASE_URL,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type":"application/json", AUTH_HDR: AUTH_VAL}
    )
    try:
        with urllib.request.urlopen(req, context=ssl.create_default_context(), timeout=20) as r:
            j = json.load(r)
        return j["choices"][0]["message"]["content"], None
    except urllib.error.HTTPError as e:
        try:
            raw = e.read().decode("utf-8","replace")
            payload = json.loads(raw)
        except Exception:
            payload = {"message": raw[:200]}
        return None, {"http_status": e.code, "provider_error": payload, "hint":"Check API key, model, or AI_API_URL/headers."}
    except urllib.error.URLError as e:
        return None, {"network_error": str(e.reason)}
    except Exception as e:
        return None, {"exception": str(e)}

def bullets_from_titles(titles):
    prompt = "Paraphrasiere jede Schlagzeile in GENAU EINEN knappen Bullet-Satz (max 120 Zeichen), ohne Anführungszeichen & Emojis, Reihenfolge beibehalten.\n\n" + "\n".join([f"- {t}" for t in titles])
    text, err = call_chat([{"role":"user","content":prompt}])
    if err: return None, err
    lines = [l.strip(" -•") for l in text.splitlines() if l.strip()]
    return lines, None

def bullets_from_hints(hints):
    system = "Du bist ein knapper, sachlicher Analyst. Schreibe 3 kurze Bullet-Sätze (max 240 Zeichen), direkt, ohne Emojis, auf Deutsch."
    text, err = call_chat([{"role":"system","content":system},{"role":"user","content":f"Fasse die aktuelle Kryptolage in 3 Bullet-Sätzen zusammen. Hinweise: {hints}"}])
    if err: return None, err
    lines = [l.strip(" -•") for l in text.splitlines() if l.strip()][:3]
    return lines, None

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self): respond(self, 200, {})
    def do_GET(self):
        respond(self, 200, {
            "status":"ok",
            "needs_env": None if API_KEY else "API_KEY (OPENAI_API_KEY or AI_GATEWAY_API_KEY or AI_API_KEY)",
            "base_url": BASE_URL,
            "model": MODEL if INCLUDE_MODEL else None,
            "auth_header": AUTH_HDR
        })
    def do_POST(self):
        try:
            n = int(self.headers.get("Content-Length","0")); raw = self.rfile.read(n) if n>0 else b"{}"
            data = json.loads(raw.decode("utf-8"))
        except Exception:
            data = {}
        if isinstance(data.get("titles"), list) and data["titles"]:
            lines, err = bullets_from_titles(data["titles"][:8])
        else:
            hints = data.get("hints") or ""
            lines, err = bullets_from_hints(hints)
        if err:
            respond(self, 502 if 'http_status' in err or 'network_error' in err else 501, {"error": err})
        else:
            respond(self, 200, {"bullets": lines})