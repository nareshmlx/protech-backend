# ProTech Surveillance System - Backend

AI-powered security system backend using FastAPI, PostgreSQL, Redis, MQTT, and Clean Architecture.

## 📁 Project Structure

```text
protech-backend/
├── app/
│   ├── main.py                     # FastAPI application entry point
│   ├── api/
│   │   └── v1/
│   │       └── endpoints/          # HTTP route handlers
│   ├── config/                     # Settings & security configuration
│   ├── constants/                  # Application-wide constants
│   ├── controllers/                # Bridge between API layer & Service layer.
│   ├── dependencies/               # Dependency injection providers
│   ├── exceptions/                 # Custom exception hierarchy
│   ├── factories/                  # Factory patterns (notification, storage, session)
│   ├── strategies/                 # Business strategy logic
│   ├── models/                     # SQLAlchemy ORM models
│   ├── repositories/               # Data access layer
│   ├── schemas/
│   │   └── v1/                     # Pydantic request/response models
│   ├── services/                   # Business logic layer
│   │   └── strategies/             # Strategy patterns (session, notification, storage)
│   ├── middleware/                 # Auth, CORS, logging, error handling
│   └── utils/                      # Crypto, JWT, validators, decorators
│
├── infrastructure/
│   ├── db/                         # PostgreSQL session management
│   ├── redis/                      # Redis client
│   ├── mqtt/                       # MQTT broker integration
│   └── minio/                      # MinIO storage client
│
├── docker/
│   ├── docker-compose.yml                    
│   └── DockerFile                  
│
├── migrations/                     # Alembic database migration
│
├── requirements.txt
├── alembic.ini
├── .env.example
└── README.md
```

## 🏗️ Architecture

Following **Clean Architecture** with layered design:

- **API Layer**: FastAPI routers - HTTP concerns only
- **Service Layer**: Business logic and orchestration
- **Repository Layer**: Data access abstraction
- **Infrastructure Layer**: External integrations (DB, Redis, MQTT, MinIO)
- **Controller Layer**: Bridge between API Layer and Service Layer with dependency ingestion.

### Key Design Patterns

- **Dependency Injection**: FastAPI `Depends()`
- **Repository Pattern**: Abstract data access
- **Strategy Pattern**: Session storage (Redis/DB), Notifications (SMS/FCM/Email)
- **Factory Pattern**: Dynamic object creation
- **Middleware Pattern**: Cross-cutting concerns (auth, logging, CORS)

## 🚀 Tech Stack

- **FastAPI** - Modern async Python web framework
- **PostgreSQL** - Primary relational database
- **Redis** - Session storage & caching
- **MQTT (Mosquitto)** - Real-time AI event streaming
- **MinIO** - Object storage for video clips
- **Alembic** - Database migrations
- **SQLAlchemy 2.0** - Async ORM

## 🛠️ Development Setup

### Prerequisites
- Python 3.11+
- Docker & Docker Compose
- Git
- UV package manager (recommended) or pip

### Installation Steps

#### 1. Clone the Repository
```bash
git clone <repository-url>
cd protech-backend
```

#### 2. Set Up Environment Variables
```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and update the following critical values:
# - DATABASE_URL: PostgreSQL connection string
# - JWT_SECRET: Generate using: python -c "import secrets; print(secrets.token_urlsafe(32))"
# - CORS_ORIGINS: Your frontend URL(s)
```

#### 3. Start Infrastructure Services
```bash
# Start PostgreSQL, Redis, MinIO, and MQTT using Docker
cd docker
docker-compose up -d

# Verify services are running
docker-compose ps
```

#### 4. Install Python Dependencies

**Using UV (Recommended):**
```bash
# Install UV if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync

# Activate virtual environment
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows
```

**Using pip:**
```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

#### 5. Run Database Migrations
```bash
# Create initial migration
alembic revision --autogenerate -m "Initial migration with User model"

# Apply migrations
alembic upgrade head
```

#### 6. Create Admin User (Optional)
```python
# Run Python shell
python

# Execute the following:
import asyncio
from infrastructure.db.session import db_manager
from app.repositories.user_repository import UserRepository
from app.config.security import password_service
from app.models.user import UserRole

async def create_admin():
    db_manager.init_engine()
    async for session in db_manager.get_session():
        repo = UserRepository(session)
        admin = await repo.create(
            email="admin@protech.com",
            password_hash=password_service.hash_password("AdminPassword123"),
            first_name="Admin",
            last_name="User",
            role=UserRole.ADMIN
        )
        print(f"Admin created: {admin.email}")
        break

asyncio.run(create_admin())
```

#### 7. Start the Application
```bash
# Development mode (with auto-reload)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production mode
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

#### 8. Access the API
- **API Base URL**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## 📚 API Endpoints

### Authentication

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/v1/auth/signup` | Register new user | No |
| POST | `/api/v1/auth/login` | User login | No |
| POST | `/api/v1/auth/refresh` | Refresh access token | No |
| GET | `/api/v1/auth/me` | Get current user | Yes |
| POST | `/api/v1/auth/logout` | Logout user | Yes |
| GET | `/api/v1/auth/admin/users` | Get all users (admin) | Admin |

### Example API Calls

**Signup:**
```bash
curl -X POST "http://localhost:8000/api/v1/auth/signup" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123",
    "first_name": "John",
    "last_name": "Doe"
  }'
```

**Login:**
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123"
  }'
```

**Get Current User:**
```bash
curl -X GET "http://localhost:8000/api/v1/auth/me" \
  -H "Authorization: Bearer <your-access-token>"
```

## 🧪 Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/integration/test_auth_flow.py -v

# Run tests in parallel
pytest -n auto
```

## 🐳 Docker Deployment

```bash
# Build and run with Docker Compose
cd docker
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# View logs
docker-compose logs -f backend

# Stop services
docker-compose down
```

## 📊 Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# View migration history
alembic history

# View current version
alembic current
```

## 🔐 Security Features

- **JWT Authentication**: Access tokens (no expiration) + Refresh tokens (30-day expiration)
- **Password Hashing**: Bcrypt with 12 rounds
- **RBAC**: Role-based access control (USER, ADMIN)
- **Input Validation**: Pydantic schemas with email validation
- **SQL Injection Prevention**: SQLAlchemy ORM with parameterized queries
- **CORS Configuration**: Whitelist-based origin control
- **Secure Headers**: Production-ready security headers

## 🔍 Troubleshooting

### Database Connection Issues
```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# View PostgreSQL logs
docker-compose logs postgres

# Test connection
psql postgresql://postgres:postgres@localhost:5432/protech_surveillance
```

### Migration Issues
```bash
# Reset database (WARNING: deletes all data)
alembic downgrade base
alembic upgrade head

# Or drop and recreate database
docker-compose down -v
docker-compose up -d
```

### Import Errors
```bash
# Ensure you're in the project root and virtual environment is activated
pwd  # Should show: /path/to/protech-backend
which python  # Should show: /path/to/protech-backend/.venv/bin/python

# Reinstall dependencies
uv sync --reinstall  # or pip install -r requirements.txt --force-reinstall
```

## 🌍 Environment Variables Reference

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `DATABASE_URL` | PostgreSQL connection string | - | Yes |
| `JWT_SECRET` | Secret key for JWT signing (min 32 chars) | - | Yes |
| `JWT_ALGORITHM` | JWT signing algorithm | HS256 | No |
| `ACCESS_TOKEN_EXPIRE_HOURS` | Access token expiration (empty = never) | None | No |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token expiration | 30 | No |
| `CORS_ORIGINS` | Allowed CORS origins (comma-separated) | localhost | Yes |
| `REDIS_URL` | Redis connection string | redis://localhost:6379/0 | Yes |
| `MINIO_ENDPOINT` | MinIO server endpoint | localhost:9000 | Yes |
| `MQTT_BROKER` | MQTT broker address | localhost | Yes |
| `BCRYPT_ROUNDS` | Bcrypt hashing rounds | 12 | No |
| `MIN_PASSWORD_LENGTH` | Minimum password length | 8 | No |
| `ENVIRONMENT` | Environment (development/production) | development | No |
| `DEBUG` | Enable debug mode | true | No |

## 📝 Commit Convention

- `setup:` - Workspace/Project Setup
- `feature:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation update
- `refactor:` - Code refactoring
- `test:` - Test additions/updates
- `chore:` - Maintenance tasks
- `setup` - File Setups

---

**Built by BigVision LLC for ProTech AI-Surveillance System**