# Database Migrations

This folder contains the database schema migrations for the Task Management Application.

## Migration Files

- **`001_initial_schema.sql`**: Creates the `users` and `tasks` tables, foreign key relationships, performance indexes, and automatic timestamp triggers (`update_updated_at_column`).

## How to Run Migrations in Supabase

### Option 1: Supabase Web Dashboard (Recommended)
1. Log in to your [Supabase Dashboard](https://supabase.com/dashboard).
2. Select your project.
3. In the left navigation, click on **SQL Editor**.
4. Click **New query**.
5. Copy and paste the contents of `001_initial_schema.sql`.
6. Click **Run**.
7. Navigate to **Table Editor** to verify that both `users` and `tasks` tables were successfully created.

### Option 2: Supabase CLI / Direct PostgreSQL Connection (`psql`)
If you have `psql` or the Supabase CLI installed, you can connect using your PostgreSQL connection URI:

```bash
psql "postgresql://postgres:[YOUR-PASSWORD]@[YOUR-HOST]:5432/postgres" -f migrations/001_initial_schema.sql
```

## Schema Overview

### 1. `users` Table
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | UUID | PRIMARY KEY | Unique user ID generated via `uuid_generate_v4()` |
| `google_id` | VARCHAR(255) | UNIQUE, NOT NULL | Subject ID (`sub`) from Google OAuth 2.0 |
| `name` | VARCHAR(255) | NOT NULL | User's full name from Google Profile |
| `email` | VARCHAR(255) | UNIQUE, NOT NULL | User's verified Google email address |
| `profile_image` | TEXT | NULLABLE | Google profile picture URL |
| `created_at` | TIMESTAMPTZ | NOT NULL | Account creation timestamp |
| `updated_at` | TIMESTAMPTZ | NOT NULL | Last update timestamp (auto-managed by trigger) |

### 2. `tasks` Table
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | UUID | PRIMARY KEY | Unique task ID generated via `uuid_generate_v4()` |
| `title` | VARCHAR(255) | NOT NULL | Task title / headline |
| `description` | TEXT | NULLABLE | Detailed task specifications |
| `created_by` | UUID | NOT NULL, FK to `users(id)` ON DELETE CASCADE | Author of the task |
| `assigned_to` | UUID | NULLABLE, FK to `users(id)` ON DELETE SET NULL | Assigned user |
| `status` | VARCHAR(50) | NOT NULL, DEFAULT `'TODO'` | `'TODO'`, `'IN_PROGRESS'`, `'COMPLETED'` |
| `priority` | VARCHAR(50) | NOT NULL, DEFAULT `'MEDIUM'` | `'LOW'`, `'MEDIUM'`, `'HIGH'`, `'URGENT'` |
| `due_date` | TIMESTAMPTZ | NULLABLE | Deadline timestamp |
| `created_at` | TIMESTAMPTZ | NOT NULL | Task creation timestamp |
| `updated_at` | TIMESTAMPTZ | NOT NULL | Last update timestamp (auto-managed by trigger) |
| `completed_at` | TIMESTAMPTZ | NULLABLE | Timestamp when status was set to `'COMPLETED'` |
