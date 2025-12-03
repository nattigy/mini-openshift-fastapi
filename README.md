# Mini OpenShift - FastAPI Backend

A simplified OpenShift-like platform backend built with FastAPI and Kubernetes integration.

## Features

- 🔐 **Authentication & Authorization**: JWT-based authentication with role-based access control
- 👥 **User Management**: Create, update, delete, and search users
- 📦 **Project Management**: Kubernetes namespace-backed projects
- 🚀 **Deployment Management**: Create, scale, and manage Kubernetes deployments
- 🐳 **Pod Management**: Monitor, view logs, and manage pods
- 🔄 **Real-time K8s Integration**: Direct integration with Kubernetes API

## Tech Stack

- **Framework**: FastAPI
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Authentication**: JWT tokens with bcrypt password hashing
- **Kubernetes**: kubernetes_asyncio for async K8s operations
- **Migrations**: Alembic
- **Validation**: Pydantic v2

## Prerequisites

- Python 3.8+
- PostgreSQL database
- Kubernetes cluster (local or remote)
- kubectl configured

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/nattigy/mini-openshift-fastapi.git
   cd mini-openshift-fastapi
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   
   Create a `.env` file in the root directory:
   ```env
   DATABASE_URL=postgresql://user:password@localhost/miniopenshift
   SECRET_KEY=your-secret-key-here
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   ```

5. **Initialize the database**
   ```bash
   python create_db.py
   alembic upgrade head
   ```

## Running the Application

### Development Server

```bash
uvicorn app.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`

### API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Default Credentials

- **Email**: `test@example.com`
- **Password**: `password123`

## API Endpoints

### Authentication
- `POST /api/v1/login/access-token` - Login and get access token
- `POST /api/v1/login/test-token` - Test token validity

### Users
- `GET /api/v1/users/` - List all users (admin only)
- `POST /api/v1/users/` - Create new user (admin only)
- `GET /api/v1/users/me` - Get current user
- `PUT /api/v1/users/me` - Update current user
- `GET /api/v1/users/{id}` - Get user by ID
- `PUT /api/v1/users/{id}` - Update user (admin only)
- `DELETE /api/v1/users/{id}` - Delete user (admin only)

### Projects
- `GET /api/v1/projects/` - List all projects
- `POST /api/v1/projects/` - Create new project
- `GET /api/v1/projects/{id}` - Get project by ID
- `PUT /api/v1/projects/{id}` - Update project
- `DELETE /api/v1/projects/{id}` - Delete project

### Deployments
- `GET /api/v1/projects/{id}/deployments` - List deployments
- `POST /api/v1/projects/{id}/deployments` - Create deployment
- `GET /api/v1/projects/{id}/deployments/{name}` - Get deployment
- `PATCH /api/v1/projects/{id}/deployments/{name}/scale` - Scale deployment
- `DELETE /api/v1/projects/{id}/deployments/{name}` - Delete deployment

### Pods
- `GET /api/v1/projects/{id}/pods` - List pods
- `GET /api/v1/projects/{id}/pods/{name}` - Get pod details
- `GET /api/v1/projects/{id}/pods/{name}/logs` - Get pod logs
- `DELETE /api/v1/projects/{id}/pods/{name}` - Delete pod

## Testing

### Run All Tests
```bash
./run_all_tests.sh
```

### Run Individual Test Suites
```bash
# API tests
python tests/test_api.py

# Kubernetes integration
python tests/test_k8s_integration.py

# Deployment management
python tests/test_deployment_management.py

# Pod management
python tests/test_pod_management.py

# Additional endpoints
python tests/test_additional_endpoints.py

# Comprehensive test suite
python tests/test_all_apis.py
```

For detailed testing instructions, see [README_TESTING.md](README_TESTING.md)

## Project Structure

```
mini-openshift-fastapi/
├── app/
│   ├── api/
│   │   ├── deps.py              # Dependencies
│   │   └── v1/
│   │       ├── api.py           # API router
│   │       └── endpoints/       # API endpoints
│   ├── core/
│   │   ├── config.py            # Configuration
│   │   └── security.py          # Security utilities
│   ├── crud/                    # Database operations
│   ├── models/                  # SQLAlchemy models
│   ├── schemas/                 # Pydantic schemas
│   ├── services/                # Business logic & K8s integration
│   └── main.py                  # FastAPI application
├── alembic/                     # Database migrations
├── tests/                       # Test suites
├── docs/                        # Documentation
├── requirements.txt             # Python dependencies
└── README.md                    # This file
```

## Kubernetes Integration

This application integrates directly with Kubernetes to:
- Create namespaces for each project
- Manage deployments within project namespaces
- Monitor and manage pods
- Stream pod logs in real-time

Ensure your `kubectl` is configured and you have access to a Kubernetes cluster.

## Documentation

- [Testing Guide](README_TESTING.md) - Comprehensive testing instructions
- [Quick Reference](TESTING_QUICK_REFERENCE.md) - Quick testing commands
- [Project Overview](docs/project_overview.md) - High-level architecture
- [Deployment Management](docs/deployment_management_walkthrough.md) - Deployment features
- [Pod Management](docs/pod_management_walkthrough.md) - Pod management features
- [API Test Report](docs/comprehensive_api_test_report.md) - Test coverage

## Development

### Database Migrations

Create a new migration:
```bash
alembic revision --autogenerate -m "description"
```

Apply migrations:
```bash
alembic upgrade head
```

Rollback:
```bash
alembic downgrade -1
```

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
