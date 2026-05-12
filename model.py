import numpy as np
import pandas as pd

def run_model(
    years=50,
    dt=1,
    Preservation_Budget=150_000_000,
    Replacement_Share=0.10,
    Rehab_Share_Poor=0.50,   # % of preservation budget for Poor→Fair
    Rehab_Share_Fair=0.50,   # % of preservation budget for Fair→Good
    Avg_Deck_Area=12000,
    UCRehabPtoF=155,         # rehab cost per ft2
    UCRehabFtoG=125,
    UCReplacementPtoG=2500,
    UCReplacementCtoG=2500,
    scenario="poor_first"
):

    # deterioration durations
    Dur_GtoF = 35
    Dur_FtoP = 58
    Dur_PtoC = 54

    # initial stocks (bridges)
    Good = 20425507 / Avg_Deck_Area
    Fair = 30359189 / Avg_Deck_Area
    Poor = 5341995 / Avg_Deck_Area
    Closed = 31292 / Avg_Deck_Area

    results = []

    for t in range(years):

        # deterioration flows
        GtoF = Good / Dur_GtoF
        FtoP = Fair / Dur_FtoP
        Closure = Poor / Dur_PtoC

        # budgets
        Replacement_Budget = Replacement_Share * Preservation_Budget
        Rehab_Budget = (1 - Replacement_Share) * Preservation_Budget

        # rehab budget allocation
        if scenario == "poor_first":
            RehabPtoF_Budget = Rehab_Budget * 0.7
            RehabFtoG_Budget = Rehab_Budget * 0.3
        elif scenario == "fair_first":
            RehabPtoF_Budget = Rehab_Budget * 0.3
            RehabFtoG_Budget = Rehab_Budget * 0.7
        else:
            RehabPtoF_Budget = Rehab_Budget * 0.5
            RehabFtoG_Budget = Rehab_Budget * 0.5

        # rehab flows (area → bridges)
        RehabArea_PtoF = RehabPtoF_Budget / UCRehabPtoF
        RehabPtoF = RehabArea_PtoF / Avg_Deck_Area

        RehabArea_FtoG = RehabFtoG_Budget / UCRehabFtoG
        RehabFtoG = RehabArea_FtoG / Avg_Deck_Area

        # replacement flows
        ReplacementArea_PtoG = Replacement_Budget * 0.5 / UCReplacementPtoG
        ReplacementPtoG = ReplacementArea_PtoG / Avg_Deck_Area

        ReplacementArea_CtoG = Replacement_Budget * 0.5 / UCReplacementCtoG
        ReplacementCtoG = ReplacementArea_CtoG / Avg_Deck_Area

        # stock updates
        Good = Good + (RehabFtoG + ReplacementPtoG + ReplacementCtoG - GtoF) * dt
        Fair = Fair + (GtoF - FtoP + RehabPtoF - RehabFtoG) * dt
        Poor = Poor + (FtoP - RehabPtoF - ReplacementPtoG - Closure) * dt
        Closed = Closed + (Closure - ReplacementCtoG) * dt

        results.append({
            "year": t,
            "Good": Good,
            "Fair": Fair,
            "Poor": Poor,
            "Closed": Closed
        })

    return pd.DataFrame(results)
