from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass
from datetime import UTC
from datetime import datetime
from typing import Literal
from typing import Optional

import httpx
from utils_library.Logging.log import get_logger

from webhook_handler.config import WebhookClientConfig

LOGGER = get_logger(__name__)


@dataclass
class WebhookResult:
    status: Literal["sent", "failed"]
    url: str
    status_code: Optional[int] = None
    error: Optional[str] = None
    error_type: Optional[str] = None
    timestamp: str = ""

    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = datetime.now(UTC).isoformat()


class WebhookSender(ABC):
    @abstractmethod
    async def send(
        self,
        url: str,
        body: str,
        notification_type: str = "",
    ) -> WebhookResult:
        ...


class HttpWebhookSender(WebhookSender):
    """HTTP POST на webhook URL через httpx. Используется в prod."""

    def __init__(self, config: WebhookClientConfig) -> None:
        self.config = config

    async def send(
        self,
        url: str,
        body: str,
        notification_type: str = "",
    ) -> WebhookResult:
        headers = {
            "Content-Type": "application/json",
            "X-Notification-Type": notification_type,
        }
        try:
            async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                resp = await client.post(url, content=body, headers=headers)
                if resp.is_success:
                    LOGGER.info(
                        f"Webhook delivered: url={url}, "
                        f"status={resp.status_code}, type={notification_type}"
                    )
                    return WebhookResult(
                        status="sent", url=url, status_code=resp.status_code
                    )
                LOGGER.error(
                    f"Webhook error: url={url}, status={resp.status_code}, "
                    f"body={resp.text[:200]}"
                )
                return WebhookResult(
                    status="failed",
                    url=url,
                    status_code=resp.status_code,
                    error=f"{resp.status_code}: {resp.text[:200]}",
                    error_type=f"HTTP{resp.status_code}",
                )
        except httpx.HTTPError as e:
            LOGGER.error(f"Webhook HTTP error to {url}: {e}")
            return WebhookResult(
                status="failed",
                url=url,
                error=str(e),
                error_type=type(e).__name__,
            )


