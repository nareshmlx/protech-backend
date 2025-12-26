-- ============================================
-- ProTech Surveillance System
-- Database Initialization Script
-- ============================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create ENUM types
CREATE TYPE user_role AS ENUM ('USER', 'ADMIN');

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    role user_role DEFAULT 'USER',
    is_active BOOLEAN DEFAULT TRUE,
    change_password BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login_at TIMESTAMP WITH TIME ZONE
);

-- ============================================
-- Create Indexes for Performance
-- ============================================
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);

-- ============================================
-- Create Auto-Update Trigger for updated_at
-- ============================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE 'plpgsql';

CREATE TRIGGER update_users_updated_at 
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- Insert Test Users (UPPERCASE roles to match enum)
-- ============================================

-- Admin User (email: admin@protech.com, password: Admin123!)
INSERT INTO users (email, password_hash, first_name, last_name, role, is_active)
VALUES (
    'admin@protech.com',
    '$2b$12$wXxIC0GP55P9CxjWpt/Lkuhs6SEM09n4QwRhbmiXX5K3hQBxJaNLa',
    'Admin',
    'User',
    'ADMIN',  -- Changed to UPPERCASE
    TRUE
) ON CONFLICT (email) DO NOTHING;

-- Regular User (email: user@protech.com, password: User123!)
INSERT INTO users (email, password_hash, first_name, last_name, role, is_active)
VALUES (
    'user@protech.com',
    '$2b$12$k8m1kz7JIFrSMM3OSUhx9OQkIOy0kvdDI88iES.ue7Aga.Y49boQm',
    'Test',
    'User',
    'USER',  -- Changed to UPPERCASE
    TRUE
) ON CONFLICT (email) DO NOTHING;

-- ============================================
-- Grant Permissions
-- ============================================
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO protech_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO protech_user;

-- ============================================
-- Display Success Message
-- ============================================
DO $$
BEGIN
    RAISE NOTICE '============================================';
    RAISE NOTICE 'Database initialized successfully!';
    RAISE NOTICE '============================================';
    RAISE NOTICE 'Test users created:';
    RAISE NOTICE '  Admin: admin@protech.com / Admin123! (role: ADMIN)';
    RAISE NOTICE '  User: user@protech.com / User123! (role: USER)';
    RAISE NOTICE '============================================';
END $$;