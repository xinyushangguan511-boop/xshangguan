# MIS Backend Setup Guide

## Prerequisites

1. **Python 3.10+** installed
2. **PostgreSQL** database server running
3. Database created (e.g., `mis_db`)
4. Database user with permissions

## Quick Setup

### 1. Create Virtual Environment

```bash
cd E:\mis\backend
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

Create `.env` file in the backend folder:

```env
DATABASE_URL=postgresql+asyncpg://username:password@localhost:5432/mis_db
SECRET_KEY=your-secret-key-minimum-32-characters-long
CORS_ORIGINS=["http://localhost:5173","http://localhost:3000"]
UPLOAD_DIR=uploads
```

Replace `username`, `password`, and `mis_db` with your PostgreSQL credentials.

### 4. Initialize Database

**Option A: Using the script (recommended)**

```bash
python init_database.py --create-admin
```

This will:
- Create all database tables
- Prompt you to create an admin user

**Option B: Using the batch file (Windows)**

```bash
setup_db.bat
```

### 5. Start the Server

```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Existing Database Upgrade

If you pulled a newer backend version into an existing database, run the incremental migration once before starting the server:

```bash
python migrate_db.py
```

This is required for schema additions such as the attachments.module column used by the new attachment categorization logic.

The API will be available at: http://localhost:8000

API documentation: http://localhost:8000/docs

## Database Tables

| Table | Description |
|-------|-------------|
| users | System users with roles |
| projects | Project information |
| market_data | Monthly market department data |
| engineering_data | Monthly engineering department data |
| finance_data | Monthly finance department data |
| attachments | File attachments |

## User Roles

| Department | Permissions |
|------------|-------------|
| admin | Full access to everything |
| market | Create projects, edit market data |
| engineering | Edit engineering data, update project status |
| finance | Edit finance data |

## File Structure

```
backend/
├── app/
│   ├── main.py           # FastAPI entry point
│   ├── config.py         # Settings
│   ├── database.py       # DB connection
│   ├── models/           # SQLAlchemy models
│   ├── schemas/          # Pydantic schemas
│   ├── routers/          # API endpoints
│   ├── services/         # Business logic
│   └── utils/            # Helpers
├── uploads/              # File storage
├── init_database.py      # DB initialization
├── requirements.txt      # Dependencies
└── .env                  # Configuration
```

## Troubleshooting

### Database connection error
- Verify PostgreSQL is running
- Check DATABASE_URL in .env file
- Ensure database and user exist

### Permission denied errors
- Make sure user has permissions on the database
- Grant all privileges: `GRANT ALL PRIVILEGES ON DATABASE mis_db TO username;`

### Tables not created
- Run `python init_database.py` again
- Check for error messages in console
