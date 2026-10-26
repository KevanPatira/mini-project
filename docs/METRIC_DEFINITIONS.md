# AuraTour: Mathematical Metric Definitions and Evaluation Standards

> **Document Type:** Research Metric Specification  
> **System:** AuraTour (Sustainable & Crowd-Aware Tourism Recommender)  
> **Status:** Standardized & Verified against Hand-Computed Benchmarks  

---

## 1. Overview

This document specifies the exact mathematical formulas, implementation code, edge-case conventions, and scientific interpretations for all quantitative metrics used to evaluate the AuraTour recommendation engine.

All metrics are verified against analytical ground-truth test cases in `backend/app/tests/test_validation_extended.py`.

---

## 2. Core Recommender System Metrics

### 2.1 Category Match Rate at K (CMR@K)

#### Mathematical Definition
For a user with interest set $U = \{u_1, u_2, \dots, u_m\}$ and a recommended list of $K$ destinations $R = \{r_1, r_2, \dots, r_K\}$, where each destination has category set $C(r_i)$:

$$\text{CMR@}K = \frac{1}{K} \sum_{i=1}^K \mathbb{I}\left( U \cap C(r_i) \neq \emptyset \right)$$

where $\mathbb{I}(\cdot)$ is the indicator function ($1$ if true, $0$ otherwise).

#### Interpretation & Structural Boundary Note
- **Range:** $[0.0, 1.0]$. Higher is better.
- **Empirical Value:** In AuraTour experiments, $\text{CMR@10} = 1.000$ ($100\%$) across almost all configurations.
- **Why CMR@10 is 100%:**
  1. Persona profiles contain 3–4 categories (e.g. `['history', 'culture', 'nature']`).
  2. In the 45-attraction catalog, at least one of those categories appears in 35 to 45 items.
  3. Destinations with zero category overlap receive `preference_score = 0.0`. In multi-criteria ranking, matching destinations almost always outrank non-matching items.
  4. Consequently, CMR@10 serves as a **safety constraint check** confirming that sustainability criteria have not forced completely irrelevant destinations into the top-10, rather than a fine-grained ranking differentiator.

---

### 2.2 Average Continuous Preference Score ($\bar{P}@K$)

#### Mathematical Definition
While CMR@K is a binary match fraction, $\bar{P}@K$ captures the continuous depth of category alignment:

$$\bar{P}@K = \frac{1}{K} \sum_{i=1}^K \frac{|U \cap C(r_i)|}{|U|}$$

#### Interpretation
- **Range:** $[0.0, 1.0]$. Measures the exact fraction of the user's total interest profile satisfied by each recommended item on average.
- In AuraTour:
  - C1 (Baseline) achieves $\bar{P}@10 = 0.685$.
  - C5 (Full Multi-criteria) retains $\bar{P}@10 = 0.638$ ($93.1\%$ retention of baseline preference), proving that carbon and crowd dispersion do not significantly degrade user interest relevance.

---

### 2.3 Category Diversity (CD@K)

#### Mathematical Definition
The number of distinct interest categories represented across the top-$K$ recommendations:

$$\text{CD@}K = \left| \bigcup_{i=1}^K C(r_i) \right|$$

#### Interpretation
- **Range:** $[1, |\mathcal{C}|]$, where $|\mathcal{C}| = 10$ is the total category vocabulary.
- Prevents redundant recommendations (e.g., ten identical forts).
- In AuraTour, C5 increases category diversity to $5.857$ distinct categories per itinerary compared to $5.714$ in C1.

---

### 2.4 Total Estimated Emissions (TEE)

#### Mathematical Definition
The cumulative round-trip or arrival transportation emissions in kilograms of $\text{CO}_2$ equivalent ($\text{kg CO}_2\text{e}$) from the user's origin city to all $K$ recommended destinations:

$$\text{TEE} = \sum_{i=1}^K E(origin, r_i, m_i)$$

where $E(origin, r_i, m_i)$ is:

$$E(origin, r_i, m_i) = \frac{d_{\text{road}}(origin, r_i) \times \text{EF}(m_i)}{1000}$$

with emission factor $\text{EF}(m_i)$ sourced from WRI India standard averages (Train: $17.0\text{ g/pkm}$, Bus: $40.0$, Car: $150.0$, Flight: $130.0$).

#### Interpretation
- **Units:** $\text{kg CO}_2\text{e}$. Lower is better.
- **Empirical Baseline:** C1 baseline exhibits average $\text{TEE} = 203.32\text{ kg CO}_2\text{e}$.
- **Reduction:** C2 reduces this to $179.14\text{ kg}$ ($-11.89\%$), and C5 stabilizes at $185.56\text{ kg}$ ($-8.74\%$), while balancing popularity and travel time.

---

### 2.5 Normalized Emission Score ($S_{\text{emission}}$)

#### Mathematical Definition
For a candidate destination $r_i$ among the catalog candidates $\mathcal{D}$:

$$S_{\text{emission}}(r_i) = 1.0 - \frac{E(origin, r_i) - \min_{d \in \mathcal{D}} E(origin, d)}{\max_{d \in \mathcal{D}} E(origin, d) - \min_{d \in \mathcal{D}} E(origin, d)}$$

#### Meaning of Reported 0.793 Score
- In C2, the average $S_{\text{emission}}$ of the top-10 items is **0.793**.
- Because $S_{\text{emission}} = 1.0$ represents the single lowest-carbon destination available from that origin (e.g., closest train-accessible site), an average of $0.793$ indicates that the top-10 recommendations under C2 rank in the top $20.7\%$ cleanest transit tier of the entire catalog.

---

### 2.6 Popularity Gini Coefficient ($G$)

#### Mathematical Definition
Given the sorted visitor counts of the top-$K$ recommended items $y_1 \le y_2 \le \dots \le y_K$:

$$G = \frac{\sum_{i=1}^K (2i - K - 1) y_i}{K \sum_{i=1}^K y_i}$$

#### Interpretation of Gini Reduction (0.474 to 0.144)
- **What Distribution It Measures:** Intra-list visitor count inequality among the 10 recommended items on a single user's itinerary.
- In **C1 (Baseline)**, recommendations are chosen without popularity awareness, pairing mega-attractions ($5,000,000$ visitors) with niche monuments ($50,000$ visitors), producing high intra-list dispersion ($G = 0.474$).
- In **C3 / C4 / C5**, the popularity scoring objective penalizes overtouristed extremes ($1 - |2\hat{r} - 1|$), focusing recommendations on moderate-tier gems ($250,000$ to $500,000$ visitors). Because the recommended destinations possess similar, moderate footfall, intra-list visitor inequality drops by $69.6\%$ to **0.144**.

---

### 2.7 Catalog Coverage (CC)

#### Mathematical Definition
The proportion of the total attraction catalog $\mathcal{C}_{total}$ recommended at least once across all $N$ experimental persona runs:

$$\text{CC} = \frac{\left| \bigcup_{p=1}^N \mathcal{R}_p \right|}{|\mathcal{C}_{total}|}$$

where $|\mathcal{C}_{total}| = 45$.

#### Interpretation
- Measures global catalog exploration vs recommendation monopolization.
- In AuraTour:
  - C1 covers $62.2\%$ of the catalog ($28 / 45$ items).
  - C2 increases coverage to $73.3\%$ ($33 / 45$ items) by distributing users from different origins to their local clean hubs.

---

### 2.8 Geographic Spread (GS)

#### Mathematical Definition
The average pairwise great-circle distance (in kilometers) between all recommended destinations in top-$K$:

$$\text{GS} = \frac{2}{K(K - 1)} \sum_{i=1}^{K-1} \sum_{j=i+1}^K d_{\text{haversine}}(r_i, r_j)$$

#### Interpretation
- **Units:** $\text{km}$.
- Measures spatial clustering:
  - C1 exhibits $\text{GS} = 252.31\text{ km}$ (diffuse, uncoordinated statewide dispersion).
  - C2 compresses spread to $162.47\text{ km}$ (clustering around origin-accessible regions to minimize travel carbon).
  - C5 balances spread at $191.00\text{ km}$ across $6.0$ unique districts, ensuring trip feasibility.

---

### 2.9 Ranking Alignment Metrics (Jaccard & Kendall's Tau)

#### Top-K Jaccard Similarity Overlap
$$J(R_{baseline}, R_{test}) = \frac{|R_{baseline} \cap R_{test}|}{|R_{baseline} \cup R_{test}|}$$
Measures destination retention vs replacement as sustainability constraints are applied.

#### Kendall's Tau Rank Correlation ($\tau$)
Evaluated strictly over the subset of common items $C = R_{baseline} \cap R_{test}$:

$$\tau = \frac{N_{\text{concordant}} - N_{\text{discordant}}}{\frac{1}{2} |C| (|C| - 1)}$$

Measures whether destinations retained from the baseline preserve or reorder their relative priorities.
