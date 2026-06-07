# Quiz-Solver — AI Clipboard Assistant

Script de Python que corre en background (Windows) y permite consultar a Claude
con hotkeys globales, con un ícono en el system tray para feedback visual.

- `Ctrl+C` → copia el texto seleccionado (copia normal) y lo envía a Claude
- `Ctrl+J` → igual que Ctrl+C pero usa el prompt alternativo `SYSTEM_PROMPT_2`
- `ImprPant` (Print Screen) → manda el screenshot del clipboard a Claude como imagen
- `Win+Shift+S` → recortás una zona y se manda ese recorte a Claude como imagen
- `Ctrl+0` (`Cmd+0` en Mac) → captura **toda la pantalla** a memoria y la manda a Claude, sin notificación ni flash ni tocar el clipboard (silencioso). Si en pantalla hay más de una pregunta, Claude responde en formato `1A 2B 3C`
- Sostené **`J`** mientras sacás el screenshot (`ImprPant+J` / `Win+Shift+S+J`) para usar el prompt alternativo `SYSTEM_PROMPT_2` del `.env`
- `Ctrl+V` → pega la respuesta de Claude (queda en el clipboard, así que pega normal)
- `Ctrl+9` (`Cmd+9` en Mac, mantener) → muestra un cuadradito chiquito pegado al cursor con la última respuesta; al soltar, desaparece
- Ícono en el tray: muestra el estado y permite activar/desactivar los hotkeys
  por grupo — **Captura** (`Ctrl/Cmd+0`, `Ctrl/Cmd+9`), **Texto** (`Ctrl+C/J/V`)
  y **Recorte** (`Win+Shift+S`, `ImprPant`) — cada uno con su propio toggle

> **Windows vs. macOS:** los atajos de texto (`Ctrl+C`/`J`/`V`), Print Screen y
> `Win+Shift+S` son **solo de Windows**. En macOS funcionan únicamente
> **`Cmd+0`** (captura) y **`Cmd+9`** (overlay), que es lo más útil. El soporte de
> macOS está implementado pero **no testeado** (se desarrolló en Windows).

> Mientras los hotkeys están activos, `Ctrl+C` / `Ctrl+V` quedan "intervenidos":
> copiás como siempre pero se consulta a Claude, y al pegar sale su respuesta.
> Para copiar/pegar normal, desactivá los hotkeys desde el tray.

## Cómo correr

```bash
pip install -r requirements.txt
copy .env.example .env   # en bash/macOS: cp .env.example .env
# Editá .env con tu ANTHROPIC_API_KEY
python main.py
```

El script arranca minimizado en el system tray (sin ventana). Click derecho en
el ícono → menú con un toggle por grupo de hotkeys (Captura / Texto / Recorte) y
la opción de salir. El ícono queda gris solo si apagás todos los grupos.

| Estado | Ícono | Significado |
|--------|-------|-------------|
| Activo | Verde | Hotkeys activos, idle |
| Procesando | Amarillo | Esperando respuesta de la API |
| Listo | Azul (check) | Respuesta lista para pegar (~2.5s) |
| Desactivado | Gris | Hotkeys desactivados |

> **Permisos en Windows:** `pynput` necesita escuchar el teclado de forma
> global. Si los hotkeys no responden, ejecutá la terminal/script como
> administrador.

> **Permisos en macOS:** hay que dar permiso a la app/terminal en
> *Configuración del Sistema → Privacidad y seguridad* en **Accesibilidad**
> (para escuchar el teclado global) y en **Grabación de pantalla** (para la
> captura de `Cmd+0`). Sin esos permisos los hotkeys no disparan y la captura
> sale en negro.

Ver [`CLAUDE.md`](CLAUDE.md) para la especificación completa.
