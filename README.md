# Authentication Management Component

A robust, secure authentication and authorization service built with FastAPI, JWT, SQLAlchemy, and PostgreSQL.

## Features

- **User Authentication**
  - Email/Password registration and login
  - JWT-based authentication with access and refresh tokens
  - Password hashing with Bcrypt
  - Email verification
  - Password reset functionality

- **Authorization**
  - Role-based access control
  - Permission-based authorization
  - Scope-based token validation

- **Security Features**
  - Protection against common attacks (CSRF, XSS, etc.)
  - Rate limiting
  - IP-based blocking
  - Session management

- **User Management**
  - User profile management
  - Account settings
  - Multi-factor authentication (optional)

- **API Integration**
  - RESTful API endpoints
  - Comprehensive API documentation with Swagger/ReDoc
  - API versioning

## Tech Stack

- **Backend Framework**: FastAPI
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Authentication**: JWT (JSON Web Tokens)
- **Password Hashing**: Bcrypt
- **Validation**: Pydantic
- **Email Service**: SMTP/SendGrid integration
- **Testing**: pytest, pytest-asyncio
- **Code Quality**: mypy, flake8, black
- **Build System**: Poetry
- **Containerization**: Docker, docker-compose
- **CI/CD**: GitHub Actions

## Getting Started

### Prerequisites

- Python 3.9+
- PostgreSQL
- Docker and docker-compose (optional)

### Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/yourusername/auth-server-fastapi.git
   cd auth-server-fastapi
   ```

2. **Set up environment variables**

   ```bash
   cp .env.example .env
   # Edit .env file with your configuration
   ```

3. **Install dependencies with Poetry**

   ```bash
   poetry install
   ```

   Or with pip:

   ```bash
   pip install -r requirements.txt
   ```

4. **Run database migrations**

   ```bash
   alembic upgrade head
   ```

5. **Start the development server**

   ```bash
   uvicorn app.main:app --reload
   ```

### Using Docker

1. **Build and start the containers**

   ```bash
   docker-compose up -d --build
   ```

2. **Run migrations in the container**

   ```bash
   docker-compose exec app alembic upgrade head
   ```

## API Documentation

Once the server is running, you can access the API documentation at:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Development

### Project Structure

```
auth-server-fastapi/
├── app/
│   ├── api/
│   │   ├── dependencies/
│   │   ├── endpoints/
│   │   └── routes/
│   ├── core/
│   │   ├── config.py
│   │   ├── security.py
│   │   └── settings.py
│   ├── db/
│   │   ├── base.py
│   │   ├── session.py
│   │   └── init_db.py
│   ├── models/
│   ├── schemas/
│   ├── services/
│   ├── utils/
│   └── main.py
├── alembic/
├── tests/
├── .env.example
├── .gitignore
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
└── README.md
```

### Running Tests

```bash
pytest
```

With coverage:

```bash
pytest --cov=app
```

### Code Quality

```bash
# Format code
black app tests

# Sort imports
isort app tests

# Type checking
mypy app

# Linting
flake8 app tests
```

## License

[MIT License](LICENSE)

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request
