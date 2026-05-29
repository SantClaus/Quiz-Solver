# Quiz-Solver — AI Clipboard Assistant

Script de Python que corre en background (Windows) y permite consultar a Claude
con hotkeys globales, con un ícono en el system tray para feedback visual.

- `Ctrl+C` → copia el texto seleccionado (copia normal) y lo envía a Claude
- `Ctrl+J` → igual que Ctrl+C pero usa el prompt alternativo `SYSTEM_PROMPT_2`
- `ImprPant` (Print Screen) → manda el screenshot del clipboard a Claude como imagen
- `Win+Shift+S` → recortás una zona y se manda ese recorte a Claude como imagen
- Sostené **`J`** mientras sacás el screenshot (`ImprPant+J` / `Win+Shift+S+J`) para usar el prompt alternativo `SYSTEM_PROMPT_2` del `.env`
- `Ctrl+V` → pega la respuesta de Claude (queda en el clipboard, así que pega normal)
- Ícono en el tray: muestra el estado y permite activar/desactivar los hotkeys

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
el ícono → menú con el toggle de hotkeys y la opción de salir.

| Estado | Ícono | Significado |
|--------|-------|-------------|
| Activo | Verde | Hotkeys activos, idle |
| Procesando | Amarillo | Esperando respuesta de la API |
| Listo | Azul (check) | Respuesta lista para pegar (~2.5s) |
| Desactivado | Gris | Hotkeys desactivados |

> **Permisos en Windows:** `pynput` necesita escuchar el teclado de forma
> global. Si los hotkeys no responden, ejecutá la terminal/script como
> administrador.

Ver [`CLAUDE.md`](CLAUDE.md) para la especificación completa.
