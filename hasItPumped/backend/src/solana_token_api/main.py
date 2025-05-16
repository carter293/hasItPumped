"""
Solana Token Analysis API

Main application module with FastAPI endpoints.
"""

import os
import logging
from datetime import datetime, timezone
from typing import List

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import pandas as pd
import xgboost as xgb

# Local imports
from solana_token_api.models.database import get_db, TokenData
from solana_token_api.models.schema import (
    TokenRequest,
    TokenResponse,
    TokenDataPoint,
    DatabaseStats,
    TokenSummary,
    PoolResponse,
)
from solana_token_api.utils.logger import setup_logger
from solana_token_api.utils.data_fetcher import get_solana_dex_trade_data
from solana_token_api.utils.feature_engineering import engineer_features
from solana_token_api.utils.database_utils import (
    get_latest_tokens,
    update_token_predictions,
)
from solana_token_api.utils.model_utils import load_model, make_prediction

# Configure application logging
logger = setup_logger("api")

# Load the XGBoost model
model = load_model()

# Initialize FastAPI app
app = FastAPI(
    title="Solana Token Analysis API",
    description="API for analyzing Solana token price data and determining pre/post peak status",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/healthcheck")
def read_root():
    """API health check endpoint"""
    return {"status": "healthy", "message": "Solana Token Analysis API"}


@app.get("/stats", response_model=DatabaseStats)
def get_stats(db: Session = Depends(get_db)):
    """Get overall statistics of the database"""
    logger.info("Fetching database statistics")

    # Get latest token data
    latest_tokens = get_latest_tokens(db)

    # Count tokens
    total_tokens = len(latest_tokens)

    # Count pre/post peak
    pre_peak_count = sum(1 for token in latest_tokens if token.is_pre_peak == True)
    post_peak_count = sum(1 for token in latest_tokens if token.is_pre_peak == False)

    # Get 10 most recent tokens
    recent_tokens = []
    for token in latest_tokens[:10]:

        recent_tokens.append(
            TokenSummary(
                mint_address=token.mint_address,
                last_updated=(
                    token.created_at.isoformat() if token.created_at else "N/A"
                ),
                is_pre_peak=(
                    token.is_pre_peak if token.is_pre_peak is not None else False
                ),
                current_price=token.close if token.close is not None else 0.0,
                days_of_data=token.days_of_data,
                volume_24h=token.volume if token.volume is not None else 0.0,
            )
        )

    return DatabaseStats(
        total_tokens=total_tokens,
        pre_peak_count=pre_peak_count,
        post_peak_count=post_peak_count,
        recent_tokens=recent_tokens,
    )


@app.post("/analyze_token", response_model=TokenResponse)
async def analyze_token(
    request: TokenRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Analyze token price data and determine if it's pre or post peak"""
    mint_address = request.mint_address
    logger.info(f"Analyzing token: {mint_address}")

    # Get existing data
    existing_rows = (
        db.query(TokenData)
        .filter(TokenData.mint_address == mint_address)
        .order_by(TokenData.date.desc())
        .all()
    )
    latest_local_date = existing_rows[0].date if existing_rows else None
    today_utc = datetime.now(timezone.utc).date()

    # Calculate missing days
    if latest_local_date is None:
        missing_days = 300  # First-time back-fill
    else:
        missing_days = max(0, (today_utc - latest_local_date).days - 1)

    # Fetch new data if necessary
    token_data = []
    if missing_days > 0:
        logger.info(f"Fetching last {missing_days} day(s) for {mint_address}")
        try:
            api_data = get_solana_dex_trade_data(mint_address, limit_days=missing_days)

            # Process API response
            rows = api_data["data"]["Solana"]["DEXTradeByTokens"]
            if not rows:
                raise HTTPException(404, "No data returned by BitQuery API")

            for day in rows:
                date_str = day["Block"]["Timefield"]
                pk = f"{mint_address}_{date_str}"

                # Skip if already present (id is UNIQUE)
                exists = db.query(TokenData.id).filter_by(id=pk).scalar()
                if exists:
                    continue

                date_only = datetime.strptime(date_str[:10], "%Y-%m-%d").date()
                db.add(
                    TokenData(
                        id=pk,
                        mint_address=mint_address,
                        date=date_only,
                        open=day["Trade"]["open"],
                        high=day["Trade"]["high"],
                        low=day["Trade"]["low"],
                        close=day["Trade"]["close"],
                        volume=day["volume"],
                        created_at=today_utc,
                    )
                )

                token_data.append(
                    {
                        "date": date_str,
                        "open": day["Trade"]["open"],
                        "high": day["Trade"]["high"],
                        "low": day["Trade"]["low"],
                        "close": day["Trade"]["close"],
                        "volume": day["volume"],
                    }
                )

            db.commit()
        except Exception as e:
            logger.error(f"Error fetching data: {str(e)}")
            raise HTTPException(
                status_code=503, detail=f"Failed to fetch data: {str(e)}"
            )
    else:
        logger.info(f"Local copy up-to-date (latest {latest_local_date})")

    # Integrate with existing rows for model input
    if existing_rows:
        token_data.extend(
            {
                "date": r.date.isoformat(),
                "open": r.open,
                "high": r.high,
                "low": r.low,
                "close": r.close,
                "volume": r.volume,
            }
            for r in existing_rows
        )

    # Keep newest→oldest order
    token_data.sort(key=lambda x: x["date"], reverse=True)

    # Check if we have enough data
    if len(token_data) < 3:
        raise HTTPException(
            status_code=400, detail="Not enough data (minimum 3 days required)"
        )

    # Create DataFrame for model input
    df = pd.DataFrame(token_data)
    df_processed = engineer_features(df)

    # Make prediction
    is_pre_peak, confidence = make_prediction(model, df_processed)

    # Schedule background task to update database with prediction
    background_tasks.add_task(
        update_token_predictions,
        db_session=db,
        mint_address=mint_address,
        df=df_processed,
        is_pre_peak=is_pre_peak,
    )

    # Format response
    response_data = [
        TokenDataPoint(
            date=item["date"],
            open=item["open"],
            high=item["high"],
            low=item["low"],
            close=item["close"],
            volume=item["volume"],
        )
        for item in token_data
    ]

    return TokenResponse(
        mint_address=mint_address,
        data=response_data,
        is_pre_peak=is_pre_peak,
        confidence=float(confidence),
        days_of_data=len(token_data),
    )


# For running the app directly
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("solana_token_api.main:app", host="0.0.0.0", port=8000, reload=True)
