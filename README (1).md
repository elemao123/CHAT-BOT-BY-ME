# Agente "Sofía" · Smart Home Inmobiliaria

Atiende WhatsApp, califica al cliente y lo lleva a **agendar una visita** (o lo deriva a un asesor si quiere separar/comprar).
Solo usa Python 3.9+ estándar (sin instalar nada).

## Archivos
- `knowledge.md` — datos de la web. **Aquí agrega precios, bonos, entrega** cuando los tengas; el agente no inventa lo que no está.
- `agent.py` — cerebro (Claude + herramientas: ver horarios, agendar, guardar lead, derivar).
- `server.py` — webhook de WhatsApp Cloud API. `cli.py` — chat de prueba. `test_agent.py` — pruebas sin red.
- `bienvenida.txt` — presentación que se envía al primer mensaje de cada cliente nuevo (edítala cuando quieras).
- `render.yaml` — configuración para desplegar en Render (con disco persistente para la base de datos).

## Probar
    export ANTHROPIC_API_KEY=sk-ant-...
    python3 cli.py

## Conectar a WhatsApp (Meta Cloud API)
Variables: `IGNORE_PHONES` (opcional: familia/amigos que el bot nunca contesta, separados por coma), `ANTHROPIC_API_KEY`, `WA_VERIFY_TOKEN` (inventa uno), `WA_ACCESS_TOKEN`, `WA_PHONE_NUMBER_ID`, `ADVISOR_PHONE` (ej. 51945820310; recibe avisos de visitas y derivaciones).
1. Corre `python3 server.py` en un servidor con HTTPS (Render, Railway, Fly, VPS).
2. En Meta for Developers → WhatsApp → Configuración: Callback URL = tu URL, Verify token = `WA_VERIFY_TOKEN`, suscribe el campo `messages`.
Nota: un número registrado de forma normal en la API deja de funcionar en la app de WhatsApp. Para usar ambos a la vez hace falta Coexistence (ver abajo), que depende de que Meta lo habilite para tu cuenta.

## Reglas
Visitas L-D 9:00-19:00 (hora Lima), cupos de 2 por hora (`SLOT_CAPACITY`), mínimo 2 h de anticipación. Si derivan a un humano, el bot calla en ese chat.

## Si usas tu número personal (Coexistence)
- El bot solo inicia conversación si el primer mensaje habla de inmuebles (Smart Home, departamento, precio, visita…); "hola mamá" lo ignora. Lista negra: `IGNORE_PHONES`.
- Si respondes tú a mano desde la app, el bot se calla en ese chat. Escribe `/bot` en ese chat para reactivarlo. (En Meta suscribe también el campo `smb_message_echoes`; verifícalo en la prueba.)
- Tip: en la web usa un botón wa.me con texto prellenado ("Hola, quiero información de Smart Home") para que el bot siempre entre.

## Instagram y Facebook Messenger (24/7)
- Mismo webhook (`/`). Variable extra: `PAGE_ACCESS_TOKEN` (token de la página de Facebook; sirve también para los mensajes de Instagram).
- En Meta: agrega los casos de uso "Messenger" e "Instagram", vincula la página y la cuenta profesional de Instagram, activa "Permitir acceso a mensajes" en Instagram, y suscribe `messages` en los webhooks de **Page** e **Instagram** con la misma URL y el mismo `WA_VERIFY_TOKEN`.
- Sofía no tiene el teléfono de estos clientes: lo pide antes de agendar la visita. Si respondes tú a mano desde la página/IG, el bot se calla en ese chat (`/bot` lo reactiva).
- Solo responde mensajes directos, no comentarios públicos. Para clientes reales (no solo administradores/testers de la app) Meta exige revisión de la app (App Review) y negocio verificado.
