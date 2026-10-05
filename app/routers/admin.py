from fastapi import APIRouter
from app.db import get_connection
from app.redis_client import get_redis
from app.config import settings
from app.metrics import stock_available, stock_reserved, stock_sold
import os

router = APIRouter(prefix="/admin", tags=["admin"])

SEED_STOCK = 100  # ← change this to adjust starting inventory

@router.get("/stats")
async def get_stats():
    async with await get_connection() as conn:
        row = await conn.fetchrow("SELECT sum(available_quantity) as available, sum(reserved_quantity) as reserved, sum(sold_quantity) as sold FROM inventory")
        if not row or row['available'] is None:
            available, reserved, sold = 0, 0, 0
        else:
            available = row['available']
            reserved = row['reserved']
            sold = row['sold']
            
        redis = get_redis()
        r_stock = await redis.get("stock:X")
        if r_stock is not None:
            r_stock = int(r_stock)
        
        # Push to Prometheus gauges
        stock_available.set(available)
        stock_reserved.set(reserved)
        stock_sold.set(sold)
        
        total = available + reserved + sold
        invariants = {
            "sold_le_total": sold <= total if total > 0 else True,
            "available_ge_0": available >= 0,
            "sum_equals_total": True
        }
        
        reservations_raw = await conn.fetch("SELECT status, count(*) FROM inventory_reservation GROUP BY status")
        reservations = {r['status']: r['count'] for r in reservations_raw}
        
        return {
            "available": available,
            "reserved": reserved,
            "sold": sold,
            "redis_stock": r_stock,
            "api_instance": os.getenv("HOSTNAME", "local"),
            "reservations": reservations,
            "invariants": invariants,
            "naive_mode": settings.NAIVE_MODE
        }

@router.post("/reset")
async def reset_db():
    async with await get_connection() as conn:
        await conn.execute("TRUNCATE inventory, inventory_reservation, payment, orders, order_status_history, outbox RESTART IDENTITY CASCADE;")
        await conn.execute(
            "INSERT INTO inventory(product_id, total_quantity, available_quantity, reserved_quantity, sold_quantity) VALUES ('X', $1, $1, 0, 0);",
            SEED_STOCK
        )
        
        redis = get_redis()
        await redis.flushall()
        await redis.set("stock:X", SEED_STOCK)
        await redis.set("reserved:X", 0)

    # Update Prometheus gauges after reset
    stock_available.set(SEED_STOCK)
    stock_reserved.set(0)
    stock_sold.set(0)
        
    return {"status": "reset", "seed_stock": SEED_STOCK}

@router.post("/config")
async def update_config(naive_mode: bool):
    settings.NAIVE_MODE = naive_mode
    return {"status": "config updated", "naive_mode": settings.NAIVE_MODE}

