-- Create a sample users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Insert seed data
INSERT INTO users (username, email) VALUES
    ('admin_user', 'admin@example.com'),
    ('demo_user', 'demo@example.com')
ON CONFLICT (email) DO NOTHING;