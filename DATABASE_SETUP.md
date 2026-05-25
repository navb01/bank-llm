# PostgreSQL Setup Guide for Bank LLM

## Quick Start (2 Options)

### Option 1: SQLite (Zero Setup - Recommended for Testing)
**Best for**: Development, testing, single-server deployment
- No installation required
- Database file: `bank_llm.db` (automatically created)
- Perfect for your current setup
- Default already configured

**Just run**:
```bash
python backend/db_init.py
```

Database will be created as SQLite at: `c:\Users\aruna\OneDrive\Desktop\bank llm\bank-llm\bank_llm.db`

---

### Option 2: PostgreSQL (Recommended for Production/Scaling)
**Best for**: Multi-user access, cloud deployment, enterprise scaling

#### Step 1: Install PostgreSQL
Windows:
- Download from: https://www.postgresql.org/download/windows/
- Choose version 15+ (latest stable)
- During installation:
  - Accept all defaults
  - Set superuser password (remember it!)
  - Port: 5432 (default)
  - Installation directory: `C:\Program Files\PostgreSQL`

#### Step 2: Create Database
After installation, open **pgAdmin** (included) or use Command Line:

**Via pgAdmin (GUI - Easier)**:
1. Open pgAdmin from Start menu
2. Connect with default superuser `postgres`
3. Right-click → Create → Database
4. Name: `bank_llm`
5. Click Create

**Via Command Line**:
```bash
psql -U postgres
CREATE DATABASE bank_llm;
\q
```

#### Step 3: Configure Connection
Edit `backend/config.py` and replace:
```python
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"sqlite:///{BASE_DIR / 'bank_llm.db'}"
)
```

With:
```python
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:your_password@localhost:5432/bank_llm"
)
```

Or set environment variable:
```bash
set DATABASE_URL=postgresql://postgres:your_password@localhost:5432/bank_llm
```

#### Step 4: Initialize Database
```bash
cd backend
python db_init.py
```

This will:
- Create all tables
- Migrate data from JSON files (if any)
- Set up indexes for performance

---

## Verify Installation

Run this to confirm database is working:

```bash
cd backend
python -c "from database import SessionLocal, init_db; init_db(); print('✓ Database ready')"
```

---

## Data Migration (Optional)

If you have existing data in JSON files, the initialization script will automatically migrate:
- User profiles → `user_profiles` table
- Query cache → `query_cache` table
- Performance metrics → `performance_metrics` table
- Query rewrites → `query_rewrites` table
- Feedback → `feedback` table

No manual action needed!

---

## Connection Strings Reference

### SQLite (Local File)
```
sqlite:///C:/path/to/bank_llm.db
```

### PostgreSQL (Local)
```
postgresql://username:password@localhost:5432/database_name
```

### PostgreSQL (Remote Cloud)
```
postgresql://user:pass@cloud-host.region.rds.amazonaws.com:5432/database_name
```

---

## Troubleshooting

### "Connection refused" error
- **Cause**: PostgreSQL service not running
- **Fix**: 
  - Windows: Start → Services → postgresql-x64-15 → Right-click → Start
  - Or: `net start postgresql-x64-15`

### "No such table" error
- **Cause**: Database not initialized
- **Fix**: Run `python backend/db_init.py`

### "psycopg2 not found" error
- **Cause**: Dependencies not installed
- **Fix**: `pip install -r requirements.txt`

### "Cannot connect to database"
- **Check**: 
  - PostgreSQL is running
  - Credentials are correct
  - Database exists: `psql -l`
  - Port 5432 is not blocked

---

## Performance Tips

### For SQLite (Small Deployments)
- Works great for < 10K records
- No maintenance needed
- Single file backup

### For PostgreSQL (Production)
- Better for > 100K records
- Enable automatic backups
- Monitor with: `SELECT pg_database.datname, pg_size_pretty(pg_database_dn_size(pg_database.oid)) as size FROM pg_database;`
- Use connection pooling in production

---

## Next Steps

1. **Initialize Database**: `python backend/db_init.py`
2. **Start Backend**: `python backend/main.py`
3. **Test**: Visit http://localhost:8000

The system will automatically use your configured database!

---

## Environment Variables

You can configure via `.env` file:

```
DATABASE_URL=postgresql://user:pass@localhost:5432/bank_llm
DB_ECHO=false
LOG_LEVEL=INFO
```

Then load with `python-dotenv` (already in requirements.txt)
