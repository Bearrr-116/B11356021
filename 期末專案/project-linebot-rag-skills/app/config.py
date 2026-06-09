from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_env: str = "development"
    app_name: str = "project-linebot-rag-skills"
    app_port: int = 8000

    line_channel_secret: str = ""
    line_channel_access_token: str = ""
    line_api_base: str = "https://api.line.me"

    ai_provider: str = "gemini"
    embedding_provider: str = "gemini"

    router_model: str = "gemini-2.5-flash"
    generator_model: str = "gemini-2.5-pro"
    embedding_model: str = "gemini-embedding-2"

    openai_api_key: str = ""

    supabase_url: str = ""
    supabase_service_role_key: str = ""

    knowledge_top_k: int = 8
    final_context_k: int = 4
    line_max_message_chars: int = 4500
    skills_dir: str = "skills"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()