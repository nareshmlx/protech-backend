# ProTech Backend - Code Architecture & Explanation

## 📋 Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Layer Responsibilities](#layer-responsibilities)
3. [Directory Structure Explained](#directory-structure-explained)
4. [Authentication Flow](#authentication-flow)
5. [Key Components](#key-components)
6. [Design Patterns](#design-patterns)
7. [Request Lifecycle](#request-lifecycle)

---

## 🏛️ Architecture Overview

This project follows **Clean Architecture** principles with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────┐
│                     API Layer (FastAPI)                 │
│              HTTP Requests/Responses, Routing           │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│                   Service Layer                         │
│          Business Logic, Validation, Orchestration      │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│                 Repository Layer                        │
│            Data Access, Query Building, ORM             │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│              Infrastructure Layer                       │
│       Database, Redis, MQTT, MinIO, External Services   │
└─────────────────────────────────────────────────────────┘
```

### Why This Architecture?

- **Testability**: Each layer can be tested independently
- **Maintainability**: Changes in one layer don't affect others
- **Scalability**: Easy to add new features without breaking existing code
- **Flexibility**: Swap implementations (e.g., change database) without affecting business logic

---

## 📂 Layer Responsibilities

### 1. API Layer (`app/api/v1/endpoints/`)
**Purpose**: Handle HTTP concerns only

**Responsibilities**:
- Define route endpoints
- Parse HTTP requests
- Validate request data (Pydantic schemas)
- Call service layer methods
- Format HTTP responses
- Handle HTTP-specific errors (401, 403, 404, etc.)

**Example**: [`auth.py`](app/api/v1/endpoints/auth.py)
```python
@router.post("/login")
async def login(request: LoginRequest, auth_service: AuthServiceDep):
    auth_data = await auth_service.login(request.email, request.password)
    return {"user": auth_data["user"], "access_token": auth_data["access_token"]}
```

---

### 2. Service Layer (`app/services/`)
**Purpose**: Implement business logic

**Responsibilities**:
- Validate business rules
- Orchestrate multiple repository calls
- Transform data between layers
- Implement business workflows
- Raise domain-specific exceptions

**Example**: [`auth_service.py`](app/services/auth_service.py)
```python
async def login(self, email: str, password: str):
    user = await self.user_repository.get_by_email(email)
    if not user or not password_service.verify_password(password, user.password_hash):
        raise InvalidCredentialsError()
    
    access_token = token_service.create_access_token(str(user.id), user.role.value)
    return {"user": user, "access_token": access_token}
```

---

### 3. Repository Layer (`app/repositories/`)
**Purpose**: Abstract data access

**Responsibilities**:
- Execute database queries
- Map database rows to domain models
- Provide CRUD operations
- Hide SQL/ORM implementation details

**Example**: [`user_repository.py`](app/repositories/user_repository.py)
```python
async def get_by_email(self, email: str) -> Optional[User]:
    result = await self.session.execute(
        select(User).where(User.email == email)
    )
    return result.scalar_one_or_none()
```

---

### 4. Infrastructure Layer (`infrastructure/`)
**Purpose**: Manage external dependencies

**Responsibilities**:
- Database connection management
- Redis client configuration
- MQTT broker integration
- MinIO object storage
- External API clients

**Example**: [`session.py`](infrastructure/db/session.py)
```python
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async for session in db_manager.get_session():
        yield session
```

---

## 📁 Directory Structure Explained

### Core Application (`app/`)

#### `config/`
- **`settings.py`**: Environment variables and configuration using Pydantic Settings
- **`security.py`**: Password hashing (bcrypt) and JWT token utilities

#### `models/`
- SQLAlchemy ORM models
- **`user.py`**: User model with fields, relationships, and enums

#### `schemas/v1/`
- Pydantic models for request/response validation
- **`auth_schemas.py`**: Login, signup, token refresh schemas

#### `repositories/`
- Data access layer
- **`base_repository.py`**: Generic CRUD operations (create, read, update, delete)
- **`user_repository.py`**: User-specific queries

#### `services/`
- Business logic layer
- **`auth_service.py`**: Authentication workflows (signup, login, token refresh)

#### `dependencies/`
- FastAPI dependency injection
- **`auth.py`**: Get current user, verify admin, inject services
- **`database.py`**: Provide database sessions

#### `api/v1/endpoints/`
- HTTP route handlers
- **`auth.py`**: Authentication endpoints (signup, login, me, logout)

#### `exceptions/`
- Custom exception hierarchy
- **`base_exceptions.py`**: Base exceptions (AuthenticationError, ValidationError)
- **`auth_exceptions.py`**: Auth-specific exceptions

#### `middleware/`
- Request/response interceptors
- CORS, logging, error handling

#### `utils/`
- Helper functions
- Crypto, JWT, validators, decorators

---

## 🔐 Authentication Flow

### 1. User Signup Flow
```
1. Client sends POST /api/v1/auth/signup with {email, password, first_name, last_name}
   ↓
2. API endpoint validates request schema (SignupRequest)
   ↓
3. AuthService.signup() checks if email exists
   ↓
4. Password is hashed using bcrypt (12 rounds)
   ↓
5. UserRepository.create() inserts user into database
   ↓
6. User is automatically logged in
   ↓
7. Access token (no expiration) and refresh token (30 days) are generated
   ↓
8. Response: {user, access_token, refresh_token}
```

### 2. User Login Flow
```
1. Client sends POST /api/v1/auth/login with {email, password}
   ↓
2. API endpoint validates request schema (LoginRequest)
   ↓
3. AuthService.login() fetches user by email
   ↓
4. Password is verified using bcrypt.checkpw()
   ↓
5. Check if user.is_active == true
   ↓
6. Update user.last_login_at timestamp
   ↓
7. Generate JWT tokens:
   - Access token: {sub: user_id, role: user_role, type: "access"} - NO expiration
   - Refresh token: {sub: user_id, type: "refresh", exp: 30 days}
   ↓
8. Response: {user, access_token, refresh_token}
```

### 3. Protected Route Access Flow
```
1. Client sends GET /api/v1/auth/me with "Authorization: Bearer <token>"
   ↓
2. FastAPI dependency get_current_user() extracts token from header
   ↓
3. Token is decoded and verified using JWT secret
   ↓
4. Token type is validated (must be "access")
   ↓
5. User is fetched from database using token's "sub" claim
   ↓
6. Check if user.is_active == true
   ↓
7. User object is injected into endpoint
   ↓
8. Response: {user details}
```

### 4. Token Refresh Flow
```
1. Client sends POST /api/v1/auth/refresh with {refresh_token}
   ↓
2. AuthService.refresh_access_token() decodes refresh token
   ↓
3. Validate token type is "refresh"
   ↓
4. Check if token has expired (exp claim)
   ↓
5. Fetch user from database
   ↓
6. Generate new access token
   ↓
7. Response: {access_token}
```

---

## 🔑 Key Components

### 1. **PasswordService** (`app/config/security.py`)
- Hashes passwords using bcrypt with configurable rounds (default: 12)
- Verifies passwords using constant-time comparison
- Never stores plain text passwords

### 2. **TokenService** (`app/config/security.py`)
- Creates JWT access tokens (no expiration)
- Creates JWT refresh tokens (30-day expiration)
- Decodes and validates tokens
- Validates token type to prevent confusion attacks

### 3. **UserRepository** (`app/repositories/user_repository.py`)
- Extends BaseRepository with User-specific methods
- `get_by_email()`: Find user by email
- `update_last_login()`: Update login timestamp
- `email_exists()`: Check email availability

### 4. **AuthService** (`app/services/auth_service.py`)
- `signup()`: Register new user with validation
- `login()`: Authenticate user and generate tokens
- `refresh_access_token()`: Exchange refresh token for access token
- `get_current_user()`: Decode token and fetch user
- `logout()`: Log event (client discards tokens)

### 5. **Dependencies** (`app/dependencies/auth.py`)
- `get_current_user()`: Extract and validate Bearer token
- `get_current_active_user()`: Ensure user is active
- `get_current_admin()`: Enforce admin role
- Type aliases for cleaner endpoint signatures

---

## 🎨 Design Patterns

### 1. **Repository Pattern**
**Problem**: Direct database access couples business logic to ORM
**Solution**: Repositories abstract data access

```python
# Instead of:
user = await session.execute(select(User).where(User.email == email))

# Use:
user = await user_repository.get_by_email(email)
```

### 2. **Dependency Injection**
**Problem**: Creating service instances manually in every endpoint
**Solution**: FastAPI Depends() injects dependencies

```python
@router.get("/me")
async def get_me(current_user: CurrentActiveUser):
    return current_user  # Injected automatically
```

### 3. **Strategy Pattern** (Future)
**Problem**: Different notification methods (SMS, Email, Push)
**Solution**: Strategy interface with multiple implementations

```python
class NotificationStrategy(ABC):
    async def send(self, recipient: str, message: str): ...

class EmailStrategy(NotificationStrategy): ...
class SMSStrategy(NotificationStrategy): ...
```

### 4. **Factory Pattern**
**Problem**: Complex object creation logic scattered
**Solution**: Factories centralize object creation

```python
class NotificationFactory:
    @staticmethod
    def create(type: str) -> NotificationStrategy:
        if type == "email": return EmailStrategy()
        if type == "sms": return SMSStrategy()
```

---

## 🔄 Request Lifecycle

### Example: `POST /api/v1/auth/login`

```
1. Request arrives at FastAPI
   ↓
2. CORS middleware checks origin
   ↓
3. Logging middleware logs request
   ↓
4. Route matched: auth.login()
   ↓
5. Pydantic validates LoginRequest schema
   ↓
6. FastAPI injects AuthService via Depends()
   ↓
7. auth_service.login() executes:
   - UserRepository fetches user from PostgreSQL
   - Password verified with bcrypt
   - JWT tokens generated
   ↓
8. Response serialized using Pydantic AuthResponse
   ↓
9. Error handler catches any exceptions
   ↓
10. Logging middleware logs response
   ↓
11. Response sent to client
```

---

## 🧪 Testing Strategy

### Unit Tests
- Test services with mocked repositories
- Test repositories with in-memory database
- Test utilities in isolation

### Integration Tests
- Test full request/response cycle
- Test database operations
- Test authentication flows

### Example Test Structure:
```python
async def test_login_success():
    # Setup: Create test user
    # Execute: Call login endpoint
    # Assert: Check response status and tokens
    # Cleanup: Delete test user
```

---

## 📊 Database Schema

### Users Table
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    role VARCHAR(20) DEFAULT 'user',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE,
    last_login_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_is_active ON users(is_active);
CREATE INDEX idx_users_role ON users(role);
```

---

## 🔒 Security Best Practices Implemented

1. **Password Security**
   - Bcrypt hashing with 12 rounds
   - Salt automatically generated
   - Constant-time comparison

2. **JWT Security**
   - HS256 algorithm
   - Token type validation
   - Access tokens: no expiration (persistent login)
   - Refresh tokens: 30-day expiration

3. **Input Validation**
   - Pydantic schemas validate all inputs
   - Email format validation
   - Password length enforcement

4. **Error Handling**
   - Never expose internal error details
   - Generic error messages for auth failures
   - Proper HTTP status codes

5. **Database Security**
   - Async SQLAlchemy with parameterized queries
   - No raw SQL (prevents injection)
   - Connection pooling with limits

---

## 🚀 Adding New Features

### Example: Add "Change Password" Endpoint

1. **Add Schema** (`app/schemas/v1/auth_schemas.py`):
```python
class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=8)
```

2. **Add Service Method** (`app/services/auth_service.py`):
```python
async def change_password(self, user: User, old_password: str, new_password: str):
    if not password_service.verify_password(old_password, user.password_hash):
        raise InvalidCredentialsError()
    new_hash = password_service.hash_password(new_password)
    await self.user_repository.update(user.id, password_hash=new_hash)
```

3. **Add Endpoint** (`app/api/v1/endpoints/auth.py`):
```python
@router.post("/change-password")
async def change_password(
    request: ChangePasswordRequest,
    current_user: CurrentActiveUser,
    auth_service: AuthServiceDep
):
    await auth_service.change_password(
        current_user, request.old_password, request.new_password
    )
    return {"message": "Password changed successfully"}
```

---

## 📚 Further Reading

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy 2.0 Docs](https://docs.sqlalchemy.org/en/20/)
- [Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
- [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [JWT Best Practices](https://datatracker.ietf.org/doc/html/rfc8725)

---

**Questions or Issues?** Check the main README.md or contact the development team.
