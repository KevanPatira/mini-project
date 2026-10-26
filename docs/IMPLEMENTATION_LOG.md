# Implementation Log

## Phase 1: Workspace Inspection and Research Planning

### Date: 2026-10-18

**Status:** ✅ Complete

**Actions:**
1. Inspected workspace — found empty directory at `d:\Btech_Projects\mini_project`
2. Created project directory structure:
   - `docs/` — research documentation
   - `backend/app/` — Python backend modules
   - `backend/data/` — datasets (raw, processed, emissions, weather)
   - `backend/scripts/` — data pipeline scripts
   - `frontend/src/` — React frontend
3. Created documentation:
   - `docs/PROJECT_OVERVIEW.md`
   - `docs/RESEARCH_PLAN.md`
   - `docs/DATA_SOURCE_AUDIT.md`
   - `docs/SYSTEM_ARCHITECTURE.md`
   - `docs/EXPERIMENT_PLAN.md`
   - `docs/IMPLEMENTATION_LOG.md`

**Decisions:**
- **Geographic scope:** Rajasthan, India — chosen for data availability, attraction diversity, and manageable scope
- **Primary data sources:** OSM (attractions), ORS (routing), Open-Meteo (weather), WRI India (emissions), Ministry of Tourism (visitor stats)
- **Crowd forecasting:** Marked as future extension — no suitable open timestamped data found
- **Seasonal demand:** Will use heuristic combining weather comfort + known tourism patterns (explicitly labelled)

**Key findings from data audit:**
- OSM has good coverage for major Rajasthan attractions
- India-specific emission factors are well-documented (WRI India / India GHG Program)
- Open-Meteo provides free historical weather data (no API key needed)
- Monthly tourism statistics are limited (mostly annual); will need seasonal heuristic
- No real-time crowd data available for Indian attractions

---

## Phase 2: Dataset Discovery and Data Pipeline

### Date: 2026-10-18

**Status:** ✅ Complete

**Actions:**
1. Curated dataset of 45 major tourist attractions across 10 Rajasthan districts (Jaipur, Jodhpur, Udaipur, Jaisalmer, Pushkar, Bikaner, Mount Abu, Sawai Madhopur, Bharatpur, Chittorgarh, Bundi).
2. Defined category mappings connecting user interests (history, architecture, nature, wildlife, culture, religion, adventure, food, shopping, relaxation) to OSM amenity/tourism tags.
3. Compiled India-specific transportation emission factors (WRI India / India GHG Program 2023-24) for train (17 g/pkm), bus (40 g/pkm), flight (130 g/pkm), and private car (150 g/pkm).
4. Formulated seasonal demand and weather benchmarks incorporating Open-Meteo & IMD climate norms for Rajasthan.
5. Implemented `backend/scripts/export_datasets.py` exporting clean CSV artifacts to `backend/data/processed/`, `backend/data/emissions/`, and `backend/data/weather/`.

---

## Phase 3: Core Scoring Engine and Itinerary Builder

### Date: 2026-10-18

**Status:** ✅ Complete

**Actions:**
1. Built transparent multi-criteria recommendation engine (`backend/app/recommendation/engine.py`) supporting C1 baseline and C2–C5 multi-criteria configurations.
2. Built scoring module (`backend/app/sustainability/scoring.py`) with inverted emission scores, popularity de-concentration penalties, and seasonal demand balancing.
3. Developed carbon-aware day-by-day itinerary builder (`backend/app/itinerary/builder.py`) with greedy/TSP travel sequencing, realistic visit durations, and per-leg carbon footprint accounting.
4. Added deterministic, transparent template-based explanations for all recommendations detailing why attractions were ranked and acknowledging data provenance.

---

## Phase 4: Quantitative Evaluation and Verification

### Date: 2026-10-18

**Status:** ✅ Complete

**Actions:**
1. Implemented full suite of academic evaluation metrics (`backend/app/evaluation/metrics.py`):
   - Category Match Rate (CMR@10)
   - Category Diversity (CD@10)
   - Total Estimated Emissions (TEE)
   - Popularity Gini coefficient
   - Geographic Spread (mean pairwise distance)
   - Kendall's Tau rank correlation & Jaccard overlap
2. Designed 7 standard evaluation personas (P1–P7) across diverse origins, interest profiles, and sustainability priorities.
3. Executed full experiment runner across C1–C5 configurations and sensitivity sweeps:
   - C1 Baseline: 100% CMR@10, Popularity Gini 0.474.
   - C3/C4 Crowd-Aware: Popularity Gini dropped to 0.144 (reducing crowd concentration by >69%).
   - C2/C5 Low-Carbon: Avg emission score elevated to 0.742–0.793.
4. Resolved Python 3.14 / Pandas 2 string dtype parsing edge case in `backend/app/data_ingestion/loader.py` and `backend/app/recommendation/engine.py` ensuring non-scalar safe evaluation.
5. All 50 unit and integration tests passing (`test_scoring.py`, `test_itinerary.py`, `test_evaluation.py`).

---

## Phase 5: Modern Interactive Web Application & API

### Date: 2026-10-18

**Status:** ✅ Complete

**Actions:**
1. Developed FastAPI backend (`backend/app/api/main.py`) exposing endpoints:
   - `/api/recommend` (Baseline and Multi-criteria recommendations)
   - `/api/compare` (Side-by-side C1–C5 breakdown)
   - `/api/itinerary` (Carbon-optimized travel itineraries)
   - `/api/evaluation/summary`, `/api/evaluation/sensitivity`, `/api/evaluation/experiments` (Research dashboard)
   - `/api/destinations` and `/api/meta/*`
2. Built React frontend with modern UI (`frontend/src/`):
   - Preference configuration form with real-time sliders and origin selection.
   - Interactive Leaflet map visualizing attraction coordinates, categories, and routes.
   - Comparative evaluation view showing side-by-side configuration shifts.
   - Day-by-day itinerary builder with transport mode breakdown and total CO₂e metrics.
   - Research dashboard visualizing sensitivity curves, metric comparisons, and data provenance.
3. Verified clean production build of frontend with Vite.

