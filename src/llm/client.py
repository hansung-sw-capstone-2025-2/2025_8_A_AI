from langchain_anthropic import ChatAnthropic
from functools import lru_cache

from src.core.config import settings


class LLMClientFactory:
    @staticmethod
    @lru_cache(maxsize=10)
    def create(
        model: str = None,
        temperature: float = 0,
        max_tokens: int = 1000,
        cache_enabled: bool = True
    ) -> ChatAnthropic:
        model = model or settings.model_sonnet

        headers = {
            "Helicone-Auth": f"Bearer {settings.helicone_api_key}",
            "Helicone-Property-Member": settings.member_name,
        }

        if cache_enabled:
            headers["Helicone-Cache-Enabled"] = "true"
        else:
            headers["Helicone-Cache-Enabled"] = "false"

        return ChatAnthropic(
            model=model,
            anthropic_api_key=settings.anthropic_api_key,
            base_url="https://anthropic.hconeai.com/",
            temperature=temperature,
            max_tokens=max_tokens,
            default_headers=headers
        )

    @staticmethod
    def create_haiku(temperature: float = 0, max_tokens: int = 1000) -> ChatAnthropic:
        return LLMClientFactory.create(
            model=settings.model_haiku,
            temperature=temperature,
            max_tokens=max_tokens
        )

    @staticmethod
    def create_sonnet(temperature: float = 0, max_tokens: int = 1000) -> ChatAnthropic:
        return LLMClientFactory.create(
            model=settings.model_sonnet,
            temperature=temperature,
            max_tokens=max_tokens
        )
