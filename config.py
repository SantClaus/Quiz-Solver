"""Carga de configuración desde el archivo .env."""

import os
import sys

from dotenv import load_dotenv

load_dotenv()

# --- Plataforma ---------------------------------------------------------
# En macOS el modificador primario es Cmd (⌘); en Windows/Linux es Ctrl. Los
# hotkeys (Ctrl/Cmd + 0 y + 9) se arman con PRIMARY_MOD según el SO.
IS_MAC = sys.platform == "darwin"
PRIMARY_MOD = "<cmd>" if IS_MAC else "<ctrl>"

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "").strip()
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-haiku-4-5-20251001").strip()
SYSTEM_PROMPT = os.getenv(
    "SYSTEM_PROMPT",
    "Respondé de forma concisa y directa. Sin formateo markdown innecesario.",
).strip()

# Prompt alternativo para los screenshots con la tecla J sostenida
# (ImprPant+J / Win+Shift+S+J). Si no está definido, cae en SYSTEM_PROMPT.
SYSTEM_PROMPT_2 = os.getenv("SYSTEM_PROMPT_2", "").strip() or SYSTEM_PROMPT

# Prompt de la captura de pantalla completa (Ctrl/Cmd+0). Pensado para resolver
# lo que aparezca en pantalla; si hay varias preguntas, exige el formato '1A 2B'.
SCREEN_PROMPT = os.getenv(
    "SCREEN_PROMPT",
    "Resolvé lo que aparece en la captura de pantalla. Respondé de forma concisa "
    "y directa, sin markdown ni explicaciones salvo que se pidan. Si hay más de "
    "una pregunta, respondé únicamente con el número de cada una seguido de la "
    "letra de la opción correcta, en el formato '1A 2B 3C', separados por espacios.",
).strip()

try:
    MAX_TOKENS = int(os.getenv("MAX_TOKENS", "1024"))
except ValueError:
    MAX_TOKENS = 1024


def validate() -> None:
    """Falla temprano si falta configuración indispensable."""
    if not ANTHROPIC_API_KEY or ANTHROPIC_API_KEY.startswith("sk-ant-..."):
        raise RuntimeError(
            "Falta ANTHROPIC_API_KEY. Copiá .env.example a .env y completá tu API key real."
        )
