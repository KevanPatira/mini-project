# Scientific Limitations and Boundary Conditions of the DRL Tourism Recommender

In adhering to rigorous academic standards and scientific honesty, this document explicitly identifies the operational, data, and algorithmic limitations of the AuraTour Deep Reinforcement Learning implementation.

---

## 1. Data Availability & Trajectory Limitations

### 1. Absence of Individual Tourist Trajectories (Why Mode B Was Required)
- **Verona Setup vs Indian Reality:** The reference paper by Dalla Vecchia et al. (2024) utilized longitudinal GPS tracking data from Verona card holders over multiple years. In India, public tourism repositories (Kaggle Indian Tourist Places, ASI annual reports, and Ministry of Tourism statistics) contain **cross-sectional, single-visit records or annual aggregate headcounts**.
- **Scientific Implication:** No authentic sequential tourist trajectories currently exist in open Indian datasets. Mode B (Simulator-based DRL) was selected out of scientific necessity. The agent learns an optimal policy in a simulated MDP under authentic site locations and fees; **it does not claim to have learned observed human tourist transition behavior**.

### 2. Annual Visitor Totals Are Not Real-Time Crowd Forecasts
- **ASI Headcounts:** Annual visitor figures (e.g., 1.4 million annual visitors at Amber Palace) provide a macro-level measure of popularity and overtourism pressure.
- **Scientific Implication:** Annual figures cannot be converted into hourly crowd density, queue wait times, or real-time site congestion without unverifiable synthetic assumptions. The crowding feature in the reward function must be treated as a **macro popularity-pressure proxy**, not a predictive queue model.

---

## 2. Transit and Geographic Limitations

### 1. Detour Factor Road Distances
- Inter-attraction road distances are calculated using Haversine great-circle distance multiplied by an empirical Indian highway circuity detour factor ($1.30\times$).
- While empirically supported by Indian transport engineering literature, this does not account for real-time traffic jams, seasonal road closures, monsoon flooding, or mountain pass terrain (e.g. Aravalli range near Mount Abu).

### 2. Static Transit Schedules and Fares
- Transit fares (₹2.0/km for broad-gauge rail, ₹1.5/km for state buses, ₹14.0/km for urban taxis) reflect published standard fare rates rather than dynamic surge pricing or specific train classes (e.g., Vande Bharat vs General Sleeper).

---

## 3. Carbon Accounting & Emission Factors

### 1. National Average Emission Factors
- Emissions are calculated using WRI India / India GHG Program national averages ($17\text{ g CO}_2\text{e/pkm}$ for Indian Railways, $40\text{ g}$ for buses, $150\text{ g}$ for cars).
- Actual emissions vary depending on the local electricity grid's coal vs renewable mix (Rajasthan solar generation vs Northern Grid thermal plants), train coach occupancy, and vehicle age.

---

## 4. Algorithmic and Generalizability Boundaries

### 1. Simulator Generalizability
- The policy trained in this environment is optimized for the 45 curated Rajasthan attractions and the specific reward weights ($w_p = 0.40, w_v = 0.15, w_t = 0.15, w_c = 0.10, w_b = 0.12, w_e = 0.08$).
- Transferring this policy to other Indian states (e.g. Kerala backwaters or Himachal mountain circuits) would require re-calibrating transit speeds, operational hours, and terrain circuity factors.

### 2. Accommodation and Meal Costs
- The budget constraint strictly models **transit fares and monument entrance fees**. Accommodation, food, shopping, and local guide fees are not modelled and must be funded out of the traveler's remaining budget.
