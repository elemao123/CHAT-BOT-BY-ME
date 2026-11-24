"""Chatea con el agente en la terminal (necesita ANTHROPIC_API_KEY)."""
import agent
print("Chat de prueba (Ctrl+C para salir)")
while True:
    t = input("Tú: ")
    out = agent.reply("51999000111", t, notify=lambda m: print("  [AVISO ASESOR]", m))
    for part in out or ["(el bot no responde a este mensaje)"]: print("Sofía:", part, "\n")
