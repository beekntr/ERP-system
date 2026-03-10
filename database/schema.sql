CREATE TYPE order_status AS ENUM (
    'draft',
    'pending', 
    'approved',
    'ordered',
    'received',
    'cancelled'
);

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    oauth_provider VARCHAR(50) DEFAULT 'google',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_email ON users(email);

COMMENT ON TABLE users IS 'Stores authenticated user information from OAuth providers';
COMMENT ON COLUMN users.oauth_provider IS 'OAuth provider: google, microsoft, development';

CREATE TABLE vendors (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    contact_info TEXT,
    rating DECIMAL(3,2) DEFAULT 0.00 CHECK (rating >= 0 AND rating <= 5),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_vendors_name ON vendors(name);

COMMENT ON TABLE vendors IS 'Stores vendor/supplier information for purchase orders';
COMMENT ON COLUMN vendors.rating IS 'Vendor rating from 0.00 to 5.00';
COMMENT ON COLUMN vendors.contact_info IS 'Contact details: phone, email, address';

CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    sku VARCHAR(100) UNIQUE NOT NULL,
    unit_price DECIMAL(12,2) NOT NULL DEFAULT 0.00 CHECK (unit_price >= 0),
    stock_level INTEGER DEFAULT 0 CHECK (stock_level >= 0),
    description TEXT,
    ai_description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_products_name ON products(name);
CREATE INDEX idx_products_sku ON products(sku);

COMMENT ON TABLE products IS 'Stores product information including pricing and inventory';
COMMENT ON COLUMN products.sku IS 'Stock Keeping Unit - unique product identifier';
COMMENT ON COLUMN products.ai_description IS 'AI-generated marketing description';

CREATE TABLE purchase_orders (
    id SERIAL PRIMARY KEY,
    reference_no VARCHAR(50) UNIQUE NOT NULL,
    vendor_id INTEGER NOT NULL REFERENCES vendors(id) ON DELETE RESTRICT,
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status order_status DEFAULT 'draft',
    subtotal DECIMAL(12,2) DEFAULT 0.00,
    tax DECIMAL(12,2) DEFAULT 0.00,
    total_amount DECIMAL(12,2) DEFAULT 0.00,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES users(id)
);

CREATE INDEX idx_po_reference ON purchase_orders(reference_no);
CREATE INDEX idx_po_vendor ON purchase_orders(vendor_id);
CREATE INDEX idx_po_status ON purchase_orders(status);
CREATE INDEX idx_po_date ON purchase_orders(order_date);

COMMENT ON TABLE purchase_orders IS 'Stores purchase order header information';
COMMENT ON COLUMN purchase_orders.reference_no IS 'Unique PO reference number (e.g., PO-2024-0001)';
COMMENT ON COLUMN purchase_orders.tax IS 'Calculated as 5% of subtotal';
COMMENT ON COLUMN purchase_orders.total_amount IS 'subtotal + tax';

CREATE TABLE po_items (
    id SERIAL PRIMARY KEY,
    purchase_order_id INTEGER NOT NULL REFERENCES purchase_orders(id) ON DELETE CASCADE,
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE RESTRICT,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price DECIMAL(12,2) NOT NULL CHECK (unit_price >= 0),
    line_total DECIMAL(12,2) NOT NULL
);

CREATE INDEX idx_po_items_order ON po_items(purchase_order_id);
CREATE INDEX idx_po_items_product ON po_items(product_id);

COMMENT ON TABLE po_items IS 'Stores line items for each purchase order';
COMMENT ON COLUMN po_items.unit_price IS 'Price at time of order (may differ from current product price)';
COMMENT ON COLUMN po_items.line_total IS 'quantity * unit_price';

CREATE TABLE ai_description_logs (
    id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES products(id) ON DELETE SET NULL,
    product_name VARCHAR(255),
    prompt_text TEXT NOT NULL,
    response_text TEXT,
    model_used VARCHAR(100),
    tokens_used INTEGER,
    generation_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_ai_logs_product ON ai_description_logs(product_id);
CREATE INDEX idx_ai_logs_date ON ai_description_logs(created_at);

COMMENT ON TABLE ai_description_logs IS 'Logs all AI-generated descriptions for auditing';

CREATE OR REPLACE FUNCTION calculate_line_total()
RETURNS TRIGGER AS $$
BEGIN
    NEW.line_total := NEW.quantity * NEW.unit_price;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_calculate_line_total
    BEFORE INSERT OR UPDATE ON po_items
    FOR EACH ROW
    EXECUTE FUNCTION calculate_line_total();

CREATE OR REPLACE FUNCTION update_po_totals()
RETURNS TRIGGER AS $$
DECLARE
    v_subtotal DECIMAL(12,2);
    v_tax DECIMAL(12,2);
    v_po_id INTEGER;
BEGIN
    IF TG_OP = 'DELETE' THEN
        v_po_id := OLD.purchase_order_id;
    ELSE
        v_po_id := NEW.purchase_order_id;
    END IF;
    SELECT COALESCE(SUM(line_total), 0) INTO v_subtotal
    FROM po_items
    WHERE purchase_order_id = v_po_id;
    v_tax := v_subtotal * 0.05;
    UPDATE purchase_orders
    SET subtotal = v_subtotal,
        tax = v_tax,
        total_amount = v_subtotal + v_tax
    WHERE id = v_po_id;
    
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_update_po_totals
    AFTER INSERT OR UPDATE OR DELETE ON po_items
    FOR EACH ROW
    EXECUTE FUNCTION update_po_totals();

CREATE OR REPLACE FUNCTION generate_po_reference()
RETURNS TRIGGER AS $$
DECLARE
    v_year TEXT;
    v_seq INTEGER;
    v_ref TEXT;
BEGIN
    IF NEW.reference_no IS NULL OR NEW.reference_no = '' THEN
        v_year := TO_CHAR(CURRENT_DATE, 'YYYY');
        
        SELECT COALESCE(MAX(
            CAST(SUBSTRING(reference_no FROM 'PO-' || v_year || '-(\d+)') AS INTEGER)
        ), 0) + 1 INTO v_seq
        FROM purchase_orders
        WHERE reference_no LIKE 'PO-' || v_year || '-%';
        
        NEW.reference_no := 'PO-' || v_year || '-' || LPAD(v_seq::TEXT, 4, '0');
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_generate_po_reference
    BEFORE INSERT ON purchase_orders
    FOR EACH ROW
    EXECUTE FUNCTION generate_po_reference();

INSERT INTO vendors (name, contact_info, rating) VALUES
    ('Tech Supplies Inc', 'contact@techsupplies.com | +1-555-0101', 4.5),
    ('Office Pro Ltd', 'sales@officepro.com | +1-555-0102', 4.2),
    ('Industrial Parts Co', 'orders@industrialparts.com | +1-555-0103', 3.8),
    ('Green Solutions', 'info@greensolutions.com | +1-555-0104', 4.7);

INSERT INTO products (name, sku, unit_price, stock_level, description) VALUES
    ('Laptop Dell XPS 15', 'DELL-XPS-15', 1299.99, 50, 'High-performance laptop'),
    ('Wireless Mouse', 'WL-MOUSE-001', 29.99, 200, 'Ergonomic wireless mouse'),
    ('USB-C Hub', 'USB-HUB-7P', 49.99, 150, '7-port USB-C hub'),
    ('Monitor 27inch', 'MON-27-4K', 399.99, 30, '4K UHD monitor'),
    ('Keyboard Mechanical', 'KB-MECH-RGB', 89.99, 100, 'RGB mechanical keyboard'),
    ('Webcam HD', 'CAM-HD-1080', 79.99, 75, '1080p HD webcam'),
    ('Desk Lamp LED', 'LAMP-LED-01', 34.99, 120, 'Adjustable LED desk lamp'),
    ('Printer Laser', 'PRT-LSR-BW', 249.99, 25, 'Black & white laser printer');

CREATE OR REPLACE VIEW v_purchase_order_summary AS
SELECT 
    po.id,
    po.reference_no,
    po.order_date,
    po.status,
    v.name AS vendor_name,
    v.contact_info AS vendor_contact,
    po.subtotal,
    po.tax,
    po.total_amount,
    COUNT(pi.id) AS item_count,
    u.name AS created_by_name
FROM purchase_orders po
JOIN vendors v ON po.vendor_id = v.id
LEFT JOIN po_items pi ON po.id = pi.purchase_order_id
LEFT JOIN users u ON po.created_by = u.id
GROUP BY po.id, po.reference_no, po.order_date, po.status, 
         v.name, v.contact_info, po.subtotal, po.tax, 
         po.total_amount, u.name
ORDER BY po.order_date DESC;

CREATE OR REPLACE VIEW v_product_inventory AS
SELECT 
    p.id,
    p.name,
    p.sku,
    p.unit_price,
    p.stock_level,
    CASE 
        WHEN p.stock_level = 0 THEN 'Out of Stock'
        WHEN p.stock_level < 20 THEN 'Low Stock'
        ELSE 'In Stock'
    END AS stock_status,
    COALESCE(SUM(pi.quantity), 0) AS total_ordered
FROM products p
LEFT JOIN po_items pi ON p.id = pi.product_id
GROUP BY p.id, p.name, p.sku, p.unit_price, p.stock_level;