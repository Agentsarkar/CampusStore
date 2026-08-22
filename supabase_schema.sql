-- =======================================================
-- SUPABASE DATABASE SCHEMA FOR CAMPUS E-COMMERCE
-- =======================================================
-- Run these queries in the Supabase SQL Editor to initialize your database tables.

-- 1. Users Table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    mobile TEXT DEFAULT NULL,
    status TEXT DEFAULT 'Active',
    role TEXT DEFAULT 'USER',  -- 'USER' | 'ADMIN' | 'CANTEEN_OP'
    outlet_category_id UUID DEFAULT NULL, -- For CANTEEN_OP: links them to their outlet category
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 2. Categories Table
CREATE TABLE IF NOT EXISTS categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL UNIQUE,
    image TEXT DEFAULT '',
    section TEXT DEFAULT 'flash',  -- 'flash' for Campus Flash, 'canteen' for Campus Canteen
    address TEXT DEFAULT '',       -- Physical location of the outlet
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 3. Products Table
CREATE TABLE IF NOT EXISTS products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    image TEXT[] DEFAULT '{}',
    unit TEXT DEFAULT '',
    stock INTEGER DEFAULT 0,
    price NUMERIC DEFAULT 0,
    discount NUMERIC DEFAULT 0,
    description TEXT DEFAULT '',
    category_id UUID REFERENCES categories(id) ON DELETE SET NULL,
    section TEXT DEFAULT 'flash',      -- 'flash' or 'canteen'
    food_type TEXT DEFAULT NULL,       -- 'veg' or 'non-veg' (canteen specific)
    prep_time TEXT DEFAULT '8 mins',   -- Estimated prep time (canteen specific)
    publish BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 4. Cart Items Table (for Campus Flash / regular products)
CREATE TABLE IF NOT EXISTS cart_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    product_id UUID REFERENCES products(id) ON DELETE CASCADE,
    quantity INTEGER DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    UNIQUE(user_id, product_id)
);

-- 4b. Canteen Cart Items Table (outlet-scoped, like Zomato single-restaurant cart)
CREATE TABLE IF NOT EXISTS canteen_cart_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    product_id UUID REFERENCES products(id) ON DELETE CASCADE,
    outlet_category_id UUID REFERENCES categories(id) ON DELETE CASCADE,
    quantity INTEGER DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    UNIQUE(user_id, product_id)
);

-- 5. Delivery Address Table (Campus Specific)
CREATE TABLE IF NOT EXISTS addresses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    room_number TEXT NOT NULL,
    building_name TEXT NOT NULL,
    branch TEXT NOT NULL,
    status BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 5b. Riders Table (Delivery Partners)
CREATE TABLE IF NOT EXISTS riders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    phone TEXT NOT NULL,
    campus_id_url TEXT NOT NULL,
    status TEXT DEFAULT 'PENDING',  -- 'PENDING' | 'VERIFIED' | 'REJECTED'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 6. Orders Table (for Campus Flash delivery orders)
CREATE TABLE IF NOT EXISTS orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    order_id TEXT NOT NULL,
    product_details JSONB NOT NULL,
    total_amt NUMERIC NOT NULL,
    payment_status TEXT DEFAULT 'PAY ON DELIVERY',
    delivery_address TEXT NOT NULL,
    delivery_status TEXT DEFAULT 'PENDING', -- 'PENDING' | 'ASSIGNED' | 'PICKED_UP' | 'DELIVERED'
    rider_id UUID REFERENCES riders(id) ON DELETE SET NULL,
    delivery_otp VARCHAR(6),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 7. Canteen Tokens Table (outlet-scoped, sequential token numbers)
CREATE TABLE IF NOT EXISTS canteen_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    token_number INTEGER NOT NULL,
    outlet_category_id UUID REFERENCES categories(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    product_details JSONB NOT NULL,    -- Snapshot: [{name, price, quantity, image}]
    total_amt NUMERIC NOT NULL DEFAULT 0,
    status TEXT DEFAULT 'ACTIVE',      -- 'ACTIVE' | 'DONE' | 'CANCELLED'
    notify_batch INTEGER DEFAULT 0,    -- Which notify-next-10 batch window this belongs to
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_canteen_tokens_outlet ON canteen_tokens(outlet_category_id);
CREATE INDEX IF NOT EXISTS idx_canteen_tokens_status ON canteen_tokens(status);
CREATE INDEX IF NOT EXISTS idx_canteen_tokens_number ON canteen_tokens(token_number);
CREATE INDEX IF NOT EXISTS idx_products_section ON products(section);
CREATE INDEX IF NOT EXISTS idx_categories_section ON categories(section);
CREATE INDEX IF NOT EXISTS idx_canteen_cart_user ON canteen_cart_items(user_id);

-- Disable Row Level Security (RLS) for all tables
ALTER TABLE users DISABLE ROW LEVEL SECURITY;
ALTER TABLE categories DISABLE ROW LEVEL SECURITY;
ALTER TABLE products DISABLE ROW LEVEL SECURITY;
ALTER TABLE cart_items DISABLE ROW LEVEL SECURITY;
ALTER TABLE canteen_cart_items DISABLE ROW LEVEL SECURITY;
ALTER TABLE addresses DISABLE ROW LEVEL SECURITY;
ALTER TABLE orders DISABLE ROW LEVEL SECURITY;
ALTER TABLE canteen_tokens DISABLE ROW LEVEL SECURITY;

-- Enable public uploads/selects on the 'grocery-images' Supabase Storage Bucket
CREATE POLICY IF NOT EXISTS "Allow public select from grocery-images" 
ON storage.objects FOR SELECT 
TO public 
USING (bucket_id = 'grocery-images');

CREATE POLICY IF NOT EXISTS "Allow public insert to grocery-images" 
ON storage.objects FOR INSERT 
TO public 
WITH CHECK (bucket_id = 'grocery-images');

CREATE POLICY IF NOT EXISTS "Allow public update to grocery-images" 
ON storage.objects FOR UPDATE 
TO public 
USING (bucket_id = 'grocery-images')
WITH CHECK (bucket_id = 'grocery-images');

-- =======================================================
-- MIGRATION: Run these if you already have an existing DB
-- =======================================================
-- ALTER TABLE categories ADD COLUMN IF NOT EXISTS section TEXT DEFAULT 'flash';
-- ALTER TABLE products ADD COLUMN IF NOT EXISTS section TEXT DEFAULT 'flash';
-- ALTER TABLE products ADD COLUMN IF NOT EXISTS food_type TEXT DEFAULT NULL;
-- ALTER TABLE products ADD COLUMN IF NOT EXISTS prep_time TEXT DEFAULT '8 mins';
-- ALTER TABLE users ADD COLUMN IF NOT EXISTS outlet_category_id UUID DEFAULT NULL;
-- ALTER TABLE orders ADD COLUMN IF NOT EXISTS delivery_status TEXT DEFAULT 'PENDING';
-- ALTER TABLE orders ADD COLUMN IF NOT EXISTS rider_id UUID REFERENCES riders(id) ON DELETE SET NULL;
-- ALTER TABLE orders ADD COLUMN IF NOT EXISTS store_name TEXT DEFAULT '';
-- ALTER TABLE orders ADD COLUMN IF NOT EXISTS store_address TEXT DEFAULT '';
-- ALTER TABLE categories ADD COLUMN IF NOT EXISTS notify_offset INTEGER DEFAULT 0;
-- ALTER TABLE categories ADD COLUMN IF NOT EXISTS notify_rev INTEGER DEFAULT 0;

-- =======================================================
-- MIGRATION: RIDER MODULE
-- =======================================================
CREATE TABLE IF NOT EXISTS riders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    phone TEXT NOT NULL,
    roll_number TEXT,
    campus_id_url TEXT NOT NULL,
    status TEXT DEFAULT 'PENDING',  -- 'PENDING' | 'VERIFIED' | 'REJECTED'
    is_online BOOLEAN DEFAULT false,
    earnings NUMERIC DEFAULT 0,
    declined_orders INT DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

ALTER TABLE riders DISABLE ROW LEVEL SECURITY;

-- =======================================================
-- MIGRATION: ID-CARD BUCKET POLICIES (Run in SQL Editor)
-- =======================================================
-- Note: Make sure the 'id-card' bucket exists before running these
CREATE POLICY "Allow public select from id-card" 
ON storage.objects FOR SELECT 
TO public 
USING (bucket_id = 'id-card');

CREATE POLICY "Allow public insert to id-card" 
ON storage.objects FOR INSERT 
TO public 
WITH CHECK (bucket_id = 'id-card');

CREATE POLICY "Allow public update to id-card" 
ON storage.objects FOR UPDATE 
TO public 
USING (bucket_id = 'id-card')
WITH CHECK (bucket_id = 'id-card');

CREATE POLICY "Allow public delete from id-card" 
ON storage.objects FOR DELETE 
TO public 
USING (bucket_id = 'id-card');

-- =======================================================
-- MIGRATION: PRINTOUT BUCKET POLICIES (Run in SQL Editor)
-- =======================================================
-- Note: Make sure the 'printout' bucket exists before running these
CREATE POLICY "Allow public select from printout" 
ON storage.objects FOR SELECT 
TO public 
USING (bucket_id = 'printout');

CREATE POLICY "Allow public insert to printout" 
ON storage.objects FOR INSERT 
TO public 
WITH CHECK (bucket_id = 'printout');

CREATE POLICY "Allow public update to printout" 
ON storage.objects FOR UPDATE 
TO public 
USING (bucket_id = 'printout')
WITH CHECK (bucket_id = 'printout');

CREATE POLICY "Allow public delete from printout" 
ON storage.objects FOR DELETE 
TO public 
USING (bucket_id = 'printout');
-- =======================================================
-- MIGRATION: OTP CODES TABLE FOR PASSWORD RESETS
-- =======================================================
CREATE TABLE IF NOT EXISTS otp_codes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT NOT NULL,
    otp_code TEXT NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_otp_codes_email ON otp_codes(email);
ALTER TABLE otp_codes DISABLE ROW LEVEL SECURITY;

-- =======================================================
-- MIGRATION: PRINTING SYSTEM (PRINT_ORDERS & BUCKET POLICIES)
-- =======================================================
-- Role support: 'USER' | 'ADMIN' | 'CANTEEN_OP' | 'PRINT_OP'

CREATE TABLE IF NOT EXISTS print_orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id TEXT NOT NULL,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    file_url TEXT NOT NULL,
    file_name TEXT NOT NULL,
    file_size_mb NUMERIC DEFAULT 0,
    print_type TEXT NOT NULL DEFAULT 'BW',  -- 'BW' (₹2/page) or 'COLOR' (₹5/page)
    pages_count INTEGER NOT NULL DEFAULT 1,
    copies INTEGER NOT NULL DEFAULT 1,
    instructions TEXT DEFAULT '',
    total_amt NUMERIC NOT NULL DEFAULT 0,
    payment_status TEXT DEFAULT 'PAID',
    delivery_address TEXT NOT NULL,
    delivery_status TEXT DEFAULT 'PENDING',  -- 'PENDING' | 'PRINTING' | 'READY_FOR_RIDER' | 'PICKED_UP' | 'DELIVERED' | 'COMPLETED'
    delivery_otp VARCHAR(6),
    rider_id UUID REFERENCES riders(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_print_orders_user ON print_orders(user_id);
CREATE INDEX IF NOT EXISTS idx_print_orders_status ON print_orders(delivery_status);
ALTER TABLE print_orders DISABLE ROW LEVEL SECURITY;

-- Storage Policies for 'printout' bucket
CREATE POLICY IF NOT EXISTS "Allow public select from printout" 
ON storage.objects FOR SELECT 
TO public 
USING (bucket_id = 'printout');

CREATE POLICY IF NOT EXISTS "Allow public insert to printout" 
ON storage.objects FOR INSERT 
TO public 
WITH CHECK (bucket_id = 'printout');

CREATE POLICY IF NOT EXISTS "Allow public update to printout" 
ON storage.objects FOR UPDATE 
TO public 
USING (bucket_id = 'printout')
WITH CHECK (bucket_id = 'printout');

CREATE POLICY IF NOT EXISTS "Allow public delete from printout" 
ON storage.objects FOR DELETE 
TO public 
USING (bucket_id = 'printout');

-- =======================================================
-- MIGRATION: FLIGHT PRICE HISTORY (FLIGHTS MODULE)
-- =======================================================
CREATE TABLE IF NOT EXISTS flight_price_history (
  id BIGSERIAL PRIMARY KEY,
  flight_number TEXT NOT NULL,
  airline TEXT,
  departure_id TEXT NOT NULL,
  arrival_id TEXT NOT NULL,

  -- TWO date columns — this is the key architectural decision:
  departure_date DATE NOT NULL,        -- When THIS SPECIFIC flight departs (e.g. Sep 30, Aug 30, Jul 30)
  recorded_date  DATE NOT NULL,        -- When the price was OBSERVED (e.g. Sep 10 = 20 days before Sep 30)
  days_before_departure INT,           -- departure_date - recorded_date (for trend comparison across months)

  price INTEGER NOT NULL,
  seats_available BOOLEAN DEFAULT TRUE,
  source TEXT DEFAULT 'recorded',      -- 'recorded' = generated baseline, 'api' = live from SearchAPI
  created_at TIMESTAMPTZ DEFAULT NOW(),

  -- Prevents: same observation for same flight on same departure date being stored twice
  -- But ALLOWS: flight 6E 2222 on Sep 30 AND flight 6E 2222 on Aug 30 as separate rows
  UNIQUE (flight_number, departure_id, arrival_id, departure_date, recorded_date)
);

-- Efficient lookup: all departure months of the same flight on a route
CREATE INDEX IF NOT EXISTS idx_fph_flight_dep ON flight_price_history
  (departure_id, arrival_id, flight_number, departure_date, recorded_date);

-- Disable RLS so backend can read/write freely
ALTER TABLE flight_price_history DISABLE ROW LEVEL SECURITY;
