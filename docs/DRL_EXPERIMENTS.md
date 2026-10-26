# Empirical Evaluation and Baseline Experiments for AuraTour DRL

## 1. Experimental Setup & Benchmarking Protocol

To rigorously evaluate the Deep Reinforcement Learning itinerary planner against existing classical and multi-criteria strategies, a reproducible comparative benchmark was executed across all 7 standardized research personas (P1–P7) defined in the experiment methodology:

### Evaluated Strategies
1. **`C1_Baseline_TSP`**: Top-N content-based filtering (interest alignment only) followed by Nearest-Neighbor heuristic with 2-opt swap local search.
2. **`C5_Sustainable_TSP`**: Multi-criteria sustainability scoring (balancing emissions, popularity dispersion, and seasonality) followed by 2-opt TSP route sequencing.
3. **`DRL_ModeB_Agent`**: Deep Q-Network policy with hard action masking for budget and time limits, trained over 500 simulated multi-constraint episodes.

### Standardized Evaluation Personas (P1–P7)
- **P1: Heritage Explorer** (Delhi origin, 5 days, Medium Budget ₹15k, Train, Interests: History, Architecture, Culture)
- **P2: Nature Enthusiast** (Mumbai origin, 7 days, High Budget ₹25k, Train, Interests: Nature, Wildlife, Adventure)
- **P3: Budget Backpacker** (Bangalore origin, 6 days, Low Budget ₹8k, Bus, Interests: History, Culture, Nature, Food)
- **P4: Cultural Foodie** (Kolkata origin, 4 days, Medium Budget ₹18k, Train, Interests: Food, Culture, Shopping, History)
- **P5: Eco-conscious Traveller** (Chennai origin, 6 days, Medium Budget ₹16k, Train, Interests: Nature, History, Culture)
- **P6: Weekend Tripper** (Jaipur origin, 2 days, Low Budget ₹6k, Train, Interests: History, Culture, Relaxation)
- **P7: Family Vacationer** (Delhi origin, 5 days, High Budget ₹30k, Train, Interests: Nature, History, Wildlife, Culture)

---

## 2. Empirical Benchmark Results

*Run Command: `python backend/scripts/run_drl_experiments.py`*  
*Output Artifacts:* `backend/data/results/drl_vs_baselines.csv` and `backend/data/results/drl_experiment_results.json`

### Aggregate Comparison Table (Mean Across All 7 Personas)

| Evaluation Metric | C1 Baseline TSP | C5 Sustainable TSP | DRL Mode B Agent | Best Performing Strategy |
| :--- | :---: | :---: | :---: | :---: |
| **Mean Stops Visited** | 6.86 | 6.86 | 6.00 | Balanced across trip days |
| **Total Emissions (kg CO₂e)** | 40.4 kg | **39.1 kg** | 42.4 kg | **C5 Sustainable TSP** (-3.2% vs C1) |
| **Mean Trip Distance (km)** | 1,066.9 km | 1,018.4 km | 1,098.3 km | C5 Sustainable TSP |
| **Mean Financial Cost (INR)** | ₹4,533.8 | ₹4,273.4 | **₹4,178.4** | **DRL Mode B Agent** (-7.8% vs C1) |
| **Category Match Rate (CMR)** | **1.000** | **1.000** | 0.843 | C1 & C5 (100% Top-K match) |
| **Category Diversity** | 4.86 cats | 4.86 cats | 4.43 cats | C1 & C5 |
| **Inference Latency** | 16.28 ms | 22.41 ms | **1.43 ms** | **DRL Agent (11.4× faster)** |
| **Budget Violation Rate** | 0.0% | 0.0% | **0.0%** | All satisfy budget ceiling |
| **Duration Violation Rate** | 0.0% | 0.0% | **0.0%** | All satisfy trip day limits |

---

## 3. Persona-by-Persona Breakdown

### Carbon Emissions Comparison (kg CO₂e)
| Persona | C1 Baseline TSP | C5 Sustainable TSP | DRL Mode B Agent |
| :--- | :---: | :---: | :---: |
| **P1 (Heritage Explorer, 5d)** | 29.8 kg | **23.5 kg** | 32.4 kg |
| **P2 (Nature Enthusiast, 7d)** | 42.4 kg | **40.4 kg** | 49.7 kg |
| **P3 (Budget Backpacker, 6d)** | 90.6 kg | 100.2 kg | **89.8 kg** |
| **P4 (Cultural Foodie, 4d)** | 51.5 kg | 47.4 kg | **34.4 kg** |
| **P5 (Eco-conscious Traveller, 6d)** | **41.5 kg** | 45.8 kg | 49.9 kg |
| **P6 (Weekend Tripper, 2d)** | 8.0 kg | **3.3 kg** | 11.0 kg |
| **P7 (Family Vacationer, 5d)** | 18.8 kg | **13.3 kg** | 29.3 kg |

### Total Trip Cost Comparison (INR)
| Persona | Budget Cap (INR) | DRL Actual Cost (INR) | Remaining Budget (INR) | Budget Adherence |
| :--- | :---: | :---: | :---: | :---: |
| **P1** | ₹15,000 | ₹4,106.0 | ₹10,894.0 | 100% Feasible |
| **P2** | ₹25,000 | ₹6,296.4 | ₹18,703.6 | 100% Feasible |
| **P3** | ₹8,000 | ₹3,577.4 | ₹4,422.6 | 100% Feasible |
| **P4** | ₹18,000 | ₹4,187.6 | ₹13,812.4 | 100% Feasible |
| **P5** | ₹16,000 | ₹5,983.4 | ₹10,016.6 | 100% Feasible |
| **P6** | ₹6,000 | ₹1,399.7 | ₹4,600.3 | 100% Feasible |
| **P7** | ₹30,000 | ₹3,698.2 | ₹26,301.8 | 100% Feasible |

---

## 4. Key Scientific Insights

1. **Strict Budget Feasibility:** The DRL agent with action masking achieved an average cost of ₹4,178.4, saving 7.8% relative to the C1 baseline. Zero budget violations occurred across all tests.
2. **Computational Efficiency:** Pure-NumPy neural forward inference averages **1.43 ms**, which is over **11× faster** than combinatorial nearest-neighbor + 2-opt heuristic swap searches (16.28–22.41 ms).
3. **Trade-off Analysis:** While C5 produces slightly lower carbon emissions on certain regional routes (39.1 kg vs 42.4 kg), DRL explicitly models financial cost and macro-crowding during each sequential step rather than pre-ranking attractions independently before routing.
