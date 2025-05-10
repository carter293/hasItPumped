# Solana Token Analysis API

A production-ready API for analyzing Solana token price data and determining if tokens are in pre-peak or post-peak phases.

## Features

- Fetch and analyze historical price data for Solana tokens
- ML-based prediction of token market phase (pre-peak or post-peak)
- Structured data storage with SQLite (configurable for other databases)
- Comprehensive logging system with rotation and JSON formatting
- RESTful API with proper validation and error handling
- Docker support for easy deployment
- Test suite for reliable functionality


## Environment Setup

1. Create a `.env` file with required environment variables:

```
BITQUERY_ACCESS_TOKEN=your_bitquery_api_key
```

2. Install dependencies:

```bash
poetry install
```

3. Run the setup script to initialize the database:

```bash
python setup.py
```

## Running the API

### Local Development

```bash
uvicorn app:app --reload
```

The API will be available at http://localhost:8000, with interactive documentation at http://localhost:8000/docs.

### Docker Deployment

```bash
# Build the Docker image
docker build -t solana-token-api .

# Run the container
docker run -p 8000:8000 -v $(pwd)/data:/app/data solana-token-api
```

## Using the API

### Endpoints

- `GET /` - Health check
- `GET /stats` - Get database statistics
- `POST /analyze_token` - Analyze a token (fetches latest data if needed)

### Example Requests

Analyze a token:

```bash
curl -X POST "http://localhost:8000/analyze_token" \
     -H "Content-Type: application/json" \
     -d '{"mint_address": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"}'
```

## Testing

Run the test suite:

```bash
pytest
```

Generate a coverage report:

```bash
pytest --cov=. --cov-report=html
```

## License

[MIT License](LICENSE)