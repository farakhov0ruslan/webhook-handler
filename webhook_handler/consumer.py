from datetime import UTC
from datetime import datetime
from typing import Callable

from notification_registry import DeliveryFailedPayload
from notification_registry import NotificationChannel
from notification_registry import NotificationConsumer
from notification_registry import NotificationMessage
from notification_registry import NotificationMetadata
from notification_registry import NotificationPriority
from notification_registry import NotificationType
from notification_registry import deserialize_message
from notification_registry import serialize_message
from utils_library.Logging.log import get_logger
from utils_library.RabbitMQ.publisher import RabbitPublisher
from utils_library.RabbitMQ.rabbitmq import RabbitMQConfig

from webhook_handler.config import WEBHOOK_HANDLER_CONFIG
from webhook_handler.processor import process_webhook_message

LOGGER = get_logger(__name__)


def build_on_max_retries(publisher: RabbitPublisher) -> Callable[[bytes], None]:

    def on_max_retries(body: bytes) -> None:
        original = deserialize_message(body)
        LOGGER.error(
            f"Max retries exhausted for notification_id={original.metadata.notification_id}, "
            f"type={original.metadata.notification_type}. "
            f"Publishing DELIVERY_FAILED to notification.platform"
        )

        failed_msg = NotificationMessage(
            metadata=NotificationMetadata(
                notification_type=NotificationType.DELIVERY_FAILED,
                channel=NotificationChannel.PLATFORM,
                priority=NotificationPriority.HIGH,
            ),
            payload=DeliveryFailedPayload(
                user_id=original.payload.user_id,
                recipient_email=original.payload.recipient_email,
                recipient_phone=getattr(original.payload, "recipient_phone", None),
                webhook_url=getattr(original.payload, "webhook_url", None),
                original_channel="webhook",
                original_type=str(original.metadata.notification_type),
                error_message="Webhook delivery failed after all retries",
                retry_count=WEBHOOK_HANDLER_CONFIG.max_retries,
                failed_at=datetime.now(UTC),
            ),
        )

        publisher.publish(
            message=serialize_message(failed_msg).decode("utf-8"),
            queue=NotificationChannel.PLATFORM.queue_name,
        )

    return on_max_retries


def create_consumer(
    rabbitmq_config: RabbitMQConfig,
    publisher: RabbitPublisher,
) -> NotificationConsumer:
    return NotificationConsumer(
        queue_name=NotificationChannel.WEBHOOK.queue_name,
        on_message=process_webhook_message,
        on_max_retries=build_on_max_retries(publisher),
        rabbitmq_config=rabbitmq_config,
        max_retries=WEBHOOK_HANDLER_CONFIG.max_retries,
        retry_delay=WEBHOOK_HANDLER_CONFIG.retry_delay,
    )
