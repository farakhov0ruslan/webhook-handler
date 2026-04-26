import os
import signal

import fire
from notification_registry import NotificationChannel
from prometheus_client import start_http_server
from utils_library.Logging.log import configure_logger
from utils_library.Logging.log import get_logger
from utils_library.RabbitMQ.correct_consumer import ThreadedRabbitConsumer
from utils_library.RabbitMQ.publisher import RabbitPublisher
from utils_library.RabbitMQ.rabbitmq import RABBIT_MQ_CONFIG

from webhook_handler.config import WEBHOOK_HANDLER_CONFIG
from webhook_handler.consumer import create_consumer

LOGGER = get_logger(__name__)


def serve(env: str = "local") -> None:
    os.environ["env"] = env
    LOGGER.info(f"Starting webhook-handler in '{env}' mode")
    start_http_server(WEBHOOK_HANDLER_CONFIG.metrics_port)
    LOGGER.info(f"Prometheus metrics on :{WEBHOOK_HANDLER_CONFIG.metrics_port}")

    with RabbitPublisher(RABBIT_MQ_CONFIG) as publisher:
        consumer = create_consumer(RABBIT_MQ_CONFIG, publisher)
        threaded = ThreadedRabbitConsumer(consumer)

        def _shutdown(signum, _frame) -> None:
            LOGGER.info(f"Received signal {signum}, shutting down gracefully...")
            threaded.stop()

        signal.signal(signal.SIGINT, _shutdown)
        signal.signal(signal.SIGTERM, _shutdown)

        LOGGER.info(
            f"Webhook handler started, listening on {NotificationChannel.WEBHOOK.queue_name}"
        )
        threaded.start()
        threaded.join()

    LOGGER.info("Webhook handler stopped")


if __name__ == "__main__":  # pragma: no cover
    configure_logger("webhook_handler", "INFO", json_logger=True)
    configure_logger(__name__, "INFO", json_logger=True)
    fire.Fire(serve)
