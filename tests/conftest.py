import pytest

import webhook_handler.sender as sender_module
from notification_registry import NotificationType
from webhook_handler.config import WebhookClientConfig
from tests.utils.factories import AnalyticsPayloadFactory
from tests.utils.factories import LinkedInDisconnectedPayloadFactory
from tests.utils.factories import ResetPasswordPayloadFactory
from tests.utils.messages import build_message


@pytest.fixture
def reset_password_payload():
    return ResetPasswordPayloadFactory.build()


@pytest.fixture
def analytics_payload():
    return AnalyticsPayloadFactory.build()


@pytest.fixture
def linkedin_disconnected_payload():
    return LinkedInDisconnectedPayloadFactory.build()


@pytest.fixture
def reset_password_message(reset_password_payload):
    return build_message(reset_password_payload, NotificationType.RESET_PASSWORD)


@pytest.fixture
def analytics_message(analytics_payload):
    return build_message(analytics_payload, NotificationType.ANALYTICS)


@pytest.fixture
def linkedin_disconnected_message(linkedin_disconnected_payload):
    return build_message(linkedin_disconnected_payload, NotificationType.LINKEDIN_DISCONNECTED)


@pytest.fixture
def webhook_client_config():
    WebhookClientConfig.set_setting("timeout", 30.0)
    return WebhookClientConfig()


@pytest.fixture(autouse=True)
def _reset_sender_singleton():
    sender_module._webhook_sender = None
    yield
    sender_module._webhook_sender = None
