# AuraTour: Deep Reinforcement Learning (DRL) Integration Plan

> **Document Type:** Research Architecture Audit & Implementation Plan  
> **Topic:** Adapting Dalla Vecchia et al. (2024) DRL Sequential Recommendation to Rajasthan Heritage Tourism  
> **Status:** Phase 1 Complete (Audited, Datasets Explored, Architecture Specified)  

---

## 1. Executive Context & Research Scope

This document details the architectural plan to integrate Deep Reinforcement Learning (DRL) into AuraTour, inspired by the paper:
> **"Promoting sustainable tourism by recommending sequences of attractions with deep reinforcement learning"**  
> Anna Dalla Vecchia, Sara Migliorini, Elisa Quintarelli, Mauro Gambini, Alberto Belussi. *Information Technology & Tourism*, 2024.  
> [Springer Article](https://link.springer.com/article/10.1007/s40558-024-00288-x) | [GitHub: smigliorini/itinerary-drl](https://github.com/smigliorini/itinerary-drl)

### 1.1 Adaptation Mandate
Rather than naively copying the Verona-specific implementation (which relied on synthetic crowd forecasters and city-scale foot travel), we adapt the sequential decision-making framework to the geographic realities and data availability of **Rajasthan, India**. 

This adaptation addresses:
1. **Regional Inter-City & Intra-City Scale:** Managing multi-day itineraries spanning hundreds of kilometers across desert, plain, and hill terrains.
2. **Authentic Indian Tourism Datasets:** Leveraging recently provided authentic Indian tourism and transport datasets.
3. **Transparent Scientific Integrity:** Explicitly acknowledging data limitations, using simulator-based training (Mode B) because authentic sequential tourist trajectories are not available in public Indian repositories.

---

## 2. Comprehensive Audit of Existing Codebase

### 2.1 Architecture and Data Flow
```
User Travel Request (Interests, Origin City, Month, Duration, Budget, λ)
                                  │
                                  ▼
                [ Candidate Pre-Filtering & Loading ]
                    (45 Curated Attractions)
                                  │
                                  ▼
      ┌───────────────────────────┴───────────────────────────┐
      ▼                                                       ▼
[ Traditional Scoring Engine ]                          [ DRL Sequence Planner ]
(C1 Baseline through C5 Multi-Criteria)                 (Markov Decision Process Agent)
      │                                                       │
      ▼                                                       ▼
Top-k Ranked Attraction List                            Ordered Sequential Itinerary
      │                                                       │
      ▼                                                       ▼
[ Itinerary Builder (2-Opt TSP) ]                             │
      └───────────────────────────┬───────────────────────────┘
                                  ▼
                     Day-by-Day Route Schedule
                (Transit Modes, Emissions, Fares, Pacing)
```

### 2.2 Existing Attraction Catalog (`curated_attractions.py`)
- **Size:** 45 curated cultural, architectural, wildlife, and natural attractions.
- **Coverage:** 21 unique cities across 15 administrative districts of Rajasthan.
- **Attributes:** Coordinates, city, district, interest tags, visit duration, entrance fees (INR), annual visitor estimates (9 ASI observed, 36 median-imputed proxies), and description.

### 2.3 Existing Recommendation Strategies (C1–C5)
- **C1 (Baseline):** Pure content-based category cosine similarity ($w_p = 1.0$).
- **C2 (Preference + Emissions):** Low-carbon transit optimization ($w_p = 0.5, w_e = 0.5$).
- **C3 (Pref + Emis + Crowding):** Overtourism avoidance via visitor count penalty ($w_p = 0.45, w_e = 0.25, w_c = 0.30$).
- **C4 (Pref + Emis + Crowding + Seasonality):** Microclimate and summer heat penalties.
- **C5 (Full Multi-Criteria Composite):** Complete balanced index ($w_p=0.45, w_e=0.20, w_c=0.15, w_s=0.10, w_f=0.10$).

### 2.4 Existing Itinerary Builder (`builder.py`)
- **Ordering:** Greedy Nearest-Neighbor heuristic initialized from the user's departure city.
- **Refinement:** 2-opt pairwise edge exchange local search to untangle crossing paths.
- **Daily Grouping:** Splits attractions into day buckets assuming 9:00 AM to 6:00 PM operational windows (max 9 hours/day including travel and visits).
- **Circuity Factor:** $1.30\times$ Haversine heuristic (empirically audited at 6.8% MAPE).

### 2.5 Test Status Baseline
- **Pytest Suite:** 77 passing tests across scoring, evaluation metrics, itinerary builder, extended validation, and privacy-preserving user study API.
- **OpenBLAS Safety:** Configured with single-thread limits (`conftest.py`, `app/__init__.py`) to prevent Windows memory allocation faults.

---

## 3. Audit of Newly Provided Datasets

### 3.1 Dataset 1: Indian Tourist Places Dataset (`kaggle_indian_tourist_places_dataset.zip`)
- **File:** `indian_tourist_places_dataset.csv` (3.38 MB uncompressed).
- **Scale:** 13,000 total visitor observations across 12 Indian states.
- **Rajasthan Records:** 1,053 records spanning 6 major Jaipur heritage sites:
  1. *Hawa Mahal*: 182 records, INR 30 entry fee, duration < 1h, rating 4.35
  2. *Nahargarh Fort*: 181 records, INR 40 entry fee, duration 4–6h, rating 4.37
  3. *Jantar Mantar*: 165 records, INR 150 entry fee, duration < 1h, rating 4.27
  4. *Jal Mahal*: 170 records, INR 50 entry fee, duration 2–4h, rating 4.20
  5. *City Palace Jaipur*: 172 records, duration 2–4h, rating 4.43
  6. *Amber Fort*: 183 records, duration 1–2h, rating 4.53
- **Features Extracted:** Authentic entry fees in INR, visit durations, crowd levels (`Low`, `Medium`, `High`), weather conditions, user ratings, and visitor travel types (`Family`, `Solo`, `Couple`, `Group`).
- **Critical Structural Finding:** Records represent **independent, non-sequential visit observations** rather than linked multi-stop tourist trajectories. There is no `user_id` or trajectory tracking across multiple monuments.

### 3.2 Dataset 2: Central Zone OpenStreetMap GeoPackage (`central-zone.gpkg`)
- **File:** `central-zone-261022-free.gpkg/central-zone.gpkg` (1.81 GB SQLite GeoPackage).
- **Coverage:** Bounding box $[74.22^\circ\text{ E}, 17.78^\circ\text{ N}]$ to $[84.58^\circ\text{ E}, 31.36^\circ\text{ N}]$, encompassing Central India (MP, Chhattisgarh, UP border, and Eastern Rajasthan).
- **Transport Features:** 1,875 railway stations, 184 bus stations, 702 bus stops, and 21,513 rail line segments (including the primary Howrah–Delhi and central rail corridors).
- **Utility:** Supplies authentic railway station locations and connectivity distances for rail transit modeling.

---

## 4. Methodological Decision: Mode B (Simulator-Based DRL)

The research prompt defines two possible training modes:
- **Mode A (Data-driven sequential learning):** Requires authentic, timestamped sequential tourist trajectories.
- **Mode B (Simulator-based Deep Reinforcement Learning):** Uses authentic attraction metadata, documented geographic coordinates, observed entrance fees, and realistic transit models within an episodic simulation environment.

### 4.1 Justification for Mode B
The audit confirms that **no open dataset contains individual multi-stop tourist trajectories for Rajasthan**. The Kaggle dataset provides authentic point-in-time observations at individual attractions, while ASI and Ministry of Tourism datasets provide annual monument aggregations.

Attempting Mode A would require fabricating fake tourist journey sequences, which would violate scientific integrity. Therefore, **Mode B is the only defensible and scientifically rigorous choice**. 

The simulator will:
1. Model the decision environment using authentic Rajasthan attraction locations, fees, visit durations, and visitor volumes.
2. Formulate sequential itinerary construction as a finite-horizon Markov Decision Process (MDP).
3. Explicitly label all training episodes as **simulated** in all documentation, reports, and UI dashboards.

---

## 5. DRL System Architecture & MDP Formulation

Following Dalla Vecchia et al. (2024), we model the sequential travel recommender as a finite-horizon MDP: $\mathcal{M} = \langle \mathcal{S}, \mathcal{A}, \mathcal{P}, \mathcal{R}, \gamma \rangle$.

### 5.1 State Space $\mathcal{S}$
A dense continuous/binary feature vector $s_t \in \mathbb{R}^{d}$ encoding:
1. **Current Location:** One-hot or coordinate embedding of the last visited attraction (or origin city at $t=0$).
2. **Visited Mask:** Binary vector $m \in \{0, 1\}^{N_{\text{att}}}$ preventing duplicate visits.
3. **Temporal Budget:** Remaining trip hours normalized: $\tau_{\text{rem}} / \tau_{\text{total}}$.
4. **Financial Budget:** Remaining budget normalized: $B_{\text{rem}} / B_{\text{total}}$.
5. **Day Context:** Current itinerary day $d / D_{\text{max}}$ and remaining hours in the active day.
6. **User Preferences:** Vector of category affinity scores for the 10 interest genres.
7. **Seasonality Context:** Normalized travel month indicator (1–12).

### 5.2 Action Space $\mathcal{A}$
- **Action $a \in \{0, \dots, N_{\text{att}}-1\}$:** Recommends attraction $a$ as the next stop.
- **Action $a = N_{\text{att}}$ (Stop Action):** Explicitly concludes the itinerary.
- **Action Masking:** Actions that violate hard constraints (exceeding total budget, exceeding maximum trip days, or revisiting an attraction) are strictly masked by setting their logits / Q-values to $-\infty$.

### 5.3 Multi-Objective Reward Function $\mathcal{R}(s_t, a_t)$
Inspired by Dalla Vecchia et al. and tuned for user requirements:
$$R_t = w_p \cdot P(a_t) + w_v \cdot V(a_t) - w_t \cdot T(s_t, a_t) - w_c \cdot C(a_t) - w_b \cdot B(s_t, a_t) - w_e \cdot E(s_t, a_t)$$

Where:
- $P(a_t) \in [0, 1]$: User interest category alignment.
- $V(a_t) \in [0, 1]$: Marginal category diversity contribution.
- $T(s_t, a_t) \in [0, 1]$: Normalized travel time penalty.
- $C(a_t) \in [0, 1]$: Historical crowd / popularity pressure penalty.
- $B(s_t, a_t) \in [0, 1]$: Normalized financial cost penalty (transit fare + entry fee).
- $E(s_t, a_t) \in [0, 1]$: Normalized transit carbon emissions penalty.

**Constraint Priority:** As mandated, **budget penalty $w_b$ is strictly higher than emissions penalty $w_e$** ($w_b = 0.20$ vs. $w_e = 0.08$), and hard feasibility limits are enforced via action masking.

### 5.4 Neural Architecture: Lightweight Deep Q-Network (DQN)
- **Framework:** Lightweight, dependency-free NumPy/SciPy neural implementation (or PyTorch CPU if compatible), avoiding heavy multi-gigabyte GPU framework bloat.
- **Architecture:** Fully connected network with input dimension $d$, two hidden dense layers (128 units, 64 units) with ReLU activations, and linear output layer of size $|\mathcal{A}| = 46$ (45 attractions + 1 stop action).
- **Optimization:** Experience replay buffer ($10,000$ transitions), target Q-network with periodic hard/soft updates ($\tau = 0.01$), Adam optimizer, and $\epsilon$-greedy exploration with exponential decay.

---

## 6. Implementation Workflow & Milestones

1. **Phase 2 — Data Readiness:**
   - Create `backend/app/data_ingestion/monument_matcher.py`: Clean Kaggle dataset, match monuments to the 45 catalog attractions, and export `backend/data/processed/matched_monument_attributes.csv`.
2. **Phase 3 — RL Environment:**
   - Create `backend/app/rl/environment.py`, `state.py`, and `reward.py`.
   - Write comprehensive environment unit tests in `backend/app/tests/test_rl_env.py` (state transitions, action masking, budget/time termination).
3. **Phase 4 — Deep RL Agent:**
   - Create `backend/app/rl/agent.py` and `backend/scripts/train_drl.py`.
   - Implement training loop with seed control, loss logging, and checkpoint serialization (`backend/data/models/drl_itinerary_agent.json`).
4. **Phase 5 — Baseline Comparison & Evaluation:**
   - Create `backend/app/rl/evaluation.py` and run comparative benchmarking against C1 Baseline and Greedy TSP + 2-opt across the 7 evaluation personas.
5. **Phase 6 & 7 — API & Frontend Integration:**
   - Expose DRL in `backend/app/api/main.py` (`POST /api/itinerary` with `strategy="drl"`).
   - Update `ItineraryView.jsx` and `ResearchDashboard.jsx` to let users toggle DRL and view research metrics with provenance disclosures.
6. **Phase 8 — Regression Testing & Research Deliverables:**
   - Run the 77-test regression suite + new RL tests.
   - Author `DRL_METHODOLOGY.md`, `DRL_DATA_PROVENANCE.md`, `DRL_EXPERIMENTS.md`, `DRL_LIMITATIONS.md`, and `DRL_RUNBOOK.md`.
