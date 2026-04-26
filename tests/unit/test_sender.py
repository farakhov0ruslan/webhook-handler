import asyncio

import httpx
import pytest
import respx

from webhook_handler.sender import HttpWebhookSender


_URL = "https://webhook.example.com/notify"


class TestHttpWebhookSender:
    def test_returns_sent_on_200(self, webhook_client_config):
        with respx.mock(assert_all_called=True) as mock:
            mock.post(_URL).mock(return_value=httpx.Response(200))
            result = asyncio.run(HttpWebhookSender(webhook_client_config).send(_URL, "{}"))
        assert result.status == "sent"
        assert result.status_code == 200

    def test_returns_sent_on_201(self, webhook_client_config):
        with respx.mock(assert_all_called=True) as mock:
            mock.post(_URL).mock(return_value=httpx.Response(201))
            result = asyncio.run(HttpWebhookSender(webhook_client_config).send(_URL, "{}"))
        assert result.status == "sent"

    def test_returns_failed_on_4xx(self, webhook_client_config):
        with respx.mock(assert_all_called=True) as mock:
            mock.post(_URL).mock(return_value=httpx.Response(404, text="Not found"))
            result = asyncio.run(HttpWebhookSender(webhook_client_config).send(_URL, "{}"))
        assert result.status == "failed"
        assert result.status_code == 404
        assert result.error_type == "HTTP404"

    def test_returns_failed_on_5xx(self, webhook_client_config):
        with respx.mock(assert_all_called=True) as mock:
            mock.post(_URL).mock(return_value=httpx.Response(500, text="Error"))
            result = asyncio.run(HttpWebhookSender(webhook_client_config).send(_URL, "{}"))
        assert result.status == "failed"
        assert result.error_type == "HTTP500"

    def test_returns_failed_on_connection_error(self, webhook_client_config):
        with respx.mock() as mock:
            mock.post(_URL).mock(side_effect=httpx.ConnectError("refused"))
            result = asyncio.run(HttpWebhookSender(webhook_client_config).send(_URL, "{}"))
        assert result.status == "failed"
        assert result.error_type == "ConnectError"

    def test_sends_json_content_type(self, webhook_client_config):
        with respx.mock() as mock:
            route = mock.post(_URL).mock(return_value=httpx.Response(200))
            asyncio.run(HttpWebhookSender(webhook_client_config).send(_URL, '{"x": 1}'))
        assert route.calls.last.request.headers["content-type"] == "application/json"

    def test_sends_notification_type_header(self, webhook_client_config):
        with respx.mock() as mock:
            route = mock.post(_URL).mock(return_value=httpx.Response(200))
            asyncio.run(
                HttpWebhookSender(webhook_client_config).send(
                    _URL, "{}", notification_type="reset_password"
                )
            )
        assert route.calls.last.request.headers["x-notification-type"] == "reset_password"

    def test_sends_body_as_given(self, webhook_client_config):
        body = '{"key": "value"}'
        with respx.mock() as mock:
            route = mock.post(_URL).mock(return_value=httpx.Response(200))
            asyncio.run(HttpWebhookSender(webhook_client_config).send(_URL, body))
        assert route.calls.last.request.content.decode() == body

    def test_url_stored_in_result(self, webhook_client_config):
        with respx.mock() as mock:
            mock.post(_URL).mock(return_value=httpx.Response(200))
            result = asyncio.run(HttpWebhookSender(webhook_client_config).send(_URL, "{}"))
        assert result.url == _URL
