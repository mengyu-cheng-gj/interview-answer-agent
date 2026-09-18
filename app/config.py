from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8-sig",
        extra="ignore",
    )

    # 模型配置：保留前面使用的变量名称
    LLM_MODEL: str = ""
    LLM_BASE_URL: str = ""
    LLM_API_KEY: SecretStr = SecretStr("")

    # Redis 缓存
    CACHE_ENABLED: bool = False
    REDIS_URL: str = "redis://localhost:6379/0"

    CACHE_TTL_SECONDS: int = Field(
        default=3600,
        ge=1,
    )

    # 修改亮点提示词或输出结构后，更新版本，使旧缓存失效
    HIGHLIGHT_CACHE_VERSION: str = "v1"

    def require_llm_config(self) -> None:
        """创建模型客户端前检查配置。"""
        missing = []

        if not self.LLM_MODEL.strip():
            missing.append("LLM_MODEL")

        if not self.LLM_BASE_URL.strip():
            missing.append("LLM_BASE_URL")

        if not self.LLM_API_KEY.get_secret_value().strip():
            missing.append("LLM_API_KEY")

        if missing:
            raise ValueError(
                "请在项目根目录 .env 或环境变量中配置："
                + "、".join(missing)
            )


settings = Settings()