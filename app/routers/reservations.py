from fastapi import APIRouter
from pydantic import BaseModel
from app.services.reservation import create_reservation

router = APIRouter(prefix="/v1", tags=["reservations"])

class ReservationRequest(BaseModel):
    customer_id: str
    product_id: str
    quantity: int = 1

@router.post("/reservations")
async def post_reservation(req: ReservationRequest):
    return await create_reservation(req.customer_id, req.product_id, req.quantity)
