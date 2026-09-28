from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_openai import ChatOpenAI
from pydantic import Field, SecretStr

from app.core.config import settings


class MockChatModel(BaseChatModel):
    """Deterministic mock LLM for offline testing and CI workflows."""

    response_content: str = Field(
        default="Adaptive guidance generated from grounded pathway state."
    )
    tool_calls_sequence: list[list[dict]] = Field(default_factory=list)
    call_count: int = Field(default=0)

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> ChatResult:
        tool_calls = []
        if self.call_count < len(self.tool_calls_sequence):
            tool_calls = self.tool_calls_sequence[self.call_count]
            self.call_count += 1
            ai_msg = AIMessage(content="", tool_calls=tool_calls)
        else:
            ai_msg = AIMessage(content=self.response_content)

        return ChatResult(generations=[ChatGeneration(message=ai_msg)])

    def bind_tools(self, tools: Any, **kwargs: Any) -> Any:
        return self

    @property
    def _llm_type(self) -> str:
        return "mock-chat-model"


def get_llm(
    provider: str | None = None,
    model: str | None = None,
    temperature: float | None = None,
    mock_tool_calls: list[list[dict]] | None = None,
    mock_response: str | None = None,
) -> BaseChatModel:
    """Instantiate and return the configured BaseChatModel."""
    selected_provider = (provider or settings.llm_provider).lower()
    temp = temperature if temperature is not None else settings.temperature

    if selected_provider == "mock":
        return MockChatModel(
            response_content=mock_response or "Grounded educational feedback.",
            tool_calls_sequence=mock_tool_calls or [],
        )

    if selected_provider in {"huggingface", "hf", "hugging_face"}:
        api_key = settings.huggingface_api_key or "hf_dummy_for_testing"
        return ChatOpenAI(
            base_url=settings.huggingface_base_url,
            api_key=SecretStr(api_key),
            model=model or settings.huggingface_model,
            temperature=temp,
            timeout=settings.request_timeout,
            max_tokens=settings.max_tokens,
        )

    if selected_provider == "groq":
        api_key = settings.groq_api_key or "gsk_dummy_for_testing"
        return ChatOpenAI(
            base_url=settings.groq_base_url,
            api_key=SecretStr(api_key),
            model=model or settings.groq_model,
            temperature=temp,
            timeout=settings.request_timeout,
        )

    # Default to openrouter
    api_key = settings.openrouter_api_key or "sk-or-dummy_for_testing"
    return ChatOpenAI(
        base_url=settings.openrouter_base_url,
        api_key=SecretStr(api_key),
        model=model or settings.default_model,
        temperature=temp,
        timeout=settings.request_timeout,
    )
