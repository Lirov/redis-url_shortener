# Redis URL Shortener

A fast, secure URL shortener built with FastAPI, Redis, and JWT authentication.

## Features

- 🔗 **URL Shortening**: Create short URLs with custom codes
- 🔐 **Authentication**: JWT-based user authentication
- 📊 **Analytics**: Track clicks and view popular links
- ⏰ **TTL Support**: Set expiration times for URLs
- 🚀 **Fast**: Built with FastAPI and Redis for high performance
- 🐳 **Docker Ready**: Easy deployment with Docker Compose

## API Endpoints

### Authentication
- `POST /auth/register` - Register a new user
- `POST /auth/login` - Login and get JWT token

### URL Management
- `POST /shorten` - Create a short URL (requires authentication)
- `GET /{code}` - Redirect to original URL (public)
- `GET /stats/{code}` - Get URL statistics (requires authentication)
- `GET /top` - Get most popular URLs (requires authentication)

## Quick Start

### Prerequisites
- Python 3.11+
- Redis server
- Docker (optional)

### Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd redis-url-shortener
   ```

2. **Create virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Start Redis**
   ```bash
   # Using Docker
   docker run -d -p 6379:6379 redis:7
   
   # Or install Redis locally
   # Ubuntu/Debian: sudo apt install redis-server
   # macOS: brew install redis
   # Windows: Download from https://redis.io/download
   ```

5. **Run the application**
   ```bash
   uvicorn app.main:app --reload
   ```

The API will be available at `http://localhost:8000`

### Using Docker Compose

```bash
docker-compose up --build
```

## Usage Examples

### 1. Register a User
```bash
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"username": "myuser", "password": "mypassword"}'
```

### 2. Login
```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "myuser", "password": "mypassword"}'
```

Response:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer"
}
```

### 3. Create Short URL
```bash
curl -X POST "http://localhost:8000/shorten" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com", "ttl_sec": 3600}'
```

Response:
```json
{
  "code": "abc123",
  "short_url": "http://localhost:8000/abc123"
}
```

### 4. Get URL Statistics
```bash
curl -X GET "http://localhost:8000/stats/abc123" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 5. Get Popular URLs
```bash
curl -X GET "http://localhost:8000/top?limit=10" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Configuration

Create a `.env` file in the project root:

```env
REDIS_URL=redis://localhost:6379/0
BASE_URL=http://localhost:8000
JWT_SECRET=your-secret-key-here
JWT_EXPIRES_MINUTES=60
DEFAULT_CODE_LENGTH=7
```

## Development

### Running Tests
```bash
pytest -v
```

### Code Formatting
```bash
black .
ruff check .
```

### Project Structure
```
redis-url-shortener/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI application
│   ├── config.py        # Configuration settings
│   ├── storage.py       # Redis operations
│   ├── users.py         # User management
│   └── security.py      # JWT authentication
├── tests/
│   ├── test_api.py      # API tests
│   └── test_auth.py     # Authentication tests
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md
```

## Technology Stack

- **FastAPI**: Modern, fast web framework for building APIs
- **Redis**: In-memory data store for caching and session management
- **JWT**: JSON Web Tokens for secure authentication
- **Pydantic**: Data validation and settings management
- **Passlib**: Password hashing with bcrypt
- **Pytest**: Testing framework
- **Docker**: Containerization

## Security Features

- 🔐 JWT-based authentication
- 🔒 Password hashing with bcrypt
- 🛡️ Input validation with Pydantic
- 🔑 Configurable JWT secrets
- ⏰ Token expiration

## Performance Features

- ⚡ Redis for fast data access
- 🚀 Async FastAPI for high concurrency
- 📊 Efficient click tracking
- 🔄 Connection pooling

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For questions or issues, please open an issue on GitHub.
