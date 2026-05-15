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
    /* Middle column background */
    .middle-column {
        background-color: #f2f2f2;
        padding: 1.5rem;
        border-radius: 8px;
    }

    /* Center the Run Model button and color it salmon */
    div.stButton > button:first-child {
        background-color: #fa8072;
        color: white;
        border-radius: 6px;
        border: none;
        padding: 0.5rem 1.5rem;
        font-weight: 600;
    }

    /* Slider color override (green) */
    div[data-baseweb="slider"] > div > div {
        background-color: #2e8b57 !important;
    }
    div[data-baseweb="slider"] > div > div > div {
        background-color: #2e8b57 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# --- Helper for formatting numbers ---
def fmt_pct(x):
    return f"{x*100:.1f}%"


def fmt_num(x):
    return f"{x:,.0f}"


# --- Layout: three columns ---
left_col, middle_col, right_col = st.columns([1.2, 2.0, 1.2])

# --- LEFT COLUMN: Overview ---
with left_col:
    today = date.today().strftime("%B %d, %Y")

    st.markdown(
        """
        ## Bridge Network Strategy Simulator

        Washington’s bridge network includes more than 56 million square feet of deck area, much of it aging and increasingly expensive to maintain. Recent closures — including the Carbon River Bridge on SR 165 and the Wishkah River Bridge in Aberdeen — highlight the consequences of deferred preservation and the growing challenge of prioritizing limited maintenance dollars.

        This simulator provides a system‑level view of how different preservation and replacement strategies influence long‑term bridge conditions under constrained budgets. It is not designed to predict the future of any specific structure. Instead, it illustrates how funding levels, prioritization rules, and preservation timing shape statewide outcomes over time.

        Users can adjust key parameters, explore alternative strategies, and compare the long‑term implications of preventive versus reactive investment approaches. The goal is to support decision‑makers by making the tradeoffs between strategies visible, intuitive, and grounded in the structure of Washington’s bridge network.
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        **Developed by:** Ashley Carle, WSDOT Fellow  
        **Published:** {today}  
        **Data Used:** WSDOT Bridge Inventory & Condition Data (2024)
        """
    )

# --- MIDDLE COLUMN: sliders, strategy, charts ---
with middle_col:
    st.markdown('<div class="middle-column">', unsafe_allow_html=True)

    st.subheader("Model Inputs & Strategy Selection")

    # Sliders
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

    pres_cost = st.slider(
        "Preservation Cost per ft² ($)",
        min_value=10,
        max_value=80,
        value=30,
        step=5,
    )

    repl_cost = st.slider(
        "Replacement Cost per ft² ($)",
        min_value=150,
        max_value=800,
        value=400,
        step=25,
    )

    st.markdown("**Initial Condition Distribution (Deck Area, ft²)**")
    init_good = st.slider(
        "Initial Good Deck Area",
        min_value=0,
        max_value=40_000_000,
        value=15_000_000,
        step=1_000_000,
    )
    init_fair = st.slider(
        "Initial Fair Deck Area",
        min_value=0,
        max_value=40_000_000,
        value=30_000_000,
        step=1_000_000,
    )
    init_poor = st.slider(
        "Initial Poor Deck Area",
        min_value=0,
        max_value=20_000_000,
        value=5_000_000,
        step=500_000,
    )

    years = st.slider(
        "Simulation Horizon (years)",
        min_value=5,
        max_value=50,
        value=30,
        step=5,
    )

    st.markdown("**Annual Deterioration Rates**")
    det_good_to_fair = st.slider(
        "Good → Fair (per year)",
        min_value=0.0,
        max_value=0.10,
        value=0.02,
        step=0.01,
    )
    det_fair_to_poor = st.slider(
        "Fair → Poor (per year)",
        min_value=0.0,
        max_value=0.10,
        value=0.03,
        step=0.01,
    )
    det_poor_to_closed = st.slider(
        "Poor → Closed (per year)",
        min_value=0.0,
        max_value=0.10,
        value=0.02,
        step=0.01,
    )

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
        index=0,  # default: Rehab Fair Condition First
    )
    strategy_key = strategy_label_to_key[strategy_label]

    # Centered Run button
    run_col1, run_col2, run_col3 = st.columns([1, 1, 1])
    with run_col2:
        run = st.button("Run Model")

    st.markdown("---")

    if run:
        df, closed_series, stats = simulate_network(
            years=years,
            strategy=strategy_key,
            annual_budget=annual_budget,
            avg_deck_area=avg_deck_area,
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

        chart_df = df.copy()
        chart_df.index.name = "Year"

        st.line_chart(
            chart_df[[GOOD, FAIR, POOR, CLOSED]].rename(
                columns={
                    GOOD: "Good",
                    FAIR: "Fair",
                    POOR: "Poor",
                    CLOSED: "Closed",
                }
            ),
            height=350,
        )

        # Summary table for condition trajectories
        st.markdown("**Summary at End of Horizon**")
        summary_data = {
            "Condition": ["Good", "Fair", "Poor", "Closed"],
            "Share of Deck Area": [
                fmt_pct(stats["final_share_good"]),
                fmt_pct(stats["final_share_fair"]),
                fmt_pct(stats["final_share_poor"]),
                fmt_pct(stats["final_share_closed"]),
            ],
        }
        summary_df = pd.DataFrame(summary_data)
        st.table(summary_df)

        st.markdown(
            f"**Total Deck Area Preserved:** {fmt_num(stats['total_preserved'])} ft²  \n"
            f"**Total Deck Area Replaced:** {fmt_num(stats['total_replaced'])} ft²"
        )

        st.markdown("---")
        st.subheader("Closed Bridges Over Time")

        closed_df = pd.DataFrame({"Closed": closed_series})
        closed_df.index.name = "Year"

        st.line_chart(closed_df, height=300)

        # Summary table for closed bridges
        st.markdown("**Closed Bridges Summary**")
        closed_summary = pd.DataFrame(
            {
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
            }
        )
        st.table(closed_summary)

    st.markdown("</div>", unsafe_allow_html=True)

# --- RIGHT COLUMN: Strategy descriptions ---
with right_col:
    st.subheader("Policy Strategies")

    st.markdown(
        """
        **Rehab Fair Condition First**  
        Prioritizes preserving Fair bridges to prevent deterioration into Poor condition. This strategy reflects WSDOT’s current preservation philosophy and supports the statewide goal of maintaining at least 90% of bridges in Fair or better condition. Replacement of Poor bridges occurs only after Fair bridges have been addressed.
        """
    )

    st.markdown(
        """
        **Rehab Poor Condition First**  
        Allocates funding to Poor bridges before preserving Fair bridges. This reactive strategy focuses on the worst‑condition structures but may allow Fair bridges to deteriorate if budgets are limited. Replacement occurs only after Poor bridges have been rehabilitated as much as possible.
        """
    )

    st.markdown(
        """
        **Replace Closed Bridges First**  
        Directs funding first toward replacing Closed bridges, then Poor bridges, and finally preserving Fair bridges. This strategy highlights the long‑term cost of allowing closures to accumulate and demonstrates the “mortgaging the future” effect when backlogs grow faster than available funding.
        """
    )

    st.markdown(
        """
        **Balanced Strategy (50/50)**  
        Splits the annual budget evenly between preserving Fair bridges and replacing Closed/Poor bridges. Half of the budget is dedicated to Fair preservation; the other half is used to replace Closed bridges first, then Poor bridges. This strategy represents a middle‑ground approach that attempts to prevent deterioration while also reducing the backlog of closures.
        """
    )

