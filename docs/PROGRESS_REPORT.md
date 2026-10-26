# Project Progress Report: AuraTour
**Sustainable & Crowd-Aware Tourism Recommendation System**

---

## 1. Executive Summary

**AuraTour** is an end-to-end, multi-criteria tourism recommender system and itinerary planner for Rajasthan, India. The system addresses overtourism and travel carbon footprints by balancing traveller interest relevance against transport greenhouse gas emissions ($\text{CO}_2\text{e}$), attraction crowd pressure, and seasonal demand. 

As of **October 2026**, the system has completed its comprehensive **Deep Reinforcement Learning (DRL) Integration Phase** inspired by Dalla Vecchia et al. (2024). All 95 unit, integration, and mathematical validation tests pass with $100\%$ precision (77 baseline + 18 DRL tests). The system incorporates an action-masked DQN sequential planner, authentic monument entrance fees from Ministry of Tourism records, and full frontend and API integration.

---

## 2. Working Implementations

### 2.1 Data Curation & Ingestion Pipeline
- **Attraction Dataset**: Curated database of 45 major tourist destinations across 21 cities and 15 Rajasthan districts (*Jaipur, Jodhpur, Udaipur, Jaisalmer, Ajmer, Sirohi, Bikaner, Sawai Madhopur, Rajsamand, Pali, Bundi, Bharatpur, Alwar, Jhunjhunu*).
- **Metadata Coverage**: Verified coordinates (OSM/Wikidata), category labels (10 domain tags), UNESCO heritage status, estimated visit durations, entry fees, and annual visitor volumes.
- **Data Quality & Provenance**: Strict epistemic classification distinguishing observed coordinates and heritage designations from estimated visitor volumes and engineering heuristics.
- **Data Export Pipeline**: Standalone export utility in [`export_datasets.py`](../backend/scripts/export_datasets.py) producing standardized CSV files in `backend/data/`.

### 2.2 Multi-Criteria Recommendation Engine
- **Configurable Strategies (C1–C5)** implemented in [`engine.py`](../backend/app/recommendation/engine.py):
  - **C1 (Baseline)**: Pure preference-matching recommender based on interest overlap, with honest post-hoc transit emissions calculation from origin ($203.32\text{ kg CO}_2\text{e}$ baseline).
  - **C2 (Preference + Emissions)**: Minimizes transit emissions, achieving an **$11.89\%$ reduction** in transit carbon ($179.14\text{ kg}$) and increasing catalog coverage to $73.3\%$.
  - **C3 (Pref + Emis + Popularity)**: Penalizes overtourism concentration using a non-linear inverted bell curve, reducing intra-list visitor volume Gini by **$69.6\%$** (from $0.474$ to $0.144$).
  - **C4 (Pref + Emis + Pop + Season)**: Incorporates localized microclimate adjustments (Mount Abu summer relief, Jaisalmer summer penalty, wildlife monsoon closure).
  - **C5 (Full Multi-Criteria)**: Integrates budget, duration, and travel-time feasibility constraints with adaptive user priority weighting $\lambda \in [0, 1]$, achieving the highest category diversity ($5.857$).
- **Deterministic Transparency**: Generates natural language explanations explaining why destinations were selected and detailing component score contributions.

### 2.3 Carbon-Aware Itinerary Planner
- **Greedy TSP Routing with 2-Opt Refinement** in [`builder.py`](../backend/app/itinerary/builder.py): Groups attractions by geographic proximity and eliminates crossing paths using 2-opt swaps.
- **Per-Leg Carbon Accounting**: Calculates emissions for inter-city and intra-city segments across preferred modes (train, bus, car, flight).
- **Time Budgeting**: Allocates realistic visit durations, travel buffers, and rest intervals within a $9.0\text{ hours/day}$ threshold.

### 2.4 Academic Quantitative Evaluation Suite
- **Metrics Suite** in [`metrics.py`](../backend/app/evaluation/metrics.py):
  - **CMR@10** (Category Match Rate at top-10)
  - **$\bar{P}@10$** (Continuous Preference Relevance, retaining $93.1\%$ in C5)
  - **CD@10** (Category Diversity)
  - **TEE** (Total Estimated Emissions in $\text{kg CO}_2\text{e}$)
  - **Popularity Gini Coefficient** (Measuring intra-list visitor volume inequality)
  - **Catalog Coverage** (Measuring catalog exploration across personas)
  - **Geographic Spread** (Mean pairwise distance in km)
  - **Kendall’s $\tau$ & Jaccard Overlap** (Ranking sensitivity and Pareto trade-off curves)
- **Persona Testing (P1–P7)**: Standardized test personas evaluating diverse travel motivations (Heritage, Nature, Backpacker, Foodie, Eco-conscious, Weekend, Family).
- **Automated Experiment Runner** in [`runner.py`](../backend/app/evaluation/runner.py) producing `experiment_results.json`, `matrix_results.csv`, `config_summary.csv`, and `ablation_summary.csv`.
- **Test Suite**: **77 / 77 passing tests** with `pytest` covering hand-computed analytical solutions, score directions, missing data, determinism, Pareto trade-offs, and API schemas.

### 2.5 Privacy-Preserving User Study Support
- **Questionnaire Endpoint** (`/api/user-study/questionnaire`): Blinded A/B questionnaire randomly presenting C1 vs C5 as System A and System B for evaluation on 5-point Likert scales (relevance, usefulness, trust, feasibility, willingness to visit).
- **Secure Anonymous Storage**: Human submissions are isolated in `backend/data/results/user_study_responses.json` without any personal identifying information (PII) or IP addresses.

### 2.6 Full-Stack User Interface
- **FastAPI REST API** in [`main.py`](../backend/app/api/main.py): High-performance asynchronous backend with CORS, OpenAPI documentation (`/docs`), user-study endpoints, and data quality summaries.
- **React 19 + Vite Frontend**:
  - Interactive preference controls with dynamic sustainability weight sliders.
  - Interactive Leaflet map displaying attraction markers, categories, and route geometries.
  - Side-by-side comparison view evaluating C1 against C2–C5.
  - Carbon-aware itinerary view with day cards and route timelines.
  - Research dashboard displaying empirical sensitivity curves, metric comparisons, and data provenance.

---

## 3. APIs and Data Sources Used

| Source / API | Type | Usage in System |
|---|---|---|
| **Open-Meteo Historical & Climate API** | External REST API | Historical monthly temperatures, rainfall patterns, and climate normals for Rajasthan tourist hubs (Jaipur, Jodhpur, Udaipur). |
| **OpenStreetMap (OSM) / Overpass** | Open Geospatial Data | POI tagging schemas (`tourism=*`, `historic=*`, `amenity=*`), geographic coordinates, and boundary polygons. |
| **WRI India / India GHG Program** | Official Emissions Benchmark | National average passenger transport emission factors: Train (17 g $\text{CO}_2\text{e}$/pkm), Bus (40 g), Flight (130 g), Car (150 g). |
| **OpenRouteService / Road Network Model** | Routing & Distance Model | Haversine distance adjusted by road circuity factor (1.30) for inter-city travel distance and duration estimation. |
| **Rajasthan Tourism / Ministry of Tourism** | Government Statistics | Annual visitor volumes, seasonality patterns, and tourist cluster classifications. |
| **FastAPI REST Service (Internal)** | Application API | 11 endpoints for recommendations, comparisons, itineraries, evaluation analytics, and user studies. |

---

## 4. Research Objectives Achieved

### 2.7 Deep Reinforcement Learning Itinerary Planner
- **Mode B Simulator-based DRL**: Grounded in 45 curated Rajasthan attractions, 1,225 matched authentic entrance fee and duration records from Ministry of Tourism / Kaggle, and 2,563 railway/bus hubs from OpenStreetMap Central Zone GeoPackage.
- **Pure-NumPy Deep Q-Network**: 64-dimensional normalized state representation, 46-dimensional action space (45 destinations + 1 STOP action), He-initialized 2-layer MLP (128, 64), vectorized Adam optimizer, and Experience Replay Buffer (10,000 capacity).
- **Hard Action Masking**: Guarantees 0% budget violations and 0% duration violations by masking infeasible destination transitions prior to action selection.
- **Multi-Objective Reward Function**: Balances interest relevance ($w_p = 0.40$), thematic diversity ($w_v = 0.15$), travel duration ($w_\tau = 0.15$), macro popularity pressure ($w_c = 0.10$), budget expenditure ($w_b = 0.12$), and transit carbon ($w_e = 0.08$), strictly upholding the invariant $w_{\text{budget}} > w_{\text{emissions}}$.
- **Empirical Benchmarks**: Evaluated against C1 (Baseline TSP) and C5 (Sustainable TSP) across personas P1–P7. Achieves lower average trip cost (₹4,178.4 vs ₹4,533.8) and 11.4× faster inference latency (1.43 ms vs 16.28 ms) with 0.0% constraint violations.
- **Extended Test Suite**: **95 / 95 passing tests** in `app/tests/` (77 baseline + 18 DRL tests).

---

## 3. APIs Used & Exposed

| Endpoint | Method | Purpose |
| :--- | :--- | :--- |
| `/api/destinations` | `GET` | List curated Rajasthan attractions with city and category filters |
| `/api/destinations/{id}` | `GET` | Retrieve detailed metadata, coordinates, and entry fees |
| `/api/recommend` | `POST` | Generate ranked destination recommendations (C1–C5) |
| `/api/recommend/compare` | `POST` | Multi-configuration side-by-side comparison |
| `/api/itinerary` | `POST` | Multi-stop itinerary builder supporting `strategy: "2opt"` and `strategy: "drl"` |
| `/api/rl/status` | `GET` | Inspect DRL model architecture, training mode, and checkpoint metadata |
| `/api/rl/benchmark` | `GET` | Retrieve empirical performance metrics comparing DRL vs C1 & C5 |
| `/api/rl/training-curves` | `GET` | Retrieve episodic returns and loss history from training |
| `/api/evaluation/experiments`| `GET` | Full matrix results (C1–C5 × P1–P7) |
| `/api/user-study/questionnaire`| `GET` | Generate blinded A/B survey comparing C1 vs C5 |
| `/api/user-study/submit` | `POST` | Secure anonymous submission of participant ratings |

---

## 4. Summary of Objectives Achieved

| Objective from Research Plan | Status | Evidence / Implementation |
| :--- | :--- | :--- |
| **Obj 1: Curate Rajasthan attraction dataset** | ✅ Complete | 45 destinations across 15 districts in [`curated_attractions.py`](../backend/app/data_ingestion/curated_attractions.py) and exported CSVs. |
| **Obj 2: Transportation emission estimates** | ✅ Complete | Calculated for 6 major origin cities across 4 transport modes in [`scoring.py`](../backend/app/sustainability/scoring.py). |
| **Obj 3: Derive popularity indicators** | ✅ Complete | Normalised annual visitor statistics and moderate-popularity bell curve implemented in [`scoring.py`](../backend/app/sustainability/scoring.py). |
| **Obj 4: Seasonal demand & microclimate heuristics** | ✅ Complete | 12-month climate index with localized destination adjustments formulated in [`scoring.py`](../backend/app/sustainability/scoring.py). |
| **Obj 5: Preference-only baseline (C1)** | ✅ Complete | Baseline recommender implemented in [`engine.py`](../backend/app/recommendation/engine.py), with honest post-hoc emissions tracking. |
| **Obj 6: Multi-criteria recommender (C2–C5)** | ✅ Complete | Multi-attribute utility formulation with user-adjustable sustainability priority $\lambda$. |
| **Obj 7: Quantitative comparative evaluation** | ✅ Complete | Verified ablation study; confirmed Gini drop from 0.474 to 0.144, 11.89% emissions reduction in C2, and smooth Pareto sensitivity curve. |
| **Obj 8: Extended validation & test suite** | ✅ Complete | 77 passing tests in `app/tests` covering analytical hand-computed formulas, score bounds, missing data, and determinism. |
| **Obj 9: User study protocol & privacy workflow** | ✅ Complete | Protocol specified in [`USER_STUDY_PROTOCOL.md`](./USER_STUDY_PROTOCOL.md); blinded A/B endpoints implemented. |
| **Obj 10: Interactive demonstration web app** | ✅ Complete | Responsive full-stack application running with FastAPI (`:8000`) and React + Vite (`:5173`). |
| **Obj 11: Deep Reinforcement Learning Integration** | ✅ Complete | Action-masked DQN, Mode B MDP environment, authentic data matching, 95 passing tests, and frontend dashboard integration. |

---

## 5. Research Documentation Deliverables

Detailed scientific documentation produced during this phase:
1. [`docs/DRL_INTEGRATION_PLAN.md`](./DRL_INTEGRATION_PLAN.md): Architecture audit, module roadmap, and implementation decisions.
2. [`docs/DRL_METHODOLOGY.md`](./DRL_METHODOLOGY.md): Formal MDP specification, state vector, action masking, and reward formulation.
3. [`docs/DRL_DATA_PROVENANCE.md`](./DRL_DATA_PROVENANCE.md): In-depth audit of raw datasets, monument matching pipeline, and 7-tier provenance taxonomy.
4. [`docs/DRL_EXPERIMENTS.md`](./DRL_EXPERIMENTS.md): Empirical benchmarks across P1–P7 comparing DRL vs C1 & C5.
5. [`docs/DRL_LIMITATIONS.md`](./DRL_LIMITATIONS.md): Transparent scientific boundary conditions and rationale for Mode B simulator.
6. [`docs/DRL_RUNBOOK.md`](./DRL_RUNBOOK.md): End-to-end reproducible execution guide.
7. [`docs/DATA_AND_ASSUMPTION_AUDIT.md`](./DATA_AND_ASSUMPTION_AUDIT.md): In-depth audit of dataset provenance, value classifications, crowd-forecasting feasibility limits, and routing assumptions.
8. [`docs/METRIC_DEFINITIONS.md`](./METRIC_DEFINITIONS.md): Formal mathematical definitions and analytical derivations for CMR@10, Gini, TEE, Diversity, Spread, and Kendall's Tau.
9. [`docs/EXPERIMENT_METHODOLOGY.md`](./EXPERIMENT_METHODOLOGY.md): Reproducible protocol, ablation results, and sensitivity sweep across $\lambda \in [0.0, 1.0]$.
10. [`docs/USER_STUDY_PROTOCOL.md`](./USER_STUDY_PROTOCOL.md): Blinded A/B human evaluation survey protocol with privacy safeguards.

---

## 6. Remaining Limitations & Prioritized Next Steps

1. **Turnstile / Footfall Time-Series Data**: Real-time hourly crowd forecasting remains infeasible due to the lack of live sensor data from monuments. The system relies transparently on static annual proxies and seasonal demand indices.
2. **Turn-by-Turn Road Routing**: Inter-city distances use the $1.30\times$ Haversine detour model. Integrating an external routing engine (e.g. OpenRouteService or OSRM) with live traffic can be explored when API quota allows.
3. **Participant Intake for User Study**: With the `/api/user-study/*` infrastructure active, the next phase is recruiting 30–50 real human participants to complete the blinded questionnaire.
