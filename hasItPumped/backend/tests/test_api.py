"""
Test suite for the Solana Token Analysis API endpoints.
"""
import os
import sys
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock

# Add src directory to Python path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from solana_token_api.main import app
from solana_token_api.models.database import Base, TokenData, get_db

# Create in-memory database for testing
TEST_DB_URL = "sqlite:///:memory:"

# Setup function to create test database
@pytest.fixture(scope="function")
def test_db():
    """Create an in-memory test database for each test"""
    import logging
    logger = logging.getLogger(__name__)
    logger.debug("[FIXTURE] Setting up test_db")

    engine = create_engine(
        TEST_DB_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    logger.debug(f"[FIXTURE] Engine: {engine}")

    Base.metadata.create_all(bind=engine)
    logger.debug("[FIXTURE] Tables created")

    from sqlalchemy import inspect
    inspector = inspect(engine)
    logger.debug(f"[FIXTURE] Tables: {inspector.get_table_names()}")

    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    logger.debug("[FIXTURE] Session factory created")

    def override_get_db():
        logger.debug("[FIXTURE] Providing DB session")
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()
            logger.debug("[FIXTURE] Closed DB session")

    app.dependency_overrides[get_db] = override_get_db
    logger.debug("[FIXTURE] Overrode get_db")

    yield TestingSessionLocal
    Base.metadata.drop_all(bind=engine)
    logger.debug("[FIXTURE] Dropped tables")
# Create test client
client = TestClient(app=app)

@pytest.fixture
def sample_token_data():
    """Create sample token data for testing"""
    return {
        "mint_address": "9BB6NFEcjBCtnNLFko2FqVQBq8HHM13kCyYcdQbgpump",
        "date": datetime.now(timezone.utc).date().isoformat(),
        "open": 1.0,
        "high": 1.2,
        "low": 0.9,
        "close": 1.1,
        "volume": 1000.0,
    }


def insert_sample_data(db_session, token_data, days=5):
    """Insert sample token data into the test database"""
    today = datetime.now(timezone.utc).date()
    
    inserted_dates = []
    for i in range(days):
        date = today - timedelta(days=i+10)  # Create data for dates in the past
        inserted_dates.append(date)
        close_price = token_data["close"] * (1 + (i * 0.05))

        db_session.add(
            TokenData(
                id=f"{token_data['mint_address']}_{date.isoformat()}",
                mint_address=token_data["mint_address"],
                date=date,
                open=token_data["open"] * (1 + (i * 0.03)),
                high=token_data["high"] * (1 + (i * 0.04)),
                low=token_data["low"] * (1 + (i * 0.02)),
                close=close_price,
                volume=token_data["volume"] * (1 + (i * 0.1)),
                created_at=today,
                is_pre_peak=(i < 3),  # First 3 days pre-peak, rest post-peak
            )
        )

    db_session.commit()
    return inserted_dates


# Test 1: Root endpoint
def test_root_endpoint():
    """Test the root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    assert "status" in response.json()
    assert "message" in response.json()


# Test 2: Stats endpoint with properly mocked database
def test_stats_endpoint(test_db, sample_token_data):
    """Test the stats endpoint"""
    # Insert sample data
    db = test_db()
    insert_sample_data(db, sample_token_data, days=3)
    db.close()

    # Test endpoint
    response = client.get("/stats")
    assert response.status_code == 200
    data = response.json()

    # Validate response structure
    assert "total_tokens" in data
    assert "pre_peak_count" in data
    assert "post_peak_count" in data
    assert "recent_tokens" in data

    # Check specific values
    assert data["total_tokens"] == 1
    assert len(data["recent_tokens"]) == 1
    assert data["recent_tokens"][0]["mint_address"] == sample_token_data["mint_address"]


# Test 3: Analyze token endpoint with mocked data fetcher and DB data
@patch("solana_token_api.main.get_solana_dex_trade_data")
def test_analyze_token_success(mock_get_data, test_db, sample_token_data):
    """Test successful token analysis with DB data + API data"""
    # Insert enough data in the database

    db = test_db()
    insert_sample_data(db, sample_token_data, days=5)
    db.close()
    
    # Mock API response with valid data structure
    mock_date = datetime.now(timezone.utc)
    mock_response = {
        "data": {
            "Solana": {
                "DEXTradeByTokens": [
                    {
                        "Block": {
                            "Timefield": mock_date.strftime("%Y-%m-%dT%H:%M:%S")
                        },
                        "Trade": {"open": 1.0, "high": 1.2, "low": 0.9, "close": 1.1},
                        "volume": 1000.0,
                    }
                ]
            }
        }
    }
    mock_get_data.return_value = mock_response

    # Call API
    response = client.post("/analyze_token", json={"mint_address": sample_token_data["mint_address"]})
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    
    # Verify structure
    assert data["mint_address"] == sample_token_data["mint_address"]
    assert "data" in data
    assert "is_pre_peak" in data
    assert "confidence" in data
    assert "days_of_data" in data
    
    # Should have at least all the data we inserted
    assert data["days_of_data"] >= 5
    assert len(data["data"]) >= 5


@patch("solana_token_api.main.get_solana_dex_trade_data")
def test_analyze_token_api_only(mock_get_data, test_db):
    """Test token analysis with only API data (no DB data)"""
    from datetime import datetime, timezone, timedelta

    # Create unique mint address
    unique_token = f"API_ONLY_TOKEN_{datetime.now().isoformat()}"

    # Mock API response
    mock_dates = [datetime.now(timezone.utc) - timedelta(days=i) for i in range(5)]
    mock_data = [
        {
            "Block": {"Timefield": date.strftime("%Y-%m-%dT%H:%M:%S")},
            "Trade": {"open": 1.0, "high": 1.2, "low": 0.9, "close": 1.1},
            "volume": 1000.0
        } for date in mock_dates
    ]
    mock_response = {"data": {"Solana": {"DEXTradeByTokens": mock_data}}}
    mock_get_data.return_value = mock_response

    # Call API
    response = client.post("/analyze_token", json={"mint_address": unique_token})

    # Verify response
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert data["mint_address"] == unique_token
    assert "data" in data
    assert "is_pre_peak" in data
    assert "confidence" in data
    assert "days_of_data" in data
    assert data["days_of_data"] >= 5
    assert len(data["data"]) >= 5


# Test 5: Analyze token with API error
@patch("solana_token_api.main.get_solana_dex_trade_data")
def test_analyze_token_api_error(mock_get_data, test_db):
    """Test error handling when API throws an exception"""
    # Set up mock to raise an exception
    mock_get_data.side_effect = Exception("API error")
    
    # Use a unique token address
    unique_token = f"ERROR_TEST_TOKEN_{datetime.now().isoformat()}"
    
    # Call API
    response = client.post("/analyze_token", json={"mint_address": unique_token})
    
    # Verify error response
    assert response.status_code == 503
    assert "detail" in response.json()
    assert "Failed to fetch data" in response.json()["detail"]


# Test 6: Empty API response but enough DB data
@patch("solana_token_api.main.get_solana_dex_trade_data")
def test_analyze_token_empty_api_response(mock_get_data, test_db, sample_token_data):
    """Test behavior when API returns empty response but DB has data"""
    # Insert sample data
    db = test_db()
    insert_sample_data(db, sample_token_data, days=5)  # Enough data in DB
    db.close()
    
    # Mock empty API response but with correct structure
    mock_get_data.return_value = {
        "data": {
            "Solana": {
                "DEXTradeByTokens": []  # Empty list
            }
        }
    }
    
    # Call API
    response = client.post("/analyze_token", json={"mint_address": sample_token_data["mint_address"]})
    
    # HTTP 404 is expected from API when no data returned, but we have DB data
    # This might be handled as 503 in your app's error handling
    # We need to check both possibilities
    if response.status_code == 503:
        # If it returns 503, we check it contains the right error
        assert "detail" in response.json()
        assert "No data returned by BitQuery API" in response.json()["detail"]
    else:
        # If it succeeds, we should have enough data from DB
        assert response.status_code == 200
        data = response.json()
        assert data["mint_address"] == sample_token_data["mint_address"]
        assert "data" in data
        assert data["days_of_data"] >= 5