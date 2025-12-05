# ==============================================
# SETUP DEVELOPMENT ENVIRONMENT
# ==============================================
# PowerShell script for Windows

Write-Host "╔═══════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║   Tabitabe Development Environment Setup    ║" -ForegroundColor Green
Write-Host "╚═══════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""

# Check if Docker is installed
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Docker is not installed. Please install Docker Desktop first." -ForegroundColor Red
    exit 1
}

# Check if Docker Compose is available
if (-not (Get-Command docker-compose -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Docker Compose is not installed. Please install Docker Compose first." -ForegroundColor Red
    exit 1
}

Write-Host "✓ Docker and Docker Compose are installed" -ForegroundColor Green
Write-Host ""

# Create .env.development if not exists
if (-not (Test-Path .env.development)) {
    Write-Host "⚙ Creating .env.development from .env.example..." -ForegroundColor Yellow
    Copy-Item .env.example .env.development
    Write-Host "✓ .env.development created" -ForegroundColor Green
    Write-Host "⚠ Please update .env.development with your configuration" -ForegroundColor Yellow
} else {
    Write-Host "✓ .env.development already exists" -ForegroundColor Green
}

Write-Host ""

# Start Docker services
Write-Host "🚀 Starting Docker services..." -ForegroundColor Yellow
docker-compose up -d

Write-Host ""
Write-Host "✓ Docker services started successfully!" -ForegroundColor Green
Write-Host ""

# Wait for services to be healthy
Write-Host "⏳ Waiting for services to be healthy..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Check PostgreSQL
Write-Host "Checking PostgreSQL..." -ForegroundColor Yellow
docker-compose exec -T postgres pg_isready -U postgres
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ PostgreSQL is ready" -ForegroundColor Green
} else {
    Write-Host "❌ PostgreSQL is not ready" -ForegroundColor Red
}

# Check Redis
Write-Host "Checking Redis..." -ForegroundColor Yellow
docker-compose exec -T redis redis-cli ping
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Redis is ready" -ForegroundColor Green
} else {
    Write-Host "❌ Redis is not ready" -ForegroundColor Red
}

Write-Host ""
Write-Host "╔═══════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║          Services are running at:            ║" -ForegroundColor Green
Write-Host "╠═══════════════════════════════════════════════╣" -ForegroundColor Green
Write-Host "║ PostgreSQL:  localhost:5432                  ║" -ForegroundColor Green
Write-Host "║ Redis:       localhost:6379                  ║" -ForegroundColor Green
Write-Host "║ MinIO:       localhost:9000 (API)            ║" -ForegroundColor Green
Write-Host "║              localhost:9001 (Console)        ║" -ForegroundColor Green
Write-Host "║ Keycloak:    localhost:8080                  ║" -ForegroundColor Green
Write-Host "║              Admin: admin / admin            ║" -ForegroundColor Green
Write-Host "╚═══════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""

Write-Host "📝 Next steps:" -ForegroundColor Yellow
Write-Host "  1. Setup Python virtual environment: " -NoNewline; Write-Host "cd backend; python -m venv venv" -ForegroundColor Green
Write-Host "  2. Activate virtual environment: " -NoNewline; Write-Host "venv\Scripts\activate" -ForegroundColor Green
Write-Host "  3. Install Python dependencies: " -NoNewline; Write-Host "pip install -r requirements/dev.txt" -ForegroundColor Green
Write-Host "  4. Run Django migrations: " -NoNewline; Write-Host "python manage.py migrate" -ForegroundColor Green
Write-Host "  5. Create superuser: " -NoNewline; Write-Host "python manage.py createsuperuser" -ForegroundColor Green
Write-Host "  6. Run Django server: " -NoNewline; Write-Host "python manage.py runserver" -ForegroundColor Green
Write-Host ""
Write-Host "Happy coding! 🚀" -ForegroundColor Green
