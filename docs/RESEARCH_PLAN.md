# Research Plan

## 1. Problem Statement

Tourism recommender systems typically optimise for user preference match and destination popularity, reinforcing overtourism patterns. This project investigates whether integrating sustainability indicators — transportation emissions, popularity-based crowding pressure, and seasonal demand — into recommendation ranking can produce recommendations that balance personal relevance with environmental and social sustainability, while remaining transparent about the trade-offs involved.

## 2. Research Questions

**RQ1:** How does incorporating transportation CO₂e emissions into tourism recommendations affect the set of recommended destinations compared to a preference-only baseline?

**RQ2:** What is the effect of adding popularity-based overtourism pressure and seasonal demand indicators on recommendation diversity and ranking stability?

**RQ3:** How sensitive are the multi-criteria recommendations to changes in component weights, and can users meaningfully control the sustainability–relevance trade-off?

**RQ4 (optional):** Can historical visitor patterns or contextual features (weather, holidays) be used to provide temporal crowd-level estimates that improve recommendation quality?

## 3. Hypotheses

**H1:** A multi-criteria ranking model that penalises high-emission transport options will shift recommendations toward destinations accessible by lower-emission transport modes, at some cost to preference relevance.

**H2:** Incorporating popularity and seasonal-demand indicators will increase recommendation diversity (measured by category and geographic spread) compared to a preference-only baseline.

**H3:** The sustainability–relevance trade-off is controllable: users who set higher sustainability weights will receive measurably different recommendations than users who prioritise preferences.

## 4. Objectives

1. Curate a dataset of tourist attractions in Rajasthan with category labels, coordinates, and available metadata.
2. Compute transportation emission estimates for major origin–destination pairs using documented emission factors.
3. Derive popularity indicators from available OSM and review data.
4. Collect seasonal tourism demand data from official government statistics.
5. Build a preference-only baseline recommender.
6. Build a multi-criteria recommender incorporating sustainability scores.
7. Compare both systems using appropriate evaluation metrics.
8. Deliver a web application demonstrating the system.

## 5. Scope

### In scope
- Tourist attractions within Rajasthan, India
- Major origin cities within India (Delhi, Mumbai, Bangalore, etc.) for transport emissions
- Transportation modes: train, bus, car, flight (where data available)
- Sustainability components: emissions, popularity, seasonality
- Deterministic template-based explanations
- Scenario-based evaluation (no live user study in initial phase)

### Out of scope
- Real-time crowd monitoring or live data feeds
- Hotel booking or accommodation recommendations
- Multi-country destinations
- LLM-based natural language generation (optional future extension)
- User accounts and persistent preference storage

## 6. Assumptions

1. OpenStreetMap has adequate POI coverage for major Rajasthan tourist attractions.
2. India-specific CO₂ emission factors from WRI India / IEA are representative averages.
3. Ministry of Tourism annual statistics provide a reasonable proxy for relative seasonal demand.
4. Attraction categories derived from OSM tags can be mapped to user interest categories.
5. Straight-line or road-network distances are adequate for emission estimation when route APIs are rate-limited.

## 7. Limitations

1. No real user interaction data — evaluation is scenario-based.
2. Emission factors are national averages, not route-specific measurements.
3. Popularity indicators from OSM (review counts, ratings) are incomplete and biased toward tech-savvy travellers.
4. Monthly tourism statistics may only be available at state level, not per-attraction.
5. Opening hours and entry fees from OSM are often missing.
6. No real-time crowd data available for Indian attractions.

## 8. Evaluation Methodology

### 8.1 Experimental Configurations
| Config | Components |
|---|---|
| C1 | Preference-only baseline |
| C2 | Preference + Emissions |
| C3 | Preference + Emissions + Popularity |
| C4 | Preference + Emissions + Popularity + Seasonal demand |
| C5 | Full system with travel constraints (time, cost) |

### 8.2 Metrics
| Metric | Purpose |
|---|---|
| Category match rate | Proportion of recommendations matching user interest categories |
| Estimated route emissions (kg CO₂e) | Total emissions of recommended travel plans |
| Recommendation diversity | Number of distinct categories and geographic spread |
| Popularity distribution (Gini coefficient) | Whether recommendations concentrate on few popular sites |
| Travel time and cost estimates | Feasibility of recommended itineraries |
| Rank correlation (Kendall's τ) | Sensitivity of rankings to weight changes |
| Component contribution analysis | How each score component affects final ranking |

### 8.3 Scenarios
Define 5–10 user personas with distinct interest profiles (e.g., "history enthusiast from Delhi," "nature lover from Mumbai," "budget backpacker from Bangalore") and evaluate recommendations across all configurations.

### 8.4 Sensitivity Analysis
Vary sustainability weights from 0.0 to 1.0 in increments and measure:
- Rank position changes for top-K recommendations
- Total estimated emissions shift
- Diversity changes

## 9. Sustainability Scoring Framework

Reference: Banerjee et al. (2025) composite sustainability index.

### Approach
Compute a weighted multi-criteria score for each destination:

```
score(d) = w_pref × relevance(d) + w_emis × emission_score(d) + w_pop × popularity_score(d) + w_seas × seasonality_score(d) + w_feas × feasibility_score(d)
```

Where:
- All component scores are normalised to [0, 1]
- Higher score = better recommendation
- Emission score: lower emissions → higher score (inverted)
- Popularity score: moderate popularity → higher score (penalise extremes)
- Seasonality score: lower seasonal demand for travel month → higher score
- Feasibility score: shorter travel time and lower cost → higher score
- Weights are user-configurable with documented defaults

### Important notes
- Score directions are explicitly documented (lower emissions = better)
- Missing components receive neutral scores (0.5) with uncertainty flags
- Normalisation uses min–max within the candidate set
- The scoring formula is treated as a transparent heuristic, not a trained model
