"""
Feature engineering utilities for token analysis.
"""

import logging

import numpy as np
import pandas as pd

logger = logging.getLogger("api.feature_engineering")


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Engineer time-aware features for token price data.

    Args:
        df: DataFrame containing token price data with date, open, high, low, close, volume

    Returns:
        DataFrame with engineered features suitable for model input
    """
    logger.debug("Starting feature engineering process")
    df = df.copy()

    # Make sure date is datetime
    try:
        df["date"] = pd.to_datetime(
            df["date"],
            format="mixed",
            errors="coerce",
            utc=True,
        )
    except Exception as e:
        logger.warning(f"Error converting dates: {e}")
        # Fallback method for older pandas versions
        df["date"] = pd.to_datetime(df["date"], errors="coerce", utc=True)

    # Drop rows with invalid dates
    invalid_dates = df["date"].isna().sum()
    if invalid_dates > 0:
        logger.warning(f"Dropped {invalid_dates} rows with invalid dates")
        df = df.dropna(subset=["date"])

    # Sort by date
    df = df.sort_values("date")

    logger.debug("Calculating basic price features")
    # Basic features using only past data
    df["price_change"] = df["close"].pct_change()

    # For a single token series, we don't need groupby
    rolling_window = 7
    df["volatility"] = (
        df["price_change"].rolling(window=rolling_window, min_periods=1).std()
    )
    df["rolling_mean"] = (
        df["close"].rolling(window=rolling_window, min_periods=1).mean()
    )
    df["rolling_volume"] = (
        df["volume"].rolling(window=rolling_window, min_periods=1).mean()
    )

    logger.debug("Calculating technical indicators")
    # Technical indicators
    df["sma_7"] = df["close"].rolling(7, min_periods=1).mean()
    df["sma_21"] = df["close"].rolling(21, min_periods=1).mean()
    df["sma7_minus_sma21"] = df["sma_7"] - df["sma_21"]
    df["ret_21d"] = df["close"].pct_change(21)

    # Time features (days since first observation)
    df["days_since_launch"] = np.arange(1, len(df) + 1)

    logger.debug("Calculating lagged features")
    # Lagged features
    df["lag_close_1"] = df["close"].shift(1)
    df["lag_volume_1"] = df["volume"].shift(1)

    # Features required by the model
    features = [
        "price_change",
        "volatility",
        "rolling_mean",
        "rolling_volume",
        "days_since_launch",
        "lag_close_1",
        "lag_volume_1",
        "sma7_minus_sma21",
        "ret_21d",
    ]

    # Check for missing values
    for feature in features:
        missing = df[feature].isna().sum()
        if missing > 0:
            logger.warning(f"Feature '{feature}' has {missing} missing values")

    # Convert to numeric and fill missing values
    df[features] = df[features].apply(pd.to_numeric, errors="coerce")
    df[features] = df[features].fillna(0)

    logger.debug("Feature engineering completed")
    return df
