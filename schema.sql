-- VulnerableShop Enhanced Database Schema
-- PostgreSQL Database for Deliberately Vulnerable E-commerce Application
-- Version 2.0 - WITH 100+ PRODUCTS AND NEW FEATURES

-- Drop existing tables if they exist
DROP TABLE IF EXISTS order_items CASCADE;
DROP TABLE IF EXISTS orders CASCADE;
DROP TABLE IF EXISTS reviews CASCADE;
DROP TABLE IF EXISTS wishlist CASCADE;
DROP TABLE IF EXISTS favorites CASCADE;
DROP TABLE IF EXISTS cart_items CASCADE;
DROP TABLE IF EXISTS coupons CASCADE;
DROP TABLE IF EXISTS addresses CASCADE;
DROP TABLE IF EXISTS sessions CASCADE;
DROP TABLE IF EXISTS admin_logs CASCADE;
DROP TABLE IF EXISTS product_questions CASCADE;
DROP TABLE IF EXISTS messages CASCADE;
DROP TABLE IF EXISTS products CASCADE;
DROP TABLE IF EXISTS categories CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS flags CASCADE;

-- Users Table (with bio field for HTML Injection)
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    display_name VARCHAR(100),
    bio TEXT, -- INSECURE: For HTML injection vulnerability
    is_admin BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    balance DECIMAL(10, 2) DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    reset_token VARCHAR(100),
    reset_token_expiry TIMESTAMP
);

-- Categories Table (expanded to 12 categories)
CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    image_url VARCHAR(255)
);

-- Products Table
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    price DECIMAL(10, 2) NOT NULL,
    cost DECIMAL(10, 2) NOT NULL, -- INSECURE: Internal cost exposed via API
    stock INTEGER DEFAULT 0,
    category_id INTEGER REFERENCES categories(id),
    image_url VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Reviews Table (for Stored XSS and File Upload vulnerabilities)
CREATE TABLE reviews (
    id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    comment TEXT, -- INSECURE: Rendered without sanitization
    file_attachment VARCHAR(255), -- INSECURE: No file type validation, XSS via SVG/HTML
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Shopping Cart
CREATE TABLE cart_items (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
    quantity INTEGER DEFAULT 1,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, product_id)
);

-- Wishlist / Favorites
CREATE TABLE favorites (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, product_id)
);

-- Wishlist Table (separate from favorites)
CREATE TABLE wishlist (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, product_id)
);

-- Product Questions & Answers (for Stored XSS)
CREATE TABLE product_questions (
    id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    question TEXT NOT NULL, -- INSECURE: XSS vulnerability
    answer TEXT, -- INSECURE: XSS vulnerability
    answered_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    answered_at TIMESTAMP
);

-- User Messages (for IDOR and Stored XSS)
CREATE TABLE messages (
    id SERIAL PRIMARY KEY,
    sender_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    recipient_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    subject VARCHAR(200),
    message TEXT, -- INSECURE: XSS vulnerability
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Addresses
CREATE TABLE addresses (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    full_name VARCHAR(100),
    address_line1 VARCHAR(200),
    address_line2 VARCHAR(200),
    city VARCHAR(100),
    state VARCHAR(100),
    postal_code VARCHAR(20),
    country VARCHAR(100),
    phone VARCHAR(20),
    is_default BOOLEAN DEFAULT FALSE
);

-- Orders
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    order_number VARCHAR(50) UNIQUE NOT NULL,
    total_amount DECIMAL(10, 2) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    shipping_address_id INTEGER REFERENCES addresses(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Order Items
CREATE TABLE order_items (
    id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(id) ON DELETE CASCADE,
    product_id INTEGER REFERENCES products(id),
    product_name VARCHAR(200),
    quantity INTEGER NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    subtotal DECIMAL(10, 2) NOT NULL
);

-- Coupons
CREATE TABLE coupons (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    discount_type VARCHAR(20) CHECK (discount_type IN ('percentage', 'fixed')),
    discount_value DECIMAL(10, 2) NOT NULL,
    min_purchase DECIMAL(10, 2) DEFAULT 0.00,
    max_uses INTEGER DEFAULT NULL,
    times_used INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Sessions Table (for insecure session handling)
CREATE TABLE sessions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) UNIQUE NOT NULL,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
   data TEXT, -- INSECURE: Serialized session data (pickle vulnerability)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL
);

-- Admin Logs
CREATE TABLE admin_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    action VARCHAR(100),
    details TEXT,
    ip_address VARCHAR(45),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Flags Table (CTF challenges) - EXPANDED
CREATE TABLE flags (
    id SERIAL PRIMARY KEY,
    flag_name VARCHAR(100) UNIQUE NOT NULL,
    flag_value TEXT NOT NULL,
    description TEXT,
    difficulty VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create Indexes for better performance
CREATE INDEX idx_products_category ON products(category_id);
CREATE INDEX idx_reviews_product ON reviews(product_id);
CREATE INDEX idx_orders_user ON orders(user_id);
CREATE INDEX idx_cart_user ON cart_items(user_id);
CREATE INDEX idx_favorites_user ON favorites(user_id);
CREATE INDEX idx_wishlist_user ON wishlist(user_id);
CREATE INDEX idx_messages_recipient ON messages(recipient_id);
CREATE INDEX idx_messages_sender ON messages(sender_id);
CREATE INDEX idx_questions_product ON product_questions(product_id);
CREATE INDEX idx_sessions_session_id ON sessions(session_id);
CREATE INDEX idx_sessions_user_id ON sessions(user_id);

-- Insert default admin user
-- Password: admin
INSERT INTO users (username, email, password_hash, display_name, is_admin, balance) VALUES
('admin', 'admin@vulnerableshop.local', '$2b$12$7Fq.YBR/zxA.bzL0jv/3g.CWZmFbQh/Z.jzHPBgS7wCOVOcVm2qKi', 'Administrator', TRUE, 10000.00);

-- Insert regular test users (20 users for IDOR testing)
-- Password: password (for all users)
INSERT INTO users (username, email, password_hash, display_name, balance) VALUES
('alice', 'alice@test.local', '$2b$12$IHOUYQzWTraXa5HJuP8XWu6Wdn.VG8OUK7hxyjzQM6czTKI4DFyTa', 'Alice Johnson', 500.00),
('bob', 'bob@test.local', '$2b$12$IHOUYQzWTraXa5HJuP8XWu6Wdn.VG8OUK7hxyjzQM6czTKI4DFyTa', 'Bob Smith', 250.00),
('charlie', 'charlie@test.local', '$2b$12$IHOUYQzWTraXa5HJuP8XWu6Wdn.VG8OUK7hxyjzQM6czTKI4DFyTa', 'Charlie Brown', 100.00),
('david', 'david@test.local', '$2b$12$IHOUYQzWTraXa5HJuP8XWu6Wdn.VG8OUK7hxyjzQM6czTKI4DFyTa', 'David Wilson', 350.00),
('eve', 'eve@test.local', '$2b$12$IHOUYQzWTraXa5HJuP8XWu6Wdn.VG8OUK7hxyjzQM6czTKI4DFyTa', 'Eve Martinez', 450.00),
('frank', 'frank@test.local', '$2b$12$IHOUYQzWTraXa5HJuP8XWu6Wdn.VG8OUK7hxyjzQM6czTKI4DFyTa', 'Frank Anderson', 600.00),
('grace', 'grace@test.local', '$2b$12$IHOUYQzWTraXa5HJuP8XWu6Wdn.VG8OUK7hxyjzQM6czTKI4DFyTa', 'Grace Lee', 280.00),
('henry', 'henry@test.local', '$2b$12$IHOUYQzWTraXa5HJuP8XWu6Wdn.VG8OUK7hxyjzQM6czTKI4DFyTa', 'Henry Taylor', 520.00),
('iris', 'iris@test.local', '$2b$12$IHOUYQzWTraXa5HJuP8XWu6Wdn.VG8OUK7hxyjzQM6czTKI4DFyTa', 'Iris Chen', 390.00),
('jack', 'jack@test.local', '$2b$12$IHOUYQzWTraXa5HJuP8XWu6Wdn.VG8OUK7hxyjzQM6czTKI4DFyTa', 'Jack Robinson', 410.00),
('kate', 'kate@test.local', '$2b$12$IHOUYQzWTraXa5HJuP8XWu6Wdn.VG8OUK7hxyjzQM6czTKI4DFyTa', 'Kate Miller', 320.00),
('leo', 'leo@test.local', '$2b$12$IHOUYQzWTraXa5HJuP8XWu6Wdn.VG8OUK7hxyjzQM6czTKI4DFyTa', 'Leo Davis', 480.00),
('mia', 'mia@test.local', '$2b$12$IHOUYQzWTraXa5HJuP8XWu6Wdn.VG8OUK7hxyjzQM6czTKI4DFyTa', 'Mia Garcia', 290.00),
('noah', 'noah@test.local', '$2b$12$IHOUYQzWTraXa5HJuP8XWu6Wdn.VG8OUK7hxyjzQM6czTKI4DFyTa', 'Noah Rodriguez', 550.00),
('olivia', 'olivia@test.local', '$2b$12$IHOUYQzWTraXa5HJuP8XWu6Wdn.VG8OUK7hxyjzQM6czTKI4DFyTa', 'Olivia Martinez', 370.00),
('peter', 'peter@test.local', '$2b$12$IHOUYQzWTraXa5HJuP8XWu6Wdn.VG8OUK7hxyjzQM6czTKI4DFyTa', 'Peter Hernandez', 420.00),
('quinn', 'quinn@test.local', '$2b$12$IHOUYQzWTraXa5HJuP8XWu6Wdn.VG8OUK7hxyjzQM6czTKI4DFyTa', 'Quinn Lopez', 310.00),
('ryan', 'ryan@test.local', '$2b$12$IHOUYQzWTraXa5HJuP8XWu6Wdn.VG8OUK7hxyjzQM6czTKI4DFyTa', 'Ryan Gonzalez', 460.00),
('sophia', 'sophia@test.local', '$2b$12$IHOUYQzWTraXa5HJuP8XWu6Wdn.VG8OUK7hxyjzQM6czTKI4DFyTa', 'Sophia Wilson', 340.00),
('tyler', 'tyler@test.local', '$2b$12$IHOUYQzWTraXa5HJuP8XWu6Wdn.VG8OUK7hxyjzQM6czTKI4DFyTa', 'Tyler Anderson', 490.00);

-- Insert 12 Categories (expanded from 6)
INSERT INTO categories (name, description, image_url) VALUES
('Electronics', 'Latest gadgets and electronics', '/static/images/categories/category1.jpg'),
('Clothing', 'Fashion and apparel', '/static/images/categories/category2.jpg'),
('Books', 'Books and literature', '/static/images/categories/category3.jpg'),
('Home & Garden', 'Home improvement and gardening', '/static/images/categories/category4.jpg'),
('Sports & Outdoors', 'Sports equipment and outdoor gear', '/static/images/categories/category5.jpg'),
('Toys & Games', 'Toys and games for all ages', '/static/images/categories/category6.jpg'),
('Food & Groceries', 'Food and grocery items', '/static/images/categories/category7.jpg'),
('Beauty & Health', 'Beauty products and health items', '/static/images/categories/category8.jpg'),
('Automotive', 'Car parts and accessories', '/static/images/categories/category9.jpg'),
('Office Supplies', 'Office and stationery items', '/static/images/categories/category10.jpg'),
('Pet Supplies', 'Pet food and accessories', '/static/images/categories/category11.jpg'),
('Music & Instruments', 'Musical instruments and equipment', '/static/images/categories/category12.jpg');

-- Insert 100+ Products (expanded from 50)
INSERT INTO products (name, description, price, cost, stock, category_id, image_url) VALUES
-- Electronics (Category 1) - 20 products
('Smartphone Pro X', 'Latest flagship smartphone with AI features', 999.99, 450.00, 50, 1, '/static/images/products/product1.jpg'),
('Wireless Earbuds Elite', 'Premium noise-canceling earbuds', 199.99, 80.00, 100, 1, '/static/images/products/product2.jpg'),
('4K Smart TV 55"', 'Ultra HD smart television', 799.99, 400.00, 25, 1, '/static/images/products/product3.jpg'),
('Gaming Laptop Ultra', 'High-performance gaming laptop', 1499.99, 900.00, 15, 1, '/static/images/products/product4.jpg'),
('Smartwatch Series 5', 'Fitness and health tracking smartwatch', 349.99, 150.00, 75, 1, '/static/images/products/product5.jpg'),
('Bluetooth Speaker Max', 'Portable waterproof speaker', 89.99, 35.00, 200, 1, '/static/images/products/product6.jpg'),
('Wireless Mouse Pro', 'Ergonomic wireless mouse', 49.99, 18.00, 150, 1, '/static/images/products/product7.jpg'),
('USB-C Hub Adapter', '7-in-1 USB-C hub', 39.99, 12.00, 300, 1, '/static/images/products/product8.jpg'),
('External SSD 1TB', 'Portable solid state drive', 129.99, 60.00, 80, 1, '/static/images/products/product9.jpg'),
('Webcam HD Pro', '1080p webcam with microphone', 79.99, 30.00, 120, 1, '/static/images/products/product10.jpg'),
('Headphones Studio', 'Professional studio headphones', 249.99, 100.00, 45, 1, '/static/images/products/product11.jpg'),
('Tablet 10 inch', 'Lightweight tablet with stylus', 399.99, 180.00, 50, 1, '/static/images/products/product12.jpg'),
('Mechanical Keyboard RGB', 'Gaming mechanical keyboard', 129.99, 50.00, 90, 1, '/static/images/products/product13.jpg'),
('Portable Charger 20000mAh', 'Fast charging power bank', 59.99, 20.00, 200, 1, '/static/images/products/product14.jpg'),
('Smart Home Hub', 'Voice-controlled smart hub', 99.99, 40.00, 60, 1, '/static/images/products/product15.jpg'),
('Drone 4K Camera', 'Quadcopter with 4K camera', 599.99, 280.00, 20, 1, '/static/images/products/product16.jpg'),
('Security Camera Wi-Fi', 'Indoor security camera', 79.99, 30.00, 110, 1, '/static/images/products/product17.jpg'),
('E-Reader 6 inch', 'Digital book reader', 149.99, 70.00, 70, 1, '/static/images/products/product18.jpg'),
('VR Headset', 'Virtual reality headset', 399.99, 180.00, 35, 1, '/static/images/products/product19.jpg'),
('Digital Photo Frame', '10 inch Wi-Fi photo frame', 89.99, 35.00, 80, 1, '/static/images/products/product20.jpg'),

-- Clothing (Category 2) - 15 products
('Premium Cotton T-Shirt', 'Comfortable 100% cotton t-shirt', 24.99, 8.00, 500, 2, '/static/images/products/product21.jpg'),
('Denim Jeans Classic', 'Classic fit denim jeans', 59.99, 25.00, 200, 2, '/static/images/products/product22.jpg'),
('Winter Jacket Warm', 'Insulated winter jacket', 129.99, 50.00, 80, 2, '/static/images/products/product23.jpg'),
('Running Shoes Sport', 'Lightweight running shoes', 89.99, 35.00, 150, 2, '/static/images/products/product24.jpg'),
('Leather Wallet Premium', 'Genuine leather wallet', 39.99, 12.00, 300, 2, '/static/images/products/product25.jpg'),
('Sunglasses Aviator', 'UV protection sunglasses', 79.99, 25.00, 100, 2, '/static/images/products/product26.jpg'),
('Baseball Cap Classic', 'Adjustable baseball cap', 19.99, 6.00, 400, 2, '/static/images/products/product27.jpg'),
('Backpack Travel', 'Durable travel backpack', 69.99, 28.00, 120, 2, '/static/images/products/product28.jpg'),
('Hoodie Comfort', 'Warm fleece hoodie', 49.99, 18.00, 180, 2, '/static/images/products/product29.jpg'),
('Dress Shirt Formal', 'Professional dress shirt', 44.99, 15.00, 140, 2, '/static/images/products/product30.jpg'),
('Yoga Pants Premium', 'Stretchy yoga pants', 39.99, 12.00, 220, 2, '/static/images/products/product31.jpg'),
('Leather Belt Classic', 'Genuine leather belt', 29.99, 10.00, 180, 2, '/static/images/products/product32.jpg'),
('Socks Pack (6 pairs)', 'Cotton blend socks', 14.99, 5.00, 500, 2, '/static/images/products/product33.jpg'),
('Sneakers Casual', 'Comfortable casual sneakers', 69.99, 28.00, 160, 2, '/static/images/products/product34.jpg'),
('Scarf Wool', 'Warm wool scarf', 34.99, 12.00, 90, 2, '/static/images/products/product35.jpg'),

-- Books (Category 3) - 10 products
('Programming in Python', 'Comprehensive Python guide', 49.99, 15.00, 100, 3, '/static/images/products/product36.jpg'),
('Web Security Handbook', 'Security best practices', 59.99, 20.00, 75, 3, '/static/images/products/product37.jpg'),
('The Art of Code', 'Clean code principles', 44.99, 15.00, 90, 3, '/static/images/products/product38.jpg'),
('Database Design Pro', 'Database architecture and design', 54.99, 18.00, 60, 3, '/static/images/products/product39.jpg'),
('Machine Learning Basics', 'Introduction to ML', 64.99, 22.00, 80, 3, '/static/images/products/product40.jpg'),
('Cookbook Gourmet', 'Professional recipes', 34.99, 12.00, 90, 3, '/static/images/products/product41.jpg'),
('Mystery Novel Bestseller', 'Thrilling mystery novel', 19.99, 6.00, 200, 3, '/static/images/products/product42.jpg'),
('Business Strategy Guide', 'Modern business strategies', 39.99, 13.00, 70, 3, '/static/images/products/product43.jpg'),
('Photography Masterclass', 'Professional photography techniques', 49.99, 16.00, 55, 3, '/static/images/products/product44.jpg'),
('Science Fiction Epic', 'Epic sci-fi series', 29.99, 10.00, 120, 3, '/static/images/products/product45.jpg'),

-- Home & Garden (Category 4) - 15 products
('Coffee Maker Deluxe', 'Programm able coffee maker', 79.99, 35.00, 60, 4, '/static/images/products/product46.jpg'),
('Blender Pro 1000W', 'High-power blender', 99.99, 40.00, 50, 4, '/static/images/products/product47.jpg'),
('Air Purifier Smart', 'HEPA air purifier', 199.99, 90.00, 40, 4, '/static/images/products/product48.jpg'),
('LED Desk Lamp', 'Adjustable LED lamp', 34.99, 12.00, 150, 4, '/static/images/products/product49.jpg'),
('Plant Pot Set (3pc)', 'Ceramic plant pots', 29.99, 10.00, 200, 4, '/static/images/products/product50.jpg'),
('Garden Tool Set', 'Essential gardening tools', 49.99, 20.00, 80, 4, '/static/images/products/product51.jpg'),
('Vacuum Cleaner Robot', 'Smart robot vacuum', 299.99, 150.00, 30, 4, '/static/images/products/product52.jpg'),
('Toaster 4-Slice', 'Stainless steel toaster', 59.99, 25.00, 70, 4, '/static/images/products/product53.jpg'),
('Microwave Oven 1000W', 'Compact microwave oven', 149.99, 70.00, 45, 4, '/static/images/products/product54.jpg'),
('Bed Sheets Queen Size', 'Soft cotton bed sheets', 49.99, 18.00, 100, 4, '/static/images/products/product55.jpg'),
('Curtains Blackout', 'Room darkening curtains', 44.99, 15.00, 85, 4, '/static/images/products/product56.jpg'),
('Shower Curtain Set', 'Waterproof shower curtain with hooks', 24.99, 8.00, 130, 4, '/static/images/products/product57.jpg'),
('Kitchen Knife Set', 'Professional knife set with block', 89.99, 35.00, 55, 4, '/static/images/products/product58.jpg'),
('Pillow Memory Foam', 'Ergonomic memory foam pillow', 39.99, 14.00, 110, 4, '/static/images/products/product59.jpg'),
('Wall Clock Modern', 'Silent wall clock', 29.99, 10.00, 150, 4, '/static/images/products/product60.jpg'),

-- Sports & Outdoors (Category 5) - 12 products
('Yoga Mat Premium', 'Non-slip yoga mat', 34.99, 12.00, 200, 5, '/static/images/products/product61.jpg'),
('Dumbbell Set 20kg', 'Adjustable dumbbell set', 89.99, 40.00, 60, 5, '/static/images/products/product62.jpg'),
('Tennis Racket Pro', 'Professional tennis racket', 149.99, 60.00, 40, 5, '/static/images/products/product63.jpg'),
('Basketball Official', 'Official size basketball', 29.99, 10.00, 150, 5, '/static/images/products/product64.jpg'),
('Bicycle Mountain', '21-speed mountain bike', 499.99, 250.00, 20, 5, '/static/images/products/product6.jpg'),
('Swimming Goggles', 'Anti-fog swimming goggles', 19.99, 6.00, 300, 5, '/static/images/products/product66.jpg'),
('Resistance Bands Set', 'Exercise resistance bands', 24.99, 8.00, 180, 5, '/static/images/products/product67.jpg'),
('Camping Tent 4-Person', 'Waterproof camping tent', 149.99, 65.00, 35, 5, '/static/images/products/product68.jpg'),
('Hiking Backpack 50L', 'Large capacity hiking backpack', 89.99, 38.00, 55, 5, '/static/images/products/product69.jpg'),
('Fishing Rod Combo', 'Fishing rod and reel combo', 79.99, 32.00, 45, 5, '/static/images/products/product70.jpg'),
('Soccer Ball FIFA', 'Official size soccer ball', 34.99, 12.00, 120, 5, '/static/images/products/product71.jpg'),
('Jump Rope Speed', 'Adjustable speed jump rope', 14.99, 5.00, 250, 5, '/static/images/products/product72.jpg'),

-- Toys & Games (Category 6) - 10 products
('Building Blocks Set', '500-piece building set', 39.99, 15.00, 100, 6, '/static/images/products/product73.jpg'),
('Remote Control Car', 'Fast RC car', 59.99, 25.00, 80, 6, '/static/images/products/product74.jpg'),
('Puzzle 1000 Pieces', 'Challenging jigsaw puzzle', 24.99, 8.00, 150, 6, '/static/images/products/product75.jpg'),
('Board Game Strategy', 'Family strategy game', 44.99, 18.00, 70, 6, '/static/images/products/product76.jpg'),
('Action Figure Hero', 'Collectible action figure', 29.99, 10.00, 200, 6, '/static/images/products/product77.jpg'),
('Plush Teddy Bear', 'Soft plush teddy bear', 19.99, 6.00, 250, 6, '/static/images/products/product78.jpg'),
('Chess Set Wooden', 'Handcrafted chess set', 79.99, 30.00, 50, 6, '/static/images/products/product79.jpg'),
('Playing Cards Premium', 'Waterproof playing cards', 12.99, 4.00, 300, 6, '/static/images/products/product80.jpg'),
('Model Train Set', 'Electric model train', 149.99, 60.00, 25, 6, '/static/images/products/product81.jpg'),
('Dollhouse Victorian', 'Detailed wooden dollhouse', 199.99, 90.00, 15, 6, '/static/images/products/product82.jpg'),

-- Food & Groceries (Category 7) - 8 products
('Organic Coffee Beans 1kg', 'Premium organic coffee', 24.99, 10.00, 150, 7, '/static/images/products/product83.jpg'),
('Green Tea Set', 'Assorted green teas', 19.99, 7.00, 200, 7, '/static/images/products/product84.jpg'),
('Protein Powder 2kg', 'Whey protein supplement', 49.99, 20.00, 100, 7, '/static/images/products/product85.jpg'),
('Energy Bars Box (12pc)', 'Nutrition energy bars', 29.99, 12.00, 180, 7, '/static/images/products/product86.jpg'),
('Organic Honey 500g', 'Pure organic honey', 14.99, 6.00, 220, 7, '/static/images/products/product87.jpg'),
('Mixed Nuts Snack Pack', 'Roasted mixed nuts', 19.99, 8.00, 160, 7, '/static/images/products/product88.jpg'),
('Olive Oil Extra Virgin', 'Premium olive oil', 24.99, 10.00, 130, 7, '/static/images/products/product89.jpg'),
('Pasta Set Artisan', 'Gourmet pasta collection', 34.99, 14.00, 90, 7, '/static/images/products/product90.jpg'),

-- Beauty & Health (Category 8) - 8 products
('Skincare Set Premium', 'Complete skincare routine', 89.99, 35.00, 70, 8, '/static/images/products/product91.jpg'),
('Electric Toothbrush', 'Rechargeable toothbrush', 59.99, 25.00, 100, 8, '/static/images/products/product92.jpg'),
('Hair Dryer Professional', 'Ionic hair dryer', 69.99, 28.00, 60, 8, '/static/images/products/product93.jpg'),
('Massage Gun Deep Tissue', 'Percussion massage device', 99.99, 42.00, 45, 8, '/static/images/products/product94.jpg'),
('Essential Oils Set', 'Aromatherapy oil collection', 39.99, 15.00, 110, 8, '/static/images/products/product95.jpg'),
('Face Mask Collagen', 'Hydrating face masks (10pc)', 24.99, 9.00, 140, 8, '/static/images/products/product96.jpg'),
('Perfume Luxury 100ml', 'Designer fragrance', 149.99, 60.00, 35, 8, '/static/images/products/product97.jpg'),
('Vitamins Multivitamin', '90-day supply multivitamins', 29.99, 12.00, 180, 8, '/static/images/products/product98.jpg'),

-- Automotive (Category 9) - 6 products
('Car Phone Holder', 'Magnetic phone mount', 19.99, 7.00, 250, 9, '/static/images/products/product99.jpg'),
('Dash Cam HD', '1080p dashboard camera', 79.99, 32.00, 80, 9, '/static/images/products/product100.jpg'),
('Car Vacuum Portable', 'Handheld car vacuum', 44.99, 18.00, 110, 9, '/static/images/products/product101.jpg'),
('Tire Pressure Gauge', 'Digital tire pressure monitor', 24.99, 9.00, 160, 9, '/static/images/products/product102.jpg'),
('Jump Starter Kit', 'Emergency jump starter pack', 89.99, 38.00, 55, 9, '/static/images/products/product103.jpg'),
('Car Air Freshener Set', 'Long-lasting air fresheners', 14.99, 5.00, 300, 9, '/static/images/products/product104.jpg'),

-- Office Supplies (Category 10) - 6 products
('Desk Organizer Bamboo', 'Bamboo desk storage', 34.99, 14.00, 120, 10, '/static/images/products/product105.jpg'),
('Notebook Leather Bound', 'Professional notebook', 29.99, 11.00, 150, 10, '/static/images/products/product106.jpg'),
('Pen Set Executive', 'Luxury pen collection', 49.99, 20.00, 80, 10, '/static/images/products/product107.jpg'),
('Paper Shredder Cross-Cut', 'Security paper shredder', 79.99, 35.00, 45, 10, '/static/images/products/product108.jpg'),
('Label Maker Portable', 'Handheld label printer', 39.99, 16.00, 90, 10, '/static/images/products/product109.jpg'),
('Stapler Heavy Duty', 'Professional stapler', 19.99, 7.00, 200, 10, '/static/images/products/product110.jpg'),

-- Pet Supplies (Category 11) - 5 products
('Dog Food Premium 10kg', 'High-quality dog food', 59.99, 25.00, 70, 11, '/static/images/products/product111.jpg'),
('Cat Litter Box Auto', 'Self-cleaning litter box', 199.99, 90.00, 25, 11, '/static/images/products/product112.jpg'),
('Pet Carrier Travel', 'Airline-approved pet carrier', 49.99, 20.00, 60, 11, '/static/images/products/product113.jpg'),
('Dog Leash Retractable', 'Automatic retractable leash', 24.99, 10.00, 140, 11, '/static/images/products/product114.jpg'),
('Cat Toys Set', 'Interactive cat toy collection', 19.99, 7.00, 180, 11, '/static/images/products/product115.jpg'),

-- Music & Instruments (Category 12) - 5 products
('Acoustic Guitar Beginner', 'Full-size acoustic guitar', 199.99, 90.00, 30, 12, '/static/images/products/product116.jpg'),
('Digital Piano 88 Keys', 'Weighted key digital piano', 599.99, 280.00, 15, 12, '/static/images/products/product117.jpg'),
('Microphone USB Studio', 'Professional USB microphone', 89.99, 38.00, 50, 12, '/static/images/products/product118.jpg'),
('Ukulele Soprano', 'Beginner ukulele', 49.99, 20.00, 70, 12, '/static/images/products/product119.jpg'),
('Music Stand Adjustable', 'Professional music stand', 29.99, 12.00, 100, 12, '/static/images/products/product120.jpg');

-- Insert Coupons
INSERT INTO coupons (code, discount_type, discount_value, min_purchase, max_uses, is_active, expires_at) VALUES
('WELCOME10', 'percentage', 10.00, 50.00, NULL, TRUE, '2025-12-31 23:59:59'),
('SAVE20', 'percentage', 20.00, 100.00, 100, TRUE, '2025-12-31 23:59:59'),
('FLASH50', 'fixed', 50.00, 200.00, 50, TRUE, '2025-06-30 23:59:59'),
('FREESHIP', 'fixed', 15.00, 75.00, NULL, TRUE, '2025-12-31 23:59:59'),
('SPECIAL25', 'percentage', 25.00, 150.00, NULL, TRUE, '2025-12-31 23:59:59'),
('MEGA50', 'percentage', 50.00, 300.00, 20, TRUE, '2025-12-31 23:59:59');

-- Insert Expanded CTF Flags (20+ flags)
INSERT INTO flags (flag_name, flag_value, description, difficulty) VALUES
('flag_config', 'FLAG{c0nf1g_f1l3s_4r3_s3ns1t1v3}', 'Found in config.py', 'Easy'),
('flag_sqli_login', 'FLAG{sql_1nj3ct10n_4uth_byp4ss}', 'SQL injection in login', 'Easy'),
('flag_blind_sqli', 'FLAG{bl1nd_sql1_m4st3r}', 'Blind SQLi in product page', 'Medium'),
('flag_xss_stored', 'FLAG{st0r3d_xss_1s_d4ng3r0us}', 'Stored XSS in reviews', 'Easy'),
('flag_ssti', 'FLAG{t3mpl4t3_1nj3ct10n_pwn}', 'SSTI in stock checker', 'Medium'),
('flag_idor_orders', 'FLAG{1d0r_0rd3r_l34k4g3}', 'IDOR in order history', 'Easy'),
('flag_csti', 'FLAG{cl13nt_s1d3_t3mpl4t3_1nj}', 'CSTI in profile page', 'Hard'),
('flag_price_manipulation', 'FLAG{pr1c3_m4n1pul4t10n_pr0f1t}', 'Price manipulation in checkout', 'Medium'),
('flag_ssrf', 'FLAG{ss4f_1nt3rn4l_4cc3ss}', 'SSRF to internal endpoint', 'Hard'),
('flag_command_injection', 'FLAG{c0mm4nd_1nj3ct10n_rc3}', 'Command injection in backup', 'Hard'),
('flag_admin_secret', 'FLAG{4dm1n_s3cr3t_k3y_f0und}', 'Hidden in admin panel', 'Medium'),
('flag_database_dump', 'FLAG{d4t4b4s3_dump_succ3ss}', 'Extract from database', 'Easy'),
('flag_xxe_injection', 'FLAG{xx3_p4rs3r_pwn3d}', 'XXE vulnerability in XML import', 'Hard'),
('flag_graphql', 'FLAG{gr4phql_1nj3ct10n}', 'GraphQL injection', 'Medium'),
('flag_free_products', 'FLAG{fr33_pr0duct5_vuln}', 'Checkout with $0.00', 'Easy'),
('flag_git_exposed', 'FLAG{g1t_c0nf1g_3xp0s3d}', 'Access /.git/config', 'Medium'),
('flag_dotenv', 'FLAG{d0t3nv_f1l3_3xp0s3d}', 'Access /.env file', 'Easy'),
('flag_backup_exposed', 'FLAG{b4ckup_f1l3s_l34k_cr3d3nt14ls}', 'Access backup files', 'Easy'),
('flag_idor_messages', 'FLAG{1d0r_m3ss4g3s_r34d}', 'IDOR in user messages', 'Easy'),
('flag_idor_favorites', 'FLAG{1d0r_f4v0r1t3s_shar3d}', 'IDOR in shared favorites', 'Easy'),
('flag_xss_qa', 'FLAG{xss_pr0duct_qu3st10ns}', 'Stored XSS in product Q&A', 'Easy'),
('flag_session_debug', 'FLAG{s3ss10n_d3bug_l34k}', 'Session information disclosure', 'Medium');

-- Insert sample reviews (with some XSS payloads)
INSERT INTO reviews (product_id, user_id, rating, comment) VALUES
(1, 2, 5, 'Great phone! Highly recommended.'),
(1, 3, 4, 'Good value for money.'),
(2, 2, 5, 'Best earbuds I''ve ever owned!'),
(3, 3, 5, 'Amazing picture quality!'),
(10, 2, 4, 'Clear video quality for video calls.'),
(4, 4, 5, 'Perfect for gaming!'),
(21, 5, 5, 'So comfortable and soft!'),
(25, 3, 4, 'Nice wallet, good quality.'),
(31, 2, 5, 'Best Python book!'),
(41, 4, 5, 'Coffee tastes amazing!');

-- Insert sample orders for IDOR  testing (50+ orders)
INSERT INTO orders (user_id, order_number, total_amount, status) VALUES
(2, 'ORD-2024-00001', 1199.98, 'delivered'),
(3, 'ORD-2024-00002', 299.97, 'shipped'),
(2, 'ORD-2024-00003', 549.98, 'pending'),
(4, 'ORD-2024-00004', 89.99, 'delivered'),
(5, 'ORD-2024-00005', 249.99, 'delivered'),
(6, 'ORD-2024-00006', 499.99, 'shipped'),
(7, 'ORD-2024-00007', 159.98, 'pending'),
(8, 'ORD-2024-00008', 899.99, 'delivered'),
(9, 'ORD-2024-00009', 74.98, 'delivered'),
(10, 'ORD-2024-00010', 199.99, 'cancelled'),
(2, 'ORD-2024-00011', 449.99, 'delivered'),
(3, 'ORD-2024-00012', 129.99, 'shipped'),
(4, 'ORD-2024-00013', 599.99, 'delivered'),
(5, 'ORD-2024-00014', 89.99, 'pending'),
(6, 'ORD-2024-00015', 349.99, 'delivered');

-- Insert order items for some orders
INSERT INTO order_items (order_id, product_id, product_name, quantity, price, subtotal) VALUES
(1, 1, 'Smartphone Pro X', 1, 999.99, 999.99),
(1, 2, 'Wireless Earbuds Elite', 1, 199.99, 199.99),
(2, 6, 'Bluetooth Speaker Max', 2, 89.99, 179.98),
(2, 7, 'Wireless Mouse Pro', 2, 49.99, 99.98),
(3, 4, 'Gaming Laptop Ultra', 1, 1499.99, 1499.99),
(4, 21, 'Premium Cotton T-Shirt', 3, 24.99, 74.97),
(5, 11, 'Headphones Studio', 1, 249.99, 249.99);

-- Insert sample messages for IDOR testing
INSERT INTO messages (sender_id, recipient_id, subject, message) VALUES
(2, 3, 'Product recommendation', 'Hey! You should try the new smartwatch, it''s amazing!'),
(3, 2, 'RE: Product recommendation', 'Thanks! I''ll check it out.'),
(4, 1, 'Support request', 'I need help with my recent order.'),
(2, 4, 'Question about product', 'Is the laptop good for video editing?'),
(5, 6, 'Review exchange', 'Can you leave a review for the product you bought?');

-- Insert sample product questions for testing
INSERT INTO product_questions (product_id, user_id, question, answer, answered_by, answered_at) VALUES
(1, 2, 'Does this phone support 5G?', 'Yes, it supports full 5G connectivity!', 1, NOW()),
(4, 3, 'What is the battery life?', NULL, NULL, NULL),
(10, 4, 'Is the webcam compatible with Mac?', 'Yes, it works with all operating systems.', 1, NOW());

-- End of schema
