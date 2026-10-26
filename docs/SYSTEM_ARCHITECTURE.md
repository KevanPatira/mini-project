# System Architecture

## 1. High-Level Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                      React Frontend                         │
│  ┌──────────┐ ┌────────────┐ ┌─────────┐ ┌──────────────┐  │
│  │Preference│ │Recommendation│ │  Map   │ │  Research   │  │
│  │  Form    │ │   Results   │ │  View  │ │  Dashboard  │  │
│  └──────────┘ └────────────┘ └─────────┘ └──────────────┘  │
└────────────────────────┬─────────────────────────────────────┘
                         │ REST API (JSON)
┌────────────────────────┴─────────────────────────────────────┐
│                    FastAPI Backend                            │
│  ┌─────────┐ ┌──────────────┐ ┌────────────┐ ┌───────────┐ │
│  │   API   │ │Recommendation│ │Sustainability│ │ Itinerary │ │
│  │ Routes  │ │   Engine     │ │  Scoring    │ │  Builder  │ │
│  └─────────┘ └──────────────┘ └────────────┘ └───────────┘ │
│  ┌─────────────┐ ┌──────────────┐ ┌─────────────────────┐  │
│  │Data Ingestion│ │Data Processing│ │    Evaluation      │  │
│  └─────────────┘ └──────────────┘ └─────────────────────┘  │
└────────────────────────┬─────────────────────────────────────┘
                         │
┌────────────────────────┴─────────────────────────────────────┐
│                    Data Layer                                 │
│  ┌───────────┐ ┌──────────┐ ┌──────────┐ ┌───────────────┐ │
│  │Attractions│ │Transport │ │Popularity│ │Weather/Season │ │
│  │  (CSV)    │ │Emissions │ │  (CSV)   │ │   (CSV)       │ │
│  │           │ │  (CSV)   │ │          │ │               │ │
│  └───────────┘ └──────────┘ └──────────┘ └───────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

## 2. Backend Module Responsibilities

### `backend/app/data_ingestion/`
- Load and validate raw CSV/Parquet datasets
- Schema validation with Pydantic models
- Data quality checks (missing values, coordinate ranges, duplicate detection)

### `backend/app/data_processing/`
- Clean and normalise attraction data
- Compute derived features (distance calculations, category mapping)
- Join datasets (attractions + popularity + seasonal data)
- Feature preparation for scoring

### `backend/app/sustainability/`
- **Emissions calculator:** CO₂e estimation based on distance × emission factor × transport mode
- **Popularity scorer:** Normalised popularity index from visitor counts / search interest
- **Seasonality scorer:** Monthly demand index based on tourism statistics + weather comfort
- **Composite score:** Weighted multi-criteria sustainability index

### `backend/app/recommendation/`
- **Baseline recommender:** Preference-only ranking using interest category matching
- **Multi-criteria recommender:** Full sustainability-aware ranking
- **Score explanation generator:** Template-based explanation of each score component
- **Comparison engine:** Side-by-side ranking with different weight configurations

### `backend/app/crowd_forecasting/` (optional)
- Placeholder for future crowd-level prediction
- Currently uses seasonal heuristic as transparent proxy

### `backend/app/itinerary/`
- Multi-stop itinerary builder
- Travel time and sequence optimisation
- Constraint checking (trip duration, opening hours if available)

### `backend/app/evaluation/`
- Experiment runner for all configurations (C1–C5)
- Metric computation (diversity, emission totals, rank correlation)
- Sensitivity analysis across weight ranges
- Result serialisation to JSON/CSV

### `backend/app/api/`
- FastAPI router definitions
- Pydantic request/response models
- Input validation and error handling
- CORS configuration

### `backend/app/tests/`
- Unit tests for scoring, normalisation, ranking
- Integration tests for API endpoints
- Data validation tests

## 3. API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/api/destinations` | GET | List available destinations with filters |
| `/api/destinations/{id}` | GET | Destination detail with full metadata |
| `/api/recommend` | POST | Get ranked recommendations based on preferences |
| `/api/compare` | POST | Compare rankings with different weight configs |
| `/api/itinerary` | POST | Generate multi-stop itinerary |
| `/api/evaluation/summary` | GET | Research evaluation metrics |
| `/api/evaluation/sensitivity` | GET | Weight sensitivity analysis |
| `/api/meta/categories` | GET | Available interest categories |
| `/api/meta/origins` | GET | Available origin cities |
| `/api/health` | GET | Service health check |

## 4. Frontend Components

| Component | Description |
|---|---|
| `PreferenceForm` | Multi-step form for interests, origin, dates, budget, weights |
| `RecommendationList` | Ranked cards showing scores, explanations, sustainability badges |
| `ComparisonView` | Side-by-side ranking comparison with different settings |
| `MapView` | Leaflet map showing destinations, routes, clusters |
| `ItineraryView` | Day-by-day trip plan with timing and transport |
| `ResearchDashboard` | Dataset stats, experiment results, sensitivity plots |
| `ScoreBreakdown` | Visual decomposition of recommendation score |

## 5. Data Flow

```
User submits preferences
  → API validates input (Pydantic)
  → Load candidate destinations (data_ingestion)
  → Filter by constraints (data_processing)
  → Compute preference relevance score
  → Compute emission score (origin → destination)
  → Compute popularity score
  → Compute seasonal demand score (for travel month)
  → Compute feasibility score (travel time/cost)
  → Combine with user-specified weights
  → Rank and return top-K with explanations
```

## 6. Configuration

All scoring parameters stored in `backend/app/config.py`:
- Default weights for each component
- Emission factors by transport mode
- Normalisation bounds
- API rate limit settings
- Data file paths
