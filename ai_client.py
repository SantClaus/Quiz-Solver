"""Cliente de la Claude API usando el SDK de anthropic."""

from anthropic import Anthropic

import config


class AIClient:
    def __init__(self) -> None:
        self._client = Anthropic(api_key=config.ANTHROPIC_API_KEY)

    def ask(self, question: str, cancel_event=None) -> str | None:
        """Envía `question` a Claude y devuelve la respuesta como texto.

        Si `cancel_event` queda activado durante/después de la llamada, devuelve
        None para que el caller descarte el resultado.
        """
        response = self._client.messages.create(
            model=config.CLAUDE_MODEL,
            max_tokens=config.MAX_TOKENS,
            system=config.SYSTEM_PROMPT,
            messages=[{"role": "user", "content": question}],
        )

        if cancel_event is not None and cancel_event.is_set():
            return None

        parts = [
            block.text
            for block in response.content
            if getattr(block, "type", None) == "text"
        ]
        return "\n".join(parts).strip()
