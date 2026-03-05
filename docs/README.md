# Cross-Department MIS

A Management Information System connecting Marketing, Engineering, and Finance departments with unified project management, monthly data entry, file attachments, and role-based permissions.

## Tech Stack

- **Backend**: FastAPI + SQLAlchemy + PostgreSQL
- **Frontend**: React TypeScript + Ant Design
- **Auth**: JWT tokens
- **File Storage**: Local filesystem

## Project Structure

```
E:/mis/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app entry
│   │   ├── config.py            # Settings & env vars
│   │   ├── database.py          # DB connection
│   │   ├── models/              # SQLAlchemy models
│   │   ├── schemas/             # Pydantic schemas
│   │   ├── routers/             # API routes
│   │   ├── services/            # Business logic
│   │   └── utils/               # Helpers
│   ├── uploads/                 # File storage
│   ├── requirements.txt
│   └── alembic/                 # DB migrations
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/            # API calls
│   │   ├── stores/              # State management
│   │   ├── types/               # TypeScript types
│   │   └── utils/
│   ├── package.json
│   └── vite.config.ts
└── docs/
```

## Setup

### Prerequisites

- Python 3.10+
- Node.js 18+
- PostgreSQL 14+

### Database Setup

1. Create a PostgreSQL database:
```sql
CREATE DATABASE mis_db;
```

### Backend Setup

1. Create virtual environment:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment:
```bash
cp .env.example .env
# Edit .env with your database credentials
```

4. Run migrations:
```bash
alembic upgrade head
```

5. Start server:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup

1. Install dependencies:
```bash
cd frontend
npm install
```

2. Start development server:
```bash
npm run dev
```

## API Documentation

Once the backend is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Endpoints

### Auth
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login, returns JWT
- `POST /api/auth/refresh` - Refresh token
- `GET /api/auth/me` - Current user info

### Projects
- `GET /api/projects/` - List projects
- `POST /api/projects/` - Create project (Marketing only)
- `GET /api/projects/{id}` - Project details
- `PUT /api/projects/{id}` - Update project
- `DELETE /api/projects/{id}` - Delete project (Marketing only)

### Market Data
- `GET /api/market/{project_id}/data` - List market entries
- `POST /api/market/{project_id}/data` - Add monthly entry
- `PUT /api/market/{project_id}/data/{id}` - Update entry
- `DELETE /api/market/{project_id}/data/{id}` - Delete entry

### Engineering Data
- `GET /api/engineering/{project_id}/data` - List engineering entries
- `POST /api/engineering/{project_id}/data` - Add monthly entry
- `PUT /api/engineering/{project_id}/data/{id}` - Update entry
- `DELETE /api/engineering/{project_id}/data/{id}` - Delete entry
- `PUT /api/engineering/{project_id}/status` - Update project status

### Finance Data
- `GET /api/finance/{project_id}/data` - List finance entries
- `POST /api/finance/{project_id}/data` - Add monthly entry
- `PUT /api/finance/{project_id}/data/{id}` - Update entry
- `DELETE /api/finance/{project_id}/data/{id}` - Delete entry

### Attachments
- `GET /api/attachments/{project_id}` - List attachments
- `POST /api/attachments/{project_id}/upload` - Upload file
- `GET /api/attachments/{id}/download` - Download file
- `DELETE /api/attachments/{id}` - Delete file

### Statistics
- `GET /api/statistics/market/summary` - Market aggregations
- `GET /api/statistics/engineering/summary` - Engineering aggregations
- `GET /api/statistics/finance/summary` - Finance aggregations
- `GET /api/statistics/project/{id}/report` - Project full report

## Permission Rules

| Department | Create Project | View Data | Edit Data |
|------------|---------------|-----------|-----------|
| Market | Yes | All | Market data + Project |
| Engineering | No | All | Engineering data + Status |
| Finance | No | All | Finance data |
| Admin | Yes | All | All |

## Default Users

Register users through the UI or API. Use these departments:
- `market` - Marketing department
- `engineering` - Engineering department
- `finance` - Finance department
- `admin` - Administrator

## Features

- **Dashboard**: Overview with charts and statistics
- **Projects**: CRUD operations with status management
- **Department Data**: Monthly data entry for each department
- **File Attachments**: Upload/download files per project
- **Statistics**: Aggregated reports and charts
- **Role-based Access**: Department-specific permissions
