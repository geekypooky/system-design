CREATE TABLE inventory (
  inventory_id SERIAL PRIMARY KEY,
  product_id TEXT UNIQUE NOT NULL,
  total_quantity INT NOT NULL,
  available_quantity INT NOT NULL CHECK (available_quantity >= 0),
  reserved_quantity  INT NOT NULL CHECK (reserved_quantity  >= 0),
  sold_quantity      INT NOT NULL CHECK (sold_quantity      >= 0),
  version INT NOT NULL DEFAULT 0,
  updated_at TIMESTAMPTZ DEFAULT now(),
  CHECK (available_quantity + reserved_quantity + sold_quantity = total_quantity)
);

CREATE TABLE inventory_reservation (
  reservation_id UUID PRIMARY KEY,
  product_id TEXT NOT NULL REFERENCES inventory(product_id),
  customer_id TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN
    ('RESERVED','PAYMENT_PENDING','CONFIRMED','SOLD','RELEASED')),
  expires_at TIMESTAMPTZ NOT NULL,
  idempotency_key TEXT UNIQUE NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX ON inventory_reservation(status, expires_at);
CREATE UNIQUE INDEX one_active_per_customer ON inventory_reservation(customer_id, product_id)
  WHERE status IN ('RESERVED','PAYMENT_PENDING','CONFIRMED','SOLD');

CREATE TABLE payment (
  payment_id UUID PRIMARY KEY,
  reservation_id UUID UNIQUE NOT NULL REFERENCES inventory_reservation,
  status TEXT NOT NULL CHECK (status IN ('PENDING','SUCCESS','FAILED','UNKNOWN','REFUNDED')),
  gateway_txn_id TEXT UNIQUE,
  amount NUMERIC(12,2) NOT NULL,
  updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE orders (
  order_id UUID PRIMARY KEY,
  payment_id UUID UNIQUE NOT NULL REFERENCES payment,
  customer_id TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('CREATED','PAYMENT_PENDING','CONFIRMED','PROCESSING',
    'SHIPPED','OUT_FOR_DELIVERY','DELIVERED','CANCELLED')),
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE order_status_history (
  id BIGSERIAL PRIMARY KEY, order_id UUID, from_status TEXT, to_status TEXT, at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE outbox (
  event_id UUID PRIMARY KEY, event_type TEXT NOT NULL, aggregate_id UUID NOT NULL,
  payload JSONB NOT NULL, published_at TIMESTAMPTZ, created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX ON outbox(published_at) WHERE published_at IS NULL;
