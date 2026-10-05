#!/bin/bash
docker compose exec -T db psql -U postgres -d salestorm -c "TRUNCATE inventory, inventory_reservation, payment, orders, order_status_history, outbox RESTART IDENTITY CASCADE;"
docker compose exec -T db psql -U postgres -d salestorm -c "INSERT INTO inventory(product_id,total_quantity,available_quantity,reserved_quantity,sold_quantity) VALUES ('X',100,100,0,0);"
docker compose exec -T redis redis-cli FLUSHALL
docker compose exec -T redis redis-cli SET stock:X 100
echo "Database seeded."
