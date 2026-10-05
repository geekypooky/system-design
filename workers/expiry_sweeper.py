import asyncio
import asyncpg
from redis.asyncio import Redis
import os

DB_DSN = os.getenv("DB_DSN", "postgresql://postgres:password@localhost:5432/salestorm")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

async def sweep():
    conn = await asyncpg.connect(DB_DSN)
    redis = Redis.from_url(REDIS_URL)
    
    print("Started expiry sweeper")
    while True:
        try:
            expired = await conn.fetch("SELECT reservation_id, product_id FROM inventory_reservation WHERE status = 'RESERVED' AND expires_at < now()")
            for row in expired:
                async with conn.transaction():
                    res = await conn.execute("UPDATE inventory_reservation SET status = 'RELEASED' WHERE reservation_id = $1 AND status = 'RESERVED'", row['reservation_id'])
                    if res != "UPDATE 0":
                        await conn.execute("UPDATE inventory SET available_quantity = available_quantity + 1, reserved_quantity = reserved_quantity - 1 WHERE product_id = $1", row['product_id'])
                        
                        stock_key = f"stock:{row['product_id']}"
                        reserved_key = f"reserved:{row['product_id']}"
                        await redis.incr(stock_key)
                        await redis.decr(reserved_key)
        except Exception as e:
            print("Sweeper error:", e)
        await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(sweep())
