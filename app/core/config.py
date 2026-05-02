from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')

    app_env: str = 'development'
    log_level: str = 'INFO'
    webhook_secret: str = 'change-me'

    github_app_id: str | None = None
    github_private_key_path: str | None = None
    github_installation_id: str | None = None
    github_token: str | None = None

    openai_api_key: str | None = None
    openai_model: str = 'gpt-4.1-mini'

    max_file_bytes: int = 200000
    max_files_per_pr: int = 25
    doc_targets: str = 'README.md,docs/API.md,docs/USAGE.md'

    @property
    def doc_target_list(self) -> list[str]:
        return [x.strip() for x in self.doc_targets.split(',') if x.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
