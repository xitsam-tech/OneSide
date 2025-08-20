
from http.server import BaseHTTPRequestHandler
import json, os, urllib.request, urllib.error, ssl

API_KEY = (os.getenv("OPENAI_API_KEY") or os.getenv("AI_GATEWAY_API_KEY") or os.getenv("AI_API_KEY"))
BASE_URL = os.getenv("AI_API_URL", "https://api.openai.com/v1/chat/completions")
MODEL    = os.getenv("AI_MODEL", "gpt-4o-mini")
AUTH_HDR = os.getenv("AI_AUTH_HEADER", "Authorization")
AUTH_VAL = os.getenv("AI_AUTH_VALUE") or (("Bearer " + API_KEY) if AUTH_HDR.lower()=="authorization" else (API_KEY or ""))
ALLOWED  = os.getenv("ALLOWED_ORIGINS","*")
TIMEOUT  = int(os.getenv("AI_TIMEOUT","8"))
INCLUDE_MODEL = os.getenv("AI_INCLUDE_MODEL","1") not in ("0","false","no")

def respond(h, code, data):
    h.send_response(code)
    h.send_header("Content-Type","application/json; charset=utf-8")
    h.send_header("Access-Control-Allow-Origin", ALLOWED)
    h.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
    h.send_header("Access-Control-Allow-Headers", "Content-Type")
    h.end_headers()
    h.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))

def chat(messages):
    if not API_KEY:
        return None, {"error":"missing_api_key","hint":"Set AI_GATEWAY_API_KEY or OPENAI_API_KEY"}
    body = {"messages": messages, "temperature": 0.2}
    if INCLUDE_MODEL: body["model"] = MODEL
    req = urllib.request.Request(BASE_URL, data=json.dumps(body).encode("utf-8"),
                                 headers={"Content-Type":"application/json", AUTH_HDR: AUTH_VAL})
    try:
        with urllib.request.urlopen(req, context=ssl.create_default_context(), timeout=TIMEOUT) as r:
            j = json.load(r)
        return j["choices"][0]["message"]["content"], None
    except urllib.error.HTTPError as e:
        try: payload = json.loads(e.read().decode("utf-8","replace"))
        except Exception: payload = {"message":"http error"}
        return None, {"http_status": e.code, "provider_error": payload}
    except Exception as e:
        return None, {"error": str(e)}

def extract_titles(data):
    if isinstance(data.get("titles"), list) and data["titles"]:
        return [str(t or "") for t in data["titles"]][:4]
    items = data.get("items") or []
    out = []
    for it in items:
        t = (it.get("title") if isinstance(it, dict) else None) or ""
        if t: out.append(str(t))
    return out[:4]

def pick_lang(data):
    lang = (data.get("lang") or "en").lower()
    return "de" if lang.startswith("de") else "en"

def bullets(titles, lang="en"):
    if lang=="de":
        sys = "Antworte in Deutsch. Schreibe GENAU 4 extrem knappe Bullets (max 18 Wörter), ohne Einleitung/Outro. Fokus: Geopolitik/Makro mit Bezug zu Krypto/Finanzen."
    else:
        sys = "Answer in concise English. Write EXACTLY 4 ultra-short bullets (max 18 words), no intro/outro. Focus on geopolitics/macro with crypto/finance relevance."
    user = "\\n".join(f"- {t}" for t in titles)
    txt, err = chat([{"role":"system","content":sys},{"role":"user","content":user}])
    if err:
        txt, err = chat([{"role":"system","content":sys},{"role":"user","content":user}])
        if err: return titles, True, err
    lines = [l.strip(" -•") for l in txt.splitlines() if l.strip()][:4]
    if len(lines)<4: lines = (lines + titles)[:4]
    return lines, False, None

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self): respond(self, 200, {})
    def do_GET(self): respond(self, 200, {"status":"ok","provider":"openai","needs_env": (None if API_KEY else "OPENAI_API_KEY/AI_GATEWAY_API_KEY")})
    def do_POST(self):
        n = int(self.headers.get("Content-Length","0"))
        raw = self.rfile.read(n) if n>0 else b"{}"
        try: data = json.loads(raw.decode("utf-8"))
        except Exception: data = {}
        titles = extract_titles(data)
        if not titles:
            respond(self, 400, {"error":"missing titles"}); return
        lang = pick_lang(data)
        out, used_fallback, err = bullets(titles, lang=lang)
        payload = {"bullets": out}
        if used_fallback: payload.update({"used_fallback": True, "error": err})
        respond(self, 200, payload)
