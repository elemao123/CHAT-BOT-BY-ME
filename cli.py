"""Chatea con el agente en la terminal (necesita ANTHROPIC_API_KEY)."""
import agent
print("Chat de prueba (Ctrl+C para salir)")
while True:
    t = input("Tú: ")
    print("Sofía:", agent.reply("51999000111", t, notify=lambda m: print("  [AVISO ASESOR]", m)), "\n")
