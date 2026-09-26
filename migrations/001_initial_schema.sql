-- Migration: 001_initial_schema.sql
-- Description: Initial schema for Task Management Application
-- Target: Supabase PostgreSQL / Standard PostgreSQL 14+

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- 1. USERS TABLE
-- Stores user profiles authenticated via Google OAuth 2.0
-- ============================================================================
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    google_id VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    profile_image TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Comments on users table columns
COMMENT ON TABLE users IS 'Registered users authenticated via Google OAuth 2.0';
COMMENT ON COLUMN users.google_id IS 'Unique identifier (sub) returned by Google Identity Services';
COMMENT ON COLUMN users.email IS 'User Google account email';

-- ============================================================================
-- 2. TASKS TABLE
-- Stores task entities with ownership, assignment, priority, and lifecycle status
-- ============================================================================
CREATE TABLE IF NOT EXISTS tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    created_by UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    assigned_to UUID REFERENCES users(id) ON DELETE SET NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'TODO' 
        CHECK (status IN ('TODO', 'IN_PROGRESS', 'COMPLETED')),
    priority VARCHAR(50) NOT NULL DEFAULT 'MEDIUM' 
        CHECK (priority IN ('LOW', 'MEDIUM', 'HIGH', 'URGENT')),
    due_date TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMPTZ
);

-- Comments on tasks table columns
COMMENT ON TABLE tasks IS 'Tasks tracked in the system';
COMMENT ON COLUMN tasks.created_by IS 'Foreign key referencing the user who authored the task';
COMMENT ON COLUMN tasks.assigned_to IS 'Foreign key referencing the user assigned to execute the task';
COMMENT ON COLUMN tasks.status IS 'Lifecycle state: TODO, IN_PROGRESS, or COMPLETED';
COMMENT ON COLUMN tasks.priority IS 'Priority level: LOW, MEDIUM, HIGH, or URGENT';
COMMENT ON COLUMN tasks.completed_at IS 'Timestamp when status was updated to COMPLETED';

-- ============================================================================
-- 3. INDEXES
-- Optimized for high-frequency queries: filtering by user, status, priority, due date
-- ============================================================================
CREATE INDEX IF NOT EXISTS idx_tasks_created_by ON tasks(created_by);
CREATE INDEX IF NOT EXISTS idx_tasks_assigned_to ON tasks(assigned_to);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_priority ON tasks(priority);
CREATE INDEX IF NOT EXISTS idx_tasks_due_date ON tasks(due_date);
CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON tasks(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_google_id ON users(google_id);

-- ============================================================================
-- 4. AUTOMATIC TIMESTAMP TRIGGER
-- Updates the `updated_at` column whenever a row is modified
-- ============================================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_users_updated_at ON users;
CREATE TRIGGER trigger_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS trigger_tasks_updated_at ON tasks;
CREATE TRIGGER trigger_tasks_updated_at
    BEFORE UPDATE ON tasks
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
