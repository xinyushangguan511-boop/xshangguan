from pydantic_settings import BaseSettings
from functools import lru_cache
import os


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://wanfaliang:870498@localhost:5432/mis_db"

    # JWT
    SECRET_KEY: str = "your-secret-key-change-in-production-minimum-32-characters"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # File Upload
    UPLOAD_DIR: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    ALLOWED_EXTENSIONS: set = {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".png", ".jpg", ".jpeg", ".zip"}

    # CORS
    CORS_ORIGINS: list = ["http://localhost:5173", "http://localhost:3000"]

    # ===== 新增：多板块Excel配置 =====
    # 1. 通用Excel限制（所有板块共用）
    EXCEL_MAX_ROWS: int = 1000  # 单次上传最大行数
    # 2. 各板块Excel规则（key=板块名，value=列映射+sheet名）
    EXCEL_CONFIG: dict = {
        # project板块（优先实现）
        "project": {
            "sheet_name": "sheet1",
            "header_map": {  # Excel列名 → 数据库字段名
            "项目编号": "project_code",
            "项目名称": "project_name",
            "项目描述": "description",
            "建设单位": "construction_unit",
            "项目地点": "location",
            "合同开始日期": "contract_start_date",
            "合同结束日期": "contract_end_date",
            "合同工期": "contract_duration",
            "实际开始日期": "actual_start_date",
            "项目状态": "status"
            }
            
        }
        
    }

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
