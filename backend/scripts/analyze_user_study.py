#!/usr/bin/env python3
"""
AuraTour: Reproducible Statistical Analysis Pipeline for User Study Responses.

Loads validated user-study responses, applies pre-registered exclusion criteria,
computes descriptive distributions and non-parametric paired inferential statistics
(Wilcoxon Signed-Rank Test, Cliff's Delta, Rank-Biserial Correlation, Bootstrap 95% CIs),
and produces publication-quality charts and CSV/JSON summary outputs.

Author: AuraTour Research Team
"""

import os
import sys
import json
import argparse
import numpy as np
import pandas as pd
from scipy import stats
import matplotlib.pyplot as plt
import seaborn as sns

# Set publication style
plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
plt.rcParams.update({
    "font.sans-serif": "DejaVu Sans",
    "font.size": 11,
    "axes.labelsize": 12,
    "axes.titlesize": 13,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "legend.fontsize": 10,
    "figure.titlesize": 14,
    "figure.dpi": 300,
})

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DEFAULT_INPUT_FILE = os.path.join(BASE_DIR, "data", "results", "user_study_responses.json")
SUMMARY_CSV_FILE = os.path.join(BASE_DIR, "data", "results", "user_study_summary.csv")
STATS_JSON_FILE = os.path.join(BASE_DIR, "data", "results", "user_study_stats.json")
FIGURES_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "docs", "figures"))

DIMENSIONS = [
    ("relevance", "Interest Relevance"),
    ("perceived_sustainability", "Perceived Sustainability"),
    ("usefulness", "Practical Usefulness"),
    ("trust", "Trust & Credibility"),
    ("feasibility", "Itinerary Feasibility"),
    ("willingness_to_visit", "Willingness to Visit"),
]


def load_and_filter_responses(file_path: str):
    """
    Load raw response records and apply pre-registered exclusion criteria:
    1. Consent must be explicitly granted (consent_given == True).
    2. All 6 Likert items must be completed for both systems.
    3. Automated test entries (participant_id starting with 'test_') are isolated.
    4. Duplicate participant submissions for the same persona are excluded.
    """
    if not os.path.exists(file_path):
        return [], {"total_raw": 0, "excluded_missing_consent": 0, "excluded_incomplete": 0, "excluded_test_ids": 0, "excluded_duplicates": 0, "valid_count": 0}

    with open(file_path, "r", encoding="utf-8") as f:
        try:
            records = json.load(f)
        except Exception as e:
            print(f"[Error] Failed to read JSON from {file_path}: {e}")
            return [], {}

    total_raw = len(records)
    valid_records = []
    seen_pairs = set()

    counts = {
        "total_raw": total_raw,
        "excluded_missing_consent": 0,
        "excluded_incomplete": 0,
        "excluded_test_ids": 0,
        "excluded_duplicates": 0,
        "valid_count": 0,
    }

    dim_keys = [d[0] for d in DIMENSIONS]

    for r in records:
        # Exclusion 1: Consent
        if not r.get("consent_given", False):
            counts["excluded_missing_consent"] += 1
            continue

        # Exclusion 2: Test IDs
        pid = r.get("participant_id", "")
        if pid.startswith("test_"):
            counts["excluded_test_ids"] += 1
            continue

        # Exclusion 3: Incomplete ratings
        ratings_a = r.get("ratings_system_a", {})
        ratings_b = r.get("ratings_system_b", {})
        if not all(k in ratings_a and ratings_a[k] is not None for k in dim_keys) or \
           not all(k in ratings_b and ratings_b[k] is not None for k in dim_keys):
            counts["excluded_incomplete"] += 1
            continue

        # Exclusion 4: Duplicate submissions
        persona = r.get("persona_id", "").upper()
        pair_key = (pid, persona)
        if pair_key in seen_pairs:
            counts["excluded_duplicates"] += 1
            continue
        seen_pairs.add(pair_key)

        valid_records.append(r)

    counts["valid_count"] = len(valid_records)
    return valid_records, counts


def compute_cliffs_delta(x, y):
    """
    Compute Cliff's Delta non-parametric effect size:
    delta = #(x_i > y_j) - #(x_i < y_j) / (n_x * n_y)
    """
    n_x, n_y = len(x), len(y)
    if n_x == 0 or n_y == 0:
        return 0.0
    greater = 0
    less = 0
    for i in x:
        for j in y:
            if i > j:
                greater += 1
            elif i < j:
                less += 1
    return (greater - less) / (n_x * n_y)


def compute_bootstrap_ci(diffs, n_bootstraps=1000, ci=0.95):
    """Compute bootstrap percentile confidence interval for mean paired difference."""
    if len(diffs) < 3:
        return (float(np.mean(diffs)), float(np.mean(diffs)))
    boot_means = []
    rng = np.random.default_rng(42)
    for _ in range(n_bootstraps):
        sample = rng.choice(diffs, size=len(diffs), replace=True)
        boot_means.append(np.mean(sample))
    lower = np.percentile(boot_means, (1 - ci) / 2 * 100)
    upper = np.percentile(boot_means, (1 + ci) / 2 * 100)
    return (float(lower), float(upper))


def run_power_analysis(effect_size=0.55, alpha=0.05, n_range=range(10, 85, 5)):
    """
    Conduct exact power analysis for two-tailed Wilcoxon signed-rank test
    across sample sizes N=10 to 80 under anticipated effect size d_z=0.55.
    Uses normal approximation with Wilcoxon variance.
    """
    power_curve = []
    for n in n_range:
        # Standardized Wilcoxon mean and variance under H0
        # W has mean = n*(n+1)/4, var = n*(n+1)*(2n+1)/24
        # Under H1 with effect size delta / std = d_z
        # Asymptotic relative efficiency compared to paired t-test is >= 0.864 (typically ~0.955 for logistic)
        crit_z = stats.norm.ppf(1 - alpha / 2)
        shift = effect_size * np.sqrt(n * 0.955)
        # Power = P(Z > crit_z - shift) + P(Z < -crit_z - shift)
        power = 1 - stats.norm.cdf(crit_z - shift) + stats.norm.cdf(-crit_z - shift)
        power_curve.append({"n": n, "power": float(power)})
    return power_curve


def generate_power_chart(power_curve, output_dir):
    """Plot publication-quality statistical power curve."""
    os.makedirs(output_dir, exist_ok=True)
    fig, ax = plt.subplots(figsize=(7, 4.5), dpi=300)

    ns = [p["n"] for p in power_curve]
    powers = [p["power"] for p in power_curve]

    ax.plot(ns, powers, marker="o", color="#10b981", linewidth=2.2, label=r"Wilcoxon Signed-Rank ($d_z = 0.55, \alpha = 0.05$)")
    ax.axhline(0.80, color="#ef4444", linestyle="--", linewidth=1.5, label="Standard Power Threshold (80%)")
    ax.axvline(35, color="#3b82f6", linestyle=":", linewidth=1.5, label="Target Sample Window (N = 35–50)")

    ax.set_xlabel("Sample Size ($N$ Paired Participants)", fontweight="bold")
    ax.set_ylabel("Statistical Power ($1 - \\beta$)", fontweight="bold")
    ax.set_title("AuraTour Study: Statistical Power vs. Participant Cohort Size", fontweight="bold", pad=12)
    ax.set_ylim(0.2, 1.02)
    ax.set_xlim(8, 82)
    ax.legend(loc="lower right", frameon=True)
    plt.tight_layout()

    out_file = os.path.join(output_dir, "fig3_study_power_curve.png")
    fig.savefig(out_file)
    plt.close(fig)
    print(f"[Figure] Saved power analysis curve to {out_file}")


def generate_study_charts(df_pairs, preferred_dist, output_dir):
    """Plot publication-quality dimension comparison and preference distribution charts."""
    os.makedirs(output_dir, exist_ok=True)

    # 1. Dimension Comparison Boxplot
    fig, ax = plt.subplots(figsize=(10, 5.5), dpi=300)

    plot_rows = []
    for _, row in df_pairs.iterrows():
        dim = row["dimension"]
        dim_label = dict(DIMENSIONS).get(dim, dim)
        plot_rows.append({"Dimension": dim_label, "Score": row["c1_score"], "Condition": "C1 Baseline"})
        plot_rows.append({"Dimension": dim_label, "Score": row["c5_score"], "Condition": "C5 Multi-Criteria"})

    df_plot = pd.DataFrame(plot_rows)

    palette = {"C1 Baseline": "#94a3b8", "C5 Multi-Criteria": "#10b981"}
    sns.boxplot(
        data=df_plot,
        x="Dimension",
        y="Score",
        hue="Condition",
        palette=palette,
        ax=ax,
        width=0.55,
        boxprops=dict(alpha=0.85),
    )
    ax.set_ylabel("Likert Rating (1–5)", fontweight="bold")
    ax.set_xlabel("Evaluation Dimension", fontweight="bold")
    ax.set_title("Human Participant Evaluation: C1 Baseline vs. C5 Multi-Criteria", fontweight="bold", pad=12)
    ax.set_ylim(0.8, 5.2)
    plt.xticks(rotation=15, ha="right")
    ax.legend(title="Algorithm Condition", frameon=True)
    plt.tight_layout()

    out_dim = os.path.join(output_dir, "fig1_study_dimension_comparison.png")
    fig.savefig(out_dim)
    plt.close(fig)
    print(f"[Figure] Saved dimension comparison plot to {out_dim}")

    # 2. Preference Distribution Bar
    fig, ax = plt.subplots(figsize=(6, 4.2), dpi=300)
    labels = list(preferred_dist.keys())
    counts = [preferred_dist[k] for k in labels]
    colors = ["#10b981" if "C5" in l else ("#94a3b8" if "C1" in l else "#f59e0b") for l in labels]

    bars = ax.bar(labels, counts, color=colors, width=0.5, edgecolor="none", alpha=0.9)
    for bar in bars:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, h + 0.1, f"{int(h)}", ha="center", va="bottom", fontweight="bold")

    ax.set_ylabel("Number of Participants", fontweight="bold")
    ax.set_title("Overall Preferred System (Forced-Choice)", fontweight="bold", pad=12)
    ax.set_ylim(0, max(counts) * 1.25 if counts and max(counts) > 0 else 5)
    plt.tight_layout()

    out_pref = os.path.join(output_dir, "fig2_study_preference_distribution.png")
    fig.savefig(out_pref)
    plt.close(fig)
    print(f"[Figure] Saved preference distribution plot to {out_pref}")


def analyze(input_file: str, generate_figures: bool = True):
    print("=" * 72)
    print("AuraTour: User Study Statistical Analysis Pipeline")
    print(f"Data Source: {input_file}")
    print("=" * 72)

    records, audit_counts = load_and_filter_responses(input_file)

    print("\n[Data Audit & Participant Intake Status]")
    print(f"• Total Raw Submissions Received: {audit_counts.get('total_raw', 0)}")
    print(f"• Excluded (Missing Consent):      {audit_counts.get('excluded_missing_consent', 0)}")
    print(f"• Excluded (Incomplete Ratings):   {audit_counts.get('excluded_incomplete', 0)}")
    print(f"• Excluded (Automated Test IDs):   {audit_counts.get('excluded_test_ids', 0)}")
    print(f"• Excluded (Duplicate Submissions):{audit_counts.get('excluded_duplicates', 0)}")
    print(f"• Validated Human Participants:    {audit_counts.get('valid_count', 0)}")

    # Power analysis is always computed for research rigor
    power_curve = run_power_analysis()
    if generate_figures:
        generate_power_chart(power_curve, FIGURES_DIR)

    if audit_counts.get("valid_count", 0) == 0:
        print("\n[Notice] No validated human participant responses currently in the repository.")
        print("         The intake phase is open at http://localhost:5173/ ('User Study Survey').")
        print("         Generating pre-registered statistical analysis specification and power curve.")

        empty_summary = {
            "status": "intake_phase_active",
            "participant_count": 0,
            "target_cohort": "30-50",
            "exclusion_audit": audit_counts,
            "power_analysis": {
                "n_35_power": round(power_curve[5]["power"], 3),
                "n_50_power": round(power_curve[8]["power"], 3),
                "test": "Wilcoxon Signed-Rank Test (two-tailed)",
                "alpha": 0.05,
            },
        }

        with open(STATS_JSON_FILE, "w", encoding="utf-8") as f:
            json.dump(empty_summary, f, indent=2)

        # Empty CSV specification
        spec_df = pd.DataFrame([
            {"dimension": d[0], "dimension_label": d[1], "n": 0, "c1_mean": np.nan, "c5_mean": np.nan, "mean_diff": np.nan, "wilcoxon_w": np.nan, "p_value": np.nan, "cliffs_delta": np.nan, "boot_ci_95_lower": np.nan, "boot_ci_95_upper": np.nan}
            for d in DIMENSIONS
        ])
        spec_df.to_csv(SUMMARY_CSV_FILE, index=False)
        print(f"[Output] Created analysis template at {SUMMARY_CSV_FILE}")
        print(f"[Output] Created status summary at {STATS_JSON_FILE}")
        return empty_summary

    # Unpack paired records
    pair_rows = []
    preferred_counts = {"C5_full": 0, "C1_baseline": 0, "No preference": 0}

    for r in records:
        blinded_a = r["blinded_a_is"]  # "C1_baseline" or "C5_full"
        r_a = r["ratings_system_a"]
        r_b = r["ratings_system_b"]

        if blinded_a == "C1_baseline":
            c1_r, c5_r = r_a, r_b
        else:
            c1_r, c5_r = r_b, r_a

        pref = r.get("preferred_system")
        if pref == "System A":
            preferred_counts[blinded_a] += 1
        elif pref == "System B":
            other = "C5_full" if blinded_a == "C1_baseline" else "C1_baseline"
            preferred_counts[other] += 1
        else:
            preferred_counts["No preference"] += 1

        for d_key, _ in DIMENSIONS:
            if d_key in c1_r and d_key in c5_r:
                pair_rows.append({
                    "participant_id": r["participant_id"],
                    "persona_id": r["persona_id"],
                    "dimension": d_key,
                    "c1_score": int(c1_r[d_key]),
                    "c5_score": int(c5_r[d_key]),
                    "diff": int(c5_r[d_key]) - int(c1_r[d_key]),
                })

    df_pairs = pd.DataFrame(pair_rows)

    # Compute Statistical Tests for Each Dimension
    summary_rows = []
    stats_dict = {
        "status": "completed",
        "participant_count": audit_counts["valid_count"],
        "exclusion_audit": audit_counts,
        "preference_distribution": preferred_counts,
        "dimension_results": {},
    }

    print("\n" + "=" * 72)
    print("Item-Level Statistical Results (Paired Wilcoxon Signed-Rank Test)")
    print("=" * 72)
    print(f"{'Dimension':<26} {'C1 Mean(SD)':<14} {'C5 Mean(SD)':<14} {'Diff (95% CI)':<18} {'W':<6} {'p-value':<9} {'Cliff δ':<8}")
    print("-" * 95)

    for d_key, d_label in DIMENSIONS:
        subset = df_pairs[df_pairs["dimension"] == d_key]
        n_dim = len(subset)
        if n_dim == 0:
            continue

        c1_vals = subset["c1_score"].values
        c5_vals = subset["c5_score"].values
        diffs = subset["diff"].values

        c1_mean = np.mean(c1_vals)
        c1_sd = np.std(c1_vals, ddof=1) if n_dim > 1 else 0.0
        c5_mean = np.mean(c5_vals)
        c5_sd = np.std(c5_vals, ddof=1) if n_dim > 1 else 0.0
        mean_diff = np.mean(diffs)

        ci_lower, ci_upper = compute_bootstrap_ci(diffs)
        delta = compute_cliffs_delta(c5_vals, c1_vals)

        # Non-zero differences for Wilcoxon test
        non_zero = diffs[diffs != 0]
        if len(non_zero) >= 1:
            try:
                res = stats.wilcoxon(c5_vals, c1_vals, zero_method="pratt", alternative="two-sided")
                w_stat = float(res.statistic)
                p_val = float(res.pvalue)
            except Exception:
                w_stat = np.nan
                p_val = 1.0
        else:
            w_stat = 0.0
            p_val = 1.0

        p_str = f"{p_val:.4f}" if p_val >= 0.0001 else "< 0.0001"
        c1_str = f"{c1_mean:.2f} ({c1_sd:.2f})"
        c5_str = f"{c5_mean:.2f} ({c5_sd:.2f})"
        diff_str = f"{mean_diff:+.2f} [{ci_lower:.2f}, {ci_upper:.2f}]"

        print(f"{d_label:<26} {c1_str:<14} {c5_str:<14} {diff_str:<18} {w_stat:<6.1f} {p_str:<9} {delta:+.3f}")

        row = {
            "dimension": d_key,
            "dimension_label": d_label,
            "n": n_dim,
            "c1_mean": round(c1_mean, 3),
            "c1_sd": round(c1_sd, 3),
            "c5_mean": round(c5_mean, 3),
            "c5_sd": round(c5_sd, 3),
            "mean_diff": round(mean_diff, 3),
            "boot_ci_95_lower": round(ci_lower, 3),
            "boot_ci_95_upper": round(ci_upper, 3),
            "wilcoxon_w": round(w_stat, 2),
            "p_value": round(p_val, 5),
            "cliffs_delta": round(delta, 3),
        }
        summary_rows.append(row)
        stats_dict["dimension_results"][d_key] = row

    # Forced choice binomial test (C5 vs C1 excluding ties)
    k_c5 = preferred_counts["C5_full"]
    k_c1 = preferred_counts["C1_baseline"]
    decided = k_c5 + k_c1
    if decided > 0:
        binom_res = stats.binomtest(k_c5, decided, p=0.5, alternative="two-sided")
        stats_dict["binomial_test"] = {
            "c5_wins": k_c5,
            "c1_wins": k_c1,
            "decided_total": decided,
            "p_value": round(float(binom_res.pvalue), 5),
            "c5_proportion": round(k_c5 / decided, 3),
        }
        print("-" * 95)
        print(f"Forced Choice Preference: C5={k_c5}, C1={k_c1}, Ties={preferred_counts['No preference']}")
        print(f"Two-Tailed Binomial Test against H0 (p=0.50): p = {binom_res.pvalue:.4f}")
    else:
        stats_dict["binomial_test"] = None

    # Save summary files
    df_summary = pd.DataFrame(summary_rows)
    df_summary.to_csv(SUMMARY_CSV_FILE, index=False)
    print(f"\n[Saved] Statistical summary CSV -> {SUMMARY_CSV_FILE}")

    with open(STATS_JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(stats_dict, f, indent=2)
    print(f"[Saved] Full statistics JSON    -> {STATS_JSON_FILE}")

    if generate_figures:
        generate_study_charts(df_pairs, preferred_counts, FIGURES_DIR)

    return stats_dict


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyze AuraTour user study responses.")
    parser.add_argument("--input", default=DEFAULT_INPUT_FILE, help="Path to user_study_responses.json")
    parser.add_argument("--no-figures", action="store_true", help="Skip figure generation")
    args = parser.parse_args()

    analyze(args.input, generate_figures=not args.no_figures)
