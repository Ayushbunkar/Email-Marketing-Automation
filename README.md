# Hermes Email Marketing Agent

Autonomous email marketing agent powered by open-weight Hermes LLMs.

## Architecture

### Frontend (React + TypeScript + Vite)

The frontend is a standalone React application that communicates exclusively through REST APIs.

**Tech Stack:**
- React 19
- TypeScript
- Vite
- Tailwind CSS
- shadcn/ui
- Lucide Icons
- React Router
- TanStack Query
- React Hook Form
- Zod
- Axios
- Framer Motion
- Recharts
- Sonner

### Backend (FastAPI)

The backend is an API-only FastAPI application that exposes REST endpoints.

**Tech Stack:**
- FastAPI
- SQLAlchemy
- Alembic
- Supabase PostgreSQL
- Redis
- Brevo

## Features

- **Campaign Management**: Create and manage email campaigns with multiple steps
- **Contact Management**: CRM with lifecycle stages and segmentation
- **Email Provider Integration**: Support for Resend, Brevo, and mock provider
- **Inbound Email**: Brevo inbound webhooks for replies and engagement
- **Guardrails**: Hard caps on sends, quiet hours, auto-pause on high bounce/complaint rates
- **Approval Workflow**: Human approval for campaigns and reply drafts
- **Agent Loop**: LLM-powered campaign planning, copywriting, and optimization

## Project Structure

```
Email Marketing/
├── frontend/             # React frontend application
│   └── hermes-frontend/
│       ├── src/
│       │   ├── components/   # Reusable UI components
│       │   ├── pages/        # Page components
│       │   ├── layouts/      # Layout components
│       │   ├── hooks/        # Custom hooks
│       │   ├── services/     # API services
│       │   ├── types/        # TypeScript types
│       │   ├── store/        # State management
│       │   ├── utils/        # Utility functions
│       │   ├── styles/       # Global styles
│       │   ├── assets/       # Static assets
│       │   ├── api/          # API client
│       │   ├── contexts/     # React contexts
│       │   ├── main.tsx      # Entry point
│       │   └── routes.tsx    # Route definitions
│       ├── public/           # Public assets
│       ├── package.json      # Frontend dependencies
│       ├── tsconfig.json     # TypeScript configuration
│       └── vite.config.js    # Vite configuration
├── app/                  # Backend application
│   ├── agent/            # Agent loop and tools
│   ├── api/              # API endpoints
│   ├── config.py         # Configuration
│   ├── db.py             # Database connection
│   ├── llm/              # LLM client
│   ├── models/           # SQLAlchemy models
│   ├── providers/        # Email provider drivers
│   ├── schemas/          # Pydantic schemas
│   ├── services/         # Business logic
│   ├── web/              # Web dashboard and API
│   ├── workers/          # Background workers
│   ├── cli.py            # CLI entry point
│   ├── main.py           # FastAPI app
│   └── __init__.py
├── alembic/              # Database migrations
├── scripts/              # Utility scripts
├── tests/                # Test suite
├── Makefile              # Build targets
├── pyproject.toml        # Python dependencies
├── package.json          # Root package.json
└── .env.example          # Environment variables template
```

## Getting Started

### Prerequisites

- Node.js 18+
- Python 3.12+
- Supabase PostgreSQL (cloud)
- Upstash Redis (cloud)
- Brevo account (for production email)
- OpenRouter account (for LLM access)

### Installation

1. Clone the repository
2. Copy `.env.example` to `.env` and configure with your cloud service credentials:
   ```bash
   cp .env.example .env
   ```
3. Install frontend dependencies:
   ```bash
   cd frontend/hermes-frontend
   npm install
   ```
4. Install Python dependencies:
   ```bash
   cd ../..
   pip install -e .
   ```
5. Run database migrations:
   ```bash
   make db
   ```
6. Seed demo data:
   ```bash
   make seed
   ```

### Running the Application

#### Development Mode

Run everything (frontend + backend + workers):

```bash
npm run dev
```

Run only frontend:

```bash
npm run dev:frontend
```

Run only backend:

```bash
npm run dev:backend
```

#### Production Build

```bash
npm run build
```

## Frontend Development

### Available Scripts

```bash
cd frontend/hermes-frontend

# Run development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Run linter
npm run lint

# Format code
npm run format
```

### Pages

- `/login` - Login page
- `/dashboard` - Dashboard
- `/contacts` - Contact management
- `/segments` - Segment management
- `/campaigns` - Campaign management
- `/templates` - Email templates
- `/inbox` - Inbox
- `/replies` - Reply management
- `/analytics` - Analytics
- `/ai-assistant` - AI Assistant
- `/profile` - User profile
- `/activity-log` - Activity log
- `/system-health` - System health
- `/settings` - Settings

## Backend Development

### API Endpoints

#### Authentication
- `POST /api/auth/login` - Login
- `POST /api/auth/logout` - Logout
- `GET /api/auth/me` - Get current user

#### Contacts
- `GET /api/contacts` - List contacts
- `POST /api/contacts` - Create contact
- `PUT /api/contacts/{id}` - Update contact
- `DELETE /api/contacts/{id}` - Delete contact

#### Campaigns
- `GET /api/campaigns` - List campaigns
- `POST /api/campaigns` - Create campaign
- `GET /api/campaigns/{id}` - Get campaign details
- `PUT /api/campaigns/{id}` - Update campaign
- `DELETE /api/campaigns/{id}` - Delete campaign

#### Templates
- `GET /api/templates` - List templates
- `POST /api/templates` - Create template
- `PUT /api/templates/{id}` - Update template
- `DELETE /api/templates/{id}` - Delete template

#### Analytics
- `GET /api/analytics/dashboard` - Dashboard metrics
- `GET /api/analytics/campaigns` - Campaign analytics
- `GET /api/analytics/contacts` - Contact analytics

#### Inbox
- `GET /api/inbox` - List inbox items
- `GET /api/inbox/{id}` - Get inbox item details

#### Replies
- `GET /api/replies` - List replies
- `POST /api/replies/{id}/approve` - Approve reply
- `POST /api/replies/{id}/reject` - Reject reply

#### Settings
- `GET /api/settings` - Get settings
- `PUT /api/settings` - Update settings

## Development

### Running Tests
```bash
make test
```

### Running Linter
```bash
make lint
```

### Running Celery Worker
```bash
make worker
```

### Running Celery Beat
```bash
make beat
```

## Cloud Services Configuration

The project connects directly to managed cloud services:

- **Database**: Supabase PostgreSQL
- **Redis**: Upstash Redis
- **Email**: Brevo (production) or Mock (development)
- **LLM**: OpenRouter

Configure all service URLs and credentials in your `.env` file.

## Environment Variables

See `.env.example` for all available configuration options.

## License

MIT