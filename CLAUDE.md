# AI Clipboard Assistant

Script de Python que corre en background (Windows) y permite consultar a Claude AI con hotkeys globales, con un ícono en el system tray para feedback visual y control de activación.

## Idea central

- `Ctrl+Shift+C` → copia el texto seleccionado y lo envía a Claude API en background
- `Ctrl+Shift+V` → pega la respuesta de Claude (reemplaza el clipboard y el usuario puede hacer Ctrl+V normal)
- Ícono en tray muestra el estado del sistema y permite activar/desactivar los hotkeys

## Archivos del proyecto

```
ai-clipboard/
├── main.py           # Entry point, arranca el tray y el listener de hotkeys
├── hotkeys.py        # Registro y manejo de hotkeys globales con pynput
├── tray.py           # Ícono en system tray con pystray
├── ai_client.py      # Llamada a Claude API con anthropic SDK
├── clipboard.py      # Lectura y escritura del clipboard con pyperclip
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
| Procesando | Distinto (loading) | Sí (nuevo Ctrl+Shift+C cancela el anterior) |
| Respuesta lista | Cambia brevemente | Sí |
| Desactivado | Gris | No |

## Flujo detallado

### Ctrl+Shift+C (capturar pregunta)
1. Simular `Ctrl+C` para copiar el texto seleccionado
2. Leer el clipboard
3. Si hay texto: enviarlo a Claude API de forma **asíncrona** (no bloquear)
4. Cambiar ícono tray a "loading"
5. Al recibir respuesta: guardarla en memoria, cambiar ícono a "ready" brevemente (2-3 seg), luego volver a "active"

### Ctrl+Shift+V (pegar respuesta)
1. Si hay respuesta guardada: escribirla en el clipboard
2. Simular `Ctrl+V` para pegar automáticamente
3. Limpiar la respuesta guardada de memoria

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
- Si se presiona `Ctrl+Shift+C` mientras hay una llamada en curso, cancelar la anterior e iniciar una nueva
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
