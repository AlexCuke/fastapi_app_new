import logging
import json
from aiokafka import AIOKafkaProducer
from app.config import settings

logger = logging.getLogger("uvicorn.error")

class KafkaProducerManager:
    def __init__(self):
        self.producer: AIOKafkaProducer | None = None

    async def start(self):
        try:
            self.producer = AIOKafkaProducer(
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                client_id="fastapi-integration-service"
            )
            await self.producer.start()
            logger.info(f"Kafka Producer successfully started on {settings.KAFKA_BOOTSTRAP_SERVERS}")
        except Exception as e:
            logger.error(f"Failed to start Kafka Producer: {e}")
            self.producer = None

    async def stop(self):
        if self.producer:
            await self.producer.stop()
            logger.info("Kafka Producer stopped")

    async def send_message(self, topic: str, value: dict, key: str = None) -> bool:
        if not self.producer:
            await self.start()
        if not self.producer:
            raise RuntimeError(f"Kafka Producer is not initialized or unreachable on {settings.KAFKA_BOOTSTRAP_SERVERS}")
        
        bytes_value = json.dumps(value, ensure_ascii=False).encode('utf-8')
        bytes_key = key.encode('utf-8') if key else None
        
        await self.producer.send_and_wait(topic, value=bytes_value, key=bytes_key)
        return True

kafka_manager = KafkaProducerManager()