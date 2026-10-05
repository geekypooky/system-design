import asyncpg
from typing import Optional

pool: Optional[asyncpg.Pool] = None

async def init_db(dsn: str):
    global pool
    pool = await asyncpg.create_pool(dsn)

async def close_db():
    global pool
    if pool:
        await pool.close()

async def get_connection():
    if not pool:
        raise Exception("Database not initialized")
    return pool.acquire()
