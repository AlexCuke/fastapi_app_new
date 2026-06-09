from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # API внешний
    BASE_URL: str = "http://procedure-dev.m15.dzm"
    REQUEST_TIMEOUT: int = 10

    # Elasticsearch
    ES_HOST: str = "http://elastic-dev.m15.dzm:80/"
    INDEX_NAME: str = "default_procedure-patients-list"
    SCROLL_SIZE: int = 1000
    REQUEST_TIMEOUT_ES: int = 60
    OUTPUT_JSONL: str = "export.jsonl"
    OUTPUT_CSV: str = "output_PA.csv"

    # PostgreSQL основная БД
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "mydb"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "sa"

    # PostgreSQL вторая БД (больничная)
    DB2_HOST: str = "10.115.6.99"
    DB2_PORT: int = 5432
    DB2_NAME: str = "hospital_dev"
    DB2_USER: str = "SOFTMASTER"
    DB2_PASSWORD: str = "syS3Okan"

    # Tenant и User для заголовков запросов
    TENANT_ID: str = "14932313369"
    USER_ID: str = "1"

    # Имена в таблице config_headers
    SORT_FILENAME_DB: str = "elastic_index"
    SORT_INDEX_FILENAME_DB: str = "index_final"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()