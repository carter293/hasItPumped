"""
Test suite for the Solana Token Analysis API endpoints.
"""
import os
import sys
import json
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock

# Add parent directory to path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from solana_token_api.models.database import Base, TokenData, get_db
from solana_token_api.main import app

# Setup test database
TEST_DB_URL = "sqlite:///./test_solana_tokens.db"
engine = create_engine(TEST_DB_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Override the dependency
def override_get_db():
    """Get test database session"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

# Create test client
client = TestClient(app)

@pytest.fixture(scope="function")
def test_db():
    """Create test database tables before each test and drop after"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def sample_token_data():
    """Create sample token data for testing"""
    return {
        "mint_address": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
        "date": datetime.now(timezone.utc).date().isoformat(),
        "open": 1.0,
        "high": 1.2,
        "low": 0.9,
        "close": 1.1,
        "volume": 1000.0
    }

def insert_sample_data(db, token_data, days=5):
    """Insert sample token data into the test database"""
    today = datetime.now(timezone.utc).date()
    
    for i in range(days):
        date = today - timedelta(days=i)
        close_price = token_data["close"] * (1 + (i * 0.05))
        
        db.add(TokenData(
            id=f"{token_data['mint_address']}_{date.isoformat()}",
            mint_address=token_data["mint_address"],
            date=date,
            open=token_data["open"] * (1 + (i * 0.03)),
            high=token_data["high"] * (1 + (i * 0.04)),
            low=token_data["low"] * (1 + (i * 0.02)),
            close=close_price,
            volume=token_data["volume"] * (1 + (i * 0.1)),
            created_at=today,
            is_pre_peak=(i < 3)  # First 3 days pre-peak, rest post-peak
        ))
    
    db.commit()

# Tests
def test_root_endpoint():
    """Test the root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    assert "status" in response.json()
    assert "message" in response.json()

def test_stats_endpoint(test_db, sample_token_data):
    """Test the stats endpoint"""
    # Insert sample data
    db = TestingSessionLocal()
    insert_sample_data(db, sample_token_data)
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

@patch("app.get_solana_dex_trade_data")
def test_analyze_token_endpoint(mock_get_data, test_db, sample_token_data):
    """Test the analyze token endpoint"""
    # Mock API response
    mock_response = {
        "data": {
            "Solana": {
                "DEXTradeByTokens": [
                    {
                        "Block": {
                            "Timefield": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
                        },
                        "Trade": {
                            "open": 1.0,
                            "high": 1.2,
                            "low": 0.9,
                            "close": 1.1
                        },
                        "volume": 1000.0
                    }
                ]
            }
        }
    }
    mock_get_data.return_value = mock_response
    
    # Insert some existing data
    db = TestingSessionLocal()
    insert_sample_data(db, sample_token_data, days=3)
    db.close()
    
    # Test endpoint
    request_data = {"mint_address": sample_token_data["mint_address"]}
    response = client.post("/analyze_token", json=request_data)
    assert response.status_code == 200
    data = response.json()
    
    # Validate response structure
    assert data["mint_address"] == sample_token_data["mint_address"]
    assert "data" in data
    assert "is_pre_peak" in data
    assert "confidence" in data
    assert "days_of_data" in data
    
    # Should have more than 3 days of data now
    assert data["days_of_data"] > 3

@patch("app.get_solana_dex_trade_data")
def test_analyze_token_with_api_error(mock_get_data, test_db):
    """Test analyze token endpoint with API error"""
    # Mock API error
    mock_get_data.side_effect = Exception("API error")
    
    # Test endpoint
    request_data = {"mint_address": "some_token_address"}
    response = client.post("/analyze_token", json=request_data)
    assert response.status_code == 503
    assert "detail" in response.json()

def test_analyze_token_not_enough_data(test_db, sample_token_data):
    """Test analyze token endpoint with not enough data"""
    # Insert just 1 day of data
    db = TestingSessionLocal()
    insert_sample_data(db, sample_token_data, days=1)
    db.close()
    
    # Mock API to return empty response
    with patch("app.get_solana_dex_trade_data", return_value={"data": {"Solana": {"DEXTradeByTokens": []}}}):
        # Test endpoint
        request_data = {"mint_address": sample_token_data["mint_address"]}
        response = client.post("/analyze_token", json=request_data)
        assert response.status_code == 400
        assert "detail" in response.json()
        assert "Not enough data" in response.json()["detail"]