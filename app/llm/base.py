from abc import ABC, abstractmethod


class LLMClient(ABC):
    """Abstract LLM client interface used by services."""

    @abstractmethod
    def complete(self, system_prompt: str, user_prompt: str) -> str:
        """Return a completion as plain text."""
        raise NotImplementedError
