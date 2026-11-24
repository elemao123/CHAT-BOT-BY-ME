"""Prueba el flujo completo con un LLM simulado (sin red)."""
import os, tempfile, json
os.environ["AGENT_DB"] = tempfile.mktemp(suffix=".db")
import agent
from datetime import timedelta

day = (agent.now() + timedelta(days=2)).strftime("%Y-%m-%d")
script = iter([
 [{"type":"tool_use","id":"1","name":"ver_horarios_disponibles","input":{"fecha":day}}],
 [{"type":"tool_use","id":"2","name":"agendar_visita","input":{"nombre":"Ana","fecha":day,"hora":"16:00","proyecto":"Alameda 5","unidad":"Dpto 301"}}],
 [{"type":"text","text":"¡Listo Ana! Te esperamos."}],
 [{"type":"tool_use","id":"3","name":"agendar_visita","input":{"nombre":"Ana","fecha":day,"hora":"23:00","proyecto":"Alameda 5"}}],
 [{"type":"text","text":"Esa hora no se puede."}],
 [{"type":"tool_use","id":"4","name":"derivar_a_asesor","input":{"motivo":"quiere separar","resumen":"Ana, 301"}}],
 [{"type":"text","text":"Un asesor te escribe."}],
])
seen=[]
def fake(system, msgs):
    r = next(script); 
    if isinstance(msgs[-1]["content"], list): seen.append(msgs[-1])
    return {"content": r}
notes=[]
o = agent.reply("51911", "quiero ver el departamento 301", notes.append, fake); assert "Ana" in o[-1] and len(o)==2 and "Smart Home" in o[0]
res = json.loads(seen[0]["content"][0]["content"]); assert "16:00" in res["libres"] and "08:00" not in res["libres"]
assert json.loads(seen[1]["content"][0]["content"])["ok"] and "NUEVA VISITA" in notes[0]
o = agent.reply("51911", "otra a las 23", notes.append, fake)
assert json.loads(seen[2]["content"][0]["content"])["ok"] is False
o = agent.reply("51911", "quiero separar", notes.append, fake); assert "asesor" in o[-1]
assert agent.reply("51911", "hola?", notes.append, fake) is None   # humano atiende: bot callado
# capacidad: 2 por hora
for p in ("a","b","c"):
    agent.run_tool("agendar_visita", {"nombre":p,"fecha":day,"hora":"10:00","proyecto":"Alameda II"}, p, lambda m:None)
assert "10:00" not in json.loads(json.dumps(agent.run_tool("ver_horarios_disponibles",{"fecha":day},"x",lambda m:None)))["libres"]
# protección de chats personales
assert agent.reply("51700", "hola mamá, ¿vienes a almorzar?", notes.append, fake) is None
assert agent.reply("51700", "Hola, quiero información de Smart Home", notes.append, lambda s,m: {"content":[{"type":"text","text":"Hola!"}]}) == [agent.welcome(), "Hola!"]
agent.IGNORE_PHONES.add("51701")
assert agent.reply("51701", "precio del departamento", notes.append, fake) is None
agent.set_status("51702", "humano")
assert agent.reply("51702", "quiero una visita", notes.append, fake) is None
agent.set_status("51702", "bot")
assert agent.reply("51702", "quiero una visita", notes.append, lambda s,m: {"content":[{"type":"text","text":"ok"}]}) == ["ok"]
# derivar en el PRIMER mensaje también silencia al bot
first = iter([[{"type":"tool_use","id":"9","name":"derivar_a_asesor","input":{"motivo":"humano","resumen":"x"}}],[{"type":"text","text":"Te paso con un asesor."}]])
assert agent.reply("51703", "quiero hablar con un asesor del proyecto", notes.append, lambda s,m: {"content": next(first)})
assert agent.reply("51703", "hola?", notes.append, fake) is None
# redes sociales: sin filtro de intención, con presentación y pidiendo celular
sys_seen=[]
def fake_social(system, msgs):
    sys_seen.append(system); return {"content":[{"type":"text","text":"Hola desde IG"}]}
o = agent.reply("ig:555", "hola", notes.append, fake_social, channel="instagram")
assert o == [agent.welcome(), "Hola desde IG"] and "Instagram" in sys_seen[0] and "celular" in sys_seen[0]
assert agent._who("ig:555") == "ig:555" and agent._who("5191") == "+5191"
print("OK: todas las pruebas pasaron")
