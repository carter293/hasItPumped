# Has It Pumped? 📈

![Has It Pumped Logo](/frontend/public/pumped.png)

A Solana token analysis tool that predicts whether tokens have already peaked or still have room to grow.

## 📋 Overview

**Has It Pumped?** is a web application that helps users analyze Solana tokens, particularly those from [pump.fun](https://pump.fun), to determine if they've already reached their peak price or if they still have potential for growth. The application:

- Analyzes Solana token price history
- Predicts if tokens are "pre-peak" or "post-peak"
- Visualizes token price charts
- Provides confidence levels for predictions
- Displays recent tokens and overall statistics

## 🏗️ Project Structure

The project is organized as a full-stack application:

```
analysis/ # Analysis for prediction model
hasItPumped/
├── frontend/     # Next.js frontend application
└── backend/      # FastAPI backend service
```

### Frontend (Next.js)

The frontend is built with Next.js 14, using React, TypeScript, and Tailwind CSS. It includes:

- Interactive token analysis interface
- Token price charts via GeckoTerminal integration
- Mobile-responsive design
- Recent token listings
- Statistics dashboard

### Backend (FastAPI)

The backend is built with FastAPI and provides:

- Token analysis endpoint `/analyze_token`
- Database statistics via `/stats`
- XGBoost machine learning model for peak prediction
- Integration with BitQuery API for Solana DEX data
- Supabase database for caching token data (SQLite for local dev)

## 🚀 Features

- **Token Analysis:** Enter a Solana token mint address and get instant analysis
- **Pre-Peak/Post-Peak Prediction:** ML-powered prediction on token price potential
- **Price Visualization:** Interactive price charts showing historical token performance
- **Token Stats:** Quick view of token metadata, price, and volume
- **Recent Tokens:** Browse recently analyzed tokens
- **Dashboard Statistics:** View overall stats on analyzed tokens

## 🛠️ Technical Stack

### Frontend
- **Framework:** Next.js 14
- **Language:** TypeScript
- **Styling:** Tailwind CSS, Shadcn/UI components
- **State Management:** React Query
- **Charts:** GeckoTerminal chart integration

### Backend
- **Framework:** FastAPI
- **Language:** Python 3.11+
- **Database:** SQLite
- **Machine Learning:** XGBoost
- **Data Processing:** Pandas
- **API Integration:** BitQuery for DEX data, GeckoTerminal for token metadata

## 💻 Installation and Setup

### Prerequisites
- Node.js 22+
- Python 3.11+
- Poetry (optional, for backend dependency management)

### Backend Setup
```bash
# Navigate to backend directory
cd hasItPumped/backend

# Install dependencies using Poetry
poetry install

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys (BitQuery API)

# Setup local dev DB (one off)
poetry run python src/solana_token_api/initialise_local_dev_db.py

# Run the backend service
poetry run python run.py
```

### Frontend Setup
```bash
# Navigate to frontend directory
cd hasItPumped/frontend

# Install dependencies
npm ci

# Set up environment variables
cp .env.example .env.local

# Run the development server
npm run dev
```

## 🔄 API Endpoints

### `/analyze_token` (POST)
Analyzes a Solana token and determines if it's pre-peak or post-peak.

Request:
```json
{
  "mint_address": "SoLANATokenAddressHere..."
}
```

Response:
```json
{
  "mint_address": "SoLANATokenAddressHere...",
  "data": [...],  // Historical OHLCV data
  "is_pre_peak": true,  // Prediction result
  "confidence": 0.85,   // Confidence score (0-1)
  "days_of_data": 30    // Days of historical data
}
```

### `/stats` (GET)
Returns overall statistics about analyzed tokens.

Response:
```json
{
  "total_tokens": 150,
  "pre_peak_count": 45,
  "post_peak_count": 105,
  "recent_tokens": [...]  // List of recently analyzed tokens
}
```

## 🔍 How It Works

1. The application fetches historical price data for Solana tokens using the BitQuery API
2. Data is processed and feature engineering is applied
3. An XGBoost model trained on historical token patterns makes the pre/post-peak prediction
4. Token metadata is fetched from GeckoTerminal
5. Results are presented in the UI with visualizations


## Pre-commit hooks (Backend only)
This project uses pre-commit to automatically run checks like black, isort, and mypy before you commit code.
✅ One-time setup (required)
1. Install pre-commit (if you haven’t already):  
  `pip install pre-commit`
2. Install the Git hooks from the backend directory:  
  ```bash
  cd hasItPumped/backend
  pre-commit install
  ```
3. (Optional but recommended) Run the hooks on all files to catch issues now:  
  `pre-commit run --all-files`

## 📝 Note

This tool provides analysis based on historical patterns and should not be considered financial advice. The model is trained on historical data patterns of Solana tokens and makes predictions based on these patterns.

## 🚨 Limitations

- Only works with tokens that have sufficient historical data (minimum 3 days)
- Only analyzes Solana blockchain tokens
- Predictions are based on statistical patterns and are not guaranteed

## 📄 License

[MIT License](LICENSE)

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request