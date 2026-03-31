-- Local dev DB bootstrap (used by docker-compose)
-- Production uses Supabase (tables already created there)

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    hashed_password TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS orders (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    symbol TEXT NOT NULL,
    side TEXT CHECK (side IN ('buy', 'sell')),
    type TEXT CHECK (type IN ('market', 'limit', 'ioc', 'fok')),
    price NUMERIC,
    quantity NUMERIC NOT NULL,
    remaining_qty NUMERIC NOT NULL,
    status TEXT DEFAULT 'open',
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS trades (
    id UUID PRIMARY KEY,
    symbol TEXT NOT NULL,
    price NUMERIC NOT NULL,
    quantity NUMERIC NOT NULL,
    buyer_id UUID,
    seller_id UUID,
    timestamp TIMESTAMP DEFAULT NOW()
);
