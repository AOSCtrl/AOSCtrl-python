import json
from typing import Any, Mapping, Optional
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from orch_sdk.errors import OrchApiError

DEFAULT_BASE_URL = "http://localhost:3001"
DEFAULT_TIMEOUT_SECONDS = 30
USER_AGENT = "aosctrl-orch-sdk-python/1.0.0"


class OrchClient:
    """Orchestrator client. Callers supply an API token; APISIX validates it."""

    def __init__(self, api_token: str, base_url: str = DEFAULT_BASE_URL, timeout: float = DEFAULT_TIMEOUT_SECONDS):
        token = api_token.strip() if isinstance(api_token, str) else ""
        if not token:
            raise ValueError("api_token is required")
        self._api_token = token
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout

    def send_sms(
        self,
        request_id: str,
        phone_number: str,
        message: str,
        routing_context: Optional[Mapping[str, Any]] = None,
        unicode: Optional[bool] = None,
        correlation_id: Optional[str] = None,
    ) -> dict:
        body: dict[str, Any] = {
            "requestId": request_id,
            "phoneNumber": phone_number,
            "message": message,
        }
        if routing_context is not None:
            body["routingContext"] = dict(routing_context)
        if unicode is not None:
            body["unicode"] = unicode
        return self._request("POST", "/v1/sms/send", body, correlation_id)

    def send_otp(
        self,
        request_id: str,
        operation: Optional[str] = None,
        payload: Optional[Mapping[str, Any]] = None,
        routing_context: Optional[Mapping[str, Any]] = None,
        correlation_id: Optional[str] = None,
    ) -> dict:
        return self._service("/v1/otp/send", request_id, operation, payload, routing_context, correlation_id)

    def send_email(
        self,
        request_id: str,
        operation: Optional[str] = None,
        payload: Optional[Mapping[str, Any]] = None,
        routing_context: Optional[Mapping[str, Any]] = None,
        correlation_id: Optional[str] = None,
    ) -> dict:
        return self._service("/v1/email/send", request_id, operation, payload, routing_context, correlation_id)

    def capture(
        self,
        request_id: str,
        operation: Optional[str] = None,
        payload: Optional[Mapping[str, Any]] = None,
        routing_context: Optional[Mapping[str, Any]] = None,
        correlation_id: Optional[str] = None,
    ) -> dict:
        return self._service("/v1/capture", request_id, operation, payload, routing_context, correlation_id)

    def health_live(self, correlation_id: Optional[str] = None) -> dict:
        return self._request("GET", "/health/live", None, correlation_id)

    def health_ready(self, correlation_id: Optional[str] = None) -> dict:
        return self._request("GET", "/health/ready", None, correlation_id)

    def _service(
        self,
        path: str,
        request_id: str,
        operation: Optional[str],
        payload: Optional[Mapping[str, Any]],
        routing_context: Optional[Mapping[str, Any]],
        correlation_id: Optional[str],
    ) -> dict:
        body: dict[str, Any] = {"requestId": request_id}
        if operation is not None:
            body["operation"] = operation
        if payload is not None:
            body["payload"] = dict(payload)
        if routing_context is not None:
            body["routingContext"] = dict(routing_context)
        return self._request("POST", path, body, correlation_id)

    def _request(self, method: str, path: str, body: Optional[dict], correlation_id: Optional[str]) -> dict:
        headers = {
            "Authorization": f"Bearer {self._api_token}",
            "Accept": "application/json",
            "User-Agent": USER_AGENT,
        }
        if correlation_id:
            headers["X-Correlation-Id"] = correlation_id
        data = None
        if body is not None:
            headers["Content-Type"] = "application/json"
            data = json.dumps(body).encode("utf-8")

        request = Request(f"{self._base_url}{path}", data=data, headers=headers, method=method)
        try:
            with urlopen(request, timeout=self._timeout) as response:
                raw = response.read().decode("utf-8")
        except HTTPError as error:
            raw = error.read().decode("utf-8")
            payload = json.loads(raw) if raw else {}
            details = payload.get("error") or {}
            raise OrchApiError(
                error.code,
                details.get("code") or "HTTP_ERROR",
                details.get("message") or error.reason or "Orchestrator request failed",
                details.get("details"),
                payload.get("requestId"),
                payload.get("correlationId"),
            ) from error

        return json.loads(raw) if raw else {}
