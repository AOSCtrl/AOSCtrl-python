# Python SDK

Requires Python 3.9 or newer. The standard library is enough; the only credential is the API token.

```bash
pip install ./SDK/python
```

```python
import os
from orch_sdk import OrchClient

client = OrchClient(api_token=os.environ["API_TOKEN"], base_url="http://localhost:3001")

sms = client.send_sms(
    request_id="sms-demo-001",
    phone_number="+919999999999",
    message="Your OTP is 123456",
    routing_context={"country": "IN", "requestType": "OTP", "capabilities": ["SMS"]},
    correlation_id="corr-demo-001",
)

email = client.send_email(
    request_id="email-demo-001",
    operation="SEND",
    payload={"recipient": "user@example.com", "subject": "Test message"},
    routing_context={"tenantId": "tenant-123"},
)

client.send_otp(request_id="otp-demo-001", payload={"phoneNumber": "+919999999999"})
client.capture(request_id="capture-demo-001", payload={"source": "web"})
client.health_live()
client.health_ready()
```

Every call sends `Authorization: Bearer <api_token>` so APISIX can validate it. A non-success response raises `OrchApiError` with `status_code` and `code`. A blank token raises `ValueError` before any HTTP call.
