"""Carga de configuración desde el archivo .env."""

import os

from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "").strip()
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-haiku-4-5-20251001").strip()
SYSTEM_PROMPT = os.getenv(
    "SYSTEM_PROMPT",
    "Respondé de forma concisa y directa. Sin formateo markdown innecesario.",
).strip()

# Prompt alternativo para los screenshots con la tecla J sostenida
# (ImprPant+J / Win+Shift+S+J). Si no está definido, cae en SYSTEM_PROMPT.
SYSTEM_PROMPT_2 = os.getenv("SYSTEM_PROMPT_2", "").strip() or SYSTEM_PROMPT

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
