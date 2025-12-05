-- Initialize database extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create schemas for logical separation
CREATE SCHEMA IF NOT EXISTS admin;
CREATE SCHEMA IF NOT EXISTS restaurant;
CREATE SCHEMA IF NOT EXISTS customer;

-- Grant permissions
GRANT ALL PRIVILEGES ON SCHEMA admin TO postgres;
GRANT ALL PRIVILEGES ON SCHEMA restaurant TO postgres;
GRANT ALL PRIVILEGES ON SCHEMA customer TO postgres;

-- Create full-text search configuration for Japanese (optional)
-- You can add custom dictionaries here if needed

-- Log initialization
DO $$
BEGIN
    RAISE NOTICE 'Database initialized successfully';
END $$;
