import pytest

from notification_registry import NotificationChannel
from notification_registry import NotificationPriority
from notification_registry import NotificationType
from notification_registry import deserialize_message
from webhook_handler.client import send_webhook
from tests.utils.mocks import patched_publisher


class TestSendWebhook:
    @pytest.fixture
    def publisher(self, mocker):
        return patched_publisher(mocker)

    @staticmethod
    def _published_message(publisher):
        raw = publisher.publish.call_args.kwargs["message"].encode()
        return deserialize_message(raw)

    def test_publishes_to_webhook_queue(self, publisher, reset_password_payload):
        send_webhook(reset_password_payload)

        publisher.publish.assert_called_once()
        assert publisher.publish.call_args.kwargs["queue"] == NotificationChannel.WEBHOOK.queue_name

    @pytest.mark.parametrize(
        "payload_fixture, expected_type",
        [
            ("reset_password_payload", NotificationType.RESET_PASSWORD),
            ("analytics_payload", NotificationType.ANALYTICS),
            ("linkedin_disconnected_payload", NotificationType.LINKEDIN_DISCONNECTED),
        ],
    )
    def test_notification_type_matches_payload(
        self, publisher, request, payload_fixture, expected_type
    ):
        payload = request.getfixturevalue(payload_fixture)

        send_webhook(payload)

        assert self._published_message(publisher).metadata.notification_type == expected_type

    def test_priority_forwarded_to_metadata(self, publisher, reset_password_payload):
        send_webhook(reset_password_payload, priority=NotificationPriority.HIGH)

        assert self._published_message(publisher).metadata.priority == NotificationPriority.HIGH

    def test_default_priority_is_normal(self, publisher, reset_password_payload):
        send_webhook(reset_password_payload)

        assert self._published_message(publisher).metadata.priority == NotificationPriority.NORMAL

    def test_channel_is_always_webhook(self, publisher, analytics_payload):
        send_webhook(analytics_payload)

        assert self._published_message(publisher).metadata.channel == NotificationChannel.WEBHOOK

    def test_declare_queue_true(self, publisher, reset_password_payload):
        send_webhook(reset_password_payload)

        assert publisher.publish.call_args.kwargs["declare_queue"] is True

    def test_unknown_payload_raises_value_error(self, publisher):
        class UnknownPayload:
            pass

        with pytest.raises(ValueError, match="Unknown payload type"):
            send_webhook(UnknownPayload())  # type: ignore[arg-type]

    def test_publisher_context_manager_exits(self, publisher, reset_password_payload):
        send_webhook(reset_password_payload)

        publisher.__exit__.assert_called_once()
