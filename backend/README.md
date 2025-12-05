# Tabitabe Backend

Django backend for Tabitabe Restaurant Discovery Platform.

## Quick Start

### 1. Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements/dev.txt
```

### 3. Setup Environment Variables

```bash
# Copy .env.example from root
cp ../.env.example ../.env.development
# Edit .env.development with your settings
```

### 4. Run Migrations

```bash
python manage.py migrate
```

### 5. Create Superuser

```bash
python manage.py createsuperuser
```

### 6. Run Development Server

```bash
python manage.py runserver
```

Visit http://localhost:8000/admin/

## Project Structure

```
backend/
├── config/              # Django settings
│   ├── settings/
│   │   ├── base.py     # Base settings
│   │   ├── development.py
│   │   ├── production.py
│   │   └── test.py
│   ├── urls.py
│   ├── wsgi.py
│   ├── asgi.py
│   └── celery.py
├── apps/               # Django applications
│   ├── accounts/      # User authentication
│   ├── restaurants/   # Restaurant management
│   ├── customers/     # Customer features
│   ├── reviews/       # Review system
│   ├── campaigns/     # Gift cards & stamp rallies
│   ├── media_manager/ # Media handling
│   ├── notifications/ # Email/Push notifications
│   └── core/          # Shared utilities
├── api/               # REST API
│   └── v1/
│       ├── auth/
│       ├── customers/
│       ├── restaurants/
│       └── admin/
├── tests/             # Test suites
├── requirements/      # Python dependencies
└── docker/            # Docker configurations
```

## Commands

### Run Celery Worker

```bash
celery -A config worker -l info
```

### Run Celery Beat

```bash
celery -A config beat -l info
```

### Run Tests

```bash
pytest
```

### Code Formatting

```bash
black .
ruff check .
```

## API Documentation

- Swagger UI: http://localhost:8000/api/docs/
- ReDoc: http://localhost:8000/api/redoc/
- Schema: http://localhost:8000/api/schema/
