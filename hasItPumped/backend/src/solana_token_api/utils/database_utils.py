"""
Utility functions for database operations.
"""

import logging
from typing import List

import pandas as pd
from sqlalchemy import func
from sqlalchemy.orm import Session

from solana_token_api.models.database import TokenData

logger = logging.getLogger("api.database_utils")


def get_latest_tokens(db: Session) -> List[TokenData]:
    """
    Get the most recent record for each token in the database.

    Args:
        db: SQLAlchemy session

    Returns:
        List of TokenData objects, one per token
    """
    # Create a subquery to get the latest row per token
    latest_per_token_sq = db.query(
        TokenData.id,
        func.row_number()
        .over(
            partition_by=TokenData.mint_address,
            order_by=[TokenData.created_at.desc(), TokenData.date.desc()],
        )
        .label("rn"),
    ).subquery()

    # Join back to fetch the full rows, keeping rn = 1 only
    latest_tokens = (
        db.query(TokenData)
        .join(latest_per_token_sq, TokenData.id == latest_per_token_sq.c.id)
        .filter(latest_per_token_sq.c.rn == 1)
        .order_by(TokenData.created_at.desc())
        .all()
    )

    logger.debug(f"Found {len(latest_tokens)} unique tokens in database")
    return latest_tokens


def update_token_predictions(
    db_session: Session, mint_address: str, df: pd.DataFrame, is_pre_peak: bool
):
    """
    Update token records with prediction results.

    Args:
        db_session: SQLAlchemy session
        mint_address: Token mint address
        df: DataFrame with processed data
        is_pre_peak: Prediction result
    """
    logger.info(f"Updating predictions for token {mint_address}")

    try:
        # Begin a transaction
        for idx, row in df.iterrows():
            date_obj = (
                row["date"].date()
                if isinstance(row["date"], pd.Timestamp)
                else row["date"]
            )

            # Find the token record
            db_record = (
                db_session.query(TokenData)
                .filter(
                    TokenData.mint_address == mint_address, TokenData.date == date_obj
                )
                .first()
            )

            # Update record if found
            if db_record:
                db_record.is_pre_peak = is_pre_peak

        # Commit all updates
        db_session.commit()
        logger.info(f"Successfully updated {mint_address} predictions")

    except Exception as e:
        # Rollback on error
        db_session.rollback()
        logger.error(f"Failed to update predictions: {str(e)}")
        # Don't raise the exception as this is a background task
