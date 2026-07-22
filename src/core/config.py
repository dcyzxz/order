from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import ClassVar


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "点菜小程序"
    app_version: str = "0.1.0"
    debug: bool = True
    api_prefix: str = "/api/v1"

    # Database (MySQL for WeChat Cloud Hosting)
    database_url: str = "mysql+asyncmy://root:password@localhost:3306/order_miniapp?charset=utf8mb4"
    database_url_sync: str = "mysql+pymysql://root:password@localhost:3306/order_miniapp?charset=utf8mb4"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # JWT
    jwt_secret_key: str = "change-this-secret-key-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 72

    # Logging
    log_level: str = "INFO"
    log_format: str = "json"

    # Admin
    admin_username: str = "admin"
    admin_password: str = "admin123456"

    # Server
    port: int = 8000  # 服务端口，微信云托管通过 PORT 环境变量注入

    # Pagination
    default_page_size: int = 20
    max_page_size: int = 100

    # Async database session config
    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_echo: bool = False


settings = Settings()
