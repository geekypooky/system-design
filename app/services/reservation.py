import uuid
import datetime
from app.db import get_connection
from app.redis_client import get_redis
from app.config import settings
from fastapi import HTTPException
import os

with open(os.path.join(os.path.dirname(__file__), "../lua/reserve.lua"), "r") as f:
    LUA_SCRIPT = f.read()

async def create_reservation(customer_id: str, product_id: str, quantity: int = 1):
    idemp_key = f"res_{customer_id}_{product_id}"
    
    if not settings.NAIVE_MODE:
        redis = get_redis()
        stock_key = f"stock:{product_id}"
        reserved_key = f"reserved:{product_id}"
        
        res = await redis.eval(LUA_SCRIPT, 2, stock_key, reserved_key, quantity)
        if res == 0:
            raise HTTPException(status_code=400, detail="Out of stock (Redis)")
            
    async with await get_connection() as conn:
        async with conn.transaction():
            res_id = str(uuid.uuid4())
            expires_at = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=15)
            
            existing = await conn.fetchval("SELECT reservation_id FROM inventory_reservation WHERE idempotency_key = $1", idemp_key)
            if existing:
                return {"reservation_id": existing, "status": "existing"}
                
            result = await conn.execute("""
                UPDATE inventory 
                SET available_quantity = available_quantity - $1, 
                    reserved_quantity = reserved_quantity + $1,
                    version = version + 1
                WHERE product_id = $2 AND available_quantity >= $1
            """, quantity, product_id)
            
            if result == "UPDATE 0":
                if not settings.NAIVE_MODE:
                    await redis.incrby(stock_key, quantity)
                    await redis.decrby(reserved_key, quantity)
                raise HTTPException(status_code=400, detail="Out of stock (DB)")
                
            await conn.execute("""
                INSERT INTO inventory_reservation (reservation_id, product_id, customer_id, status, expires_at, idempotency_key)
                VALUES ($1, $2, $3, 'RESERVED', $4, $5)
            """, res_id, product_id, customer_id, expires_at, idemp_key)
            
            return {"reservation_id": res_id, "status": "RESERVED"}
