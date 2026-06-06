from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "OKX Spot Accumulation Scanner"
    database_url: str = "sqlite:///./scanner.db"
    okx_base_url: str = "https://www.okx.com"
    scan_interval_minutes: int = 360
    candle_bar: str = "1D"
    candle_limit: int = 120
    min_quote_volume_usdt: float = 300_000
    max_spread_pct: float = 0.35
    recent_pump_lookback_days: int = 7
    max_recent_pump_pct: float = 35
    min_accumulation_score: float = 70
    top_candidates_limit: int = 10

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
