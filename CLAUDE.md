# AI Clipboard Assistant

Script de Python que corre en background (Windows y macOS) y permite consultar a Claude AI con hotkeys globales, con un ícono en el system tray para feedback visual y control de activación.

## Plataformas

El modificador primario es **Ctrl en Windows/Linux** y **Cmd (⌘) en macOS**
(`config.PRIMARY_MOD`). Las funciones cross-platform son **solo `Ctrl/Cmd+0`**
(captura full) y **`Ctrl/Cmd+9`** (overlay). Los atajos de texto (`Ctrl+C/J/V`),
Print Screen y `Win+Shift+S` son **solo de Windows** (en Mac chocarían con el
copiar/pegar nativo `Cmd+C/V` y no hay tecla ImprPant). El soporte de macOS está
implementado pero **no testeado** (se desarrolló en Windows).

## Idea central

- `Ctrl+C` *(Windows)* → el usuario copia normal; se lee el texto copiado y se envía a Claude API en background
- `Ctrl+J` *(Windows)* → como Ctrl+C pero con `SYSTEM_PROMPT_2`; como Ctrl+J no copia solo, simulamos un Ctrl+C (con un flag que evita que ese Ctrl+C re-dispare el hotkey de captura)
- `ImprPant` (Print Screen) *(Windows)* → el SO deja el screenshot en el clipboard; lo leemos con `PIL.ImageGrab` y lo enviamos a Claude como imagen (mismo `SYSTEM_PROMPT`). Print Screen en Windows manda solo el evento de *release*, así que se detecta en el `on_release` del listener de tracking, no por `GlobalHotKeys`
- `Win+Shift+S` *(Windows)* → recorte de selección; esperamos (hasta 15s) a que aparezca una imagen *nueva* en el clipboard y la enviamos igual que el screenshot
- `ImprPant+J` / `Win+Shift+S+J` *(Windows)* → mismo screenshot pero con `SYSTEM_PROMPT_2` (la J sostenida la detecta un listener aparte; no es un hotkey propio)
- **`Ctrl/Cmd+0`** *(Win + Mac)* → captura toda la pantalla con `PIL.ImageGrab.grab` directo a memoria y la envía como imagen con `SCREEN_PROMPT` (en Windows usa `all_screens=True`; en Mac, `grab()` pelado). No usa el clipboard ni dispara notificación: es totalmente silencioso. Es un hotkey propio de `GlobalHotKeys`
- `Ctrl+V` *(Windows)* → al tener respuesta lista la dejamos en el clipboard, así el `Ctrl+V` normal del usuario la pega
- **`Ctrl/Cmd+9`** *(Win + Mac, sostenido)* → mientras se mantiene se muestra un cuadradito chiquito pegado al cursor con la última respuesta; al soltar se oculta. El estado "modificador+9 sostenido" lo detecta el listener de tracking (no es un hotkey propio) y el overlay (Tkinter) lo consulta por polling
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

### Ctrl/Cmd+0 (capturar toda la pantalla, silencioso) — Win + Mac
1. `clipboard.grab_screen()` hace `ImageGrab.grab()` (con `all_screens=True` en Windows) → imagen en memoria, sin tocar el clipboard ni notificar
2. Se manda a Claude como imagen por el mismo `_ask` que los screenshots (estados de ícono iguales), siempre con `SCREEN_PROMPT`
3. `SCREEN_PROMPT` pide responder en formato `1A 2B 3C` cuando hay más de una pregunta

### Ctrl/Cmd+9 (ver la respuesta en un overlay) — Win + Mac
1. Mientras el modificador primario + 9 estén sostenidos, `Hotkeys.overlay_held()` devuelve True (lo sabe por el tracking de teclas). Ojo: el vk de `9` no es portable — Windows usa `0x39`, macOS usa el keycode de Carbon `kVK_ANSI_9` (25)
2. `overlay.py` corre Tkinter por polling y muestra/oculta un `Toplevel` sin bordes, on-top, pegado al cursor, con `self._last_answer`. En Windows el Tk vive en su propio thread (`start()`) porque el principal lo ocupa pystray; en macOS Cocoa exige el thread principal, así que el overlay usa `run_main()` y el tray va `run_detached()`
3. Solo muestra la **última** respuesta; al soltar se oculta. La respuesta sigue disponible para pegar (queda en el clipboard)

### Ctrl+V (pegar respuesta)
1. La respuesta ya quedó en el clipboard al recibirla, así que el `Ctrl+V` nativo del usuario la pega solo (no lo simulamos)
2. El callback solo limpia la respuesta guardada de memoria y vuelve el ícono a "active"

### Toggle activar/desactivar (desde tray)
- Click derecho en el ícono → menú con **un toggle por grupo de hotkeys**:
  - **Captura** (`Ctrl/Cmd+0`, `Ctrl/Cmd+9`) — cross-platform
  - **Texto** (`Ctrl+C` / `J` / `V`) — solo Windows
  - **Recorte** (`Win+Shift+S`, `ImprPant`) — solo Windows
- Cada toggle prende/apaga solo su grupo (estado independiente en `self._enabled`,
  un dict por grupo). En macOS solo aparece el grupo **Captura**.
- **Por default solo arranca activo el grupo Captura** (`Ctrl/Cmd+0`, `Ctrl/Cmd+9`);
  Texto y Recorte arrancan apagados y se prenden desde el menú cuando se necesiten.
- Al apagar un grupo se cancela cualquier consulta en curso.
- El ícono refleja el estado **global**: gris solo si **todos** los grupos están
  apagados; si queda al menos uno activo, sigue verde.

## Comportamiento del ícono tray

- El ícono debe ser **pequeño y simple** (16x16 o 32x32 px)
- Tooltip con el estado actual al hover
- Click derecho → menú con:
  - "✓/✗ Captura (Ctrl/Cmd+0, Ctrl/Cmd+9)" (toggle del grupo de captura)
  - "✓/✗ Texto (Ctrl+C / J / V)" (toggle del grupo de texto, solo Windows)
  - "✓/✗ Recorte (Win+Shift+S, ImprPant)" (toggle del grupo de recorte, solo Windows)
  - Separador
  - "Salir"
- La transición a "ready" debe ser **sutil**: cambia el ícono 2-3 segundos y vuelve, sin sonido ni notificación

## Configuración (.env)

```
ANTHROPIC_API_KEY=sk-ant-...
CLAUDE_MODEL=claude-haiku-4-5-20251001
SYSTEM_PROMPT=Respondé de forma concisa y directa. Sin formateo markdown innecesario.
SCREEN_PROMPT=Resolvé lo que aparece en la captura... Si hay más de una pregunta, respondé en formato '1A 2B 3C'.
```

`SCREEN_PROMPT` es el prompt de la captura `Ctrl/Cmd+0`; si no está en el `.env`
usa un default que ya pide el formato `1A 2B 3C` para múltiples preguntas.

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
- En macOS hace falta permiso de **Accesibilidad** (teclado global) y **Grabación de pantalla** (captura de `Cmd+0`) en Configuración del Sistema → Privacidad y seguridad
- Tkinter (el overlay) y pystray (el tray) se pelean por el thread principal: en macOS Cocoa **exige Tkinter en el principal**, por eso el tray va `run_detached()` y el overlay `run_main()`; en Windows es al revés (tray bloquea, overlay en su thread)
- Los íconos se pueden generar programáticamente con Pillow si no se tienen imágenes (círculos de colores simples)
- El script debe arrancar minimizado al tray, sin ventana

## Cómo correr

```bash
pip install -r requirements.txt
cp .env.example .env
# Editar .env con tu ANTHROPIC_API_KEY
python main.py
```
