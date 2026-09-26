"""
Supabase PostgreSQL Connection & Migration Verification Script
Used in Phase 6.6 to safely verify Supabase connectivity, schema presence, and CRUD operations.
"""

import os
import sys
import uuid
from pathlib import Path
from dotenv import load_dotenv

# Ensure backend root is on sys.path
backend_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(backend_dir))

# Load environment
dotenv_path = backend_dir / ".env"
root_dotenv = backend_dir.parent / ".env"
if dotenv_path.exists():
    load_dotenv(dotenv_path)
elif root_dotenv.exists():
    load_dotenv(root_dotenv)
else:
    load_dotenv()

from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.task import Task
from sqlalchemy import text, inspect


def main():
    db_url = os.environ.get("DATABASE_URL", "").strip()
    if not db_url:
        print("\n[ERROR] DATABASE_URL is not set in backend/.env or system environment.")
        print("Please configure your Supabase connection string:")
        print("DATABASE_URL=postgresql://postgres.[project-ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres")
        sys.exit(1)

    print("\n--- 1. AUDITING DATABASE CONFIGURATION ---")
    app = create_app("development")
    
    with app.app_context():
        engine_name = db.engine.name
        print(f"Active SQLAlchemy engine: {engine_name}")
        if engine_name != "postgresql":
            print(f"[ERROR] Active database engine is '{engine_name}', expected 'postgresql' for Supabase.")
            sys.exit(1)

        print("\n--- 2. TESTING DIRECT CONNECTION & VERSION ---")
        try:
            version_res = db.session.execute(text("SELECT version();")).scalar()
            print(f"Database Server Version: {version_res}")
        except Exception as e:
            print(f"[ERROR] Connection probe failed: {e}")
            sys.exit(1)

        print("\n--- 3. CHECKING SCHEMA & TABLES ---")
        inspector = inspect(db.engine)
        existing_tables = inspector.get_table_names()
        print(f"Existing tables in database: {existing_tables}")

        schema_sql_path = backend_dir.parent / "migrations" / "001_initial_schema.sql"
        if not ("users" in existing_tables and "tasks" in existing_tables):
            print(f"Applying migration: {schema_sql_path}...")
            if not schema_sql_path.exists():
                print(f"[ERROR] Migration file not found at: {schema_sql_path}")
                sys.exit(1)
            
            with open(schema_sql_path, "r", encoding="utf-8") as f:
                sql_content = f.read()
            
            # Execute raw SQL migration statements safely
            db.session.execute(text(sql_content))
            db.session.commit()
            print("Migration applied successfully.")
        else:
            print("Tables 'users' and 'tasks' already exist. Migration not required.")

        print("\n--- 4. EXECUTING LIVE CRUD VERIFICATION ---")
        test_suffix = uuid.uuid4().hex[:8]
        test_email = f"supabase_test_{test_suffix}@example.com"
        test_google_id = f"supa_test_gid_{test_suffix}"
        
        try:
            # 1. Create User
            test_user = User(
                google_id=test_google_id,
                name="Supabase Test User",
                email=test_email,
                profile_image="https://example.com/avatar.png",
            )
            db.session.add(test_user)
            db.session.commit()
            print(f"[1/8] Created User: {test_user.id} ({test_user.email})")

            # 2. Read Users
            queried_user = User.query.filter_by(email=test_email).first()
            assert queried_user is not None, "Failed to read created user"
            print(f"[2/8] Read User successfully: {queried_user.id}")

            # 3. Create Task
            test_task = Task(
                title=f"Supabase Verification Task {test_suffix}",
                description="Testing live write to Supabase PostgreSQL",
                created_by=test_user.id,
                priority="HIGH",
                status="TODO",
            )
            db.session.add(test_task)
            db.session.commit()
            print(f"[3/8] Created Task: {test_task.id} (Status: {test_task.status})")

            # 4. Read Task
            queried_task = Task.query.get(test_task.id)
            assert queried_task is not None, "Failed to read created task"
            print(f"[4/8] Read Task successfully: {queried_task.title}")

            # 5. Update Task
            queried_task.description = "Updated description during Supabase audit"
            db.session.commit()
            print(f"[5/8] Updated Task successfully")

            # 6. Assign Task
            queried_task.assigned_to = test_user.id
            db.session.commit()
            print(f"[6/8] Assigned Task successfully to user {test_user.id}")

            # 7. Complete Task
            from datetime import datetime, timezone
            queried_task.status = "COMPLETED"
            queried_task.completed_at = datetime.now(timezone.utc)
            db.session.commit()
            print(f"[7/8] Completed Task successfully (completed_at: {queried_task.completed_at})")

            # 8. Delete Task & Cleanup Test User
            task_id = queried_task.id
            db.session.delete(queried_task)
            db.session.delete(test_user)
            db.session.commit()
            print(f"[8/8] Deleted Task {task_id} and Test User {test_user.id} successfully (Cleaned up)")

            # Final verify cleanup
            assert Task.query.get(task_id) is None, "Task cleanup verification failed"
            assert User.query.filter_by(email=test_email).first() is None, "User cleanup verification failed"
            print("Verified: No temporary test records left behind.")

        except Exception as e:
            db.session.rollback()
            print(f"[ERROR] CRUD verification failed: {e}")
            sys.exit(1)

        print("\n--- 5. SUPABASE CONNECTION & CRUD FULLY VERIFIED ---")
        print("Engine: postgresql")
        print("Status: connected")


if __name__ == "__main__":
    main()
