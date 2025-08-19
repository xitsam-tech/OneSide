
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
    h.send_header("Cache-Control", "no-store")
    h.end_headers()
    h.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))

def chat(messages):
    if not API_KEY:
        return None, {"error":"missing_api_key","hint":"Set OPENAI_API_KEY or AI_GATEWAY_API_KEY."}
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
        except Exception: payload = {"message": raw[:200]}
        return None, {"http_status": e.code, "provider_error": payload}
    except urllib.error.URLError as e:
        return None, {"network_error": str(e.reason)}
    except Exception as e:
        return None, {"exception": str(e)}

def bullets_from_titles(titles, lang="en"):
    lang = (lang or "en").lower()
    if lang.startswith("de"):
        sys = "Du antwortest auf Deutsch. Schreibe für jede Schlagzeile GENAU EINEN knappen Bullet-Satz (max 120 Zeichen), sachlich, ohne Emojis/Anführungszeichen, Reihenfolge beibehalten."
    elif lang.startswith("en") or lang=="auto":
        sys = "You answer in concise English. For each headline write EXACTLY ONE compact bullet sentence (max 120 chars), no emojis/quotes, preserve order."
    else:
        sys = "You answer in concise English. For each headline write EXACTLY ONE compact bullet sentence (max 120 chars), no emojis/quotes, preserve order."
    user = "\n".join([f"- {t}" for t in titles])
    text, err = chat([{"role":"system","content":sys},{"role":"user","content":user}])
    if err: return None, err
    lines = [l.strip(" -•") for l in text.splitlines() if l.strip()]
    return lines, None

def bullets_from_hints(hints, lang="en"):
    if (lang or "en").lower().startswith("de"):
        sys = "Du bist ein knapper, sachlicher Analyst. Schreibe 3 kurze Bullet-Sätze (max 240 Zeichen), direkt, ohne Emojis, auf Deutsch."
        usr = f"Fasse die aktuelle Kryptolage in 3 Bullet-Sätzen zusammen. Hinweise: {hints}"
    else:
        sys = "You are a concise, matter-of-fact analyst. Write 3 short bullet sentences (max 240 chars), direct, no emojis, in English."
        usr = f"Summarize the current crypto situation in 3 bullet sentences. Hints: {hints}"
    text, err = chat([{"role":"system","content":sys},{"role":"user","content":usr}])
    if err: return None, err
    lines = [l.strip(" -•") for l in text.splitlines() if l.strip()][:3]
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
        if isinstance(data.get("titles"), list) and data["titles"]:
            lines, err = bullets_from_titles(data["titles"][:8], lang=lang)
        else:
            hints = data.get("hints") or ""
            lines, err = bullets_from_hints(hints, lang=lang)
        if err:
            respond(self, 502 if ('http_status' in err or 'network_error' in err) else 501, {"error": err})
        else:
            respond(self, 200, {"bullets": lines})
