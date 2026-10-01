import json
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

from orch_sdk import OrchApiError, OrchClient


class FakeResponse:
    def __init__(self, payload):
        self._raw = json.dumps(payload).encode("utf-8")

    def read(self):
        return self._raw

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class ClientTests(unittest.TestCase):
    def test_blank_token_does_not_call_the_service(self):
        with self.assertRaises(ValueError):
            OrchClient(api_token="  ")

    def test_business_calls_send_the_bearer_token(self):
        calls = []

        def fake_urlopen(request, timeout):
            calls.append(request)
            return FakeResponse({"success": True, "status": "SUCCESS"})

        client = OrchClient(api_token="secret-token", base_url="http://orch.test/")
        with patch("orch_sdk.client.urlopen", fake_urlopen):
            client.send_sms("sms-1", "+919999999999", "hello", correlation_id="corr-1")
            client.send_otp("otp-1")
            client.send_email("email-1", payload={"recipient": "user@example.com"})
            client.capture("cap-1")
            client.health_live()
            client.health_ready()

        paths = [f"{call.get_method()} {call.full_url}" for call in calls]
        self.assertEqual(
            paths,
            [
                "POST http://orch.test/v1/sms/send",
                "POST http://orch.test/v1/otp/send",
                "POST http://orch.test/v1/email/send",
                "POST http://orch.test/v1/capture",
                "GET http://orch.test/health/live",
                "GET http://orch.test/health/ready",
            ],
        )
        for call in calls:
            self.assertEqual(call.get_header("Authorization"), "Bearer secret-token")
        self.assertEqual(calls[0].get_header("X-correlation-id"), "corr-1")

    def test_invalid_token_raises(self):
        body = json.dumps({
            "success": False,
            "error": {"code": "INVALID_API_TOKEN", "message": "A valid API token is required"},
        }).encode("utf-8")

        def fake_urlopen(request, timeout):
            raise HTTPError(request.full_url, 401, "Unauthorized", hdrs=None, fp=_Bytes(body))

        client = OrchClient(api_token="bad-token")
        with patch("orch_sdk.client.urlopen", fake_urlopen):
            with self.assertRaises(OrchApiError) as caught:
                client.send_sms("sms-1", "+919999999999", "hello")
        self.assertEqual(caught.exception.status_code, 401)
        self.assertEqual(caught.exception.code, "INVALID_API_TOKEN")


class _Bytes:
    def __init__(self, data):
        self._data = data

    def read(self):
        return self._data

    def close(self):
        return None


if __name__ == "__main__":
    unittest.main()
