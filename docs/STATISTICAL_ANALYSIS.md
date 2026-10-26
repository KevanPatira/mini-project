# AuraTour: Statistical Analysis Plan and Methodology Specification

> **Document Type:** Statistical Methodology & Reproducibility Guide  
> **System:** AuraTour Sustainable & Crowd-Aware Tourism Recommender  
> **Authors:** AuraTour Research Team  
> **Script Reference:** `backend/scripts/analyze_user_study.py`  
> **Output Artifacts:** `backend/data/results/user_study_summary.csv`, `backend/data/results/user_study_stats.json`, `docs/figures/`  

---

## 1. Statistical Framework and Measurement Scale Considerations

The AuraTour evaluation couples **offline algorithmic benchmarking** across standardized traveler personas with an **empirical within-subjects human user study**.

### 1.1 Nature of Measurement Scales
- **Likert Ratings (Q1–Q6):** Survey responses are measured on an anchored 5-point scale (1 = Very Poor to 5 = Excellent). Because Likert-type items represent **ordinal data** without guaranteed interval equidistance, parametric assumptions of normality are not assumed.
- **Forced-Choice Recommendation (Q7):** Dichotomous categorical variable with a tie category (*System A*, *System B*, *No Preference*).
- **Offline Continuous Metrics:** Ratio-scale metrics (Total transit emissions in kg CO₂e, popularity Gini coefficient, Haversine travel distance in km, category diversity count).

---

## 2. Hypothesis Testing Suite

### 2.1 Paired Ordinal Comparisons (Wilcoxon Signed-Rank Test)
For each participant $i \in \{1, \dots, N\}$ and dimension $k \in \{\text{relevance, sustainability, usefulness, trust, feasibility, willingness}\}$:
- Let $X_{5, i}^k$ and $X_{1, i}^k$ denote the ratings awarded to C5 (Multi-criteria) and C1 (Baseline).
- Paired differences are defined as:
  $$D_i^k = X_{5, i}^k - X_{1, i}^k$$
- Non-zero differences $|D_i^k| > 0$ are ranked from smallest to largest with average ranks assigned to ties.
- The Wilcoxon test statistic $W$ is the sum of ranks for positive differences:
  $$W = \sum_{i: D_i > 0} \text{Rank}(|D_i|)$$
- Significance is evaluated using the exact distribution for $N \le 25$ and the continuity-corrected normal approximation for $N > 25$:
  $$z = \frac{W - \frac{N(N+1)}{4}}{\sqrt{\frac{N(N+1)(2N+1)}{24}}}$$

### 2.2 Non-Parametric Effect Sizes
Two complementary effect size metrics are computed:

1. **Rank-Biserial Correlation ($r_{rb}$):**
   $$r_{rb} = \frac{W_+ - W_-}{W_+ + W_-}$$
   Where $r_{rb} \in [-1, +1]$. A value of $+1$ indicates complete C5 dominance, while $0$ indicates perfect parity.

2. **Cliff's Delta ($\delta$):**
   Measures the degree to which scores in condition C5 are higher than scores in condition C1:
   $$\delta = \frac{\# (X_{5, i} > X_{1, j}) - \# (X_{5, i} < X_{1, j})}{n_5 \cdot n_1}$$
   - $|\delta| < 0.147$: Negligible
   - $0.147 \le |\delta| < 0.33$: Small
   - $0.33 \le |\delta| < 0.474$: Medium
   - $|\delta| \ge 0.474$: Large

### 2.3 Bootstrap Confidence Intervals
To avoid distributional assumptions, 95% confidence intervals for the mean difference $\mu_D = \mathbb{E}[X_5 - X_1]$ are constructed via **non-parametric percentile bootstrapping** with $B = 1,000$ resamples:
$$\text{CI}_{95\%} = \left[ q_{0.025}^B, q_{0.975}^B \right]$$

### 2.4 Forced-Choice Analysis (Exact Binomial Test)
For overall system preference:
- Let $k_5$ denote participants preferring C5, and $k_1$ denote participants preferring C1 (ties/no preference excluded from binomial trial).
- The total decided count is $n_{\text{dec}} = k_5 + k_1$.
- We test the null hypothesis $H_0: p = 0.50$ against the two-sided alternative $H_1: p \neq 0.50$ using the exact Binomial distribution:
  $$p\text{-value} = 2 \cdot \sum_{x = \max(k_5, n_{\text{dec}} - k_5)}^{n_{\text{dec}}} \binom{n_{\text{dec}}}{x} 0.50^{n_{\text{dec}}}$$

---

## 3. Pre-Registered Exclusion and Data Screening Criteria

To guarantee research validity, the pipeline enforces strict pre-registered exclusion gates prior to statistical calculation:

1. **Consent Filter:** Any record where `consent_given != True` is rejected.
2. **Completeness Gate:** Any record with missing or null ratings on any of the 6 dimensions for either system is excluded.
3. **Automated Test Isolation:** Any participant ID prefixed with `test_` is identified as an automated integration test and excluded from human statistics.
4. **Duplicate Deduplication:** If an anonymous participant token submits multiple evaluations for the same persona ID, only the initial verified submission is retained.
5. **Speeding Threshold:** Submissions completed in under 45 seconds are flagged as potential straight-lining and reported in the exclusion audit.

---

## 4. Reproducible Pipeline Execution

The statistical analysis pipeline is packaged as a standalone, dependency-verified CLI tool:

```bash
# From the backend directory:
python scripts/analyze_user_study.py

# Custom input response path:
python scripts/analyze_user_study.py --input /path/to/custom_responses.json

# Run analysis without re-generating plot files:
python scripts/analyze_user_study.py --no-figures
```

### Generated Artifacts
1. **`backend/data/results/user_study_summary.csv`:** Tabular summary containing item-level statistics (means, SDs, mean difference, 95% bootstrap CIs, Wilcoxon $W$, $p$-values, Cliff's $\delta$).
2. **`backend/data/results/user_study_stats.json`:** Machine-readable JSON telemetry detailing exclusion counts, participant totals, dimension metrics, and binomial test outcomes.
3. **`docs/figures/fig1_study_dimension_comparison.png`:** Paired boxplots across the 6 evaluation dimensions.
4. **`docs/figures/fig2_study_preference_distribution.png`:** Bar chart of forced-choice preferences.
5. **`docs/figures/fig3_study_power_curve.png`:** Statistical power vs. sample size ($N$) curve.

---

## 5. Separation of Descriptive Findings from Inferential Claims

In reporting findings, AuraTour maintains a strict distinction between descriptive observations and inferential conclusions:

| Analysis Level | Scope | Legitimate Claims | Prohibited Claims |
|---|---|---|---|
| **Descriptive Statistics** | Sample distributions ($M, SD, Mdn, IQR$) | Characterizes response tendencies of the enrolled sample | Cannot claim generalizability to all travelers without inferential tests |
| **Inferential Statistics** | Hypothesis tests ($W, p, \delta, 95\%\text{ CI}$) | Evaluates whether observed differences exceed random chance | Cannot claim certainty; must report exact $p$-values and confidence intervals |
| **Simulated Personas** | Algorithmic benchmark ($N=7$ personas) | Demonstrates mathematical behavior of C1–C5 formulations | Must **never** be conflated with real human preferences |
| **Power Curve** | Theoretical power ($1 - \beta$) | Confirms sample size adequacy ($N=30\text{--}50$) for future intake | Does not substitute for collecting actual participant responses |
