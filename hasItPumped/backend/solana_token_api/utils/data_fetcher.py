"""
Utility functions for fetching data from external APIs.
"""
import os
import requests
from fastapi import HTTPException
import logging

logger = logging.getLogger("api.data_fetcher")

def get_solana_dex_trade_data(
    token_address: str,
    limit_days: int = 300,
    quote_currency_address: str = "So11111111111111111111111111111111111111112",
):
    """
    Fetch historical OHLCV for a Solana token pair from BitQuery
    
    Args:
        token_address: Mint address of the token
        limit_days: Number of days of data to fetch
        quote_currency_address: Quote currency mint address (default is SOL)
        
    Returns:
        JSON response from the BitQuery API
        
    Raises:
        HTTPException: If API call fails or returns an error
    """
    
    # Get API key from environment
    access_token = os.getenv("BITQUERY_ACCESS_TOKEN")
    if not access_token:
        logger.error("BitQuery API key not configured")
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
        logger.debug(f"Sending request to BitQuery for token {token_address}")
        resp = requests.post(url, json={"query": query}, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        
        if "errors" in data:
            logger.error(f"GraphQL errors: {data['errors']}")
            raise HTTPException(status_code=500, detail=f"BitQuery API error: {data['errors']}")
            
        logger.debug(f"Successfully fetched data for token {token_address}")
        return data
        
    except requests.RequestException as e:
        logger.error(f"Request failed: {e}")
        raise HTTPException(status_code=503, detail=f"Failed to fetch data: {str(e)}")