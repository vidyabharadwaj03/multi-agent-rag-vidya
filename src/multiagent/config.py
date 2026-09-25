from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.6-flash"
    gemini_base_url: str = "https://generativelanguage.googleapis.com/v1beta/openai/"
    chroma_persist_dir: str = "chroma_store"
    sql_database_path: str = "data/enterprise.db"
    docs_dir: str = "data/docs"
    relevance_threshold: float = 0.3


def get_settings():
    return Settings()
