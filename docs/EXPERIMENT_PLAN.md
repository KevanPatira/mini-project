# Experiment Plan

## 1. Experimental Configurations

| ID | Name | Components | Purpose |
|---|---|---|---|
| C1 | Preference-only | Interest category match | Baseline |
| C2 | Preference + Emissions | + transport CO₂e | Effect of emissions on ranking |
| C3 | Pref + Emis + Popularity | + popularity index | Effect of popularity balancing |
| C4 | Pref + Emis + Pop + Season | + seasonal demand | Full sustainability composite |
| C5 | Full system | + travel time/cost constraints | Complete multi-criteria system |

## 2. User Personas for Scenario Evaluation

| Persona | Origin | Interests | Budget | Duration | Sustainability Priority |
|---|---|---|---|---|---|
| P1: Heritage Explorer | Delhi | History, Architecture, Culture | Medium | 5 days | Medium |
| P2: Nature Enthusiast | Mumbai | Nature, Wildlife, Adventure | High | 7 days | High |
| P3: Budget Backpacker | Bangalore | All categories | Low | 10 days | Low |
| P4: Cultural Foodie | Kolkata | Food, Culture, Markets | Medium | 4 days | Medium |
| P5: Eco-conscious Traveller | Chennai | Nature, History | Medium | 6 days | Very High |
| P6: Weekend Tripper | Jaipur (local) | Any | Low | 2 days | Low |
| P7: Family Vacationer | Delhi | Family-friendly, Nature | High | 5 days | Medium |

## 3. Evaluation Metrics

### 3.1 Preference Relevance
- **Category Match Rate (CMR@K):** Fraction of top-K recommendations matching at least one user interest category
- **Average Interest Score:** Mean preference relevance score of top-K recommendations

### 3.2 Sustainability
- **Total Estimated Emissions (TEE):** Sum of CO₂e for travelling to all top-K destinations (kg)
- **Average Emission Score:** Mean emission component score across top-K
- **Popularity Gini Coefficient:** Measure of concentration in recommended destinations' popularity

### 3.3 Diversity
- **Category Diversity (CD@K):** Number of distinct attraction categories in top-K
- **Geographic Spread:** Average pairwise distance between recommended destinations (km)
- **Unique Districts:** Number of distinct districts/cities represented

### 3.4 Sensitivity
- **Kendall's τ Rank Correlation:** Between rankings at different weight settings
- **Top-K Overlap:** Jaccard similarity of top-K sets across weight configurations
- **Emission Reduction Curve:** How total emissions change as sustainability weight increases

### 3.5 Feasibility
- **Average Travel Time:** Mean estimated travel time to recommended destinations
- **Constraint Satisfaction Rate:** Fraction of recommendations within budget/duration limits

## 4. Experiment Procedures

### Experiment 1: Configuration Comparison
For each persona, run all 5 configurations and compare:
- Top-10 recommendations
- All metrics above
- Score component distributions

### Experiment 2: Sensitivity Analysis
Fix persona P1 (Heritage Explorer from Delhi), vary sustainability weight from 0.0 to 1.0 in steps of 0.1:
- Record top-10 rankings at each weight
- Plot emission reduction curve
- Plot category match rate change
- Compute pairwise rank correlations

### Experiment 3: Transport Mode Impact
Compare recommendations when user selects:
- Train only
- Car only
- Flight only
- Any mode (lowest emission)

Measure how transport mode constraint affects destination reach and emissions.

### Experiment 4: Seasonal Variation
Run recommendations for same persona across all 12 months:
- Observe how seasonal demand scores change rankings
- Identify months where off-peak recommendations differ most from peak

### Experiment 5: Missing Data Robustness
Systematically remove components and verify:
- Graceful degradation with missing popularity data
- Reasonable rankings with missing seasonal data
- Correct neutral score assignment

## 5. Reproducibility

- All random seeds documented (if any randomisation used)
- Configuration files versioned alongside results
- Scripts produce deterministic output for same inputs
- Results saved as structured JSON files in `backend/data/results/`

## 6. Limitations to Acknowledge

- No real user feedback data; evaluation is scenario-based
- Emission estimates use national averages, not route-specific measurements
- Popularity data is incomplete; covers only a subset of attractions
- Seasonal demand may only be available at state level
- Results demonstrate system behaviour, not validated recommendation quality
