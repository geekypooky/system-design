SELECT
    (sold_quantity <= total_quantity AND available_quantity >= 0) AS rule1,
    (available_quantity + reserved_quantity + sold_quantity = total_quantity) AS rule2,
    (SELECT COUNT(*) FROM inventory_reservation WHERE status = 'SOLD') = sold_quantity AS rule3,
    (SELECT COUNT(*) FROM payment GROUP BY reservation_id HAVING COUNT(*) > 1) IS NULL AS rule4a,
    (SELECT COUNT(*) FROM orders GROUP BY payment_id HAVING COUNT(*) > 1) IS NULL AS rule4b,
    (SELECT COUNT(*) FROM payment p LEFT JOIN orders o ON p.payment_id = o.payment_id WHERE p.status = 'SUCCESS' AND o.order_id IS NULL) = 0 AS rule5,
    sold_quantity = 100 AS rule6
FROM inventory WHERE product_id = 'X';
