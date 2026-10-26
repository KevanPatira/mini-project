# AuraTour: Experimental Methodology and Ablation Study

> **Document Type:** Research Experiment Protocol & Benchmark Results  
> **System:** AuraTour Sustainable & Crowd-Aware Tourism Recommender  
> **Status:** Executed & Reproducible  

---

## 1. Experimental Design & Objectives

The primary research objective is to evaluate whether integrating environmental emissions, popularity dispersion, and seasonal microclimate indicators into tourism recommendations can meaningfully reduce negative externalities without causing severe degradation of user preference satisfaction.

The experimental pipeline is fully automated and deterministic, executed by `backend/app/evaluation/runner.py`.

---

## 2. Experimental Configurations (C1 through C5)

All configurations operate on the identical set of 45 curated destinations across 21 cities in Rajasthan.

| Configuration ID | Designation | Core Objective | Mathematical Weight Vector $(w_p, w_e, w_o, w_s, w_f)$ |
|---|---|---|---|
| **C1** | **Baseline (Unconstrained)** | Pure preference alignment (traditional recommender) | $(1.0, 0.0, 0.0, 0.0, 0.0)$ |
| **C2** | **Carbon-Aware Recommender** | Preference + Transit Emission minimization | $(0.6, 0.4, 0.0, 0.0, 0.0)$ |
| **C3** | **Overtourism-Aware Recommender** | Adds moderate-popularity balancing | $(0.5, 0.25, 0.25, 0.0, 0.0)$ |
| **C4** | **Temporally-Aware Recommender** | Adds microclimate and seasonal demand optimization | $(0.4, 0.2, 0.2, 0.2, 0.0)$ |
| **C5** | **Full Multi-Criteria Recommender** | Full adaptive balance: Preference, Emissions, Popularity, Seasonality, Feasibility | Dynamic weights adjusted via priority $\lambda \in [0, 1]$ |

---

## 3. Standard Evaluation Personas (P1 through P7)

To ensure diverse geographic origins, budget constraints, travel seasons, and interest profiles, 7 standard personas are simulated:

| ID | Persona Archetype | Origin City | Interest Categories | Duration | Month | Sustainability Priority ($\lambda$) |
|---|---|---|---|---|---|---|
| **P1** | Heritage Explorer | Delhi | History, Architecture, Culture | 5 days | November (Peak) | 0.50 |
| **P2** | Nature Enthusiast | Mumbai | Nature, Wildlife, Adventure | 7 days | December (Peak) | 0.80 |
| **P3** | Budget Backpacker | Bangalore | History, Culture, Nature, Food | 10 days | January (Peak) | 0.20 |
| **P4** | Cultural Foodie | Kolkata | Food, Culture, Shopping, History | 4 days | October (Shoulder) | 0.50 |
| **P5** | Eco-Conscious Traveller | Chennai | Nature, History, Culture | 6 days | February (Shoulder) | 0.95 |
| **P6** | Weekend Tripper | Jaipur | History, Culture, Relaxation | 2 days | March (Moderate) | 0.30 |
| **P7** | Family Vacationer | Delhi | Nature, History, Wildlife, Culture | 5 days | December (Peak) | 0.50 |

---

## 4. Empirical Ablation Study Results

The table below presents the verified aggregate results produced across all 7 personas and 5 configurations, saved in `data/results/ablation_summary.csv`:

| Configuration | Total Emissions ($\text{kg CO}_2\text{e}$) | $\Delta$ Emissions vs C1 ($\%$) | Preference Score ($\bar{P}@10$) | Preference Retention ($\%$) | Intra-list Gini ($G$) | Category Diversity | Geographic Spread ($\text{km}$) | Catalog Coverage |
|---|---|---|---|---|---|---|---|---|
| **C1 Baseline** | 203.32 | $0.00\%$ | 0.685 | $100.00\%$ | 0.474 | 5.71 | 252.31 | $62.2\%$ |
| **C2 + Emissions** | 179.14 | **$-11.89\%$** | 0.636 | $92.85\%$ | 0.468 | 5.57 | 162.47 | **$73.3\%$** |
| **C3 + Popularity** | 185.75 | $-8.64\%$ | 0.655 | $95.62\%$ | **0.144** ($-69.6\%$) | 5.57 | 196.52 | $60.0\%$ |
| **C4 + Seasonality** | 184.51 | $-9.25\%$ | 0.649 | $94.74\%$ | 0.144 | 5.71 | 192.05 | $60.0\%$ |
| **C5 Full System** | 185.56 | $-8.74\%$ | 0.638 | $93.14\%$ | 0.144 | **5.86** | 191.00 | $62.2\%$ |

---

## 5. Key Scientific Insights

### 1. The Carbon-Preference Trade-off (C1 vs C2)
Introducing transit emissions scoring in C2 achieves an immediate **$11.89\%$ reduction in transit emissions** ($179.14\text{ kg}$ vs $203.32\text{ kg}$). Remarkably, this carbon reduction incurs only a modest $7.15\%$ drop in preference relevance ($0.636$ vs $0.685$). Furthermore, because users traveling from different origin cities are matched with closer destinations, **catalog coverage increases from $62.2\%$ to $73.3\%$**.

### 2. Overtourism Dispersion and Visitor Gini (C2 vs C3)
In C2, the intra-list visitor volume Gini remains high ($0.468$) because emissions alone do not prevent mega-monuments from monopolizing recommendations. Adding moderate-popularity scoring in C3 drives the intra-list Gini coefficient down to **$0.144$ (a $69.6\%$ reduction)**, actively shifting tourists toward high-potential secondary heritage sites.

### 3. Incremental Seasonal Differentiation (C3 vs C4)
By factoring in destination-specific microclimates (summer penalties for desert forts, summer relief for Mount Abu, and breeding season closures for wildlife sanctuaries), C4 differentiates itself from C3 by elevating seasonally appropriate sites, improving category diversity to $5.71$.

### 4. Holism and Diversity in C5
C5 incorporates travel feasibility (budget and duration constraints) and dynamic priority scaling. It achieves the **highest overall category diversity ($5.857$ distinct categories)** while maintaining balanced geographic spread ($191.0\text{ km}$ across $6.0$ unique districts).

---

## 6. Sensitivity Analysis Across $\lambda \in [0.0, 1.0]$

The parameter $\lambda$ controls user sustainability priority. Testing on Persona P1 across 11 discrete steps demonstrates smooth, monotonic Pareto trade-offs:

```
Lambda (λ)   Emissions (kg)   Preference Score   Spread (km)   Jaccard Overlap
-----------------------------------------------------------------------------
0.0          85.54            1.0000             261.09        1.0000
0.2          85.54            1.0000             261.09        1.0000
0.4          79.76            0.9800             244.15        0.8182
0.6          64.46            0.9200             210.82        0.5385
0.8          58.83            0.8800             168.34        0.4286
1.0          53.97            0.7867             114.37        0.3333
```

- At $\lambda = 0.0$, the system behaves as an unconstrained baseline ($\text{TEE} = 85.54\text{ kg}$, $100\%$ preference match).
- As $\lambda \to 1.0$, emissions fall monotonically by **$36.9\%$** down to $53.97\text{ kg}$, while geographic spread tightens from $261.09\text{ km}$ to $114.37\text{ km}$.
- Even at maximum sustainability ($\lambda = 1.0$), preference retention remains at $78.67\%$, demonstrating that the recommendation engine does not collapse into irrelevant suggestions.

---

## 7. How to Reproduce

Execute the test matrix and regenerate all summary CSVs and JSON files via terminal:

```bash
cd backend
python -c "from app.evaluation.runner import ExperimentRunner; ExperimentRunner().run_all_experiments()"
pytest app/tests/ -v
```
All outputs will be deterministically populated in `backend/data/results/`.
