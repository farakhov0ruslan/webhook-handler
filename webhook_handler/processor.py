import asyncio

from notification_registry import WebhookChannelProcessor
from notification_registry import deserialize_message
from utils_library.Logging.log import get_logger

from webhook_handler.config import WEBHOOK_CLIENT_CONFIG
from webhook_handler.sender import HttpWebhookSender

LOGGER = get_logger(__name__)

_SENDER = HttpWebhookSender(WEBHOOK_CLIENT_CONFIG)


def process_webhook_message(body: bytes) -> None:
    message = deserialize_message(body)
    LOGGER.info(
        f"Processing webhook notification: type={message.metadata.notification_type}, "
        f"id={message.metadata.notification_id}"
    )

    processed = WebhookChannelProcessor.process(message)
    if processed is None:
        raise RuntimeError(
            f"No webhook processor for type={message.metadata.notification_type}"
        )

    try:
        result = asyncio.run(
            _SENDER.send(
                url=processed.recipient,
                body=processed.body,
                notification_type=processed.subject or "",
            )
        )
    except Exception as exc:
        LOGGER.exception(f"Unexpected error sending webhook to {processed.recipient}: {exc}")
        raise

    if result.status == "failed":
        LOGGER.error(
            f"Webhook delivery failed to {processed.recipient}: "
            f"[{result.error_type}] {result.error}"
        )
        raise RuntimeError(
            f"Webhook delivery failed to {processed.recipient}: {result.error}"
        )

    LOGGER.info(
        f"Webhook sent: url={processed.recipient}, id={message.metadata.notification_id}"
    )
