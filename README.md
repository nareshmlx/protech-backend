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

## 🔐 Security

- JWT-based authentication
- Password hashing with bcrypt
- Role-based access control (RBAC)
- Request validation with Pydantic
- SQL injection prevention (SQLAlchemy ORM)

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