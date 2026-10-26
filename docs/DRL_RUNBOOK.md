# Reproducible Runbook: AuraTour Deep Reinforcement Learning Pipeline

This runbook provides the exact, end-to-end command-line instructions required to reproduce all data ingestion, monument matching, RL agent training, empirical benchmarking, automated testing, and web application deployment.

---

## 1. Prerequisites and Environment Setup

### System Requirements
- OS: Windows, macOS, or Linux
- Python: 3.10+ (tested on Python 3.11.9)
- Node.js: 18+ (tested with Vite 8.3)
- Pure-NumPy implementation: **Zero GPU or PyTorch wheel installations required**.

### Thread Pool Configuration (Crucial on Windows)
Set single-threaded linear algebra execution to prevent OpenBLAS thread allocation contention:
```powershell
# PowerShell (Windows)
$env:OPENBLAS_NUM_THREADS = "1"
$env:OMP_NUM_THREADS = "1"
$env:MKL_NUM_THREADS = "1"
```

```bash
# Bash (Linux/macOS)
export OPENBLAS_NUM_THREADS=1
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
```

---

## 2. Phase 1: Data Ingestion and Monument Matching

Processes raw Kaggle tourist places records (`kaggle_indian_tourist_places_dataset.zip`) and OpenStreetMap railway infrastructure (`central-zone.gpkg`):

```bash
cd backend

# Execute monument matching, fuzzy alignment, and dataset normalization
python app/data_ingestion/monument_matcher.py
```

### Generated Artifacts
- `backend/data/processed/monument_matching_registry.csv` (74 places audited)
- `backend/data/processed/cleaned_tourist_places_rajasthan.csv` (1,225 Rajasthan records)
- `backend/data/processed/central_zone_stations.csv` (2,563 stations & bus hubs)
- `backend/data/processed/monument_matching_report.json`

---

## 3. Phase 2: DRL Agent Training

Trains the Deep Q-Network agent across 500 simulated multi-constraint traveler episodes:

```bash
cd backend

# Train DRL Agent with default parameters (500 episodes, seed 42)
python scripts/train_drl.py --episodes 500 --seed 42 --batch-size 32 --lr 0.001
```

### Output Checkpoint & Curves
- Trained Model Checkpoint: `backend/data/models/drl_itinerary_agent.json`
- Training Curves JSON: `backend/data/results/drl_training_curves.json`
- Training Curves CSV: `backend/data/results/drl_training_curves.csv`

---

## 4. Phase 3: Empirical Benchmarking (DRL vs C1 & C5)

Executes comparative evaluation across standardized research personas (P1–P7):

```bash
cd backend

# Run benchmark evaluation
python scripts/run_drl_experiments.py
```

### Generated Experiment Artifacts
- Comparison Matrix CSV: `backend/data/results/drl_vs_baselines.csv`
- Full Experiment JSON: `backend/data/results/drl_experiment_results.json`

---

## 5. Phase 4: Automated Testing Suite

Executes the complete 95-test suite (77 original tests + 18 new DRL & data ingestion tests):

```bash
cd backend

# Run full pytest suite
python -m pytest app/tests/ -v
```

Expected Output:
```
============================= 95 passed in 1.31s ==============================
```

---

## 6. Phase 5: Running the Web Application

### Backend API Server (FastAPI)
```bash
cd backend
python -m uvicorn app.api.main:app --host 0.0.0.0 --port 8000 --reload
```
API Documentation available at: `http://localhost:8000/docs`

### Frontend Application (React + Vite)
```bash
cd frontend
npm run dev
```
Application accessible at: `http://localhost:5173`

To build production bundle:
```bash
cd frontend
npm run build
```
