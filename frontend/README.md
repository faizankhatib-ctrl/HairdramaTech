# Hairdrama Tech — Task Management Frontend

Modern, responsive Next.js application built with TypeScript and App Router, consuming the Flask REST API backend.

---

## Tech Stack

- **Framework**: Next.js 14+ (App Router)
- **Language**: TypeScript
- **State & Data**: React Context + Native Fetch API Client with Bearer token authentication
- **Styling**: Vanilla CSS Design System with dark mode, custom design tokens, and CSS Grid/Flexbox
- **Authentication**: Google OAuth 2.0 (`@react-oauth/google`) with server-side token validation
- **Icons**: `lucide-react`

---

## Directory Architecture

```text
frontend/
├── app/
│   ├── layout.tsx             # Root layout with AuthProvider & ToastProvider
│   ├── page.tsx               # Landing page with feature showcases
│   ├── globals.css            # Custom CSS design system tokens, badges, buttons, modals
│   ├── login/
│   │   └── page.tsx           # Google OAuth Sign-In portal
│   ├── dashboard/
│   │   └── page.tsx           # Metrics, task overview, recent task list
│   └── tasks/
│       ├── page.tsx           # Full task table with search, scope & status filters
│       └── [id]/
│           └── page.tsx       # Comprehensive task details, assignee switcher, timeline
├── components/
│   ├── auth/
│   │   └── GoogleLoginButton.tsx  # Google Identity Services integration
│   ├── dashboard/
│   │   └── StatCards.tsx          # Total, ToDo, InProgress, Completed counters
│   ├── layout/
│   │   ├── Navbar.tsx             # Brand header, profile info, and sign-out
│   │   ├── Sidebar.tsx            # Navigation links with active scope indicators
│   │   └── AppShell.tsx           # Protected route wrapper with task creation dialog
│   ├── tasks/
│   │   ├── TaskTable.tsx          # Interactive table with complete toggle and actions
│   │   ├── TaskFilters.tsx        # Search input, status & priority dropdowns
│   │   ├── CreateTaskModal.tsx    # Modal form with assignee selector
│   │   └── EditTaskModal.tsx      # Modal form for modifying task attributes
│   └── ui/
│       ├── StatusBadge.tsx        # Status pills with iconography
│       ├── PriorityBadge.tsx      # Priority pills (Low, Medium, High, Urgent)
│       ├── Modal.tsx              # Reusable accessible dialog backdrop
│       └── Toast.tsx              # Notifications with auto-dismissal
├── lib/
│   ├── api.ts                 # Typed fetch client with Bearer auth injection
│   ├── auth.tsx               # AuthContext managing user sessions and logout
│   └── types.ts               # TypeScript interfaces matching Flask schemas
└── .env.example               # Safe environment variable template
```

---

## Authentication Flow

1. User clicks **Sign in with Google** on the login page.
2. Google Identity Services authenticates the user and returns an ID token credential.
3. The frontend POSTs `{ credential }` to the Flask backend endpoint `/api/auth/google`.
4. Flask verifies the Google signature cryptographically and returns an application JWT.
5. The JWT is stored securely in `localStorage` (`hairdrama_auth_token`).
6. All subsequent requests attach `Authorization: Bearer <JWT>`.
7. If an API returns `401 Unauthorized`, the client automatically clears the session and redirects to `/login`.

---

## Environment Variables

Copy `.env.example` to `.env.local`:

```bash
NEXT_PUBLIC_API_URL=http://localhost:5000
NEXT_PUBLIC_GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
```

*Note: The frontend contains zero database passwords, JWT secrets, or Google client secrets.*

---

## Available Scripts

- `npm run dev` — Starts the Next.js development server on `http://localhost:3000`
- `npm run build` — Compiles the production build
- `npm run lint` — Runs ESLint checks
