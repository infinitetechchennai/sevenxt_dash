-- ============================================
-- ORDER TABLE INSERT QUERIES
-- ============================================

-- Sample INSERT Query for Orders Table
-- Replace values with your actual data

-- Example 1: Basic B2C Order
INSERT INTO orders (
    order_id,
    customer_type,
    customer_name,
    products,
    amount,
    payment,
    status,
    awb_number,
    address,
    email,
    phone,
    city,
    state,
    pincode,
    height,
    weight,
    breadth,
    length,
    hsn,
    sgst_percentage,
    cgst_percentage,
    original_price,
    created_at,
    updated_at
) VALUES (
    'ORD-2026-001',                                    -- order_id (unique)
    'B2C',                                             -- customer_type
    'John Doe',                                        -- customer_name
    '[{"name": "iPhone 15", "price": 79999, "quantity": 1, "hsn": "85171200"}]'::json,  -- products (JSON)
    79999.00,                                          -- amount
    'Prepaid',                                         -- payment (Prepaid/COD)
    'Pending',                                         -- status
    NULL,                                              -- awb_number (will be generated)
    '123 Main Street, Apartment 4B',                   -- address
    'john.doe@example.com',                            -- email
    '9876543210',                                      -- phone
    'Chennai',                                         -- city
    'Tamil Nadu',                                      -- state
    '600001',                                          -- pincode
    10,                                                -- height (cm)
    500,                                               -- weight (grams)
    15,                                                -- breadth (cm)
    20,                                                -- length (cm)
    '85171200',                                        -- hsn
    9.00,                                              -- sgst_percentage (9%)
    9.00,                                              -- cgst_percentage (9%)
    67795.76,                                          -- original_price (before tax)
    NOW(),                                             -- created_at
    NOW()                                              -- updated_at
);

-- Example 2: B2B Order with Multiple Products
INSERT INTO orders (
    order_id,
    customer_type,
    customer_name,
    products,
    amount,
    payment,
    status,
    address,
    email,
    phone,
    city,
    state,
    pincode,
    height,
    weight,
    breadth,
    length,
    hsn,
    sgst_percentage,
    cgst_percentage,
    created_at
) VALUES (
    'ORD-2026-002',
    'B2B',
    'ABC Electronics Pvt Ltd',
    '[
        {"name": "Samsung Galaxy S24", "price": 74999, "quantity": 2, "hsn": "85171200"},
        {"name": "Wireless Earbuds", "price": 2999, "quantity": 5, "hsn": "85183000"}
    ]'::json,
    164993.00,
    'Prepaid',
    'Ready to Pickup',
    'Plot 45, Industrial Area, Phase 2',
    'orders@abcelectronics.com',
    '9123456789',
    'Bangalore',
    'Karnataka',
    '560001',
    15,
    1200,
    25,
    30,
    '85171200',
    9.00,
    9.00,
    NOW()
);

-- Example 3: COD Order
INSERT INTO orders (
    order_id,
    customer_type,
    customer_name,
    products,
    amount,
    payment,
    status,
    address,
    email,
    phone,
    city,
    state,
    pincode,
    height,
    weight,
    breadth,
    length,
    hsn,
    sgst_percentage,
    cgst_percentage
) VALUES (
    'ORD-2026-003',
    'B2C',
    'Priya Sharma',
    '[{"name": "Laptop Charger", "price": 1299, "quantity": 1, "hsn": "85044030"}]'::json,
    1299.00,
    'COD',
    'Pending',
    '78/2, Second Floor, MG Road',
    'priya.sharma@gmail.com',
    '9988776655',
    'Mumbai',
    'Maharashtra',
    '400001',
    5,
    200,
    10,
    15,
    '85044030',
    9.00,
    9.00
);

-- ============================================
-- DELIVERY TABLE INSERT QUERIES
-- ============================================

-- Note: Delivery records are usually created automatically when order status changes
-- But here's how to insert manually if needed

-- Example 1: Delivery for Order ID 1
INSERT INTO deliveries (
    order_id,
    weight,
    length,
    breadth,
    height,
    awb_number,
    courier_partner,
    pickup_location,
    payment,
    amount,
    customer_name,
    phone,
    full_address,
    city,
    state,
    pincode,
    item_name,
    quantity,
    schedule_pickup,
    delivery_status,
    awb_label_path,
    created_at,
    updated_at
) VALUES (
    1,                                                 -- order_id (foreign key to orders.id)
    0.50,                                              -- weight (kg)
    20.00,                                             -- length (cm)
    15.00,                                             -- breadth (cm)
    10.00,                                             -- height (cm)
    '84927910001234',                                  -- awb_number (from Delhivery)
    'Delhivery',                                       -- courier_partner
    'Chennai Warehouse',                               -- pickup_location
    'Prepaid',                                         -- payment
    79999.00,                                          -- amount
    'John Doe',                                        -- customer_name
    '9876543210',                                      -- phone
    '123 Main Street, Apartment 4B, Chennai',          -- full_address
    'Chennai',                                         -- city
    'Tamil Nadu',                                      -- state
    '600001',                                          -- pincode
    'iPhone 15',                                       -- item_name
    1,                                                 -- quantity
    '2026-01-21 10:00:00',                            -- schedule_pickup
    'AWB Generated',                                   -- delivery_status
    '/uploads/awb/awb_84927910001234.pdf',            -- awb_label_path
    NOW(),                                             -- created_at
    NOW()                                              -- updated_at
);

-- ============================================
-- BULK INSERT - Multiple Orders at Once
-- ============================================

INSERT INTO orders (order_id, customer_type, customer_name, products, amount, payment, status, address, email, phone, city, state, pincode, height, weight, breadth, length, hsn, sgst_percentage, cgst_percentage)
VALUES 
    ('ORD-2026-004', 'B2C', 'Rahul Kumar', '[{"name": "Smart Watch", "price": 4999, "quantity": 1}]'::json, 4999.00, 'Prepaid', 'Pending', '45 Park Street', 'rahul@example.com', '9876543211', 'Delhi', 'Delhi', '110001', 5, 150, 8, 12, '91021200', 9.00, 9.00),
    ('ORD-2026-005', 'B2C', 'Anita Desai', '[{"name": "Bluetooth Speaker", "price": 2499, "quantity": 1}]'::json, 2499.00, 'COD', 'Pending', '12 Lake View', 'anita@example.com', '9876543212', 'Pune', 'Maharashtra', '411001', 8, 300, 12, 15, '85182200', 9.00, 9.00),
    ('ORD-2026-006', 'B2B', 'Tech Solutions Ltd', '[{"name": "Laptop", "price": 55999, "quantity": 3}]'::json, 167997.00, 'Prepaid', 'Ready to Pickup', 'IT Park, Block A', 'orders@techsolutions.com', '9876543213', 'Hyderabad', 'Telangana', '500001', 10, 2000, 30, 40, '84713000', 9.00, 9.00);

-- ============================================
-- QUERY TO CHECK INSERTED ORDERS
-- ============================================

-- View all orders
SELECT * FROM orders ORDER BY created_at DESC LIMIT 10;

-- View orders with deliveries
SELECT 
    o.order_id,
    o.customer_name,
    o.amount,
    o.status,
    d.awb_number,
    d.delivery_status,
    d.awb_label_path
FROM orders o
LEFT JOIN deliveries d ON o.id = d.order_id
ORDER BY o.created_at DESC;

-- Count orders by status
SELECT status, COUNT(*) as count 
FROM orders 
GROUP BY status;

-- ============================================
-- UPDATE QUERIES (Common Operations)
-- ============================================

-- Update order status
UPDATE orders 
SET status = 'Ready to Pickup', updated_at = NOW()
WHERE order_id = 'ORD-2026-001';

-- Add AWB number to order
UPDATE orders 
SET awb_number = '84927910001234', status = 'AWB_GENERATED', updated_at = NOW()
WHERE order_id = 'ORD-2026-001';

-- Update delivery status
UPDATE deliveries 
SET delivery_status = 'PICKED_UP', updated_at = NOW()
WHERE awb_number = '84927910001234';

-- ============================================
-- DELETE QUERIES (Use with Caution!)
-- ============================================

-- Delete specific order (will also delete related deliveries if cascade is set)
DELETE FROM orders WHERE order_id = 'ORD-2026-001';

-- Delete all test orders
DELETE FROM orders WHERE order_id LIKE 'ORD-2026-%';

-- ============================================
-- USEFUL QUERIES FOR TESTING
-- ============================================

-- Find orders without AWB numbers
SELECT order_id, customer_name, status 
FROM orders 
WHERE awb_number IS NULL;

-- Find orders ready for pickup but no delivery record
SELECT o.order_id, o.customer_name, o.status
FROM orders o
LEFT JOIN deliveries d ON o.id = d.order_id
WHERE o.status = 'Ready to Pickup' AND d.id IS NULL;

-- Get latest 5 orders with full details
SELECT 
    o.id,
    o.order_id,
    o.customer_name,
    o.customer_type,
    o.amount,
    o.payment,
    o.status,
    o.awb_number,
    o.city,
    o.state,
    o.pincode,
    o.created_at,
    d.delivery_status,
    d.awb_label_path
FROM orders o
LEFT JOIN deliveries d ON o.id = d.order_id
ORDER BY o.created_at DESC
LIMIT 5;
