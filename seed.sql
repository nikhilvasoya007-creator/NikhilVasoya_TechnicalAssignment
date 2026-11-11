USE sales_inventory;

INSERT INTO users (name, email, password_hash, role) VALUES
('Admin User', 'admin@savyant.local', '$2b$12$0ewL0oGsmzc86Lmsl9HEvO6FWSRh28583wQXp6BUpOVfaikE4UkAC', 'Admin'),
('Sales User', 'sales@savyant.local', '$2b$12$bD4Vg8wF7wxIc3GRPkN5HObgFYNyoVgVDQ3CIXFbSvdRH1WbAVIPK', 'Sales User');

INSERT INTO customers (name, email, mobile, city, is_active) VALUES
('Raj Patel', 'raj@example.com', '9876543210', 'Ahmedabad', TRUE),
('Meera Shah', 'meera@example.com', '9876543211', 'Gandhinagar', TRUE),
('Amit Desai', 'amit@example.com', '9876543212', 'Surat', TRUE);

INSERT INTO products (product_code, name, category, price, stock_quantity, is_active) VALUES
('PRD-001', 'Keyboard', 'Accessories', 1500.00, 20, TRUE),
('PRD-002', 'Mouse', 'Accessories', 500.00, 50, TRUE),
('PRD-003', 'Monitor', 'Electronics', 8500.00, 15, TRUE),
('PRD-004', 'Laptop Stand', 'Accessories', 1200.00, 30, TRUE),
('PRD-005', 'USB Cable', 'Accessories', 299.00, 100, TRUE);
