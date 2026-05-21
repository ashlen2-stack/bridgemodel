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

    move_gf = det_good_to_fair * state[GOOD]
    new_state[GOOD] -= move_gf
    new_state[FAIR] += move_gf

    move_fp = det_fair_to_poor * state[FAIR]
    new_state[FAIR] -= move_fp
    new_state[POOR] += move_fp

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

    # flows
    flow_det_gf = []
    flow_det_fp = []
    flow_det_pc = []

    flow_pres_fair = []
    flow_pres_poor = []

    flow_repl_closed = []

    for year in range(1, years + 1):

        # default zero flows this year
        preserved_fair = 0.0
        preserved_poor = 0.0
        replaced_closed = 0.0

        # deterioration FIRST
        prev_state = state.copy()
        state = simulate_deterioration(
            state,
            det_good_to_fair,
            det_fair_to_poor,
            det_poor_to_closed,
        )

        flow_det_gf.append(state[FAIR] - prev_state[FAIR])
        flow_det_fp.append(state[POOR] - prev_state[POOR])
        flow_det_pc.append(state[CLOSED] - prev_state[CLOSED])

        budget = annual_budget

        # ---------- STRATEGIES ----------

        if strategy == "fair_first":
            # 1) preserve fair
            state, budget, preserved = apply_preservation_fair(state, budget, pres_cost)
            preserved_fair = preserved
            total_preserved += preserved

            # 2) preserve poor
            state, budget, rehabbed = apply_rehab_poor(state, budget, pres_cost)
            preserved_poor = rehabbed
            total_preserved += rehabbed

            # 3) replace closed if budget remains
            state, budget, repl_closed = apply_replace_closed(state, budget, repl_cost)
            replaced_closed = repl_closed
            total_replaced += repl_closed

        elif strategy == "poor_first":
            # 1) preserve poor
            state, budget, rehabbed = apply_rehab_poor(state, budget, pres_cost)
            preserved_poor = rehabbed
            total_preserved += rehabbed

            # 2) preserve fair
            state, budget, preserved = apply_preservation_fair(state, budget, pres_cost)
            preserved_fair = preserved
            total_preserved += preserved

            # 3) replace closed if budget remains
            state, budget, repl_closed = apply_replace_closed(state, budget, repl_cost)
            replaced_closed = repl_closed
            total_replaced += repl_closed

        elif strategy == "replace_closed_first":
            # 1) replace closed
            state, budget, repl_closed = apply_replace_closed(state, budget, repl_cost)
            replaced_closed = repl_closed
            total_replaced += repl_closed

            # 2) preserve fair
            state, budget, preserved = apply_preservation_fair(state, budget, pres_cost)
            preserved_fair = preserved
            total_preserved += preserved

            # 3) preserve poor
            state, budget, rehabbed = apply_rehab_poor(state, budget, pres_cost)
            preserved_poor = rehabbed
            total_preserved += rehabbed

        elif strategy == "balanced":
            # split budget: preservation vs replacement
            replacement_share = max(0.0, min(1.0, replacement_share))
            pres_budget = budget * (1 - replacement_share)
            repl_budget = budget * replacement_share

            # preservation side: fair -> poor
            state, pres_budget, preserved = apply_preservation_fair(
                state, pres_budget, pres_cost
            )
            preserved_fair = preserved
            total_preserved += preserved

            state, pres_budget, rehabbed = apply_rehab_poor(
                state, pres_budget, pres_cost
            )
            preserved_poor = rehabbed
            total_preserved += rehabbed

            # replacement side: closed only
            state, repl_budget, repl_closed = apply_replace_closed(
                state, repl_budget, repl_cost
            )
            replaced_closed = repl_closed
            total_replaced += repl_closed

        # record flows
        flow_pres_fair.append(preserved_fair)
        flow_pres_poor.append(preserved_poor)
        flow_repl_closed.append(replaced_closed)

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

    flows = {
        "det_gf": flow_det_gf,
        "det_fp": flow_det_fp,
        "det_pc": flow_det_pc,
        "pres_fair": flow_pres_fair,
        "pres_poor": flow_pres_poor,
        "repl_closed": flow_repl_closed,
    }

    return df, closed_series, stats, flows

