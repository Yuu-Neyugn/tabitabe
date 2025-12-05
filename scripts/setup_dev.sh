#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}╔═══════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   Tabitabe Development Environment Setup    ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════╝${NC}"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed. Please install Docker first.${NC}"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose is not installed. Please install Docker Compose first.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Docker and Docker Compose are installed${NC}"
echo ""

# Create .env.development if not exists
if [ ! -f .env.development ]; then
    echo -e "${YELLOW}⚙ Creating .env.development from .env.example...${NC}"
    cp .env.example .env.development
    echo -e "${GREEN}✓ .env.development created${NC}"
    echo -e "${YELLOW}⚠ Please update .env.development with your configuration${NC}"
else
    echo -e "${GREEN}✓ .env.development already exists${NC}"
fi

echo ""

# Start Docker services
echo -e "${YELLOW}🚀 Starting Docker services...${NC}"
docker-compose up -d

echo ""
echo -e "${GREEN}✓ Docker services started successfully!${NC}"
echo ""

# Wait for services to be healthy
echo -e "${YELLOW}⏳ Waiting for services to be healthy...${NC}"
sleep 10

# Check PostgreSQL
echo -e "${YELLOW}Checking PostgreSQL...${NC}"
docker-compose exec -T postgres pg_isready -U postgres
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ PostgreSQL is ready${NC}"
else
    echo -e "${RED}❌ PostgreSQL is not ready${NC}"
fi

# Check Redis
echo -e "${YELLOW}Checking Redis...${NC}"
docker-compose exec -T redis redis-cli ping
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Redis is ready${NC}"
else
    echo -e "${RED}❌ Redis is not ready${NC}"
fi

echo ""
echo -e "${GREEN}╔═══════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║          Services are running at:            ║${NC}"
echo -e "${GREEN}╠═══════════════════════════════════════════════╣${NC}"
echo -e "${GREEN}║ PostgreSQL:  ${NC}localhost:5432${GREEN}                 ║${NC}"
echo -e "${GREEN}║ Redis:       ${NC}localhost:6379${GREEN}                 ║${NC}"
echo -e "${GREEN}║ MinIO:       ${NC}localhost:9000${GREEN} (API)           ║${NC}"
echo -e "${GREEN}║              ${NC}localhost:9001${GREEN} (Console)       ║${NC}"
echo -e "${GREEN}║ Keycloak:    ${NC}localhost:8080${GREEN}                 ║${NC}"
echo -e "${GREEN}║              ${NC}Admin: admin / admin${GREEN}          ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════╝${NC}"
echo ""

echo -e "${YELLOW}📝 Next steps:${NC}"
echo -e "  1. Setup Python virtual environment: ${GREEN}cd backend && python -m venv venv${NC}"
echo -e "  2. Activate virtual environment: ${GREEN}source venv/bin/activate${NC} (Linux/Mac) or ${GREEN}venv\\Scripts\\activate${NC} (Windows)"
echo -e "  3. Install Python dependencies: ${GREEN}pip install -r requirements/dev.txt${NC}"
echo -e "  4. Run Django migrations: ${GREEN}python manage.py migrate${NC}"
echo -e "  5. Create superuser: ${GREEN}python manage.py createsuperuser${NC}"
echo -e "  6. Run Django server: ${GREEN}python manage.py runserver${NC}"
echo ""
echo -e "${GREEN}Happy coding! 🚀${NC}"
