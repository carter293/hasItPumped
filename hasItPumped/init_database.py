import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

print("Initializing database from ohlcv_data.json...")
api_url = os.getenv("API_URL", "http://localhost:8000")

try:
    response = requests.post(f"{api_url}/load_existing_data")
    if response.status_code == 200:
        data = response.json()
        print(f"Success: {data['message']}")
    else:
        print(f"Error: {response.status_code} - {response.text}")
except Exception as e:
    print(f"Error: {str(e)}")
