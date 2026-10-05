from fastapi import FastAPI
from contextlib import asynccontextmanager
import asyncio
from app.db import init_db, close_db, get_connection
from app.redis_client import init_redis, close_redis
from app.config import settings
from app.metrics import stock_available, stock_reserved, stock_sold
from app.routers import admin, reservations, checkout
from prometheus_fastapi_instrumentator import Instrumentator

async def _gauge_poller():
    """Poll DB every 5s and push live stock values to Prometheus gauges."""
    while True:
        try:
            async with await get_connection() as conn:
                row = await conn.fetchrow(
                    "SELECT sum(available_quantity) as a, "
                    "sum(reserved_quantity) as r, "
                    "sum(sold_quantity) as s FROM inventory"
                )
                if row and row["a"] is not None:
                    stock_available.set(float(row["a"]))
                    stock_reserved.set(float(row["r"]))
                    stock_sold.set(float(row["s"]))
        except Exception:
            pass
        await asyncio.sleep(5)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db(settings.DATABASE_URL)
    await init_redis(settings.REDIS_URL)
    poller = asyncio.create_task(_gauge_poller())
    yield
    poller.cancel()
    await close_db()
    await close_redis()

app = FastAPI(lifespan=lifespan)

# Prometheus: auto-instrument all routes → exposes /metrics
Instrumentator().instrument(app).expose(app)

app.include_router(admin.router)
app.include_router(reservations.router)
app.include_router(checkout.router)

