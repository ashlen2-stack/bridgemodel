import streamlit as st
import pandas as pd
from datetime import date

from model import simulate_network, GOOD, FAIR, POOR, CLOSED

st.set_page_config(
    page_title="Bridge Network Strategy Simulator",
    layout="wide",
)

# --- Custom CSS ---
st.markdown(
    """
    <style>
    .middle-container {
        background-color: #f2f2f2;
        padding: 20px;
        border-radius: 10px;
    }
    div.stButton > button:first-child {
        background-color: #fa8072;
        color: white;
        border-radius: 6px;
        border: none;
        padding: 0.5rem 1.5rem;
        font-weight: 600;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

def fmt_pct(x):
    return f"{x*100:.1f}%"

def fmt_num(x):
    return f"{x:,.0f}"

left_col, middle_col, right_col = st.columns([1.2, 2.0, 1.2])

# --- LEFT COLUMN ---
with left_col:
    today = date.today().strftime("%B %d, %Y")

    st.markdown(
        """
        ## Bridge Network Strategy Simulator

        Washington’s bridge network includes more than 56 million square feet of deck area, much of it aging and increasingly expensive to maintain. Recent closures — including the Carbon River Bridge on SR 165 and the Wishkah River Bridge in Aberdeen — highlight the consequences of deferred preservation and the growing challenge of prioritizing limited maintenance dollars.

        This simulator provides a system‑level view of how different preservation and replacement strategies influence long‑term bridge conditions under constrained budgets. It is not designed to predict the future of any specific structure. Instead, it illustrates how funding levels, prioritization rules, and preservation timing shape statewide outcomes over time.

        Users can adjust key parameters, explore alternative strategies, and compare the long‑term implications of preventive versus reactive investment approaches. The goal is to support decision‑makers by making the tradeoffs between strategies visible, intuitive, and grounded in the structure of Washington’s bridge network.
        """
    )

    st.markdown(
        f"""
        **Developed by:** Ashley Carle, WSDOT Fellow  
        **Published:** {today}  
        **Data Used:** WSDOT Bridge Inventory & Condition Data (2024)
        """
    )

# --- MIDDLE COLUMN ---
with middle_col:
    st.markdown('<div class="middle-container">', unsafe_allow_html=True)

    st.subheader("Model Inputs & Strategy Selection")

    # Essential sliders only
    annual_budget_m = st.slider(
        "Annual Budget (million $)",
        min_value=50,
        max_value=400,
        value=150,
        step=10,
    )
    annual_budget = annual_budget_m * 1_000_000

    avg_deck_area = st.slider(
        "Average Deck Area per Bridge (ft²)",
        min_value=5_000,
        max_value=40_000,
        value=20_000,
        step=1_000,
    )

    # Hard-coded model parameters
    pres_cost = 30
    repl_cost = 400

    init_good = 15_000_000
    init_fair = 30_000_000
    init_poor = 5_000_000

    det_good_to_fair = 0.02
    det_fair_to_poor = 0.03
    det_poor_to_closed = 0.02

    # Summary tables
    st.markdown("### Initial Condition Summary")
    st.table(pd.DataFrame({
        "Condition": ["Good", "Fair", "Poor"],
        "Deck Area (ft²)": [init_good, init_fair, init_poor]
    }))

    st.markdown("### Cost Parameters")
    st.table(pd.DataFrame({
        "Cost Type": ["Preservation Cost", "Replacement Cost"],
        "Value": [f"${pres_cost}/ft²", f"${repl_cost}/ft²"]
    }))

    st.markdown("### Deterioration Rates")
    st.table(pd.DataFrame({
        "Transition": ["Good → Fair", "Fair → Poor", "Poor → Closed"],
        "Annual Rate": [
            f"{det_good_to_fair*100:.1f}%",
            f"{det_fair_to_poor*100:.1f}%",
            f"{det_poor_to_closed*100:.1f}%"
        ]
    }))

    st.markdown("---")

    strategy_label_to_key = {
        "Rehab Fair Condition First": "fair_first",
        "Rehab Poor Condition First": "poor_first",
        "Replace Closed Bridges First": "replace_closed_first",
        "Balanced Strategy (50/50)": "balanced",
    }

    strategy_label = st.selectbox(
        "Select Strategy",
        options=list(strategy_label_to_key.keys()),
        index=0,
    )
    strategy_key = strategy_label_to_key[strategy_label]

    run_col1, run_col2, run_col3 = st.columns([1, 1, 1])
    with run_col2:
        run = st.button("Run Model")

    st.markdown("---")

    if run:
        df, closed_series, stats = simulate_network(
            years=30,
            strategy=strategy_key,
            annual_budget=annual_budget,
            pres_cost=pres_cost,
            repl_cost=repl_cost,
            init_good=init_good,
            init_fair=init_fair,
            init_poor=init_poor,
            det_good_to_fair=det_good_to_fair,
            det_fair_to_poor=det_fair_to_poor,
            det_poor_to_closed=det_poor_to_closed,
        )

        st.subheader("Condition Trajectories Over Time")
        st.line_chart(df[[GOOD, FAIR, POOR, CLOSED]])

        st.markdown("**Summary at End of Horizon**")
        st.table(pd.DataFrame({
            "Condition": ["Good", "Fair", "Poor", "Closed"],
            "Share of Deck Area": [
                fmt_pct(stats["final_share_good"]),
                fmt_pct(stats["final_share_fair"]),
                fmt_pct(stats["final_share_poor"]),
                fmt_pct(stats["final_share_closed"]),
            ],
        }))

        st.markdown(
            f"**Total Deck Area Preserved:** {fmt_num(stats['total_preserved'])} ft²  \n"
            f"**Total Deck Area Replaced:** {fmt_num(stats['total_replaced'])} ft²"
        )

        st.markdown("---")
        st.subheader("Closed Bridges Over Time")
        st.line_chart(pd.DataFrame({"Closed": closed_series}))

        st.markdown("**Closed Bridges Summary**")
        st.table(pd.DataFrame({
            "Metric": [
                "Closed at Year 0",
                "Closed at Year 10",
                "Closed at Year 20",
                "Peak Closed",
                "Year of Peak Closed",
            ],
            "Value": [
                fmt_num(stats["closed_year_0"]),
                fmt_num(stats["closed_year_10"]),
                fmt_num(stats["closed_year_20"]),
                fmt_num(stats["peak_closed"]),
                stats["year_peak_closed"],
            ],
        }))

    st.markdown("</div>", unsafe_allow_html=True)

# --- RIGHT COLUMN ---
with right_col:
    st.subheader("Policy Strategies")

    st.markdown(
        """
        **Rehab Fair Condition First**  
        Prioritizes preserving Fair bridges to prevent deterioration into Poor condition. This strategy reflects WSDOT’s current preservation philosophy and supports the statewide goal of maintaining at least 90% of bridges in Fair or better condition.
        """
    )

    st.markdown(
        """
        **Rehab Poor Condition First**  
        Allocates funding to Poor bridges before preserving Fair bridges. This reactive strategy focuses on the worst‑condition structures but may allow Fair bridges to deteriorate if budgets are limited.
        """
    )

    st.markdown(
        """
        **Replace Closed Bridges First**  
        Directs funding first toward replacing Closed bridges, then Poor bridges, and finally preserving Fair bridges. This strategy highlights the long‑term cost of allowing closures to accumulate.
        """
    )

    st.markdown(
        """
        **Balanced Strategy (50/50)**  
        Splits the annual budget evenly between preserving Fair bridges and replacing Closed/Poor bridges. Half of the budget is dedicated to Fair preservation; the other half is used to replace Closed bridges first, then Poor bridges.
        """
    )
