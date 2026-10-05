import uuid
import json
import pybreaker
import httpx
from app.db import get_connection
from app.adapters.psp import PaymentProvider
from fastapi import HTTPException

psp = PaymentProvider()

async def process_checkout(reservation_id: str, amount: float):
    # Notice we need reservation_id to be UUID in DB usually, but FastAPI receives string.
    async with await get_connection() as conn:
        res = await conn.fetchrow("SELECT customer_id, status FROM inventory_reservation WHERE reservation_id = $1 FOR UPDATE", reservation_id)
        if not res or res['status'] != 'RESERVED':
            raise HTTPException(status_code=400, detail="Invalid reservation or already processed")
            
        await conn.execute("UPDATE inventory_reservation SET status = 'PAYMENT_PENDING' WHERE reservation_id = $1", reservation_id)
        
        payment_id = str(uuid.uuid4())
        await conn.execute("""
            INSERT INTO payment (payment_id, reservation_id, status, amount)
            VALUES ($1, $2, 'PENDING', $3)
        """, payment_id, reservation_id, amount)

    try:
        psp_result = await psp.charge(reservation_id, amount)
        gw_id = psp_result.get("transaction_id")
        psp_status = psp_result.get("status")
    except (pybreaker.CircuitBreakerError, httpx.RequestError):
        psp_status = "UNKNOWN"
        gw_id = None
        
    db_status = 'SUCCESS' if psp_status == 'SUCCESS' else 'UNKNOWN' if psp_status == 'UNKNOWN' else 'FAILED'

    async with await get_connection() as conn:
        async with conn.transaction():
            await conn.execute("UPDATE payment SET status = $1, gateway_txn_id = $2 WHERE payment_id = $3", db_status, gw_id, payment_id)
            if db_status == 'SUCCESS':
                await conn.execute("UPDATE inventory_reservation SET status = 'CONFIRMED' WHERE reservation_id = $1", reservation_id)
                
                # Shift stock from reserved to sold
                await conn.execute("""
                    UPDATE inventory 
                    SET reserved_quantity = reserved_quantity - $1, 
                        sold_quantity = sold_quantity + $1 
                    WHERE product_id = (
                        SELECT product_id FROM inventory_reservation WHERE reservation_id = $2
                    )
                """, res['quantity'] if 'quantity' in res else 1, reservation_id)

                event_id = str(uuid.uuid4())
                payload = json.dumps({"payment_id": payment_id, "reservation_id": reservation_id, "customer_id": res['customer_id']})
                await conn.execute("INSERT INTO outbox (event_id, event_type, aggregate_id, payload) VALUES ($1, 'PaymentSuccess', $2, $3)",
                                   event_id, payment_id, payload)
            else:
                await conn.execute("UPDATE inventory_reservation SET status = 'RESERVED' WHERE reservation_id = $1", reservation_id)

    return {"payment_id": payment_id, "status": db_status}
