# AuraTour: Data and Assumption Audit

> **Document Type:** Scientific & Engineering Research Audit  
> **System:** AuraTour (Sustainable & Crowd-Aware Tourism Recommender)  
> **Scope:** Rajasthan, India (45 Curated Tourist Destinations)  
> **Status:** Audited & Verified  

---

## 1. Executive Summary

This document presents a rigorous research audit of all datasets, external benchmarks, mathematical assumptions, and empirical heuristics used in AuraTour. The objective is to uphold scientific transparency, eliminate unwarranted claims of data precision, and clarify the exact boundary between **observed measurements**, **sourced factors**, **calculated values**, **engineering estimates**, and **heuristics**.

---

## 2. Dataset Provenance and Specifications

The table below catalogs every data source currently ingested or referenced in the AuraTour pipeline.

| Dataset / Source | Provider / Origin | Year | Geographic Scope | Licence | Raw Units | Ingested Features | Data Classification |
|---|---|---|---|---|---|---|---|
| **Attraction Coordinates** | OpenStreetMap (OSM) via Overpass API & Wikidata | 2023–2024 | Rajasthan (21 cities, 15 districts) | ODbL / CC0 | Decimal degrees (WGS84) | `latitude`, `longitude`, `name`, `city`, `district` | **Observed** |
| **Attraction Categories** | Curated domain taxonomy | 2024 | Rajasthan | Open (Project internal) | Categorical string tags | `categories` (10 categories: history, architecture, culture, nature, wildlife, religion, adventure, relaxation, shopping, food) | **Curated** |
| **Heritage Status** | Archaeological Survey of India (ASI) & UNESCO World Heritage | 2023 | Rajasthan | Public Domain / Official records | Text designation | `heritage_status` (UNESCO World Heritage, ASI Protected, or Unlisted) | **Observed** |
| **Annual Visitor Volumes** | Ministry of Tourism India / State Tourism Compendiums | 2023 | Rajasthan (Subset of 9 monuments) | Official reports / Public disclosures | Annual visitor counts (visitors/year) | `annual_visitors`, `visitor_data_source`, `visitor_data_year` | **Estimated / Sourced** (9 destinations); **Imputed Median Proxy** (36 destinations) |
| **Transport Emission Factors** | World Resources Institute (WRI) India / India GHG Program | 2023–2024 | National Standard (India) | Research publication / Public standard | Grams $\text{CO}_2\text{e}$ per passenger-km ($\text{g CO}_2\text{e}/\text{pkm}$) | Train (17.0), Bus (40.0), Flight (130.0), Private Car (150.0) | **Sourced Standard** |
| **Regional Seasonality Benchmarks** | IMD Historical Normals & Open-Meteo Historical Archive | 2010–2023 | Rajasthan State Norms | Public Open Data | Monthly index ($[0, 1]$), Temperature ($^\circ\text{C}$), Rainfall ($\text{mm}$) | `seasonal_demand_index`, `avg_max_temp_c`, `avg_min_temp_c`, `rainfall_mm` | **Observed Normals + Heuristic Demand Index** |
| **Travel Speed & Detour Factors** | Empirical road network detour benchmarks | 2024 | India Highway & Railway Network | Empirical engineering heuristic | Speed ($\text{km/h}$), Detour factor (dimensionless) | Train ($60\text{ km/h}$), Bus ($50\text{ km/h}$), Car ($60\text{ km/h}$ inter-city, $30\text{ km/h}$ intra-city), Flight ($500\text{ km/h} + 2.0\text{h}$ overhead), Road detour factor ($1.30\times$) | **Engineering Heuristic** |

---

## 3. Strict Classification of Pipeline Values

To ensure research integrity, every variable computed or displayed in AuraTour is classified under one of six epistemic tiers:

```
[ Tier 1: OBSERVED ]    ──> Exact real-world coordinates, names, administrative boundaries, UNESCO records
[ Tier 2: SOURCED ]      ──> Published academic or institutional benchmark values (WRI emission factors)
[ Tier 3: CALCULATED ]   ──> Closed-form mathematical derivations (Haversine formula, Gini coefficient)
[ Tier 4: ESTIMATED ]    ──> Engineering models based on observed inputs (detour-adjusted road distance)
[ Tier 5: HEURISTIC ]    ──> Domain-expert rule-based approximations (monthly demand index, visit duration)
[ Tier 6: PROXY/IMPUTED] ──> Default fallback values when empirical data is absent (0.5 score, median visitors)
```

### Detailed Feature Breakdown

| Feature Name | Primary Code Location | Classification | Epistemic Justification & Known Limitations |
|---|---|---|---|
| `latitude`, `longitude` | `curated_attractions.py` | **Observed** | Verified coordinates matching physical monument entry gates via OSM/Wikidata. Accuracy within $\pm 50$ meters. |
| `haversine_distance_km` | `scoring.py:16` | **Calculated** | Exact spherical trigonometric great-circle distance assuming Earth radius $R = 6,371.0\text{ km}$. |
| `road_distance_km` | `builder.py:25` | **Estimated** | Multiplies great-circle distance by a regional detour factor of $1.30$. Accounts for Rajasthan terrain winding; is not a verified turn-by-turn road network graph. |
| `transport_emissions_kg` | `scoring.py:59` | **Calculated** | Evaluated as $\frac{\text{distance\_km} \times \text{EF}_{\text{mode}}}{1000}$. Assumes standard fleet-average vehicle occupancy (WRI India standards). |
| `annual_visitors` | `curated_attractions.py` | **Estimated / Sourced** (9 items) <br> **Proxy / Imputed** (36 items) | Real ASI/Ministry statistics exist only for 9 flagship monuments (e.g. Amber Fort 5.0M, Hawa Mahal 4.5M). For unlisted sites, a median proxy ($300,000$ visitors) is imputed for Gini evaluation, while popularity scoring assigns neutral default $0.5$. |
| `popularity_score` | `scoring.py:201` | **Heuristic** | Uses an inverted bell-curve on log-transformed visitor volume ($1 - |2\hat{r} - 1|$) to penalize overtourism at the top and infrastructural deficiency at the bottom. |
| `seasonality_score` | `scoring.py:257` | **Heuristic** | Inverts state-wide seasonal demand ($1.0 - \text{demand}$) with localized microclimate adjustments (Mount Abu summer relief, Jaisalmer summer penalty, wildlife monsoon closure). |
| `feasibility_score` | `scoring.py:275` | **Heuristic** | Piecewise linear decay based on transit duration ($>4\text{h}$, $>8\text{h}$, $>16\text{h}$) and budget tiers (low, medium, high). |
| `travel_hours` | `scoring.py:130`, `builder.py:175` | **Heuristic** | Assumes fixed average transit speeds (Train $60\text{ km/h}$, Bus $50\text{ km/h}$, Highway car $60\text{ km/h}$, City car $30\text{ km/h}$, Flight $500\text{ km/h} + 2\text{h}$ check-in). Excludes live traffic congestion, timetable schedules, and train delays. |
| `estimated_visit_duration` | `curated_attractions.py` | **Heuristic** | Guidebook standard duration for typical visitor inspection (ranging from $0.5\text{h}$ for Jal Mahal exterior to $3.0\text{h}$ for sprawling hill forts like Amber or Chittorgarh). |

---

## 4. Visitor Volumes and the Feasibility of Crowd Forecasting

### Audit Question
*Do the available visitor volumes support time-specific crowd forecasting, or only macro-level popularity analysis?*

### Audit Findings
1. **Absence of Time-Series Footfall Data:**  
   The project does **not** possess timestamped hourly, daily, or weekly visitor count records. The dataset contains only static annual approximations for 9 major sites.
2. **Defensible Application:**  
   The annual visitor metrics genuinely support **macro-level popularity ranking** and **overtourism dispersion** (channeling demand away from saturated 5-million-visitor flagship monuments toward high-quality, lesser-visited alternatives).
3. **Forecasting Infeasibility:**  
   Without chronological turnstile sensor data, any algorithmic time-series crowd prediction model (e.g., ARIMA, Prophet, LSTM) would be completely synthetic and scientifically fraudulent.
4. **Methodological Recommendation:**  
   AuraTour explicitly rejects pseudo-forecasting. The system models temporal pressure transparently via the **Seasonal Demand Index** (macro-temporal proxy) and destination popularity tiers, openly documenting this limitation.

---

## 5. Distance and Route Routing Audit

### Audit Question
*What is the accuracy of the itinerary builder's routing distances and travel time calculations?*

### Audit Findings
1. **Straight-Line vs Road Distance:**  
   - Direct great-circle calculation (`haversine_distance_km`) underestimates true driving distances by $20\%$ to $35\%$ depending on mountain passes (Aravalli Range) and desert detours.
   - The $1.30\times$ detour factor (`estimate_road_distance_km`) aligns well with empirical highway samples (e.g., Delhi to Jaipur: great circle $\approx 238\text{ km}$, road estimate $= 309.4\text{ km}$, actual NH48 highway driving distance $\approx 280\text{–}310\text{ km}$).
2. **TSP Solver:**  
   - Uses Nearest-Neighbor construction followed by 2-opt local search optimization (`builder.py:85`).
   - For itineraries of 4 to 15 stops, 2-opt provably eliminates crossing edges, producing an efficient Euclidean traveling salesperson sequence.
3. **Constraints and Realism:**  
   - Maximum daily budget: $9.0\text{ hours}$ (e.g. 09:00 to 18:00).
   - Transit duration between stops is accumulated with site visit duration. If the next leg overflows $9.0\text{ hours}$, the trip progression shifts to Day 2, Day 3, etc.
   - Operating hours and multi-modal live timetables are not connected to real-time APIs; this is explicitly flagged as a heuristic model in user-facing warnings.

---

## 6. Audit of Metric Discrepancies and Code Corrections

During this research integrity audit, four specific mathematical and data implementation issues were identified and resolved:

### Issue 1: Zero Emissions Reported for Baseline (C1)
- **Diagnosis:** In `engine.py:recommend_baseline`, `estimated_emissions_kg` was originally initialized to `None`. When `compute_total_emissions` was evaluated on C1, `sum(None or 0.0)` produced `0.0 kg`, misrepresenting baseline emissions as zero.
- **Resolution:** `recommend_baseline` was updated to accept `origin_city` and compute true post-hoc transit emissions for the top-10 items selected under pure preference ranking. C1 now accurately reports baseline emissions ($203.32\text{ kg CO}_2\text{e}$ average).

### Issue 2: Rank Invariance between C3 and C4
- **Diagnosis:** Regional seasonality was originally implemented as a uniform statewide demand scalar applied identically to all attractions. In C3 (weights 0.5/0.25/0.25) vs C4 (weights 0.4/0.2/0.2/0.2), adding a uniform constant to all items preserved identical relative score differences, yielding $100\%$ identical rankings.
- **Resolution:** Seasonality scoring (`compute_seasonality_score`) was enhanced with destination microclimate context (Mount Abu summer relief, Jaisalmer summer heat penalty, wildlife monsoon breeding closures), giving C4 genuine incremental value.

### Issue 3: Structurally Guaranteed CMR@10 = 100%
- **Diagnosis:** CMR@10 was reported as $100\%$ across all configurations. Inspection revealed that evaluation personas specify 3–4 categories that intersect with between $35$ and $45$ of the $45$ attractions in the catalog. Since preference score assigns $0.0$ to items with zero category overlap, top-10 recommendations almost never include non-matching items.
- **Resolution:** Explicitly documented in `docs/METRIC_DEFINITIONS.md`. CMR@10 measures interest presence (at least 1 category match), acting as a sanity-check boundary rather than a discriminating ranking metric. Average continuous preference score (`avg_preference_score`) is reported alongside CMR@10 to measure true preference retention.

### Issue 4: Popularity Gini Interpretation
- **Diagnosis:** The reduction of Gini from $0.474$ to $0.144$ was ambiguous.
- **Resolution:** Clarified that this Gini metric measures **intra-list visitor volume dispersion** among the 10 recommended attractions. To complement this, **Catalog Coverage** ($\%$ of unique catalog attractions exposed across personas) was implemented and added to the benchmark suite.
