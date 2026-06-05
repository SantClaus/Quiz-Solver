# AI Clipboard Assistant

Script de Python que corre en background (Windows) y permite consultar a Claude AI con hotkeys globales, con un ícono en el system tray para feedback visual y control de activación.

## Idea central

- `Ctrl+C` → el usuario copia normal; se lee el texto copiado y se envía a Claude API en background
- `Ctrl+J` → como Ctrl+C pero con `SYSTEM_PROMPT_2`; como Ctrl+J no copia solo, simulamos un Ctrl+C (con un flag que evita que ese Ctrl+C re-dispare el hotkey de captura)
- `ImprPant` (Print Screen) → el SO deja el screenshot en el clipboard; lo leemos con `PIL.ImageGrab` y lo enviamos a Claude como imagen (mismo `SYSTEM_PROMPT`). Print Screen en Windows manda solo el evento de *release*, así que se detecta en el `on_release` del listener de tracking, no por `GlobalHotKeys`
- `Win+Shift+S` → recorte de selección; esperamos (hasta 15s) a que aparezca una imagen *nueva* en el clipboard y la enviamos igual que el screenshot
- `Ctrl+0` → captura toda la pantalla con `PIL.ImageGrab.grab(all_screens=True)` directo a memoria y la envía como imagen (mismo `SYSTEM_PROMPT`). No usa el clipboard ni dispara notificación: es totalmente silencioso. Es un hotkey propio de `GlobalHotKeys`
- `ImprPant+J` / `Win+Shift+S+J` / `Ctrl+0+J` → mismo screenshot pero con `SYSTEM_PROMPT_2` (la J sostenida la detecta un listener aparte; no es un hotkey propio)
- `Ctrl+V` → al tener respuesta lista la dejamos en el clipboard, así el `Ctrl+V` normal del usuario la pega
- `Ctrl+9` (sostenido) → mientras se mantiene Ctrl+9 se muestra un cuadradito chiquito pegado al cursor con la última respuesta; al soltar se oculta. El estado "Ctrl+9 sostenido" lo detecta el listener de tracking (no es un hotkey propio) y el overlay (Tkinter en su propio thread) lo consulta por polling
- Ícono en tray muestra el estado del sistema y permite activar/desactivar los hotkeys

> **Importante:** `Ctrl+C` / `Ctrl+V` se registran con `GlobalHotKeys` de pynput,
> que es un listener **pasivo** (no suprime el evento). El copiar/pegar nativo del
> SO se ejecuta igual; nosotros solo nos enteramos. Por eso **no** se debe volver a
> simular `Ctrl+C` ni `Ctrl+V` desde los callbacks: re-dispararía el mismo hotkey y
> entraría en loop infinito.

## Archivos del proyecto

```
ai-clipboard/
├── main.py           # Entry point, arranca el tray y el listener de hotkeys
├── hotkeys.py        # Registro y manejo de hotkeys globales con pynput
├── tray.py           # Ícono en system tray con pystray
├── overlay.py        # Cuadradito flotante junto al cursor (Ctrl+9) con Tkinter
├── ai_client.py      # Llamada a Claude API con anthropic SDK
├── clipboard.py      # Lectura/escritura del clipboard y captura de pantalla
├── config.py         # Carga de configuración desde .env
├── icons/            # Imágenes del ícono en distintos estados
│   ├── active.png    # Verde o ícono normal - hotkeys activos
│   ├── inactive.png  # Gris - hotkeys desactivados
│   ├── loading.png   # Animado o distinto - esperando respuesta de API
│   └── ready.png     # Check o destello - respuesta lista para pegar
├── .env              # ANTHROPIC_API_KEY (no commitear)
├── .env.example      # Ejemplo sin valores reales
└── requirements.txt
```

## Estados del sistema

| Estado | Ícono tray | Hotkeys activos |
|--------|-----------|-----------------|
| Activo (idle) | Verde / normal | Sí |
| Procesando | Distinto (loading) | Sí (nuevo Ctrl+C cancela el anterior) |
| Respuesta lista | Cambia brevemente | Sí |
| Desactivado | Gris | No |

## Flujo detallado

### Ctrl+C (capturar pregunta)
1. El `Ctrl+C` nativo del usuario ya copió el texto seleccionado (no lo simulamos)
2. Leer el clipboard (con un pequeño delay para que el SO termine de copiar)
3. Si hay texto nuevo: enviarlo a Claude API de forma **asíncrona** (no bloquear)
4. Cambiar ícono tray a "loading"
5. Al recibir respuesta: guardarla en memoria, **dejarla en el clipboard**, cambiar ícono a "ready" brevemente (2-3 seg), luego volver a "active"

### Ctrl+0 (capturar toda la pantalla, silencioso)
1. `clipboard.grab_screen()` hace `ImageGrab.grab(all_screens=True)` → imagen en memoria, sin tocar el clipboard ni notificar
2. Se manda a Claude como imagen por el mismo `_ask` que los screenshots (estados de ícono iguales)
3. Con `J` sostenida usa `SYSTEM_PROMPT_2`

### Ctrl+9 (ver la respuesta en un overlay)
1. Mientras `Ctrl+9` están sostenidos, `Hotkeys.overlay_held()` devuelve True (lo sabe por el tracking de teclas)
2. `overlay.py` corre Tkinter en su propio thread (el principal lo ocupa pystray) y por polling muestra/oculta un `Toplevel` sin bordes, on-top, pegado al cursor, con `self._last_answer`
3. Solo muestra la **última** respuesta; al soltar Ctrl+9 se oculta. La respuesta sigue disponible para pegar con Ctrl+V

### Ctrl+V (pegar respuesta)
1. La respuesta ya quedó en el clipboard al recibirla, así que el `Ctrl+V` nativo del usuario la pega solo (no lo simulamos)
2. El callback solo limpia la respuesta guardada de memoria y vuelve el ícono a "active"

### Toggle activar/desactivar (desde tray)
- Click derecho en el ícono → menú con opción "Activar/Desactivar hotkeys"
- Al desactivar: ícono cambia a gris, hotkeys dejan de responder
- Al activar: vuelve al estado normal

## Comportamiento del ícono tray

- El ícono debe ser **pequeño y simple** (16x16 o 32x32 px)
- Tooltip con el estado actual al hover
- Click derecho → menú con:
  - "✓ Hotkeys activos" / "✗ Hotkeys desactivados" (toggle)
  - Separador
  - "Salir"
- La transición a "ready" debe ser **sutil**: cambia el ícono 2-3 segundos y vuelve, sin sonido ni notificación

## Configuración (.env)

```
ANTHROPIC_API_KEY=sk-ant-...
CLAUDE_MODEL=claude-haiku-4-5-20251001
SYSTEM_PROMPT=Respondé de forma concisa y directa. Sin formateo markdown innecesario.
```

## Stack y dependencias

```txt
anthropic          # Claude API client
pynput             # Hotkeys globales (cross-platform)
pystray            # System tray icon (Windows)
Pillow             # Manipulación de íconos/imágenes
pyperclip          # Clipboard read/write
python-dotenv      # Carga de .env
```

## Notas de implementación

- La llamada a la API debe correr en un **thread separado** para no bloquear los hotkeys
- Si se presiona `Ctrl+C` mientras hay una llamada en curso, cancelar la anterior e iniciar una nueva
- Usar `threading.Event` o similar para coordinar estados
- En Windows, `pynput` necesita permisos para escuchar hotkeys globales — documentar esto
- Los íconos se pueden generar programáticamente con Pillow si no se tienen imágenes (círculos de colores simples)
- El script debe arrancar minimizado al tray, sin ventana

## Cómo correr

```bash
pip install -r requirements.txt
cp .env.example .env
# Editar .env con tu ANTHROPIC_API_KEY
python main.py
```
