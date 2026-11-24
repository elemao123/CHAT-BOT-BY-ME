"""Webhook de WhatsApp Cloud API (Meta). Variables: ver README."""
import json, os, urllib.request, threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import agent

VERIFY = os.environ.get("WA_VERIFY_TOKEN", "")
TOKEN = os.environ.get("WA_ACCESS_TOKEN", "")
PHONE_ID = os.environ.get("WA_PHONE_NUMBER_ID", "")
ADVISOR = os.environ.get("ADVISOR_PHONE", "51945820310")   # recibe avisos de visitas/derivaciones

def send(to, text):
    req = urllib.request.Request(f"https://graph.facebook.com/v21.0/{PHONE_ID}/messages", method="POST",
        data=json.dumps({"messaging_product": "whatsapp", "to": to, "type": "text", "text": {"body": text}}).encode(),
        headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"})
    urllib.request.urlopen(req, timeout=30).read()

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
        print("error agente:", e); out = "Disculpa, tuve un inconveniente. Un asesor te escribirá en breve."; notify(f"⚠️ Error con +{phone}: {e}")
    if out: send(phone, out)

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
