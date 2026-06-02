from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Системные ID
    TENANT_ID: str = "14932313369"
    USER_ID: str = "1"

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

    # PostgreSQL
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "mydb"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "1"

    # Kafka
    KAFKA_BOOTSTRAP_SERVERS: str = "kafka-dev.m15.dzm:9092"
    KAFKA_TOPIC_NAME: str = "ProcedureService_ProcedureAssignmentTopic"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()