"""Cliente de la Claude API usando el SDK de anthropic."""

import base64
import io

from anthropic import Anthropic

import config


class AIClient:
    def __init__(self) -> None:
        self._client = Anthropic(api_key=config.ANTHROPIC_API_KEY)

    def ask(self, question: str, cancel_event=None, system=None) -> str | None:
        """Envía `question` (texto) a Claude y devuelve la respuesta.

        `system` permite elegir el system prompt (Ctrl+J usa SYSTEM_PROMPT_2);
        si es None se usa el SYSTEM_PROMPT por defecto.
        """
        return self._complete(question, cancel_event, system=system)

    def ask_image(self, image, cancel_event=None, system=None) -> str | None:
        """Envía una imagen (screenshot) a Claude y devuelve la respuesta.

        `system` permite elegir el system prompt (p. ej. SYSTEM_PROMPT_2 para los
        screenshots con J); si es None se usa el SYSTEM_PROMPT por defecto.
        """
        buffer = io.BytesIO()
        image.convert("RGB").save(buffer, format="PNG")
        data = base64.standard_b64encode(buffer.getvalue()).decode("ascii")
        content = [
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": data,
                },
            }
        ]
        return self._complete(content, cancel_event, system=system)

    def _complete(self, content, cancel_event=None, system=None) -> str | None:
        """Llama a la API con `content` (texto o lista de bloques) y parsea.

        Si `cancel_event` queda activado durante/después de la llamada, devuelve
        None para que el caller descarte el resultado.
        """
        response = self._client.messages.create(
            model=config.CLAUDE_MODEL,
            max_tokens=config.MAX_TOKENS,
            system=system if system is not None else config.SYSTEM_PROMPT,
            messages=[{"role": "user", "content": content}],
        )

        if cancel_event is not None and cancel_event.is_set():
            return None

        parts = [
            block.text
            for block in response.content
            if getattr(block, "type", None) == "text"
        ]
        return "\n".join(parts).strip()
