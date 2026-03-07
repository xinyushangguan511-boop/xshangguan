# MIS System - Complete Setup Guide

Complete installation guide for the Cross-Department Management Information System.

## Prerequisites

- **Python 3.10+**
- **Node.js 18+** and npm
- **PostgreSQL 14+**

---

## Quick Start

### 1. PostgreSQL Setup

```sql
-- Connect to PostgreSQL as admin
psql -U postgres

-- Create database and user
CREATE DATABASE mis_db;
CREATE USER mis_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE mis_db TO mis_user;

-- Connect to mis_db and grant schema permissions
\c mis_db
GRANT ALL ON SCHEMA public TO mis_user;

\q
```

### 2. Backend Setup

```bash
cd E:\mis\backend

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Linux/Mac)
# source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment

Create `backend/.env` file:

```env
DATABASE_URL=postgresql+asyncpg://mis_user:your_password@localhost:5432/mis_db
SECRET_KEY=your-secret-key-at-least-32-characters-long-change-this
CORS_ORIGINS=["http://localhost:5173","http://localhost:3000"]
UPLOAD_DIR=uploads
```

### 4. Initialize Database

```bash
cd E:\mis\backend

# Create tables and admin user
python init_database.py --create-admin
```

### 5. Frontend Setup

```bash
cd E:\mis\frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### 6. Start Backend Server

```bash
cd E:\mis\backend

# Activate virtual environment if not active
venv\Scripts\activate

# Start server
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 7. Access the System

- **Frontend:** http://localhost:5173
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs

---

## Production Deployment

### Backend (with Gunicorn)

```bash
pip install gunicorn

gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

### Frontend (Build)

```bash
cd frontend
npm run build

# Output in dist/ folder - serve with nginx or other web server
```

### Nginx Configuration Example

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Frontend
    location / {
        root /path/to/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    # Backend API
    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # File uploads
    location /uploads {
        alias /path/to/backend/uploads;
    }
}
```

---

## Database Schema

| Table | Description |
|-------|-------------|
| `users` | System users (admin, market, engineering, finance) |
| `projects` | Project information and metadata |
| `market_data` | Monthly market department records |
| `engineering_data` | Monthly engineering department records |
| `finance_data` | Monthly finance department records |
| `attachments` | File attachments per project |

---

## User Roles & Permissions

| Role | Permissions |
|------|-------------|
| **Admin** | Full access: manage users, all data |
| **Market** | Create projects, edit market data |
| **Engineering** | Edit engineering data, update project status |
| **Finance** | Edit finance data |

---

## Troubleshooting

### Database Connection Error

```
Error: connection refused
```

- Check PostgreSQL is running: `pg_isready`
- Verify DATABASE_URL in .env
- Check user permissions

### CORS Error in Browser

- Verify CORS_ORIGINS in backend .env includes frontend URL
- Restart backend after changing .env

### "Module not found" Error

```bash
# Backend
pip install -r requirements.txt

# Frontend
npm install
```

### Permission Denied on Uploads

```bash
# Create uploads directory
mkdir -p backend/uploads

# Set permissions (Linux)
chmod 755 backend/uploads
```

---

## File Structure

```
mis/
├── backend/
│   ├── app/
│   │   ├── main.py           # FastAPI entry point
│   │   ├── config.py         # Configuration
│   │   ├── database.py       # Database connection
│   │   ├── models/           # SQLAlchemy models
│   │   ├── schemas/          # Pydantic schemas
│   │   ├── routers/          # API endpoints
│   │   ├── services/         # Business logic
│   │   └── utils/            # Utilities
│   ├── uploads/              # File storage
│   ├── init_database.py      # DB initialization
│   ├── requirements.txt      # Python dependencies
│   └── .env                  # Environment config
│
└── frontend/
    ├── src/
    │   ├── components/       # React components
    │   ├── pages/            # Page components
    │   ├── services/         # API services
    │   ├── stores/           # State management
    │   ├── types/            # TypeScript types
    │   └── utils/            # Utilities
    ├── package.json          # Node dependencies
    └── vite.config.ts        # Vite configuration
```

---

## API Endpoints

### Authentication
- `POST /api/auth/login` - User login
- `POST /api/auth/register` - Register (first admin only)
- `GET /api/auth/me` - Current user info
- `PUT /api/auth/profile` - Update profile
- `PUT /api/auth/change-password` - Change password

### Users (Admin only)
- `GET /api/users/` - List all users
- `POST /api/users/` - Create user
- `PUT /api/users/{id}` - Update user
- `PUT /api/users/{id}/reset-password` - Reset password
- `DELETE /api/users/{id}` - Delete user

### Projects
- `GET /api/projects/` - List projects
- `POST /api/projects/` - Create project
- `GET /api/projects/{id}` - Get project
- `PUT /api/projects/{id}` - Update project
- `DELETE /api/projects/{id}` - Delete project

### Department Data
- `GET /api/market/{project_id}/data` - List market data
- `POST /api/market/{project_id}/data` - Create market data
- `PUT /api/market/{project_id}/data/{id}` - Update
- `DELETE /api/market/{project_id}/data/{id}` - Delete

(Similar endpoints for `/api/engineering/` and `/api/finance/`)

### Statistics
- `GET /api/statistics/market/summary` - Market summary
- `GET /api/statistics/engineering/summary` - Engineering summary
- `GET /api/statistics/finance/summary` - Finance summary
- `GET /api/statistics/project/{id}/report` - Project report
