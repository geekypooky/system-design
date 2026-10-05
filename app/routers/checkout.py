from fastapi import APIRouter
from pydantic import BaseModel
from app.services.payment import process_checkout

router = APIRouter(prefix="/v1", tags=["checkout"])

class CheckoutRequest(BaseModel):
    reservation_id: str
    amount: float

@router.post("/checkout")
async def post_checkout(req: CheckoutRequest):
    return await process_checkout(req.reservation_id, req.amount)
