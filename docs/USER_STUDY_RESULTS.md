# AuraTour: User Study Results and Recruitment Report

> **Document Type:** Human Subjects Research Evaluation Report  
> **System:** AuraTour Sustainable & Crowd-Aware Tourism Recommender (Rajasthan, India)  
> **Study Target:** $N = 30\text{--}50$ Verified Participants  
> **Status:** Participant Intake Phase Active (Pre-registered Statistical Pipeline Verified)  
> **Repository Data Store:** `backend/data/results/user_study_responses.json`  

---

## 1. Executive Summary

This report documents the empirical user study design, intake status, and statistical evaluation framework for AuraTour. The study compares **C5 Full Multi-Criteria** against **C1 Baseline** via a double-blinded, within-subjects paired comparison across six theoretical dimensions: *Relevance*, *Perceived Sustainability*, *Practical Usefulness*, *Trust & Credibility*, *Itinerary Feasibility*, and *Willingness to Visit*.

### Key Scientific Principles Maintained
1. **Zero Data Fabrication:** In strict adherence to academic integrity standards, simulated persona benchmarks (P1–P7) are stored separately from human data. The human response store currently contains $0$ fabricated responses.
2. **Pre-Registered Analysis Pipeline:** An automated, reproducible analysis script (`backend/scripts/analyze_user_study.py`) has been implemented and validated against synthetic test cohorts and power simulations.
3. **Statistical Power Verification:** A formal power calculation confirms that an intake of $N = 35\text{--}50$ participants yields **$80.2\%\text{--}92.4\%$ statistical power** ($\alpha = 0.05$) to detect medium-to-large effects ($d_z = 0.55$) using the two-tailed Wilcoxon signed-rank test.

---

## 2. Participant Recruitment and Intake Status

### 2.1 Current Enrollment Breakdown (Audited at 2026-10-25)

| Metric | Current Count | Target Threshold | Status |
|---|---|---|---|
| **Raw Submissions Received** | 0 | 35–55 | Intake Open |
| **Excluded (Missing Consent)** | 0 | — | Preregistered Gate |
| **Excluded (Incomplete Dimensions)** | 0 | — | Preregistered Gate |
| **Excluded (Automated / Test IDs)** | 0 | — | Preregistered Gate |
| **Excluded (Duplicate Submissions)** | 0 | — | Preregistered Gate |
| **Verified Human Participants ($N$)** | **0** | **30–50** | **Recruitment Active** |

> [!NOTE]
> Testing and continuous-integration runs utilize isolated ephemeral files (`isolated_user_study.json` via pytest monkeypatching) to ensure automated test executions never contaminate the verified human participant repository.

### 2.2 Recruitment Channels and Schedule
Recruitment is organized across three primary channels:
- **Academic Student & Faculty Cohorts:** Computer science and tourism management departments evaluating digital travel assistants.
- **Domestic Travel Communities:** Online forums and travel clubs with prior travel experience in Rajasthan.
- **Public Research Portal:** Direct access via the AuraTour interface (`http://localhost:5173/`, tab *"User Study Survey"*).

---

## 3. Experimental Design and Procedure

### 3.1 Paired Within-Subjects Protocol
Each participant performs an anonymous, double-blinded evaluation:
1. **Informed Consent Gate:** The participant reviews the study information sheet detailing the academic purpose and voluntary nature of the study, and gives affirmative consent.
2. **Scenario Assignment:** The participant is assigned a realistic travel scenario (one of 7 standardized traveler personas, e.g. *P1: 5-Day Solo Heritage Explorer from Delhi*).
3. **Blinded Presentation:** The backend generates recommendations for C1 (Baseline) and C5 (Multi-criteria). System labels are randomized to **System A** and **System B** with equal $50\%$ probability. Attraction descriptions and metadata are rendered in identical neutral formats to prevent unblinding.
4. **6-Dimension Likert Battery:** The participant rates both systems independently on 5-point anchored scales.
5. **Forced Choice:** The participant selects which itinerary they would personally recommend (*System A*, *System B*, or *No Preference*).
6. **Qualitative Feedback:** Optional commentary on trade-offs, pacing, and sustainability.

---

## 4. Evaluation Dimensions and Pre-Registered Hypotheses

| Dimension | Question Prompt | Scale Anchors | Null Hypothesis ($H_0$) |
|---|---|---|---|
| **Relevance** | *Do these destinations match the stated interests?* | 1 (Very Poor) to 5 (Excellent) | $\text{Median}(C5) = \text{Median}(C1)$ (Equivalence / Non-inferiority) |
| **Perceived Sustainability** | *Does this itinerary appear environmentally and socially responsible?* | 1 (Very Poor) to 5 (Excellent) | $\text{Median}(C5) \le \text{Median}(C1)$ |
| **Practical Usefulness** | *Is this set of recommendations practical, appealing, and well-balanced?* | 1 (Very Poor) to 5 (Excellent) | $\text{Median}(C5) \le \text{Median}(C1)$ |
| **Trust & Credibility** | *Do the recommendations and travel details feel credible?* | 1 (Very Poor) to 5 (Excellent) | $\text{Median}(C5) \le \text{Median}(C1)$ |
| **Itinerary Feasibility** | *Is the geographic routing and travel time realistic for the duration?* | 1 (Very Poor) to 5 (Excellent) | $\text{Median}(C5) \le \text{Median}(C1)$ |
| **Willingness to Visit** | *Would the traveller be excited to actually follow this journey?* | 1 (Very Poor) to 5 (Excellent) | $\text{Median}(C5) \le \text{Median}(C1)$ |

---

## 5. Statistical Power Analysis

A prospective power analysis was conducted for the two-tailed Wilcoxon signed-rank test using asymptotic relative efficiency adjustments ($0.955$) and an anticipated effect size of $d_z = 0.55$:

```
Sample Size (N)   Statistical Power (1 - β)   Sufficiency (α = 0.05)
--------------------------------------------------------------------
N = 15            42.8%                       Underpowered
N = 25            66.1%                       Marginal
N = 35            80.2%                       Adequate (Meets 80% Benchmark)
N = 45            89.1%                       High Power
N = 50            92.4%                       Optimal Research Standard
```

The resulting power curve is plotted and saved at `docs/figures/fig3_study_power_curve.png`.

---

## 6. Pre-Registered Reporting Specification

Once participant intake reaches the target cohort ($N \ge 30$), `backend/scripts/analyze_user_study.py` automatically generates:
1. **`user_study_summary.csv`:** Tabulated sample size ($n$), means, standard deviations, paired mean differences, 95% bootstrap confidence intervals, Wilcoxon $W$ statistics, exact two-tailed $p$-values, and Cliff's $\delta$ effect sizes for all 6 dimensions.
2. **`user_study_stats.json`:** Structured machine-readable telemetry including data audit logs, exclusion counts, and exact binomial test outcomes for forced-choice preferences.
3. **`fig1_study_dimension_comparison.png`:** Publication-ready paired boxplot comparing rating distributions between C1 and C5.
4. **`fig2_study_preference_distribution.png`:** Bar chart of forced-choice preferences across conditions.

---

## 7. Audit of Ethical and Anonymity Guarantees

- **No Cookies or Fingerprinting:** No tracking scripts, persistent client identifiers, or third-party analytics are embedded.
- **Client-Side Session Token:** Participant tokens (`anon_xxxxxxxxxxxx`) are generated locally via `crypto.randomUUID()` and stored only in browser `sessionStorage`.
- **Zero IP Logging:** Fastify/Starlette endpoints in `main.py` do not store `client.host`, IP addresses, or HTTP User-Agent headers.
- **Atomic Concurrency Protection:** Survey submissions use temporary file allocation (`tempfile.mkstemp`) and atomic directory renaming (`os.replace`) to guarantee no response file corruption under concurrent submissions.
