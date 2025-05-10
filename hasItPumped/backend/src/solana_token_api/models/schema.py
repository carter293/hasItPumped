"""
Pydantic models for request/response validation and serialization.
"""

from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class TokenRequest(BaseModel):
    """Request model for analyzing a token"""

    mint_address: str = Field(
        ...,
        description="Solana token mint address",
        example="EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
    )


class TokenDataPoint(BaseModel):
    """Model for token price data point"""

    date: str
    open: float
    high: float
    low: float
    close: float
    volume: float


class LatestTokenStats(TokenDataPoint):
    """Response model for latest token statitics"""
    mint_address: str
    created_at: str
    is_pre_peak: bool
    days_of_data: int

class PoolResponse(BaseModel):
    """Response model for pool information"""

    pool_address: str


class TokenResponse(BaseModel):
    """Response model for token analysis"""

    mint_address: str
    data: List[TokenDataPoint]
    is_pre_peak: bool
    confidence: float
    days_of_data: int


class TokenSummary(BaseModel):
    """Summary model for token information"""

    mint_address: str
    last_updated: str
    is_pre_peak: bool
    current_price: float
    days_of_data: int
    volume_24h: float


class DatabaseStats(BaseModel):
    """Response model for database statistics"""

    total_tokens: int
    pre_peak_count: int
    post_peak_count: int
    recent_tokens: List[TokenSummary]
