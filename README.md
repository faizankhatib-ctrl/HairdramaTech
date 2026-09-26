# Hairdrama Tech: Task Management Web Application

A full-stack, production-ready Task Management Web Application built with **Next.js (TypeScript, App Router)**, **Python Flask (RESTful API, SQLAlchemy)**, **Supabase PostgreSQL**, **Google OAuth 2.0**, and **Gmail SMTP Notifications**.

---

## 1. System Architecture

```mermaid
graph TD
    subgraph Client ["Frontend (Next.js 14+ App Router, TypeScript)"]
        UI[Responsive Dashboard UI]
        AuthCtx[Auth Context & Google OAuth]
        APIClient[Typed Fetch API Client]
    end

    subgraph Server ["Backend (Python Flask REST API)"]
        AppFactory["Flask App Factory (create_app)"]
        AuthBP[Auth Blueprint & Google Verifier]
        TaskBP[Tasks Blueprint & Filter Engine]
        UserBP[Users Directory Blueprint]
        StatsBP[Dashboard Stats Blueprint]
        EmailWorker[Asynchronous Gmail SMTP Worker]
    end

    subgraph Data ["Database (Supabase PostgreSQL)"]
        UsersTable[(users)]
        TasksTable[(tasks)]
        Migrations[/migrations/001_initial_schema.sql/]
    end

    UI --> AuthCtx
    UI --> APIClient
    APIClient -->|JWT Bearer Requests| AppFactory
    AppFactory --> AuthBP
    AppFactory --> TaskBP
    AppFactory --> UserBP
    AppFactory --> StatsBP
    AuthBP -->|Verify Token| GoogleAPI[Google OAuth 2.0 API]
    TaskBP -->|Trigger Event| EmailWorker
    EmailWorker -->|SMTP TLS| GmailSMTP[Gmail Mail Server]
    AuthBP --> UsersTable
    TaskBP --> TasksTable
    UserBP --> UsersTable
    StatsBP --> TasksTable
    Migrations -.->|DDL Schema & Indexes| Data
```

---

## 2. Directory Structure

```
root/
├── frontend/             # Next.js App Router, TypeScript, Responsive Dashboard (Phase 6 & 7)
├── backend/              # Python Flask REST API
│   ├── app/
│   │   ├── models/       # SQLAlchemy models (User, Task, cross-platform GUID)
│   │   ├── routes/       # Blueprints (health, auth, users, tasks, dashboard)
│   │   ├── services/     # Business logic (AuthService, TaskService, UserService, EmailService)
│   │   ├── templates/    # HTML email templates (task_assigned.html, task_completed.html)
│   │   └── utils/        # JWT decorator (@token_required), validators, standardized responses
│   ├── tests/            # Automated test suites (56 tests across all modules)
│   ├── requirements.txt  # Core dependencies & platform-conditional gunicorn
│   └── run.py            # WSGI callable & development entry point
├── migrations/           # Database DDL schema migrations (001_initial_schema.sql)
├── .env.example          # Non-sensitive configuration template
├── .gitignore            # Git exclusion rules (.env, .venv, build artifacts)
└── README.md
```

---

## 3. Database Schema (`migrations/001_initial_schema.sql`)

The database is built on **Supabase PostgreSQL** with strict constraints and automated triggers.

### `users` Table
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | UUID | PRIMARY KEY | Unique user identifier (`uuid_generate_v4()`) |
| `google_id` | VARCHAR(255) | UNIQUE, NOT NULL | Subject ID (`sub`) from Google OAuth 2.0 |
| `name` | VARCHAR(255) | NOT NULL | User's full name from Google Profile |
| `email` | VARCHAR(255) | UNIQUE, NOT NULL | User's verified Google email address |
| `profile_image` | TEXT | NULLABLE | Google profile picture URL |
| `created_at` | TIMESTAMPTZ | NOT NULL | Account creation timestamp |
| `updated_at` | TIMESTAMPTZ | NOT NULL | Last update timestamp (auto-managed by trigger) |

### `tasks` Table
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | UUID | PRIMARY KEY | Unique task identifier (`uuid_generate_v4()`) |
| `title` | VARCHAR(255) | NOT NULL | Task title / headline |
| `description` | TEXT | NULLABLE | Task details |
| `created_by` | UUID | NOT NULL, FK `users(id)` ON DELETE CASCADE | Author of the task |
| `assigned_to` | UUID | NULLABLE, FK `users(id)` ON DELETE SET NULL | Assigned user |
| `status` | VARCHAR(50) | NOT NULL, DEFAULT `'TODO'` | `'TODO'`, `'IN_PROGRESS'`, `'COMPLETED'` |
| `priority` | VARCHAR(50) | NOT NULL, DEFAULT `'MEDIUM'` | `'LOW'`, `'MEDIUM'`, `'HIGH'`, `'URGENT'` |
| `due_date` | TIMESTAMPTZ | NULLABLE | Deadline timestamp |
| `created_at` | TIMESTAMPTZ | NOT NULL | Creation timestamp |
| `updated_at` | TIMESTAMPTZ | NOT NULL | Last update timestamp (auto-managed by trigger) |
| `completed_at` | TIMESTAMPTZ | NULLABLE | Completion timestamp |

---

## 4. Authentication Flow (Google OAuth 2.0 & JWT)

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant Client as Next.js Frontend
    participant Google as Google Identity Services
    participant API as Flask Backend
    participant DB as PostgreSQL DB

    User->>Client: Clicks "Sign in with Google"
    Client->>Google: Opens Google Sign-In popup
    Google->>User: Prompts account selection
    Google-->>Client: Returns Google ID Token (JWT)
    Client->>API: POST /api/auth/google { credential: "<token>" }
    API->>API: Verify token signature against Google Public Certificates
    API->>API: Verify audience matches GOOGLE_CLIENT_ID
    API->>DB: Upsert user (Find by google_id/email or create new)
    API->>API: Generate application JWT (sub: user_id, exp: 7 days)
    API-->>Client: HTTP 200 OK { token, user }
    Client->>API: Subsequent requests with Authorization: Bearer <token>
```

---

## 5. API Endpoints Specification

All endpoints return a standardized JSON envelope:
- **Success:** `{ "success": true, "message": "...", "data": { ... } }`
- **Error:** `{ "success": false, "error": { "code": "...", "message": "..." } }`

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `GET` | `/api/health` | Operational health check probe & DB verification | No |
| `POST` | `/api/auth/google` | Exchange Google ID token for application JWT | No |
| `GET` | `/api/auth/me` | Get current authenticated user profile | Yes |
| `POST` | `/api/auth/logout` | Stateless logout confirmation | No |
| `GET` | `/api/users` | List registered users for task assignment (`?search=...`) | Yes |
| `GET` | `/api/tasks` | Filterable task list (`?status=&priority=&search=&scope=`) | Yes |
| `POST` | `/api/tasks` | Create task (creator bound to JWT identity) | Yes |
| `GET` | `/api/tasks/<id>` | Get task details | Yes |
| `PUT` | `/api/tasks/<id>` | Full update of task attributes | Yes |
| `PATCH` | `/api/tasks/<id>/assign` | Assign or unassign task | Yes |
| `PATCH` | `/api/tasks/<id>/complete` | Toggle completion status | Yes |
| `DELETE` | `/api/tasks/<id>` | Delete task (restricted to author) | Yes |
| `GET` | `/api/dashboard/stats` | Aggregated user metrics | Yes |

---

## 6. Authorization Rules Matrix

| Action | Creator / Author | Assignee | Other Registered Users |
|---|:---:|:---:|:---:|
| **View Task** | Allowed | Allowed | `403 Forbidden` |
| **Edit Title / Priority** | Allowed | `403 Forbidden` | `403 Forbidden` |
| **Edit Status / Description** | Allowed | Allowed | `403 Forbidden` |
| **Reassign / Unassign** | Allowed | `403 Forbidden` | `403 Forbidden` |
| **Complete / Reopen Task** | Allowed | Allowed | `403 Forbidden` |
| **Delete Task** | Allowed | `403 Forbidden` | `403 Forbidden` |

---

## 7. Email Notification Architecture

### Dedicated Event Trigger Sources
To prevent duplicate emails and avoid unexpected side-effects during standard field edits:
- **`POST /api/tasks` (with assignee):** Sends task assignment email to the assigned user.
- **`PATCH /api/tasks/<id>/assign`:** Sends task assignment email to the new assignee (suppressed if unassigned or identical to previous).
- **`PATCH /api/tasks/<id>/complete`:** Sends task completion email to relevant participants.
- **`PUT /api/tasks/<id>`:** Strictly updates task fields and does **NOT** independently trigger email notifications.

### Completion Notification Rules
When a task transitions from a non-`COMPLETED` state to `COMPLETED`:
1. **Creator Notification:** The task creator is notified.
2. **Assignee Notification:** If the assignee is different from the creator, the assignee is notified as well.
3. **Deduplication:** If the creator and assignee are the same user (self-assigned), only **ONE** email is sent.
4. **Idempotency:** Completing an already-`COMPLETED` task or reopening a task does **NOT** trigger duplicate notifications.

### Transactional Independence & Delivery Mechanism
1. The database transaction always commits **before** email dispatch is attempted.
2. If Gmail SMTP is unreachable or credentials are temporarily invalid, the task operation remains **100% saved in the database**.
3. Email delivery runs in a non-blocking daemon thread so API responses return immediately (< 50ms).

> **Architectural Note on Background Workers:**
> For this assignment, email delivery uses a lightweight background thread (`threading.Thread`). For a larger production system with high email throughput, a durable background job queue such as Celery/RQ with Redis would be preferable.

---

## 8. Gmail Setup Guide (App Password)

Google does not allow third-party applications to log in using standard Google account passwords. You must generate a dedicated **16-character App Password**:

1. Log in to your Google Account: [https://myaccount.google.com/](https://myaccount.google.com/).
2. Navigate to **Security** -> **How you sign in to Google**.
3. Ensure **2-Step Verification** is turned **ON** (required by Google to generate App Passwords).
4. Go to **App Passwords**: [https://myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords).
5. Enter an app name (e.g., `Hairdrama Tasks`) and click **Create**.
6. Copy the generated **16-character code** (e.g., `abcd efgh ijkl mnop`).
7. Place it into your backend `.env` file under `MAIL_PASSWORD`.

---

## 9. Environment Variables Template

Documented in `.env.example` with non-sensitive placeholders:
```env
# Backend Configuration
FLASK_ENV=development
FLASK_DEBUG=1
PORT=5000

# Security Keys
SECRET_KEY=replace-with-a-random-flask-secret-key-32-chars
JWT_SECRET_KEY=replace-with-a-random-jwt-secret-key-32-chars
JWT_EXPIRATION_DAYS=7

# Supabase PostgreSQL Database Connection
DATABASE_URL=postgresql://postgres:your-db-password@db.your-supabase-id.supabase.co:5432/postgres

# Google OAuth 2.0 Credentials
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-client-secret

# Gmail SMTP Email Notification Credentials
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-16-char-app-password
MAIL_DEFAULT_SENDER="Hairdrama Tech Tasks <your-email@gmail.com>"

# Frontend Application Origin
FRONTEND_URL=http://localhost:3000

# Frontend Variables (frontend/.env.local)
NEXT_PUBLIC_API_URL=http://localhost:5000/api
NEXT_PUBLIC_GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
```

---

## 10. Local Setup & Testing

### 1. Backend Virtual Environment
```powershell
cd "backend"
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
```

### 2. Run All Automated Tests
```powershell
cd "backend"
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```
*Current test suite: **56 passing unit, integration, and security penetration tests** covering foundation health, Google OAuth, JWT protection, Task CRUD, filtering, authorization matrix, and email notifications.*

### 3. Run Development Server (Backend)
```powershell
cd "backend"
.\.venv\Scripts\python.exe run.py
```
*Accessible at `http://127.0.0.1:5000` with health check at `http://127.0.0.1:5000/api/health`.*

### 4. Frontend Setup & Run
```powershell
cd "frontend"
npm install
npm run dev
```
*Accessible at `http://localhost:3000`.*

### 5. Frontend Quality Checks
```powershell
cd "frontend"
npm run lint
npm run build
```

---

## 11. Production Deployment (Render / Railway)

- **Entry Point:** `gunicorn run:app`
- **Environment:** Set `FLASK_ENV=production` and supply production values for `DATABASE_URL`, `JWT_SECRET_KEY`, `GOOGLE_CLIENT_ID`, `MAIL_USERNAME`, `MAIL_PASSWORD`, and `FRONTEND_URL`.
- **Database Migrations:** Run `migrations/001_initial_schema.sql` directly inside the Supabase SQL Editor.
