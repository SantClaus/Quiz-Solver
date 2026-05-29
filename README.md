# Quiz-Solver — AI Clipboard Assistant

Script de Python que corre en background (Windows) y permite consultar a Claude
con hotkeys globales, con un ícono en el system tray para feedback visual.

- `Ctrl+Shift+C` → copia el texto seleccionado y lo envía a Claude
- `Ctrl+Shift+V` → pega la respuesta de Claude
- Ícono en el tray: muestra el estado y permite activar/desactivar los hotkeys

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
