# Local Development Setup Guide

This guide will help you set up the Django backend for local development without affecting the Azure deployment.

## Quick Start

1. **Create a virtual environment** (if not already created):
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On Linux/Mac:
   source venv/bin/activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables** (optional):
   - Copy `.env.example` to `.env` if you want to customize settings
   - The system will work with defaults if no `.env` file exists

4. **Run migrations**:
   ```bash
   python manage.py migrate
   ```

5. **Create a superuser** (optional):
   ```bash
   python manage.py createsuperuser
   ```

6. **Run the development server**:
   ```bash
   python manage.py runserver
   ```

The server will start at `http://127.0.0.1:8000/`

## Database Options

### Option 1: SQLite (Default for Local Development)
If you don't configure a database, the system will automatically use SQLite (`db.sqlite3` file).
This is the easiest option for local development.

### Option 2: Local PostgreSQL
To use PostgreSQL locally:

1. Install PostgreSQL on your machine
2. Create a database:
   ```sql
   CREATE DATABASE pharmacy_db;
   ```

3. Set environment variables in `.env`:
   ```env
   DATABASE_URL=postgres://username:password@localhost:5432/pharmacy_db
   ```
   
   Or use individual variables:
   ```env
   DB_HOST=localhost
   DB_NAME=pharmacy_db
   DB_USER=postgres
   DB_PASSWORD=your_password
   DB_PORT=5432
   ```

## Environment Variables

The system automatically detects if it's running on Azure or locally:
- **Azure**: Detected by `WEBSITE_HOSTNAME` environment variable
- **Local**: Everything else

### Local Development Defaults:
- `DEBUG=True` (unless explicitly set to False)
- `ALLOWED_HOSTS=["*"]` when DEBUG=True
- SQLite database if no PostgreSQL config is found
- CORS allows all origins when DEBUG=True
- No SSL required for database connections

### Azure Production:
- `DEBUG=False` (unless explicitly set to True)
- `ALLOWED_HOSTS` includes Azure hostname
- PostgreSQL with SSL required
- CORS restricted to configured origins

## Key Differences from Azure

1. **Database SSL**: Not required locally, required on Azure
2. **Debug Mode**: Enabled by default locally, disabled on Azure
3. **Static Files**: Uses Django's default storage locally, WhiteNoise on Azure
4. **CORS**: More permissive locally for development convenience

## Troubleshooting

### Database Connection Issues
- If using PostgreSQL locally, ensure PostgreSQL is running
- Check that your database credentials are correct
- If SSL errors occur, the system will automatically try without SSL requirement

### CORS Issues
- Make sure your frontend URL is in `CORS_ALLOWED_ORIGINS` or `DEBUG=True`
- Default ports: `localhost:3000` and `localhost:5173` are allowed

### Static Files Not Loading
- Run `python manage.py collectstatic` if needed
- Check that `STATIC_ROOT` directory exists

## Notes

- The Azure deployment is **not affected** by these changes
- Azure-specific settings are only applied when `WEBSITE_HOSTNAME` is detected
- All local development features are disabled when running on Azure

