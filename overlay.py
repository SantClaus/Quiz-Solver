"""Cuadradito flotante junto al cursor con la última respuesta (Ctrl+9).

Mientras se mantiene Ctrl+9, aparece una ventanita chiquita, sin bordes y
siempre-on-top, pegada al cursor, mostrando la última respuesta de Claude. Al
soltar, se oculta. Es solo para leer "de reojo": la respuesta también queda en
el clipboard para pegar con Ctrl+V.

En **Windows** corre Tkinter en su **propio thread** (`start()`), porque el thread
principal lo ocupa el loop del system tray (pystray). En **macOS** Cocoa exige que
Tkinter viva en el thread principal, así que ahí se arranca con `run_main()` (y el
tray va "detached"). En ambos casos el Tk queda confinado a un único thread: nadie
más lo toca, solo se leen dos callbacks (`should_show` / `get_text`).
"""

import threading
import tkinter as tk

# Cada cuánto revisa si hay que mostrar/ocultar y reubicar el cuadradito.
_POLL_MS = 30
# Desplazamiento desde el cursor para no taparlo.
_OFFSET = 16
# Tope de caracteres para que el cuadradito siga siendo chiquito.
_MAX_CHARS = 800


class Overlay:
    def __init__(self, should_show, get_text) -> None:
        self._should_show = should_show
        self._get_text = get_text
        self._root: "tk.Tk | None" = None
        self._label: "tk.Label | None" = None
        self._visible = False
        self._last_text: "str | None" = None

    def start(self) -> None:
        """Arranca el overlay en su PROPIO thread (Windows)."""
        threading.Thread(target=self._run, daemon=True).start()

    def run_main(self) -> None:
        """Arranca el overlay en el thread ACTUAL y bloquea (macOS: Tkinter debe
        correr en el thread principal)."""
        self._run()

    def _run(self) -> None:
        self._root = tk.Tk()
        self._root.withdraw()
        self._root.overrideredirect(True)
        self._root.attributes("-topmost", True)
        try:
            self._root.attributes("-alpha", 0.92)
        except tk.TclError:
            pass

        frame = tk.Frame(
            self._root,
            bg="#1e1e1e",
            padx=8,
            pady=6,
            highlightbackground="#555",
            highlightthickness=1,
        )
        frame.pack()
        self._label = tk.Label(
            frame,
            text="",
            justify="left",
            anchor="nw",
            bg="#1e1e1e",
            fg="#eaeaea",
            font=("Segoe UI", 9),
            wraplength=320,
        )
        self._label.pack()

        self._tick()
        self._root.mainloop()

    def _tick(self) -> None:
        try:
            self._update()
        finally:
            if self._root is not None:
                self._root.after(_POLL_MS, self._tick)

    def _update(self) -> None:
        text = self._get_text() if self._should_show() else None
        if not text:
            if self._visible:
                self._root.withdraw()
                self._visible = False
            return

        if text != self._last_text:
            self._label.config(text=text[:_MAX_CHARS])
            self._last_text = text
        # Sigue al cursor: posición del puntero en coordenadas de pantalla.
        x, y = self._root.winfo_pointerxy()
        self._root.geometry(f"+{x + _OFFSET}+{y + _OFFSET}")
        if not self._visible:
            self._root.deiconify()
            self._visible = True

    def stop(self) -> None:
        if self._root is not None:
            try:
                self._root.after(0, self._root.quit)
            except Exception:
                pass
