import os
import json
import logging
from typing import Dict, List, Optional, Union
from datetime import datetime, timedelta, timezone
from pathlib import Path
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, Column, String, Float, Date, Boolean, func, and_
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from fastapi.responses import JSONResponse
import pandas as pd
import numpy as np
import xgboost as xgb
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('api.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load the XGBoost model
MODEL_PATH = "model.ubj"
if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError(f"Model file {MODEL_PATH} not found")

model = xgb.XGBClassifier()
model.load_model(MODEL_PATH)
logger.info(f"Model loaded from {MODEL_PATH}")

# Database setup
DATABASE_URL = "sqlite:///./solana_tokens.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class TokenData(Base):
    __tablename__ = "token_data"
    
    id = Column(String, primary_key=True)  # composite key: mint_address + date
    mint_address = Column(String, index=True)
    date = Column(Date, index=True)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(Float)
    created_at = Column(Date)
    is_pre_peak = Column(Boolean, nullable=True)  # True for pre_peak, False for post_peak

# Create tables
Base.metadata.create_all(bind=engine)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pydantic models
class TokenRequest(BaseModel):
    mint_address: str = Field(..., description="Solana token mint address")

class TokenDataPoint(BaseModel):
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: float

class PoolResponse(BaseModel): 
    pool_address: str

class TokenResponse(BaseModel):
    mint_address: str
    data: List[TokenDataPoint]
    is_pre_peak: bool
    confidence: float
    days_of_data: int

class TokenSummary(BaseModel):
    mint_address: str
    last_updated: str
    is_pre_peak: bool
    current_price: float
    days_of_data: int
    volume_24h: float

class DatabaseStats(BaseModel):
    total_tokens: int
    pre_peak_count: int
    post_peak_count: int
    recent_tokens: List[TokenSummary]

# Initialize FastAPI app
app = FastAPI(title="Solana Token Analysis API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# BitQuery API helper function
def get_solana_dex_trade_data(
    token_address: str,
    limit_days: int = 300,
    quote_currency_address: str = "So11111111111111111111111111111111111111112",
):
    """Fetch historical OHLCV for a Solana token pair from BitQuery"""
    
    # Get API key from environment
    access_token = os.getenv("BITQUERY_ACCESS_TOKEN")
    if not access_token:
        raise HTTPException(status_code=500, detail="BitQuery API key not configured")
    
    url = "https://streaming.bitquery.io/eap"
    
    query = f"""
    {{
        Solana(dataset: archive) {{
            DEXTradeByTokens(
            orderBy: {{ descendingByField: "Block_Timefield" }}
            where: {{
                Trade: {{
                Currency: {{ MintAddress: {{ is: "{token_address}" }} }}
                Side:     {{ Currency: {{ MintAddress: {{ is: "{quote_currency_address}" }} }} }}
                PriceAsymmetry: {{ lt: 0.1 }}
                }}
            }}
            limit: {{ count: {limit_days} }}
            ) {{
            Block {{
                Timefield: Time(interval: {{ in: days, count: 1 }})
            }}
            volume: sum(of: Trade_Amount)
            Trade {{
                high:  Price(maximum: Trade_Price)
                low:   Price(minimum: Trade_Price)
                open:  Price(minimum: Block_Slot)
                close: Price(maximum: Block_Slot)
            }}
            count
            }}
        }}
    }}
    """
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
    }
    
    try:
        resp = requests.post(url, json={"query": query}, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        
        if "errors" in data:
            logger.error(f"GraphQL errors: {data['errors']}")
            raise HTTPException(status_code=500, detail=f"BitQuery API error: {data['errors']}")
            
        return data
    except requests.RequestException as e:
        logger.error(f"Request failed: {e}")
        raise HTTPException(status_code=503, detail=f"Failed to fetch data: {str(e)}")

# Feature engineering function
def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Engineer time-aware features without leakage"""
    df = df.copy()
    
    # Make sure date is datetime 
    df['date'] = pd.to_datetime(
        df['date'],
        format='mixed',          # pandas ≥2.0
        errors='coerce',         # bad rows → NaT (then dropped)
        utc=True,
    )

    
    # Sort by date
    df = df.sort_values('date')
    
    # Basic features using only past data
    df['price_change'] = df['close'].pct_change()
    
    # For a single token series, we don't need groupby
    rolling_window = 7
    df['volatility'] = df['price_change'].rolling(window=rolling_window, min_periods=1).std()
    df['rolling_mean'] = df['close'].rolling(window=rolling_window, min_periods=1).mean()
    df['rolling_volume'] = df['volume'].rolling(window=rolling_window, min_periods=1).mean()
    
    # Technical indicators
    df['sma_7'] = df['close'].rolling(7, min_periods=1).mean()
    df['sma_21'] = df['close'].rolling(21, min_periods=1).mean()
    df['sma7_minus_sma21'] = df['sma_7'] - df['sma_21']
    df['ret_21d'] = df['close'].pct_change(21)
    
    # Time features (days since first observation)
    df['days_since_launch'] = np.arange(1, len(df) + 1)
    
    # Lagged features
    df['lag_close_1'] = df['close'].shift(1)
    df['lag_volume_1'] = df['volume'].shift(1)
    
    return df

# API Endpoints
@app.get("/")
def read_root():
    return {"message": "Solana Token Analysis API"}

@app.get("/stats", response_model=DatabaseStats)
def get_stats(db: Session = Depends(get_db)):
    """Get overall statistics of the database"""
    # Count tokens
    total_tokens_query = db.query(TokenData.mint_address).distinct().count()

    # ── 2. Pick *exactly one* row per token: the one whose          ────────────────
    #       • created_at is the newest, and
    #       • if two rows share the same created_at, take the one whose `date` is newer
    #
    latest_per_token_sq = (
        db.query(
            TokenData.id,                     # keep the PK so we can re-join cleanly
            func.row_number().over(
                partition_by=TokenData.mint_address,
                order_by=[
                    TokenData.created_at.desc(),   # newest update first
                    TokenData.date.desc()          # tie-breaker: most recent price date
                ]
            ).label("rn")
        )
        .subquery()
    )

    # ── 3. Join back to fetch the full rows, keeping rn = 1 only ────────────────────
    latest_tokens = (
        db.query(TokenData)
        .join(latest_per_token_sq, TokenData.id == latest_per_token_sq.c.id)
        .filter(latest_per_token_sq.c.rn == 1)       # one row per mint_address
        .order_by(TokenData.created_at.desc())       # newest tokens first
        .all()
    )
    # Count pre/post peak
    pre_peak_count = sum(1 for token in latest_tokens if token.is_pre_peak)
    post_peak_count = sum(1 for token in latest_tokens if token.is_pre_peak is False)
    
    # Get 10 most recent tokens
    recent_tokens = []
    for token in latest_tokens[:10]:
        # Count days of data for this token
        days_query = db.query(TokenData).filter(TokenData.mint_address == token.mint_address).count()
        
        # Get 24h volume (latest day)
        recent_tokens.append(TokenSummary(
            mint_address=token.mint_address,
            last_updated=token.created_at.isoformat() if token.created_at else "N/A",
            is_pre_peak=token.is_pre_peak if token.is_pre_peak is not None else False,
            current_price=token.close if token.close is not None else 0.0,
            days_of_data=days_query,
            volume_24h=token.volume if token.volume is not None else 0.0,
        ))
    
    return DatabaseStats(
        total_tokens=total_tokens_query,
        pre_peak_count=pre_peak_count,
        post_peak_count=post_peak_count,
        recent_tokens=recent_tokens
    )

@app.post("/analyze_token", response_model=TokenResponse)
def analyze_token(request: TokenRequest, db: Session = Depends(get_db)):
    """Analyze token price data and determine if it's pre or post peak"""
    mint_address = request.mint_address
    logger.info(f"Analyzing token: {mint_address}")

    # ── 1. get local history ───────────────────────────────────────────────
    existing_rows = (
        db.query(TokenData)
          .filter(TokenData.mint_address == mint_address)
          .order_by(TokenData.date.desc())
          .all()
    )
    latest_local_date = existing_rows[0].date if existing_rows else None
    today_utc = datetime.now(timezone.utc).date()

    # ── 2. compute “missing tail” length ───────────────────────────────────
    if latest_local_date is None:
        missing_days = 300                         # first-time back-fill
    else:
        missing_days = max(0, (today_utc - latest_local_date).days - 1)

    # ── 3. fetch new data only if something is missing ─────────────────────
    token_data: list[dict] = []

    if missing_days > 0:
        logger.info(f"Fetching last {missing_days} day(s) for {mint_address}")
        api = get_solana_dex_trade_data(mint_address, limit_days=missing_days)
        rows = api["data"]["Solana"]["DEXTradeByTokens"]
        if not rows:
            raise HTTPException(404, "No data returned by BitQuery")

        for day in rows:
            date_str = day["Block"]["Timefield"]                   # full ISO
            pk       = f"{mint_address}_{date_str}"

            # skip if already present (id is UNIQUE)
            exists = db.query(TokenData.id).filter_by(id=pk).scalar()
            if exists:
                continue

            date_only = datetime.strptime(date_str[:10], "%Y-%m-%d").date()
            db.add(
                TokenData(
                    id=pk,
                    mint_address=mint_address,
                    date=date_only,
                    open = day["Trade"]["open"],
                    high = day["Trade"]["high"],
                    low  = day["Trade"]["low"],
                    close= day["Trade"]["close"],
                    volume = day["volume"],
                    created_at=today_utc,
                )
            )

            token_data.append(
                {
                    "date": date_str,
                    "open": day["Trade"]["open"],
                    "high": day["Trade"]["high"],
                    "low":  day["Trade"]["low"],
                    "close":day["Trade"]["close"],
                    "volume":day["volume"],
                }
            )

        db.commit()
    else:
        logger.info(f"Local copy up-to-date (latest {latest_local_date})")

    # ── 4. integrate with existing rows (needed for model input) ───────────
    if existing_rows:
        token_data.extend(
            {
                "date": r.date.isoformat(),
                "open": r.open,
                "high": r.high,
                "low":  r.low,
                "close":r.close,
                "volume":r.volume,
            }
            for r in existing_rows
        )

    # keep newest→oldest order
    token_data.sort(key=lambda x: x["date"], reverse=True)

    # Check if we have enough data (at least 3 days)
    if len(token_data) < 3:
        raise HTTPException(status_code=400, detail="Not enough data (minimum 3 days required)")
    
    # Create DataFrame for model input
    df = pd.DataFrame(token_data)
    df = engineer_features(df)
    
    # Features required by the model
    features = [
        'price_change', 'volatility', 'rolling_mean', 'rolling_volume',
        'days_since_launch', 'lag_close_1', 'lag_volume_1', 
        'sma7_minus_sma21', 'ret_21d'
    ]
    df[features] = df[features].apply(pd.to_numeric, errors="coerce")
    # Handle missing values
    X = df[features].fillna(0)
    
    # Predict
    prediction_proba = model.predict_proba(X)
    # Class 0 is pre_peak, class 1 is post_peak
    is_pre_peak = prediction_proba[-1, 0] > prediction_proba[-1, 1]
    confidence = max(prediction_proba[-1, 0], prediction_proba[-1, 1])
    
    # Update database with prediction
    for idx, row in df.iterrows():
        date_obj = row['date'].date() if isinstance(row['date'], pd.Timestamp) else datetime.strptime(row['date'], "%Y-%m-%d").date()
        db_record = db.query(TokenData).filter(
            TokenData.mint_address == mint_address,
            TokenData.date == date_obj
        ).first()
        
        if db_record:
            db_record.is_pre_peak = is_pre_peak
            db.commit()
    
    # Format response
    response_data = [
        TokenDataPoint(
            date=item["date"],
            open=item["open"],
            high=item["high"],
            low=item["low"],
            close=item["close"],
            volume=item["volume"]
        )
        for item in token_data
    ]
    
    return TokenResponse(
        mint_address=mint_address,
        data=response_data,
        is_pre_peak=is_pre_peak,
        confidence=float(confidence),
        days_of_data=len(token_data)
    )

@app.get("/token/{mint_address}", response_model=TokenResponse)
def get_token(mint_address: str, db: Session = Depends(get_db)):
    """Get token data if it exists in the database"""
    
    existing_data = db.query(TokenData).filter(
        TokenData.mint_address == mint_address
    ).order_by(TokenData.date.desc()).all()
    
    if not existing_data:
        raise HTTPException(status_code=404, detail="Token not found in database")
    
    # Get latest pre_peak status
    is_pre_peak = existing_data[0].is_pre_peak
    if is_pre_peak is None:
        # If status not available, compute it
        return analyze_token(TokenRequest(mint_address=mint_address), db)
    
    token_data = [
        TokenDataPoint(
            date=data.date.isoformat(),
            open=data.open,
            high=data.high,
            low=data.low,
            close=data.close,
            volume=data.volume
        )
        for data in existing_data
    ]
    
    return TokenResponse(
        mint_address=mint_address,
        data=token_data,
        is_pre_peak=is_pre_peak,
        confidence=0.8,  # We don't store confidence in DB, using a placeholder
        days_of_data=len(token_data)
    )

@app.post("/load_existing_data")
def load_existing_data(db: Session = Depends(get_db)):
    """Load data from ohlcv_data.json if it exists"""
    file_path = "ohlcv_data.json"
    
    if not os.path.exists(file_path):
        return JSONResponse(
            status_code=404,
            content={"message": f"File {file_path} not found"}
        )
    
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    # Process and insert data
    count = 0
    for item in data:
        mint_address = item.get("mint_address")
        date_str = item.get("date")
        
        if not mint_address or not date_str:
            continue
            
        date_obj = datetime.strptime(date_str.split('T')[0], "%Y-%m-%d").date()
        
        # Check if record already exists
        existing = db.query(TokenData).filter(
            TokenData.mint_address == mint_address,
            TokenData.date == date_obj
        ).first()
        
        if not existing:
            # Create new record
            db_record = TokenData(
                id=f"{mint_address}_{date_str}",
                mint_address=mint_address,
                date=date_obj,
                open=item.get("open", 0),
                high=item.get("high", 0),
                low=item.get("low", 0),
                close=item.get("close", 0),
                volume=item.get("volume", 0),
                created_at=datetime.strptime(item.get("created_at", date_str), "%Y-%m-%d").date()
            )
            db.add(db_record)
            count += 1
    
    db.commit()
    return {"message": f"Loaded {count} new records from {file_path}"}



# For running the app directly
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)