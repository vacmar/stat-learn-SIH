from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "manthaino AI Service"
    port: int = 8001
    environment: str = "development"

    # LLM Provider selection: "huggingface", "openrouter", "groq", or "mock"
    llm_provider: str = "mock"

    # Hugging Face (OpenAI-compatible Inference Providers router)
    huggingface_api_key: str | None = None
    huggingface_base_url: str = "https://router.huggingface.co/v1"
    huggingface_model: str = "meta-llama/Llama-3.1-8B-Instruct"

    # OpenRouter configurations
    openrouter_api_key: str | None = None
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    default_model: str = "meta-llama/llama-3.3-70b-instruct:free"

    # Groq configurations
    groq_api_key: str | None = None
    groq_base_url: str = "https://api.groq.com/openai/v1"
    groq_model: str = "llama-3.3-70b-versatile"

    # Backend Core API
    backend_api_url: str = "http://localhost:8000"

    # Inference settings
    temperature: float = 0.2
    max_tokens: int = 2048
    request_timeout: float = 90.0

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


settings = Settings()
