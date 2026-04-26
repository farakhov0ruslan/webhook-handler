import json

import pytest

from notification_registry import NotificationPriority
from notification_registry import NotificationType
from notification_registry import serialize_message

from webhook_handler.processor import process_webhook_message
from tests.utils.factories import WEBHOOK_URL
from tests.utils.messages import build_message
from tests.utils.mocks import mock_sender
from tests.utils.mocks import mock_sender_raising
from tests.utils.results import make_failed_result
from tests.utils.results import make_sent_result


class TestProcessWebhookMessage:
    def test_reset_password_happy_path(self, mocker, reset_password_payload, reset_password_message):
        sender = mock_sender(mocker, make_sent_result(url=WEBHOOK_URL))

        process_webhook_message(serialize_message(reset_password_message))

        sender.send.assert_awaited_once()
        call = sender.send.call_args
        assert call.kwargs["url"] == WEBHOOK_URL

    def test_analytics_happy_path(self, mocker, analytics_payload, analytics_message):
        sender = mock_sender(mocker, make_sent_result(url=WEBHOOK_URL))

        process_webhook_message(serialize_message(analytics_message))

        call = sender.send.call_args
        assert call.kwargs["url"] == WEBHOOK_URL

    def test_linkedin_disconnected_happy_path(
        self, mocker, linkedin_disconnected_payload, linkedin_disconnected_message
    ):
        sender = mock_sender(mocker, make_sent_result(url=WEBHOOK_URL))

        process_webhook_message(serialize_message(linkedin_disconnected_message))

        call = sender.send.call_args
        assert call.kwargs["url"] == WEBHOOK_URL
        assert call.kwargs["notification_type"] == str(NotificationType.LINKEDIN_DISCONNECTED)

    def test_body_is_valid_json(self, mocker, reset_password_message):
        sender = mock_sender(mocker, make_sent_result())

        process_webhook_message(serialize_message(reset_password_message))

        body = sender.send.call_args.kwargs["body"]
        parsed = json.loads(body)
        assert "notification_type" in parsed
        assert "notification_id" in parsed
        assert "data" in parsed

    def test_body_contains_notification_type(self, mocker, reset_password_message):
        sender = mock_sender(mocker, make_sent_result())

        process_webhook_message(serialize_message(reset_password_message))

        body = json.loads(sender.send.call_args.kwargs["body"])
        assert body["notification_type"] == str(NotificationType.RESET_PASSWORD)

    def test_raises_runtime_error_when_sender_fails(self, mocker, reset_password_message):
        mock_sender(mocker, make_failed_result(error="timeout"))

        with pytest.raises(RuntimeError, match="timeout"):
            process_webhook_message(serialize_message(reset_password_message))

    def test_raises_when_sender_throws_exception(self, mocker, reset_password_message):
        mock_sender_raising(mocker, OSError("no route to host"))

        with pytest.raises(OSError, match="no route to host"):
            process_webhook_message(serialize_message(reset_password_message))

    def test_raises_value_error_on_invalid_body(self):
        with pytest.raises(ValueError):
            process_webhook_message(b"not json at all")

    def test_error_type_logged_on_failed_result(self, mocker, reset_password_message):
        mock_sender(mocker, make_failed_result(error_type="HTTP503", error="Service Unavailable"))
        logger_mock = mocker.patch("webhook_handler.processor.LOGGER")

        with pytest.raises(RuntimeError):
            process_webhook_message(serialize_message(reset_password_message))

        error_calls = [str(c) for c in logger_mock.error.call_args_list]
        assert any("HTTP503" in c for c in error_calls)

    @pytest.mark.parametrize("priority", [NotificationPriority.LOW, NotificationPriority.HIGH])
    def test_processes_any_priority(self, mocker, reset_password_payload, priority):
        message = build_message(
            reset_password_payload,
            NotificationType.RESET_PASSWORD,
            priority=priority,
        )
        sender = mock_sender(mocker, make_sent_result())

        process_webhook_message(serialize_message(message))

        sender.send.assert_awaited_once()
