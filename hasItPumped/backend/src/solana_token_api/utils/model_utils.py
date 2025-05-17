"""
Utilities for model loading and prediction.
"""

import logging
import os
from typing import Tuple
from pathlib import Path
import pandas as pd
import xgboost as xgb
from fastapi import HTTPException
from solana_token_api.utils.feature_engineering import features

logger = logging.getLogger("api.model_utils")


def load_model(
    model_path: str = "./assets/model.ubj",
) -> xgb.XGBClassifier:
    """
    Load the XGBoost model from the specified path.

    Args:
        model_path: Path to the saved model file

    Returns:
        Loaded XGBoost model

    Raises:
        HTTPException: If model file is not found
    """
    pkg_root = Path(__file__).parent.parent
    model_path = str(pkg_root / "assets" / "model.ubj")
    if not os.path.exists(model_path):
        error_msg = f"Model file {model_path} not found"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

    try:
        model = xgb.XGBClassifier()
        model.load_model(model_path)
        logger.info(f"Model loaded successfully from {model_path}")
        return model
    except Exception as e:
        error_msg = f"Failed to load model: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)


def make_prediction(model: xgb.XGBClassifier, df: pd.DataFrame) -> Tuple[bool, float]:
    """
    Make a prediction using the loaded model.

    Args:
        model: Loaded XGBoost model
        df: DataFrame with processed features

    Returns:
        Tuple of (is_pre_peak, confidence)
    """

    # Handle missing values
    X = df[features].fillna(0)

    logger.debug(f"Making prediction on {len(X)} rows of data")

    try:
        # Predict
        prediction_proba = model.predict_proba(X)

        # Use the latest data point for final prediction
        # Class 0 is pre_peak, class 1 is post_peak
        is_pre_peak = prediction_proba[-1, 0] > prediction_proba[-1, 1]
        confidence = max(prediction_proba[-1, 0], prediction_proba[-1, 1])

        logger.info(
            f"Prediction: {'pre-peak' if is_pre_peak else 'post-peak'} with {confidence:.2f} confidence"
        )
        return is_pre_peak, confidence

    except Exception as e:
        logger.error(f"Prediction failed: {str(e)}")
        # Return a default prediction rather than failing the request
        return True, 0.5  # Default to pre-peak with 0.5 confidence
