from unittest.mock import AsyncMock

from pytest_mock import MockerFixture

from webhook_handler.sender import WebhookResult


def mock_sender(mocker: MockerFixture, result: WebhookResult):
    sender = mocker.Mock(send=AsyncMock(return_value=result))
    mocker.patch("webhook_handler.processor._SENDER", sender)
    return sender


def mock_sender_raising(mocker: MockerFixture, exc: BaseException):
    sender = mocker.Mock(send=AsyncMock(side_effect=exc))
    mocker.patch("webhook_handler.processor._SENDER", sender)
    return sender


def patched_publisher(mocker: MockerFixture):
    """Patch webhook_handler.client.RabbitPublisher to a MagicMock usable as context manager."""
    publisher = mocker.MagicMock()
    publisher.__enter__ = mocker.Mock(return_value=publisher)
    publisher.__exit__ = mocker.Mock(return_value=False)
    mocker.patch("webhook_handler.client.RabbitPublisher", return_value=publisher)
    return publisher
