from locust import HttpUser, task, between, events
from uuid import uuid4
import random

PRODUCTS = ["X"]

class Buyer(HttpUser):
    # Zero wait = max throughput (10k RPS needs many users + workers)
    wait_time = between(0, 0.05)

    @task(10)
    def full_purchase_flow(self):
        """Reserve → Checkout in one user journey"""
        cust = f"u{random.randint(1, 50_000_000)}"
        product = random.choice(PRODUCTS)

        with self.client.post(
            "/v1/reservations",
            json={"customer_id": cust, "product_id": product, "quantity": 1},
            catch_response=True,
            name="/v1/reservations"
        ) as r:
            if r.status_code == 200:
                res_id = r.json().get("reservation_id")
                if res_id:
                    self.client.post(
                        "/v1/checkout",
                        json={"reservation_id": res_id, "amount": round(random.uniform(9.99, 299.99), 2)},
                        name="/v1/checkout"
                    )
                r.success()
            elif r.status_code == 400:
                # Out of stock → expected when 100 items exhausted
                r.success()
            else:
                r.failure(f"Unexpected {r.status_code}: {r.text}")

    @task(1)
    def check_stats(self):
        """Periodically poll inventory stats"""
        self.client.get("/admin/stats", name="/admin/stats")
