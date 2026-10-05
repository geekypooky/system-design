import httpx
from app.config import settings
import pybreaker

psp_breaker = pybreaker.CircuitBreaker(fail_max=3, reset_timeout=10)

class PaymentProvider:
    @psp_breaker
    async def charge(self, idempotency_key: str, amount: float) -> dict:
        async with httpx.AsyncClient() as client:
            resp = await client.post(f"{settings.MOCK_PSP_URL}/charge", json={
                "idempotency_key": idempotency_key,
                "amount": amount
            }, timeout=2.0)
            resp.raise_for_status()
            return resp.json()
