from fastapi import FastAPI
import random
import asyncio
import uuid
from pydantic import BaseModel

app = FastAPI()

class ChargeReq(BaseModel):
    idempotency_key: str
    amount: float

@app.post("/charge")
async def charge(req: ChargeReq):
    await asyncio.sleep(0.1)
    if random.random() < 0.05:
        return {"status": "FAILED", "transaction_id": str(uuid.uuid4())}
    return {"status": "SUCCESS", "transaction_id": str(uuid.uuid4())}
