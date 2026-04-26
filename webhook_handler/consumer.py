from notification_registry import ChannelHandlerSettings
from notification_registry import NotificationChannel
from notification_registry import NotificationConsumer
from notification_registry import create_channel_consumer
from utils_library.RabbitMQ.publisher import RabbitPublisher
from utils_library.RabbitMQ.rabbitmq import RabbitMQConfig

from webhook_handler.config import WEBHOOK_HANDLER_CONFIG
from webhook_handler.processor import process_webhook_message


def create_consumer(
    rabbitmq_config: RabbitMQConfig,
    publisher: RabbitPublisher,
) -> NotificationConsumer:
    settings = ChannelHandlerSettings(
        channel=NotificationChannel.WEBHOOK,
        max_retries=WEBHOOK_HANDLER_CONFIG.max_retries,
        retry_delay=WEBHOOK_HANDLER_CONFIG.retry_delay,
        failed_error_message="Webhook delivery failed after all retries",
    )
    return create_channel_consumer(
        settings=settings,
        on_message=process_webhook_message,
        publisher=publisher,
        rabbitmq_config=rabbitmq_config,
    )
