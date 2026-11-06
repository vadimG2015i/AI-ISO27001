"""Abstract base provider interface for configurable LLM backends."""

from abc import ABC, abstractmethod
from typing import TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class AbstractLLMProvider(ABC):
    """Abstract contract for LLM backends (OpenAI, Gemini, Anthropic, Ollama, Mock).

    Enforces that all providers remain swappable, optional, and support structured JSON outputs.
    """

    @abstractmethod
    def is_available(self) -> bool:
        """Checks if provider prerequisites (e.g. API keys or local server connectivity) are met."""

    @abstractmethod
    def generate_structured(
        self,
        prompt: str,
        system_instruction: str,
        response_model: type[T],
        temperature: float = 0.1,
    ) -> T:
        """Executes prompt and parses LLM completion into a validated Pydantic model.

        Args:
            prompt: User-level analysis prompt with injected evidence context.
            system_instruction: Guardrailed domain system prompt.
            response_model: Pydantic schema class representing expected output.
            temperature: Sampling temperature (0.0 - 1.0).

        Returns:
            Validated instance of response_model.
        """

