# ITOC Dashboard - Setup Guide

## Prerequisites
- Python 3.9+
- PostgreSQL database (Supabase)
- ManageEngine ServiceDesk Plus API access

## Installation Steps

### 1. Clone/Navigate to Project
```bash
cd D:\DEV\Dashboard_ITOC
```

### 2. Create Virtual Environment
```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy `.env.example` to `.env` and fill in your credentials:

```bash
copy .env.example .env
```

Edit `.env`:
```
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@db.YOUR_PROJECT_REF.supabase.co:5432/postgres
SECRET_KEY=your-secret-key-generate-random-32-bytes
TECHNICIAN_KEY=YOUR_MANAGEENGINE_API_KEY
SESSION_TIMEOUT=30
```

**Get Supabase Credentials:**
1. Open Supabase dashboard → Settings → Database
2. Copy Connection String (URI format)
3. Replace password placeholder

**Generate SECRET_KEY:**
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### 5. Setup Database Schema
1. Open Supabase dashboard → SQL Editor
2. Copy content from `migrations/schema.sql`
3. Paste and run in SQL Editor
4. Verify tables created in Table Editor

### 6. Seed Dummy Data
```bash
flask seed-db
```

This creates:
- 10 users (username: `admin`, password: `password123`)
- 20 network links
- 300 SOC events
- 15 handover notes

### 7. Run Development Server
```bash
flask run --debug
```

Access: http://localhost:5000

### 8. Login
- Username: `admin`
- Password: `password123`

## ManageEngine Integration

### Sync Tickets Manually
Click "Sync ManageEngine" button in Service Desk tab, or use API:
```bash
curl -X POST http://localhost:5000/api/tickets/sync
```

### Verify API Connection
Test ManageEngine endpoint:
```bash
curl -H "TECHNICIAN_KEY: YOUR_KEY" "http://helpdesk.pelindomultiterminal.co.id:8080/api/v3/requests?from_date=2026-10-01&to_date=2026-10-06"
```

## Project Structure
```
Dashboard_ITOC/
├── app.py                    # Flask main app
├── config.py                 # Configuration loader
├── models.py                 # SQLAlchemy models
├── requirements.txt          # Python dependencies
├── .env                      # Environment variables (create from .env.example)
├── migrations/
│   └── schema.sql           # Database schema
├── routes/
│   ├── auth.py              # Login/logout endpoints
│   ├── api_tickets.py       # Service Desk API
│   ├── api_handovers.py     # Handover CRUD
│   └── api_shifts.py        # Shift calendar
├── utils/
│   ├── db.py                # Database connection
│   ├── auth_middleware.py   # Role-based access control
│   ├── manageengine.py      # ManageEngine sync utility
│   └── dummy_generator.py   # Seed data generator
├── static/
│   ├── css/main.css         # Styling (dark mode, grid)
│   └── js/
│       ├── api.js           # Fetch wrapper
│       ├── app.js           # Main app logic
│       ├── charts.js        # Chart.js helpers
│       ├── components.js    # UI components
│       └── import.js        # Excel parser (SheetJS)
└── templates/
    ├── login.html           # Login page
    └── index.html           # Main dashboard
```

## MVP Features (Phase 1)

### Implemented:
- ✅ Login/logout with session management
- ✅ Tab: Ringkasan (KPI cards + open handovers)
- ✅ Tab: Service Desk (ticket list + ManageEngine sync)
- ✅ Tab: Serah Terima (handover list)
- ✅ Tab: Tim & Jadwal (14-day shift calendar)
- ✅ Dark mode toggle (auto + manual)
- ✅ Real-time WIB clock
- ✅ Responsive grid layout
- ✅ Role-based access control

### Coming in Phase 2-4:
- ⏳ NOC & SLA analytics (link ranking, availability charts)
- ⏳ SOC dashboard (threat trends, blocked URLs)
- ⏳ Handover CRUD (create/edit/delete)
- ⏳ Excel import (SheetJS upload)
- ⏳ User management (Admin panel)
- ⏳ Advanced charts (Chart.js trends)

## Troubleshooting

### Database Connection Failed
- Verify `DATABASE_URL` in `.env`
- Check Supabase project is active
- Test connection: `psql "postgresql://..."`

### ManageEngine Sync Failed
- Verify `TECHNICIAN_KEY` in `.env`
- Check API endpoint accessible
- Review error in Flask console

### Session Expired Immediately
- Verify `SECRET_KEY` is set
- Check Flask session folder writable
- Clear browser cookies

### Dark Mode Not Working
- Clear browser cache
- Check localStorage: `localStorage.getItem('theme')`

## Default Users (After Seed)
| Username | Password | Role |
|----------|----------|------|
| admin | password123 | Admin |
| lead1 | password123 | Lead |
| analyst1 | password123 | ITOC Analyst |
| manager | password123 | Manajemen |

## API Endpoints

### Authentication
- `POST /api/login` - Login
- `POST /api/logout` - Logout
- `GET /api/session` - Check session

### Tickets
- `GET /api/tickets?page=1&limit=50` - List tickets
- `POST /api/tickets/sync` - Sync from ManageEngine

### Handovers
- `GET /api/handovers` - List handovers

### Shifts
- `GET /api/shifts/calendar` - 14-day shift calendar

## Next Steps
1. Configure `.env` with your credentials
2. Run database migrations
3. Seed dummy data
4. Start Flask server
5. Test ManageEngine sync
6. Customize shift rotation pattern (edit `routes/api_shifts.py`)
7. Deploy Phase 2 features (NOC, SOC, CRUD operations)

## Support
For issues or questions, check:
- Flask console logs
- Browser console (F12)
- Supabase logs (Dashboard → Logs)
- ManageEngine API documentation
