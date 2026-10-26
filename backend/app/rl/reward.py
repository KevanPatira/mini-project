"""
Configurable Multi-Objective Reward Function for the Tourism MDP.

Balances interest relevance, thematic diversity, travel duration,
crowd pressure, financial cost, and carbon emissions.
Prioritizes budget adherence over emissions reduction.
"""

from typing import Dict, List, Set, Any, Optional
import numpy as np

from app.sustainability.scoring import compute_preference_score


class ItineraryRewardCalculator:
    """
    Computes normalized step and episodic rewards.
    
    Default Weights:
    - w_preference (0.40): User interest category alignment
    - w_diversity (0.15): Marginal contribution to itinerary category breadth
    - w_travel_time (0.15): Normalized leg transit duration penalty
    - w_crowding (0.10): Macro-level overtourism / crowding pressure penalty
    - w_budget (0.12): Marginal monetary cost penalty (transit + entry fee)
    - w_emissions (0.08): Carbon emissions penalty (lower relative weight than budget)
    
    Constraint Invariant: w_budget (0.12) > w_emissions (0.08).
    """

    def __init__(
        self,
        w_preference: float = 0.40,
        w_diversity: float = 0.15,
        w_travel_time: float = 0.15,
        w_crowding: float = 0.10,
        w_budget: float = 0.12,
        w_emissions: float = 0.08,
    ):
        self.w_p = w_preference
        self.w_v = w_diversity
        self.w_t = w_travel_time
        self.w_c = w_crowding
        self.w_b = w_budget
        self.w_e = w_emissions

        # Normalization scale reference anchors (Rajasthan intercity realistic bounds)
        self.MAX_LEG_HOURS = 6.0       # Max expected driving time between consecutive sites
        self.MAX_LEG_COST_INR = 2500.0 # Upper bound for intercity transit leg + monument entry
        self.MAX_LEG_EMISSIONS = 80.0  # Max expected leg transit emissions in kg CO2e
        self.MAX_VISITOR_COUNT = 5000000.0 # 5 million annual visitors (e.g. Amber Palace)

    def compute_step_reward(
        self,
        attraction: Dict[str, Any],
        user_interests: List[str],
        travel_hours: float,
        leg_cost_inr: float,
        leg_emissions_kg: float,
        current_visited_categories: Set[str],
        is_terminal_stop_action: bool = False,
        stops_count: int = 0,
        min_stops_target: int = 3,
    ) -> Dict[str, float]:
        """
        Compute normalized multi-objective step reward R_t.
        Returns total scalar reward and component breakdown dictionary.
        """
        if is_terminal_stop_action:
            # Terminal stop bonus/penalty based on itinerary completeness
            if stops_count < min_stops_target:
                # Slight penalty for premature termination
                completion_penalty = -0.3 * (min_stops_target - stops_count)
                return {"total": completion_penalty, "components": {"completion_penalty": completion_penalty}}
            else:
                completion_bonus = 0.2
                return {"total": completion_bonus, "components": {"completion_bonus": completion_bonus}}

        # 1. Preference Relevance P_t in [0, 1]
        p_score = compute_preference_score(attraction.get("categories", []), user_interests)

        # 2. Diversity Contribution V_t in [0, 1]
        # Measures fraction of attraction's categories that are newly introduced to the itinerary
        att_cats = set(attraction.get("categories", []))
        if att_cats:
            new_cats = att_cats - current_visited_categories
            v_score = len(new_cats) / len(att_cats)
        else:
            v_score = 0.0

        # 3. Travel Time Penalty T_t in [0, 1]
        t_penalty = min(travel_hours / self.MAX_LEG_HOURS, 1.0)

        # 4. Crowd / Popularity Pressure Penalty C_t in [0, 1]
        # Uses annual visitor count as macro-popularity proxy
        visitors = attraction.get("annual_visitors")
        if visitors and visitors > 0:
            c_penalty = min(float(visitors) / self.MAX_VISITOR_COUNT, 1.0)
        else:
            c_penalty = 0.2  # Moderate default for lesser-known attractions

        # 5. Budget / Cost Penalty B_t in [0, 1]
        b_penalty = min(leg_cost_inr / self.MAX_LEG_COST_INR, 1.0)

        # 6. Carbon Emissions Penalty E_t in [0, 1]
        e_penalty = min(leg_emissions_kg / self.MAX_LEG_EMISSIONS, 1.0)

        # Multi-objective composite step reward
        total_reward = (
            self.w_p * p_score
            + self.w_v * v_score
            - self.w_t * t_penalty
            - self.w_c * c_penalty
            - self.w_b * b_penalty
            - self.w_e * e_penalty
        )

        return {
            "total": float(total_reward),
            "components": {
                "preference_reward": float(self.w_p * p_score),
                "diversity_reward": float(self.w_v * v_score),
                "travel_time_penalty": float(-self.w_t * t_penalty),
                "crowding_penalty": float(-self.w_c * c_penalty),
                "budget_penalty": float(-self.w_b * b_penalty),
                "emissions_penalty": float(-self.w_e * e_penalty),
            },
        }
