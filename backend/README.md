# Sustainable Tourism Recommendation System — Backend

## Setup

```bash
cd backend
pip install -r requirements.txt
```

## Running

```bash
uvicorn app.api.main:app --reload --port 8000
```

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── config.py              # Central configuration
│   ├── api/                   # FastAPI endpoints
│   ├── data_ingestion/        # Dataset loading & validation
│   ├── data_processing/       # Cleaning, normalisation, joins
│   ├── sustainability/        # Emissions, popularity, seasonality scoring
│   ├── recommendation/        # Baseline and multi-criteria ranking
│   ├── crowd_forecasting/     # Optional crowd prediction
│   ├── itinerary/             # Route and visit planning
│   ├── evaluation/            # Experiment runner and metrics
│   └── tests/                 # Test suite
├── data/
│   ├── raw/                   # Original downloaded datasets
│   ├── processed/             # Cleaned and joined datasets
│   ├── emissions/             # Emission factor tables
│   └── weather/               # Weather data
├── scripts/                   # Data pipeline scripts
└── requirements.txt
```
