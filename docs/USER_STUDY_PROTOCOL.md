# AuraTour: User Study Protocol, Recruitment Specification, and Survey Instrument

> **Document Type:** Human Subjects Research Protocol & Recruitment Specification  
> **System:** AuraTour Sustainable & Crowd-Aware Tourism Recommender (Rajasthan, India)  
> **Target Sample Size:** $N = 30\text{--}50$ Verified Participants  
> **Status:** Standardized, Privacy-Audited, and API-Integrated  

---

## 1. Study Objective and Research Hypotheses

This protocol governs the human-participant evaluation comparing AuraTour's multi-criteria recommendation strategy (**C5 Full Multi-Criteria: Preference + Transport Emissions + Crowding/Seasonality + Spatial Feasibility**) against a standard preference-only baseline (**C1 Baseline: Unconstrained Content-Based Filtering**).

### Primary Research Hypotheses
- **$H_1$ (Preference Retention / Non-Inferiority):** Participants will rate C5's topic relevance as non-inferior to C1 ($p > 0.05$), confirming that multi-criteria sustainability and spatial constraints do not degrade core user interest alignment.
- **$H_2$ (Spatial Routing & Feasibility Superiority):** Participants will rate C5's day-to-day itinerary feasibility and geographic layout significantly higher than C1 ($p < 0.05$, Wilcoxon signed-rank test).
- **$H_3$ (Perceived Environmental Responsibility):** Participants will perceive C5 as significantly more environmentally and socially responsible than C1 ($p < 0.001$).
- **$H_4$ (Trust and Adoption Willingness):** By offering transparent transit emissions and realistic logistics, C5 will achieve superior user trust and equal-or-higher willingness-to-visit scores.

---

## 2. Sample Size Determination and Statistical Power

To detect a statistically meaningful difference between paired recommendation lists on a 5-point Likert scale:
- **Test:** Two-tailed Wilcoxon signed-rank test for paired non-parametric samples.
- **Significance Level ($\alpha$):** 0.05.
- **Target Power ($1 - \beta$):** 0.80.
- **Anticipated Effect Size:** Medium-to-large effect ($d_z = 0.50\text{--}0.65$; Cliff's $\delta \ge 0.33$).
- **Sample Requirement:** An $N$ of 35 yields $80.2\%$ power at $\alpha=0.05$ for $d_z = 0.50$. Setting a target recruitment window of **$N = 30\text{--}50$ participants** provides robust power while accounting for potential exclusions ($\sim 10\%$).

---

## 3. Ethics, Privacy, and Data Governance

1. **Strictly Zero Personally Identifiable Information (PII):**
   - No participant names, email addresses, phone numbers, or account credentials.
   - No IP addresses, HTTP user-agent fingerprints, or advertising trackers.
2. **Anonymous Identification:**
   - Participants are assigned an ephemeral, cryptographically random identifier (`participant_id`), generated client-side via `crypto.randomUUID()` and stored only in browser `sessionStorage`.
3. **Voluntary Informed Consent Gate:**
   - Every participant must read the study disclosure and provide explicit affirmative consent (`consent_given: true`) prior to submitting evaluations.
4. **Physical Storage Isolation:**
   - Human survey responses are stored exclusively in `backend/data/results/user_study_responses.json`.
   - Simulated persona metrics and algorithmic benchmark outputs reside in distinct files (`experiment_results.json`, `matrix_results.csv`).
   - Human data and synthetic data are **never mixed or merged**.
5. **No Response Fabrication:**
   - In accordance with academic integrity guidelines, no synthetic, LLM-generated, or fake responses may ever be inserted into the human study repository. When 0 responses exist, the system transparently reports `status: no_responses_yet`.

---

## 4. Experimental Design: Double-Blinded Within-Subjects Paired Comparison

To eliminate algorithmic naming bias and halo effects, the study uses a **double-blinded within-subjects design**:

```
[ Participant Intake & Informed Consent ]
                 │
                 ▼
[ Select Traveler Scenario (P1–P7) ]
                 │
                 ▼
[ Generate 5-Item Itineraries ]
  ├── System A (e.g., C5_full)     ──┐ Counterbalanced / Randomized (50% probability)
  └── System B (e.g., C1_baseline) ──┘
                 │
                 ▼
[ Blinded Evaluation on 6 Likert Dimensions (1–5) ]
                 │
                 ▼
[ Comparative Forced-Choice & Qualitative Feedback ]
                 │
                 ▼
[ Atomic Submission to user_study_responses.json ]
```

- **Equivalent Constraints:** Both systems receive identical traveler inputs (origin city, interest tags, travel month, trip duration, budget).
- **Blinded Labels:** Systems are labeled strictly **System A** and **System B**. No strategy indicators ("Sustainable", "Baseline", "Multi-Criteria", "Optimized") appear anywhere in the interface.
- **Counterbalanced Presentation:** The assignment of C1 and C5 to System A and System B is determined by a cryptographically uniform random flip per session.

---

## 5. Survey Instrument: Dimensions and Scales

Participants rate both System A and System B independently across six theoretical constructs on an anchored 5-point Likert scale, followed by a comparative forced choice:

### Scale Anchors
- `1` = Very Poor / Strongly Disagree
- `2` = Poor / Disagree
- `3` = Neutral / Acceptable
- `4` = Good / Agree
- `5` = Excellent / Strongly Agree

### Item-Level Battery

| Construct | Question Prompt | Measured Variable |
|---|---|---|
| **Relevance** | *Do these destinations match the traveler's stated interest categories?* | Content-based alignment & accuracy |
| **Perceived Sustainability** | *Does this itinerary appear environmentally and socially responsible?* | Ecological & crowding perception |
| **Usefulness** | *Is this set of recommendations practical, appealing, and well-balanced?* | Perceived utility and overall variety |
| **Trust & Credibility** | *Do the recommendations and accompanying travel details feel credible?* | Explainability and algorithmic trust |
| **Feasibility** | *Is the geographic routing and travel time realistic for the duration?* | Spatial feasibility & route viability |
| **Willingness to Visit** | *Would the traveler be excited to actually follow this recommended journey?* | Behavioral adoption intention |

### Comparative Forced-Choice
- **Overall Recommendation:** *Which itinerary would you personally recommend for this traveler?*  
  `[ System A ]` / `[ System B ]` / `[ No Preference ]`

### Qualitative Commentary (Optional)
- *What specific factors influenced your rating (e.g., transit hours, attraction variety, carbon footprint, crowd avoidance)?* (Free text, max 1000 characters).

---

## 6. Participant Eligibility and Exclusion Criteria

To guarantee data cleanliness and integrity:
1. **Inclusion Criteria:**
   - Adults (age 18+) with interest in travel, cultural heritage, or itinerary planning.
   - Proficient in English (language of the survey instrument).
2. **Exclusion Criteria (Preregistered):**
   - **Incomplete Evaluations:** Any submission missing ratings for any of the 6 dimensions for either system is rejected at API schema validation (`HTTP 422`).
   - **Consent Absence:** Submissions without explicit consent (`consent_given == false`) are rejected (`HTTP 400`).
   - **Duplicate Evaluations:** Submissions by the same participant ID for the same persona ID are rejected (`HTTP 409 Conflict`).
   - **Speeding / Straightlining:** Submissions completed in under 45 seconds or giving identical ratings (e.g. all 1s or all 5s) across all items are flagged and excluded during statistical preprocessing.
   - **Automated / Test Entries:** Any records with participant IDs prefixed with `test_` are excluded from inferential reporting.

---

## 7. Participant Recruitment Materials

### 7.1 Participant Information Sheet (Web Display)

> **Study Title:** Evaluating Multi-Criteria Decision Support for Sustainable Heritage Tourism in Rajasthan  
> **Investigator:** AuraTour Research Team  
> **Purpose:** We are investigating how algorithms can assist travelers in discovering cultural attractions while balancing travel convenience, overcrowding, and carbon emissions.  
> **Task:** You will review a realistic travel scenario (e.g. a 5-day cultural trip starting in Delhi) and compare two candidate itineraries generated by different recommendation strategies. You will rate each itinerary on 6 criteria and indicate which one you prefer.  
> **Duration:** Approximately 5–8 minutes.  
> **Risks & Benefits:** There are no known risks. Your input will advance open scientific research on sustainable tourism algorithms.  
> **Voluntary Nature & Anonymity:** Participation is entirely voluntary. You may withdraw at any time. We do not collect your name, email, IP address, or location.  

### 7.2 Recruitment Invitation Text (Email / Social / Campus)

```text
Subject: [Research Study] Evaluating Travel Recommendation Strategies in Rajasthan (5-8 Mins)

Dear Traveler / Colleague,

We invite you to participate in an anonymous academic user study evaluating recommendation algorithms for heritage tourism in Rajasthan, India.

Study Link: http://localhost:5173/ (Navigate to "User Study Survey")

What does it involve?
- Review a brief traveler persona (e.g. 5 days, starting from Delhi, interested in heritage & architecture).
- Inspect two candidate travel itineraries (System A vs System B) presented side-by-side.
- Rate both itineraries across 6 criteria (relevance, feasibility, sustainability, usefulness, trust, willingness to visit).
- Takes only 5 to 8 minutes.

Privacy & Anonymity:
- Completely anonymous. No names, emails, IP addresses, or tracking cookies are collected.
- Target cohort: 30–50 participants.

Thank you for contributing to open scientific research on sustainable tourism!

AuraTour Research Team
```

---

## 8. Software & API Endpoints

The protocol is supported directly by live backend endpoints in `backend/app/api/main.py`:

1. **`GET /api/user-study/questionnaire?persona_id=P1`**  
   Generates the blinded comparison payload containing traveler scenario, randomized System A & B items, and question keys.
2. **`POST /api/user-study/responses`**  
   Validates Pydantic schema (`SurveySubmission`), attaches server timestamp, and atomically appends the submission to disk.
3. **`GET /api/user-study/responses`**  
   Aggregates mean Likert scores across all 6 dimensions and overall preference distribution for research inspection.

---

## 9. Preregistered Statistical Analysis Plan

When real participant intake reaches target cohort size ($N = 30\text{--}50$ participants):
- **Continuous / Ordinal Dimensions (Q1–Q6):** Two-tailed Wilcoxon Signed-Rank Test (non-parametric paired test) to compare median Likert ratings between C1 and C5, paired within participant.
- **Effect Sizes:** Rank-biserial correlation ($r_{rb}$) and Cliff's Delta ($\delta$) with 95% bootstrap confidence intervals (1,000 resamples).
- **Forced Choice:** Two-tailed Binomial Test against a null hypothesis of equal choice probability ($p = 0.50$), reporting exact $p$-values and odds ratios.
- **Internal Scale Consistency:** Cronbach's $\alpha$ across the multi-item scale to assess survey instrument reliability.
