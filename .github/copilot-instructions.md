# CurioCloud Backend - AI Coding Agent Instructions

## Project Overview
FastAPI-based user authentication system for CurioCloud, an AI-driven teacher lesson planning assistant. Built with clean architecture patterns focusing on separation of concerns and comprehensive testing.

## Architecture Patterns

### Core Structure
- **Models** (`app/models/`): SQLAlchemy ORM models using `Base` from `app.core.database`
- **Schemas** (`app/schemas/`): Pydantic models for request/response validation with `from_attributes = True`
- **Services** (`app/services/`): Business logic classes that take `Session` in `__init__(self, db: Session)`
- **Routers** (`app/routers/`): FastAPI route handlers using dependency injection pattern
- **Dependencies** (`app/dependencies/`): Reusable dependency functions for auth, DB sessions
- **Utils** (`app/utils/`): Stateless utility functions for security, JWT, etc.

### Critical Conventions

#### Database & Configuration
- Database connection via `app.core.database.get_db()` dependency
- Configuration loaded from `.env` using `pydantic_settings.BaseSettings`
- All models inherit from `Base` and use descriptive `comment` fields
- Database operations wrapped in try/catch with proper rollback on errors

#### Authentication Flow
- JWT tokens contain `{"sub": username, "user_id": id}` payload
- Use `HTTPBearer` security scheme, not OAuth2PasswordBearer
- Three auth dependency levels:
  - `get_current_user`: Required auth (401 if missing/invalid)
  - `get_current_active_user`: Requires active user (400 if inactive)
  - `get_optional_current_user`: Optional auth (returns None if missing)

#### Error Handling Pattern
```python
try:
    # business logic
    self.db.commit()
    self.db.refresh(object)
    return result
except HTTPException:
    self.db.rollback()
    raise  # Re-raise HTTP exceptions as-is
except IntegrityError as e:
    self.db.rollback()
    # Parse specific constraint violations
    raise HTTPException(status_code=400, detail="specific message")
except Exception as e:
    self.db.rollback()
    print(f"Debug: {type(e).__name__}: {e}")  # Debug logging
    raise HTTPException(status_code=500, detail="generic error")
```

#### Service Layer Pattern
Services are instantiated with DB session: `AuthService(db)` then called with data models. Always include comprehensive error handling with database rollback.

#### Schema Validation Patterns
- Use `@validator` decorators for complex validation (passwords, usernames)
- Support partial updates with `exclude_unset=True` in service layer
- Custom validators check business rules (unique emails, password strength)

## Development Workflows

### Running the Application
```bash
# Development with auto-reload
uvicorn main:app --reload

# Production deployment  
uvicorn main:app --host 0.0.0.0 --port 8000
```

### Testing Strategy
- Tests use SQLite in-memory database via `conftest.py` fixtures
- Test classes organized by feature: `TestUserRegistration`, `TestUserLogin`
- Use `TestClient` from FastAPI with dependency overrides
- Authentication tests use `auth_headers` and `authenticated_user` fixtures
- Run tests: `pytest tests/ -v` or `pytest tests/test_specific.py::TestClass::test_method -v`

### Database Operations
- Migrations are handled by `Alembic`. Use `alembic revision --autogenerate` and `alembic upgrade head`.
- For initial setup or testing, tables can be created via `create_tables()` in the startup lifespan event (`main.py`).
- Development uses MySQL with PyMySQL driver.
- Connection string format: `mysql+pymysql://user:pass@host:port/db`

## Integration Points

### External Dependencies
- **MySQL**: Primary database with connection pooling (`pool_pre_ping=True`)
- **JWT**: Using `python-jose[cryptography]` with HS256 algorithm
- **Password Hashing**: bcrypt via `passlib[bcrypt]`
- **Email Validation**: Pydantic's `EmailStr` type

### API Design Patterns
- All endpoints under `/api/{module}` prefix (e.g., `/api/auth`, `/api/user`)
- Response models always include `message` field for user feedback
- Status codes: 201 for creation, 200 for success, 401 for auth failures
- Chinese language error messages for user-facing responses

### Environment Configuration
Required `.env` variables:
```
DATABASE_HOST=localhost
DATABASE_USER=username  
DATABASE_PASSWORD=password
DATABASE_NAME=curio_cloud
JWT_SECRET_KEY=your_secret_key
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
```

## Key Files for Context
- `main.py`: FastAPI app setup, CORS, router registration, lifespan events
- `app/core/config.py`: Centralized settings with `@property database_url`
- `app/dependencies/auth.py`: Authentication dependency functions
- `tests/conftest.py`: Test configuration, fixtures, database override patterns

## Common Tasks
- **New API endpoint**: Create router function → register in `main.py` → add corresponding service method → write tests
- **Database model changes**: Update model → update schemas → adjust services → update tests
- **Authentication**: Use appropriate dependency (`get_current_user` vs `get_current_active_user`)
- **Error handling**: Follow the established try/catch pattern with proper DB rollback

## AI Teaching Module

### Conversational Flow
- State machine defined in `app/conversation_flow.py`
- Steps: ask_subject → ask_grade → ask_topic → ask_duration → finalize
- Sessions stored in `lesson_creation_sessions` table
- AI generation via OpenRouter API with structured prompts

### AI Service Integration
- `AIService` class handles OpenRouter API calls
- Generates structured lesson plans with activities, objectives, outlines
- Validates AI responses and handles retries
- Uses Gemini 2.5 Flash model by default

### Teaching Service Patterns
- Async processing for AI generation
- Session state management with status tracking
- Lesson plan CRUD with activity relationships
- Proper error handling for AI failures

Focus on maintaining the clean separation between routers (HTTP), services (business logic), and models (data), while ensuring comprehensive error handling and testing coverage.