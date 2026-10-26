# Project Overview: Sustainable and Crowd-Aware Tourism Recommendation System

## 1. Project Title

**A Sustainable and Crowd-Aware Tourism Recommendation System**

## 2. Problem Statement

Mass tourism concentrates visitors at popular destinations during peak seasons, causing environmental degradation, overcrowding, and diminished visitor experiences. Existing tourism recommender systems primarily optimise for user preferences and popularity, inadvertently exacerbating these problems by funnelling more tourists to already-strained destinations.

This project develops a tourism recommendation system that balances **traveller preferences** with **sustainability indicators** — specifically transportation emissions, destination popularity pressure, and seasonal tourism demand — to provide recommendations that are both personally relevant and environmentally conscious.

## 3. Core Research Objective

Develop and evaluate a multi-criteria tourism recommendation system that integrates:

1. **Traveller preferences and interests** — matching user categories (history, nature, food, culture, etc.)
2. **Estimated transportation CO₂e emissions** — for travel from origin to destination via different transport modes
3. **Destination popularity** — as a proxy for overtourism pressure
4. **Seasonal tourism demand** — monthly/quarterly visitor patterns
5. **Travel feasibility** — travel time, transport options, and itinerary constraints

The system recommends suitable destinations while **transparently explaining** the trade-offs between personal relevance, sustainability, and tourism pressure.

## 4. Geographic Scope

**Initial scope: Rajasthan, India**

Rationale:
- Rich diversity of tourist attractions (forts, palaces, temples, wildlife, desert landscapes)
- Strong OSM coverage for POI data
- Available official tourism statistics from Ministry of Tourism and state government
- Well-connected transport network (rail, road, air)
- Significant seasonal variation in tourism demand
- Manageable geographic area for initial research validation

## 5. Key Deliverables

| Deliverable | Description |
|---|---|
| Research documentation | Problem statement, research plan, data audit, experiment design |
| Curated datasets | Attractions, transport emissions, popularity, seasonal demand, weather |
| Baseline recommender | Preference-only ranking system |
| Multi-criteria recommender | Sustainability-aware ranking with configurable weights |
| Evaluation experiments | Comparative analysis across recommendation strategies |
| Web application | React frontend + FastAPI backend with map visualisation |
| Research dashboard | Dataset coverage, scoring diagnostics, sensitivity analysis |

## 6. Technology Stack

| Layer | Technology |
|---|---|
| Frontend | React + Vite + TypeScript |
| Backend | Python + FastAPI + Pydantic |
| Data Science | pandas, NumPy, scikit-learn, Matplotlib |
| Maps | Leaflet.js + OpenStreetMap tiles |
| Routing | OpenRouteService (free tier) / OSRM |
| Storage | CSV/Parquet for datasets, SQLite for app metadata |
| Weather | Open-Meteo Historical API (free, no key) |
| POI Data | OpenStreetMap via Overpass API |

## 7. Reference Papers

1. Banerjee, A., Mahmudov, T., Adler, E., et al. (2025). *Modeling sustainable city trips: integrating CO₂e emissions, popularity, and seasonality into tourism recommender systems.* Information Technology & Tourism.
2. Migliorini, S., Dalla Vecchia, A., Belussi, A., Quintarelli, E. (2026). *ARTEMIS: a Context-Aware Recommendation System with Crowding Forecaster for the Touristic Domain.* Information Systems Frontiers.

## 8. Ethical Commitments

- No fabricated data, metrics, or citations
- Clear distinction between observed data, estimates, and heuristics
- Transparent documentation of data provenance and limitations
- No scraping in violation of terms of service
- No committed API keys or credentials
- Synthetic data clearly labelled, never used for final validation claims
