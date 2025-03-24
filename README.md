# AskVerse

AskVerse is a powerful natural language query system that combines public LLM capabilities with proprietary knowledge. It provides an API for searching internal resources and external APIs using a multi-agent framework.

## Features

- Natural language querying of internal resources
- Integration with Confluence and Vector DB
- External API integration (Weather, Maps, etc.)
- Multi-agent architecture for complex queries
- OAuth2/JWT authentication
- Query tracking and analytics
- PII masking and security features

## Prerequisites

- Python 3.8+
- PostgreSQL database
- OpenAI API key
- Confluence API credentials
- Pinecone API key
- Weather API key
- Maps API key

## Installation

1. Clone the repository:
```bash
git clone https://github.com/chavan-manoj/askverse.git
cd askverse
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Copy the environment variables file and update with your credentials:
```bash
cp .env.example .env
```

## API Keys and Authentication Setup

### 1. OpenAI API Key
1. Go to [OpenAI Platform](https://platform.openai.com/)
2. Sign up or log in to your account
3. Navigate to "API Keys" section
4. Click "Create new secret key"
5. Copy the key and add it to your `.env` file:
```env
OPENAI_API_KEY=sk-your-key-here
```

### 2. Confluence API Credentials
1. Log in to your Confluence instance
2. Go to your profile settings
3. Navigate to "Security" or "API Tokens"
4. Generate a new API token
5. Add the credentials to your `.env` file:
```env
CONFLUENCE_URL=your-confluence-instance-url
CONFLUENCE_USERNAME=your-username
CONFLUENCE_API_TOKEN=your-api-token
```

### 3. Pinecone API Key
1. Sign up at [Pinecone](https://www.pinecone.io/)
2. Create a new index
3. Get your API key from the console
4. Add to your `.env` file:
```env
PINECONE_API_KEY=your-pinecone-key
PINECONE_ENVIRONMENT=your-environment
```

### 4. Weather API Key
1. Sign up at [OpenWeatherMap](https://openweathermap.org/)
2. Go to "My API Keys" section
3. Generate a new API key
4. Add to your `.env` file:
```env
WEATHER_API_KEY=your-weather-api-key
```

### 5. Maps API Key
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the Maps JavaScript API
4. Create credentials (API key)
5. Add to your `.env` file:
```env
MAPS_API_KEY=your-maps-api-key
```

### 6. JWT Configuration
1. Generate a secure secret key:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```
2. Add the generated key to your `.env` file:
```env
JWT_SECRET_KEY=your-generated-secret
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

## Authentication with AskVerse API

### 1. Getting an Access Token

To authenticate with the AskVerse API, you need to first obtain a JWT access token:

```bash
curl -X POST http://localhost:8000/api/v1/auth/token \
  -H "Content-Type: application/json" \
  -d '{
    "username": "your-username",
    "password": "your-password"
  }'
```

The response will contain your access token:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer"
}
```

### 2. Using the Access Token

Include the access token in your API requests:

```bash
curl -X POST http://localhost:8000/api/v1/query \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the weather in New York?",
    "context": {}
  }'
```

### 3. Token Refresh

When your access token expires, you can refresh it:

```bash
curl -X POST http://localhost:8000/api/v1/auth/refresh \
  -H "Authorization: Bearer your-current-token" \
  -H "Content-Type: application/json"
```

## Configuration

Update the `.env` file with your credentials:

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/askverse

# OpenAI
OPENAI_API_KEY=your_openai_api_key

# Confluence
CONFLUENCE_URL=your_confluence_url
CONFLUENCE_USERNAME=your_username
CONFLUENCE_API_TOKEN=your_api_token

# Pinecone
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_ENVIRONMENT=your_environment

# External APIs
WEATHER_API_KEY=your_weather_api_key
MAPS_API_KEY=your_maps_api_key

# JWT
JWT_SECRET_KEY=your_jwt_secret
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS
CORS_ORIGINS=["http://localhost:3000"]
```

## Running the Application

1. Start the database:
```bash
# Using Docker
docker-compose up -d db

# Or start your PostgreSQL instance manually
```

2. Run the application:
```bash
python run.py
```

The API will be available at `http://localhost:8000`

## Document Synchronization

The document sync job fetches documents from Confluence, processes them, and stores them in the vector database for efficient semantic search.

### Running the Sync Job

1. Run the sync job manually:
```bash
# Run full sync
python -m askverse.jobs.document_sync

# Run sync with cleanup
python -m askverse.jobs.document_sync --cleanup
```

2. Schedule the job (using cron):
```bash
# Add to crontab (runs daily at 2 AM)
0 2 * * * cd /path/to/askverse && /path/to/venv/bin/python -m askverse.jobs.document_sync
```

### Configuration

Add these settings to your `.env` file:
```env
# Document Sync Settings
CLEANUP_OLD_DOCUMENTS=true
DOCUMENT_RETENTION_DAYS=30
SYNC_BATCH_SIZE=100
```

### Monitoring

Monitor sync job status:
```bash
# View sync logs
tail -f logs/document_sync.log

# Check sync status in database
psql -d askverse -c "SELECT * FROM document_syncs ORDER BY start_time DESC LIMIT 5;"
```

## API Documentation

Once the application is running, you can access:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## API Endpoints

### Authentication
- `POST /api/v1/auth/token` - Get access token
- `POST /api/v1/auth/refresh` - Refresh access token

### Queries
- `POST /api/v1/query` - Process a natural language query
- `GET /api/v1/queries` - Get user's query history

## Development

### Project Structure

```
askverse/
├── agents/           # Specialized agents
├── api/             # API routes
├── auth/            # Authentication
├── core/            # Core functionality
├── db/              # Database models and session
├── services/        # External services
└── main.py          # FastAPI application
```

### Running Tests

```bash
pytest
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 