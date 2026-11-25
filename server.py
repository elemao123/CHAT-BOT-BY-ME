"""Webhook de WhatsApp Cloud API (Meta). Variables: ver README."""
import json, os, urllib.request, threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import agent

VERIFY = os.environ.get("WA_VERIFY_TOKEN", "")
TOKEN = os.environ.get("WA_ACCESS_TOKEN", "")
PHONE_ID = os.environ.get("WA_PHONE_NUMBER_ID", "")
PAGE_TOKEN = os.environ.get("PAGE_ACCESS_TOKEN", "")   # token de la página de Facebook (sirve para Messenger e Instagram)
ADVISOR = os.environ.get("ADVISOR_PHONE", "51945820310")   # recibe avisos de visitas/derivaciones

def send(to, text):
    req = urllib.request.Request(f"https://graph.facebook.com/v21.0/{PHONE_ID}/messages", method="POST",
        data=json.dumps({"messaging_product": "whatsapp", "to": to, "type": "text", "text": {"body": text}}).encode(),
        headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"})
    urllib.request.urlopen(req, timeout=30).read()

def send_social(uid, text):
    req = urllib.request.Request("https://graph.facebook.com/v21.0/me/messages", method="POST",
        data=json.dumps({"recipient": {"id": uid}, "messaging_type": "RESPONSE", "message": {"text": text}}).encode(),
        headers={"Authorization": f"Bearer {PAGE_TOKEN}", "Content-Type": "application/json"})
    urllib.request.urlopen(req, timeout=30).read()

def handle_social(channel, ev):
    """Mensajes directos de Instagram (instagram) o Facebook Messenger (facebook)."""
    prefix = "ig" if channel == "instagram" else "fb"
    msg = ev["message"]
    if msg.get("is_echo"):            # tú respondiste a mano desde la página/IG: el bot se calla (/bot lo reactiva)
        agent.set_status(f"{prefix}:{ev['recipient']['id']}", "bot" if (msg.get("text") or "").strip().lower() == "/bot" else "humano")
        return
    uid, key = ev["sender"]["id"], f"{prefix}:{ev['sender']['id']}"
    c = agent.db()
    if c.execute("SELECT 1 FROM seen WHERE id=?", (msg["mid"],)).fetchone(): c.close(); return
    c.execute("INSERT INTO seen VALUES(?)", (msg["mid"],)); c.commit(); c.close()
    text = msg.get("text")
    if not text:
        send_social(uid, "Por ahora solo puedo leer mensajes de texto 🙂 ¿Me cuentas por escrito qué departamento buscas?"); return
    try:
        out = agent.reply(key, text, notify, channel=channel)
    except Exception as e:
        print("error agente:", e); out = ["Disculpa, tuve un inconveniente. Un asesor te escribirá en breve."]; notify(f"⚠️ Error con {key}: {e}")
    for part in out or []: send_social(uid, part)

def notify(msg):
    try: send(ADVISOR, msg)
    except Exception as e: print("notify fallo:", e)

def handle(m):
    phone, mid = m["from"], m["id"]
    c = agent.db()
    if c.execute("SELECT 1 FROM seen WHERE id=?", (mid,)).fetchone(): c.close(); return
    c.execute("INSERT INTO seen VALUES(?)", (mid,)); c.commit(); c.close()
    text = m.get("text", {}).get("body") if m["type"] == "text" else None
    if text is None:
        send(phone, "Por ahora solo puedo leer mensajes de texto 🙂 ¿Me cuentas por escrito qué departamento buscas?"); return
    try:
        out = agent.reply(phone, text, notify)
    except Exception as e:
        print("error agente:", e); out = ["Disculpa, tuve un inconveniente. Un asesor te escribirá en breve."]; notify(f"⚠️ Error con +{phone}: {e}")
    for part in out or []: send(phone, part)

class H(BaseHTTPRequestHandler):
    def do_GET(self):
        from urllib.parse import urlparse, parse_qs
        q = parse_qs(urlparse(self.path).query)
        if urlparse(self.path).path in ("/privacidad", "/privacy"):
            try:
                with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "privacidad.html"), "rb") as f:
                    page = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers(); self.wfile.write(page)
            except OSError:
                self.send_response(404); self.end_headers()
            return
        if q.get("hub.verify_token", [""])[0] == VERIFY and VERIFY:
            self.send_response(200); self.end_headers(); self.wfile.write(q["hub.challenge"][0].encode())
        else:
            self.send_response(200 if self.path == "/" else 403); self.end_headers()
    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
        self.send_response(200); self.end_headers()      # responder rápido a Meta
        if body.get("object") in ("page", "instagram"):
            channel = "instagram" if body["object"] == "instagram" else "facebook"
            for entry in body.get("entry", []):
                for ev in entry.get("messaging", []):
                    if "message" in ev:
                        threading.Thread(target=handle_social, args=(channel, ev), daemon=True).start()
            return
        for e in body.get("entry", []):
            for ch in e.get("changes", []):
                v = ch.get("value", {})
                for m in v.get("messages", []):
                    threading.Thread(target=handle, args=(m,), daemon=True).start()
                # Coexistence: mensajes que TÚ escribes desde la app de WhatsApp Business.
                # Si respondes a mano, el bot se calla en ese chat; escribe /bot para reactivarlo.
                for echo in v.get("message_echoes", []):
                    txt = (echo.get("text") or {}).get("body", "").strip().lower()
                    agent.set_status(echo["to"], "bot" if txt == "/bot" else "humano")
    def log_message(self, *a): pass

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))
    print("Escuchando en", port); ThreadingHTTPServer(("", port), H).serve_forever()
"""Webhook de WhatsApp Cloud API (Meta). Variables: ver README."""
import json, os, urllib.request, threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import agent

VERIFY = os.environ.get("WA_VERIFY_TOKEN", "")
TOKEN = os.environ.get("WA_ACCESS_TOKEN", "")
PHONE_ID = os.environ.get("WA_PHONE_NUMBER_ID", "")
PAGE_TOKEN = os.environ.get("PAGE_ACCESS_TOKEN", "")   # token de la página de Facebook (sirve para Messenger e Instagram)
ADVISOR = os.environ.get("ADVISOR_PHONE", "51945820310")   # recibe avisos de visitas/derivaciones

def send(to, text):
    req = urllib.request.Request(f"https://graph.facebook.com/v21.0/{PHONE_ID}/messages", method="POST",
        data=json.dumps({"messaging_product": "whatsapp", "to": to, "type": "text", "text": {"body": text}}).encode(),
        headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"})
    urllib.request.urlopen(req, timeout=30).read()

def send_social(uid, text):
    req = urllib.request.Request("https://graph.facebook.com/v21.0/me/messages", method="POST",
        data=json.dumps({"recipient": {"id": uid}, "messaging_type": "RESPONSE", "message": {"text": text}}).encode(),
        headers={"Authorization": f"Bearer {PAGE_TOKEN}", "Content-Type": "application/json"})
    urllib.request.urlopen(req, timeout=30).read()

def handle_social(channel, ev):
    """Mensajes directos de Instagram (instagram) o Facebook Messenger (facebook)."""
    prefix = "ig" if channel == "instagram" else "fb"
    msg = ev["message"]
    if msg.get("is_echo"):            # tú respondiste a mano desde la página/IG: el bot se calla (/bot lo reactiva)
        agent.set_status(f"{prefix}:{ev['recipient']['id']}", "bot" if (msg.get("text") or "").strip().lower() == "/bot" else "humano")
        return
    uid, key = ev["sender"]["id"], f"{prefix}:{ev['sender']['id']}"
    c = agent.db()
    if c.execute("SELECT 1 FROM seen WHERE id=?", (msg["mid"],)).fetchone(): c.close(); return
    c.execute("INSERT INTO seen VALUES(?)", (msg["mid"],)); c.commit(); c.close()
    text = msg.get("text")
    if not text:
        send_social(uid, "Por ahora solo puedo leer mensajes de texto 🙂 ¿Me cuentas por escrito qué departamento buscas?"); return
    try:
        out = agent.reply(key, text, notify, channel=channel)
    except Exception as e:
        print("error agente:", e); out = ["Disculpa, tuve un inconveniente. Un asesor te escribirá en breve."]; notify(f"⚠️ Error con {key}: {e}")
    for part in out or []: send_social(uid, part)

def notify(msg):
    try: send(ADVISOR, msg)
    except Exception as e: print("notify fallo:", e)

def handle(m):
    phone, mid = m["from"], m["id"]
    c = agent.db()
    if c.execute("SELECT 1 FROM seen WHERE id=?", (mid,)).fetchone(): c.close(); return
    c.execute("INSERT INTO seen VALUES(?)", (mid,)); c.commit(); c.close()
    text = m.get("text", {}).get("body") if m["type"] == "text" else None
    if text is None:
        send(phone, "Por ahora solo puedo leer mensajes de texto 🙂 ¿Me cuentas por escrito qué departamento buscas?"); return
    try:
        out = agent.reply(phone, text, notify)
    except Exception as e:
        print("error agente:", e); out = ["Disculpa, tuve un inconveniente. Un asesor te escribirá en breve."]; notify(f"⚠️ Error con +{phone}: {e}")
    for part in out or []: send(phone, part)

class H(BaseHTTPRequestHandler):
    def do_GET(self):
        from urllib.parse import urlparse, parse_qs
        q = parse_qs(urlparse(self.path).query)
        if q.get("hub.verify_token", [""])[0] == VERIFY and VERIFY:
            self.send_response(200); self.end_headers(); self.wfile.write(q["hub.challenge"][0].encode())
        else:
            self.send_response(200 if self.path == "/" else 403); self.end_headers()
    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
        self.send_response(200); self.end_headers()      # responder rápido a Meta
        if body.get("object") in ("page", "instagram"):
            channel = "instagram" if body["object"] == "instagram" else "facebook"
            for entry in body.get("entry", []):
                for ev in entry.get("messaging", []):
                    if "message" in ev:
                        threading.Thread(target=handle_social, args=(channel, ev), daemon=True).start()
            return
        for e in body.get("entry", []):
            for ch in e.get("changes", []):
                v = ch.get("value", {})
                for m in v.get("messages", []):
                    threading.Thread(target=handle, args=(m,), daemon=True).start()
                # Coexistence: mensajes que TÚ escribes desde la app de WhatsApp Business.
                # Si respondes a mano, el bot se calla en ese chat; escribe /bot para reactivarlo.
                for echo in v.get("message_echoes", []):
                    txt = (echo.get("text") or {}).get("body", "").strip().lower()
                    agent.set_status(echo["to"], "bot" if txt == "/bot" else "humano")
    def log_message(self, *a): pass

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))
    print("Escuchando en", port); ThreadingHTTPServer(("", port), H).serve_forever()
