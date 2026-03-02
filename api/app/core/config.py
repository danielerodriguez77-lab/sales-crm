from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_env: str = "dev"
    database_url: str = "postgresql+psycopg2://crm:crm@db:5432/crm"
    jwt_secret: str = "change_me"
    jwt_refresh_secret: str = "change_me_refresh"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    cors_origins: str = "http://localhost:5173"
    discount_threshold_percent: float = 10.0
    sla_first_contact_hours: int = 2
    stale_opportunity_days: int = 7
    payment_reminder_days_before: int = 3

    class Config:
        env_file = ".env"
        case_sensitive = False

    @property
    def cors_origins_list(self) -> list[str]:
        return [v.strip() for v in self.cors_origins.split(",") if v.strip()]


settings = Settings()
