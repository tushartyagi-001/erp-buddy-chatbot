from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    LLM_PROVIDER: str = "gemini"
    OPENAI_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    GEMINI_MODEL: str = "gemini-flash-lite-latest"

    DB_SERVER: str = ""
    DB_NAME: str = ""
    DB_USER: str = ""
    DB_PASSWORD: str = ""

    JWT_SECRET: str = ""
    JWT_ISSUER: str = "Admin"
    JWT_AUDIENCE: str = "Admin"

    HOST: str = "127.0.0.1"
    PORT: int = 8010
    CORS_ORIGINS: str = "http://localhost,https://onboarding.erphubspot.com"

    CHAT_DAILY_LIMIT: int = 20
    CHAT_LIMIT_ADMIN_KEY: str = "1sFnWG4HnV8TZY30iTOdtVWJG8abrgnmkilopJuQZdcF2Luqm/hccMw==="
    CHAT_HISTORY_LIMIT: int = 6
    INTENT_ROUTER_ENABLED: bool = True
    RESPONSE_CACHE_TTL_SECONDS: int = 300
    TOOL_GROUPING_ENABLED: bool = True


settings = Settings()
