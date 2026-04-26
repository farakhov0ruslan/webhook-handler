from tests.utils.factories import WEBHOOK_URL
from webhook_handler.sender import WebhookResult


def make_sent_result(url: str = WEBHOOK_URL) -> WebhookResult:
    return WebhookResult(status="sent", url=url, status_code=200)


def make_failed_result(
    url: str = WEBHOOK_URL,
    error: str = "connection refused",
    error_type: str = "ConnectError",
) -> WebhookResult:
    return WebhookResult(status="failed", url=url, error=error, error_type=error_type)
