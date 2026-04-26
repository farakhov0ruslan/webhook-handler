from uuid import uuid4

from notification_registry import NotificationChannel
from notification_registry import NotificationMessage
from notification_registry import NotificationMetadata
from notification_registry import NotificationPriority
from notification_registry.models import BaseNotificationPayload
from notification_registry.serialization import PAYLOAD_TYPE_MAPPING
from notification_registry.serialization import serialize_message
from notification_registry.types import NotificationType
from utils_library.Logging.log import get_logger
from utils_library.RabbitMQ.publisher import RabbitPublisher
from utils_library.RabbitMQ.rabbitmq import RABBIT_MQ_CONFIG

LOGGER = get_logger(__name__)

_PAYLOAD_TO_TYPE: dict[type, NotificationType] = {
    payload_cls: notification_type
    for notification_type, payload_cls in PAYLOAD_TYPE_MAPPING.items()
}


def send_webhook(
    payload: BaseNotificationPayload,
    priority: NotificationPriority = NotificationPriority.NORMAL,
) -> None:
    notification_type = _PAYLOAD_TO_TYPE.get(type(payload))
    if notification_type is None:
        raise ValueError(f"Unknown payload type: {type(payload).__name__}")

    message = NotificationMessage(
        metadata=NotificationMetadata(
            notification_id=uuid4(),
            notification_type=notification_type,
            channel=NotificationChannel.WEBHOOK,
            priority=priority,
        ),
        payload=payload,
    )
    body = serialize_message(message).decode("utf-8")
    with RabbitPublisher(rabbit_config=RABBIT_MQ_CONFIG) as publisher:
        publisher.publish(
            message=body,
            queue=NotificationChannel.WEBHOOK.queue_name,
            declare_queue=True,
        )
