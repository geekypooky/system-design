from prometheus_client import Gauge

# Business-level inventory gauges — imported by main.py and admin.py
stock_available = Gauge("salestorm_stock_available", "Available inventory for product X")
stock_reserved  = Gauge("salestorm_stock_reserved",  "Reserved inventory for product X")
stock_sold      = Gauge("salestorm_stock_sold",      "Sold inventory for product X")
