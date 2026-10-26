# Deep Reinforcement Learning Methodology for Sustainable Rajasthan Tourism

## 1. Research Objective & Context

This research adapts the sequential itinerary recommendation framework proposed by:
> **"Promoting sustainable tourism by recommending sequences of attractions with deep reinforcement learning"**  
> Anna Dalla Vecchia, Sara Migliorini, Alberto Belussi, and Carola Ricci (2024).  
> *Information Technology & Tourism*, 26, 451–482. https://doi.org/10.1007/s40558-024-00288-x  
> Reference Implementation: [smigliorini/itinerary-drl](https://github.com/smigliorini/itinerary-drl)

### Formal Objective
> *"Adapt and evaluate a sustainability-aware Deep Reinforcement Learning itinerary planner for Rajasthan that generates sequential attraction recommendations under travel-time, trip-duration, budget, and preference constraints, using authentic Indian monument visitation statistics and geographic data while explicitly accounting for the limited availability of historical tourist trajectories."*

---

## 2. Adaptation from Verona (Original) to Rajasthan (AuraTour)

| Dimension | Original Paper (Verona, Italy) | AuraTour Adaptation (Rajasthan, India) | Scientific Rationale |
| :--- | :--- | :--- | :--- |
| **Geographic Scale** | Compact historic municipality ($<15 \text{ km}$ radius). Walking and cycling dominant. | Vast regional state ($342,239 \text{ km}^2$, $>600 \text{ km}$ intercity transit legs). | Requires multi-modal transit modelling (intercity express rail, regional bus, urban auto/taxi). |
| **Data Granularity** | High-density historical GPS trajectories from Verona tourist card passes. | 13,000 Kaggle single-visit records + Ministry of Tourism / ASI annual ticket counts. | **No individual sequential multi-stop trajectories exist**. Mode B Simulator-based DRL selected. |
| **Attraction Set** | 32 urban monuments and museums in Verona. | 45 verified Rajasthan heritage, natural, and religious destinations across 18 districts. | Preserves authentic catalog vetted against OpenStreetMap and ASI circles. |
| **Constraint Priorities** | Time-budget only ($T_{\text{max}}$). | **Financial Budget is prioritized over Carbon Emissions** ($w_{\text{budget}} > w_{\text{emissions}}$). | Reflects realistic Indian domestic travel constraints where monetary feasibility dominates carbon trade-offs. |
| **Operational Windows** | Continuous hourly opening schedules. | 9-hour daily operational sightseeing window (09:00 to 18:00) with day-by-day rollover. | Matches authentic monument operating hours and intercity night transit customs. |

---

## 3. Markov Decision Process (MDP) Formalism

The itinerary generation problem is framed as a finite-horizon Markov Decision Process $\langle \mathcal{S}, \mathcal{A}, \mathcal{P}, \mathcal{R}, \gamma \rangle$:

### 3.1 State Space $\mathcal{S}$ (64 Dimensions)
At decision step $t$, state vector $s_t \in \mathbb{R}^{64}$ encodes:
1. **Current Location Coordinates** (2 dims): Min-max normalized $(\text{lat}, \text{lon})$ anchored to Rajasthan bounding box $[23^\circ\text{N}-31^\circ\text{N}, 69^\circ\text{E}-79^\circ\text{E}]$.
2. **Visited Attractions Mask** (45 dims): Binary indicator vector $v_t \in \{0, 1\}^{45}$ where $v_t[i] = 1$ if attraction $i$ has already been visited.
3. **Normalized Remaining Trip Hours** (1 dim): $H_t^{\text{rem}} / H^{\text{total}} \in [0, 1]$.
4. **Normalized Remaining Budget** (1 dim): $B_t^{\text{rem}} / B^{\text{total}} \in [0, 1]$.
5. **Day Progression Features** (2 dims): Current day index normalized ($d_t / d_{\text{max}}$) and remaining sightseeing hours in current day ($h_t^{\text{day\_rem}} / 9.0$).
6. **User Preference Profile** (10 dims): Binary multi-hot vector over canonical category genres: *history, architecture, culture, nature, wildlife, adventure, religion, food, shopping, relaxation*.
7. **Seasonal Cyclical Context** (2 dims): $\sin(2\pi (m-1)/12)$ and $\cos(2\pi (m-1)/12)$ where $m \in [1, 12]$.
8. **Stops Count** (1 dim): Fraction of attractions visited $k_t / 45$.

### 3.2 Action Space $\mathcal{A}$ (46 Actions)
- Actions $a \in \{0, \dots, 44\}$: Select attraction index $a$ as the next stop in sequence.
- Action $a = 45$: Explicit `STOP` action terminating the itinerary episode.

### 3.3 Action Masking (Hard Constraints)
Rather than penalizing violations post-hoc, infeasible actions are masked before selection ($\mathcal{M}(s) \in \{0, 1\}^{46}$):
$$\mathcal{M}(s)[a] = 0 \iff \begin{cases}
v_t[a] = 1 & \text{(re-visitation prohibited)} \\
t_{\text{travel}}(s, a) + t_{\text{visit}}(a) > H_t^{\text{rem}} & \text{(exceeds trip time limit)} \\
c_{\text{transit}}(s, a) + c_{\text{entry}}(a) > B_t^{\text{rem}} & \text{(exceeds remaining budget)} \\
d(s, a) > d_{\text{max}} & \text{(exceeds maximum allowed trip days)}
\end{cases}$$
The `STOP` action is always valid once at least 1 destination has been visited.

### 3.4 Multi-Objective Normalized Reward Function
$$\mathcal{R}(s_t, a_t) = w_p P_t + w_v V_t - w_\tau T_t - w_c C_t - w_b B_t - w_e E_t$$
Where:
- $P_t \in [0, 1]$: Preference Jaccard overlap between attraction categories and user interests ($w_p = 0.40$).
- $V_t \in [0, 1]$: Marginal category diversity introduced to the itinerary ($w_v = 0.15$).
- $T_t \in [0, 1]$: Travel time penalty normalized against $6.0\text{ h}$ max leg duration ($w_\tau = 0.15$).
- $C_t \in [0, 1]$: Macro-level crowding/popularity pressure proxy from ASI annual counts normalized against $5\times 10^6$ visitors ($w_c = 0.10$).
- $B_t \in [0, 1]$: Financial cost penalty normalized against ₹$2,500$ leg threshold ($w_b = 0.12$).
- $E_t \in [0, 1]$: Transit carbon emissions penalty normalized against $80\text{ kg CO}_2\text{e}$ ($w_e = 0.08$).

**Strict Invariant:** $w_b (0.12) > w_e (0.08)$, ensuring financial feasibility always overrides carbon penalization.

---

## 4. Deep Q-Network Architecture

To guarantee lightweight, dependency-free reproducibility across any environment without CUDA or multi-gigabyte wheels, the agent is implemented as a vectorized pure-NumPy Multi-Layer Perceptron:

```
State Input (64)
    │
    ▼
Dense Layer 1 (64 -> 128) + He Normal Init + ReLU
    │
    ▼
Dense Layer 2 (128 -> 64) + He Normal Init + ReLU
    │
    ▼
Linear Output Layer (64 -> 46) -> Q(s, a)
```

- **Optimizer:** Vectorized Adam ($lr = 0.001, \beta_1 = 0.9, \beta_2 = 0.999$).
- **Loss:** Robust Huber loss ($\delta = 1.0$) with gradient clipping at $[-5.0, 5.0]$.
- **Target Network:** Periodic hard update every 50 parameter updates ($\theta^- \leftarrow \theta$).
- **Experience Replay Buffer:** Ring buffer of capacity 10,000 storing $\langle s, a, r, s', \text{done}, \mathcal{M}(s') \rangle$.
- **Exploration:** Masked $\epsilon$-greedy decaying from $1.0$ to $0.05$ with factor $0.992$.
- **Target Masking:** Target Bellman calculation masks invalid actions in $s'$:
  $$y = r + \gamma \max_{a' \in \text{valid}} Q_{\text{target}}(s', a')$$
