import asyncio
import asyncpg
import os

DB_DSN = os.getenv("DB_DSN", "postgresql://postgres:password@localhost:5432/salestorm")

async def reconcile():
    conn = await asyncpg.connect(DB_DSN)
    
    print("Started reconciler")
    while True:
        try:
            unknowns = await conn.fetch("SELECT payment_id FROM payment WHERE status = 'UNKNOWN'")
            for row in unknowns:
                async with conn.transaction():
                    await conn.execute("UPDATE payment SET status = 'FAILED' WHERE payment_id = $1", row['payment_id'])
        except Exception as e:
            print("Reconciler error:", e)
        await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(reconcile())
