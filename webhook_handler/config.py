from dataclasses import dataclass
from dataclasses import field

from utils_library.Configuration.meta_config import AbstractMetaConfig


@dataclass
class WebhookHandlerConfig(AbstractMetaConfig):
    max_retries: int = field(
        default=5,
        metadata={"docs": "Max retry attempts before DELIVERY_FAILED", "required": False},
    )
    retry_delay: float = field(
        default=2.0,
        metadata={"docs": "Delay between retries in seconds", "required": False},
    )
    metrics_port: int = field(
        default=9095,
        metadata={"docs": "Prometheus metrics port", "required": False},
    )


@dataclass
class WebhookClientConfig(AbstractMetaConfig):
    timeout: float = field(
        default=30.0,
        metadata={"docs": "HTTP request timeout in seconds", "required": False},
    )


WEBHOOK_HANDLER_CONFIG = WebhookHandlerConfig()
WEBHOOK_CLIENT_CONFIG = WebhookClientConfig()
