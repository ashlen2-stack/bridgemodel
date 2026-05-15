import numpy as np
import pandas as pd

GOOD = "Good"
FAIR = "Fair"
POOR = "Poor"
CLOSED = "Closed"

STATE_ORDER = [GOOD, FAIR, POOR, CLOSED]


def initialize_state(years: int):
    idx = pd.Index(range(years + 1), name="Year")
    df = pd.DataFrame(0.0, index=idx, columns=STATE_ORDER)
    return df


def simulate_deterioration(state, det_good_to_fair, det_fair_to_poor, det_poor_to_closed):
    new_state = state.copy()

    # Good → Fair
    move_gf = det_good_to_fair * state[GOOD]
    new_state[GOOD] -= move_gf
    new_state[FAIR] += move_gf

    # Fair → Poor
    move_fp = det_fair_to_poor * state[FAIR]
    new_state[FAIR] -= move_fp
    new_state[POOR] += move_fp

    # Poor → Closed
    move_pc = det_poor_to_closed * state[POOR]
    new_state[POOR] -= move_pc
    new_state[CLOSED] += move_pc

    return new_state


def apply_preservation_fair(state, budget, cost_per_ft2):
    if budget <= 0 or state[FAIR] <= 0:
        return state, budget, 0.0

    max_area = budget / cost_per_ft2
    treat_area = min(max_area, state[FAIR])

    state = state.copy()
    state[FAIR] -= treat_area
    state[GOOD] += treat_area

    spent = treat_area * cost_per_ft2
    return state, budget - spent, treat_area


def apply_rehab_poor(state, budget, cost_per_ft2):
    if budget <= 0 or state[POOR] <= 0:
        return state, budget, 0.0

    max_area = budget / cost_per_ft2
    treat_area = min(max_area, state[POOR])

    state = state.copy()
    state[POOR] -= treat_area
    state[FAIR] += treat_area

    spent = treat_area * cost_per_ft2
    return state, budget - spent, treat_area


def apply_replace_poor(state, budget, cost_per_ft2):
    if budget <= 0 or state[POOR] <= 0:
        return state, budget, 0.0

    max_area = budget / cost_per_ft2
    treat_area = min(max_area, state[POOR])

    state = state.copy()
    state[POOR] -= treat_area
    state[GOOD] += treat_area

    spent = treat_area * cost_per_ft2
    return state, budget - spent, treat_area


def apply_replace_closed(state, budget, cost_per_ft2):
    if budget <= 0 or state[CLOSED] <= 0:
        return state, budget, 0.0

    max_area = budget / cost_per_ft2
    treat_area = min(max_area, state[CLOSED])

    state = state.copy()
    state[CLOSED] -= treat_area
    state[GOOD] += treat_area

    spent = treat_area * cost_per_ft2
    return state, budget - spent, treat_area


def simulate_network(
    years: int,
    strategy: str,
    annual_budget: float,
    pres_cost: float,
    repl_cost: float,
    init_good: float,
    init_fair: float,
    init_poor: float,
    init_closed: float,
    det_good_to_fair: float,
    det_fair_to_poor: float,
    det_poor_to_closed: float,
    replacement_share: float,
):
    state = {
        GOOD: init_good,
        FAIR: init_fair,
        POOR: init_poor,
        CLOSED: init_closed,
    }

    df = initialize_state(years)
    df.loc[0, :] = [state[s] for s in STATE_ORDER]

    total_preserved = 0.0
    total_replaced = 0.0

    for year in range(1, years + 1):
        # Deterioration
        state = simulate_deterioration(
            state,
            det_good_to_fair,
            det_fair_to_poor,
            det_poor_to_closed,
        )

        budget = annual_budget

        if strategy == "fair_first":
            state, budget, preserved = apply_preservation_fair(state, budget, pres_cost)
            total_preserved += preserved

            state, budget, replaced = apply_replace_poor(state, budget, repl_cost)
            total_replaced += replaced

        elif strategy == "poor_first":
            state, budget, rehabbed = apply_rehab_poor(state, budget, pres_cost)
            total_preserved += rehabbed

            state, budget, preserved = apply_preservation_fair(state, budget, pres_cost)
            total_preserved += preserved

            state, budget, replaced = apply_replace_poor(state, budget, repl_cost)
            total_replaced += replaced

        elif strategy == "replace_closed_first":
            state, budget, repl_closed = apply_replace_closed(state, budget, repl_cost)
            total_replaced += repl_closed

            state, budget, repl_poor = apply_replace_poor(state, budget, repl_cost)
            total_replaced += repl_poor

            state, budget, preserved = apply_preservation_fair(state, budget, pres_cost)
            total_preserved += preserved

        elif strategy == "balanced":
            replacement_share = max(0.0, min(1.0, replacement_share))
            pres_budget = budget * (1 - replacement_share)
            repl_budget = budget * replacement_share

            state, pres_budget, preserved = apply_preservation_fair(
                state, pres_budget, pres_cost
            )
            total_preserved += preserved

            state, repl_budget, repl_closed = apply_replace_closed(
                state, repl_budget, repl_cost
            )
            total_replaced += repl_closed

            state, repl_budget, repl_poor = apply_replace_poor(
                state, repl_budget, repl_cost
            )
            total_replaced += repl_poor

        df.loc[year, :] = [state[s] for s in STATE_ORDER]

    closed_series = df[CLOSED].copy()

    final_total = df.loc[years, STATE_ORDER].sum()
    final_shares = df.loc[years, STATE_ORDER] / final_total if final_total > 0 else 0

    stats = {
        "final_share_good": final_shares.get(GOOD, 0.0),
        "final_share_fair": final_shares.get(FAIR, 0.0),
        "final_share_poor": final_shares.get(POOR, 0.0),
        "final_share_closed": final_shares.get(CLOSED, 0.0),
        "total_preserved": total_preserved,
        "total_replaced": total_replaced,
        "closed_year_0": closed_series.iloc[0],
        "closed_year_10": closed_series.iloc[min(10, years)],
        "closed_year_20": closed_series.iloc[min(20, years)],
        "peak_closed": closed_series.max(),
        "year_peak_closed": closed_series.idxmax(),
    }

    return df, closed_series, stats
