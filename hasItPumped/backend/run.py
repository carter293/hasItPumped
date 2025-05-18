"""
Entry point script to run the Solana Token Analysis API.
"""
import uvicorn

if __name__ == "__main__":
    uvicorn.run("src.solana_token_api.main:app", host="0.0.0.0", port=8000, reload=True)
