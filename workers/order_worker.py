import asyncio
import uuid
import json
import asyncpg
from redis.asyncio import Redis
import os

DB_DSN = os.getenv("DB_DSN", "postgresql://postgres:password@localhost:5432/salestorm")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

async def process_orders():
    conn = await asyncpg.connect(DB_DSN)
    redis = Redis.from_url(REDIS_URL)
    
    try:
        await redis.xgroup_create("events", "order_group", id="0", mkstream=True)
    except Exception:
        pass

    print("Started order worker")
    while True:
        try:
            messages = await redis.xreadgroup("order_group", "order_consumer", {"events": ">"}, count=10, block=2000)
            if not messages:
                continue
            
            for stream, msgs in messages:
                for msg_id, msg_data in msgs:
                    try:
                        payload = json.loads(msg_data[b'payload'].decode())
                        payment_id = payload['payment_id']
                        customer_id = payload['customer_id']
                        
                        existing = await conn.fetchval("SELECT order_id FROM orders WHERE payment_id = $1", payment_id)
                        if not existing:
                            order_id = str(uuid.uuid4())
                            await conn.execute("INSERT INTO orders (order_id, payment_id, customer_id, status) VALUES ($1, $2, $3, 'CREATED')",
                                               order_id, payment_id, customer_id)
                    except Exception as e:
                        print("Error processing message:", e)
                    finally:
                        await redis.xack("events", "order_group", msg_id)
        except Exception as e:
            print("Worker error:", e)
            await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(process_orders())
