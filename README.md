# AuraTour — Sustainable Tourism Recommendation System with Deep Reinforcement Learning

> **A research-oriented sequential tourism recommendation and itinerary planning engine for Rajasthan, India, integrating multi-criteria sustainability scoring and Deep Reinforcement Learning (DRL) under strict travel-time, trip-duration, and budget constraints.**

Inspired by:
> *“Promoting sustainable tourism by recommending sequences of attractions with deep reinforcement learning”*  
> Anna Dalla Vecchia, Sara Migliorini, Alberto Belussi, and Carola Ricci (2024).  
> *Information Technology & Tourism*, 26, 451–482. [DOI: 10.1007/s40558-024-00288-x](https://doi.org/10.1007/s40558-024-00288-x)

---

## 🌟 Key Capabilities

1. **Multi-Criteria Recommendation Configurations (C1–C5):**
   - **C1 (Baseline):** Content-based interest category matching.
   - **C2 (Emissions-Aware):** Modal transit carbon optimization ($17\text{ g/pkm}$ rail, $40\text{ g}$ bus, $150\text{ g}$ car).
   - **C3 (Popularity-Aware):** Macro-level congestion relief reducing Gini coefficient from 0.474 down to 0.144.
   - **C4 (Seasonality-Aware):** Climate and seasonal demand optimization.
   - **C5 (Full Composite):** Pareto-optimal multi-criteria ranking.

2. **Sequential Itinerary Optimization:**
   - **Heuristic Baseline:** Nearest-neighbor greedy TSP with 2-opt local search swap optimization.
   - **Deep Reinforcement Learning (Mode B):** Pure-NumPy Deep Q-Network (DQN) with **hard action masking** for remaining budget and 9-hour daily sightseeing windows.

3. **Authentic Indian Data Grounding:**
   - **Kaggle Indian Tourist Places Dataset:** 13,000 national records; 1,225 matched Rajasthan records with authentic entry fees and visit durations.
   - **OpenStreetMap & Central Zone GeoPackage:** 2,563 regional transit stations and railway geometries.
   - **Archaeological Survey of India (ASI):** Central protected ticketed monument visitation headcounts.
   - **45 Verified Destinations:** Curated across 18 districts of Rajasthan.

---

## 📊 Empirical Research Findings

Benchmark across 7 standardized traveler personas (P1–P7):

| Strategy | Avg Stops | Avg CO₂e (kg) | Avg Cost (INR) | CMR Match | Inference Latency | Budget Violations |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **C1 Baseline TSP** | 6.86 | 40.4 kg | ₹4,533.8 | 100% | 16.28 ms | 0.0% |
| **C5 Sustainable TSP** | 6.86 | **39.1 kg** | ₹4,273.4 | 100% | 22.41 ms | 0.0% |
| **DRL Mode B Agent** | 6.00 | 42.4 kg | **₹4,178.4** | 84.3% | **1.43 ms (11.4× faster)** | **0.0%** |

---

## 🚀 Quickstart Guide

### 1. Run Automated Test Suite (95 Tests)
```bash
cd backend
python -m pytest app/tests/ -v
```

### 2. Ingest and Match Monument Datasets
```bash
cd backend
python app/data_ingestion/monument_matcher.py
```

### 3. Train DRL Agent (500 Episodes)
```bash
cd backend
python scripts/train_drl.py --episodes 500 --seed 42
```

### 4. Run Benchmark Experiments (C1 vs C5 vs DRL)
```bash
cd backend
python scripts/run_drl_experiments.py
```

### 5. Launch Backend & Frontend
```bash
# Terminal 1: Backend API
cd backend
python -m uvicorn app.api.main:app --port 8000 --reload

# Terminal 2: React Frontend
cd frontend
npm run dev
```

Visit the application at `http://localhost:5173`.

---

## 📚 Documentation Catalogue

- [DRL Integration Plan](docs/DRL_INTEGRATION_PLAN.md): Architecture audit, module roadmap, and implementation rationale.
- [DRL Methodology](docs/DRL_METHODOLOGY.md): MDP formalization, state vector (64 dims), action masking, and reward formulation.
- [DRL Data Provenance](docs/DRL_DATA_PROVENANCE.md): Complete audit of raw datasets, matching pipeline, and 7-tier provenance taxonomy.
- [DRL Experiments](docs/DRL_EXPERIMENTS.md): Detailed comparative benchmarks across P1–P7 personas.
- [DRL Limitations](docs/DRL_LIMITATIONS.md): Transparent scientific boundaries and reasons for Mode B simulator selection.
- [DRL Runbook](docs/DRL_RUNBOOK.md): Complete step-by-step reproduction commands.
