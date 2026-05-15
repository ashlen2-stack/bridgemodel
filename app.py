import streamlit as st
import pandas as pd
import altair as alt
from datetime import date

from model import simulate_network, GOOD, FAIR, POOR, CLOSED

st.set_page_config(
    page_title="Washington State Bridge Network Strategy Simulator",
    layout="wide",
)

# --- Core UI CSS ---
st.markdown(
    """
    <style>
    /* Slider bar color */
    div[data-baseweb="slider"] > div > div {
        background-color: #007b3e !important;
        height: 6px !important;
    }
    div[data-baseweb="slider"] > div > div > div {
        background-color: #007b3e !important;
    }

    /* Increase slider label + dropdown label font */
    label[data-testid="stWidgetLabel"] {
        font-size: 1.05rem !important;
        font-weight: 500 !important;
    }

    /* Run button */
    div.stButton > button:first-child {
        background-color: #fa8072;
        color: white;
        border-radius: 6px;
        border: none;
        padding: 0.5rem 1.5rem;
        font-weight: 600;
    }

    /* Table readability */
    .stTable, .stDataFrame {
        background-color: white !important;
        color: black !important;
        border: 1px solid black !important;
    }
    .stTable td, .stTable th {
        background-color: white !important;
        color: black !important;
        border: 1px solid black !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# --- Background Image (proper layering) ---
st.markdown(
    f"""
    <style>
    .stApp {{
        position: relative;
        background: none;
    }}

    .stApp::before {{
        content: "";
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-image: url("https://raw.githubusercontent.com/ashlen2-stack/bridgemodel/4282854ff80fb53251f0071f79c8964f50ed5d37/assets/396099625_710e826d1d_b.jpg");
        background-size: cover;
        background-repeat: no-repeat;
        background-attachment: fixed;
        opacity: 0.18;
        z-index: -1;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

def fmt_pct(x):
    return f"{x*100:.1f}%"

def fmt_num(x):
    return f"{x:,.0f}"

# --- Title ---
st.markdown(
    "<h2 style='text-align:center; margin-top:-55px;'>Washington State Bridge Network Strategy Simulator</h2>",
    unsafe_allow_html=True,
)

left_col, middle_col, right_col = st.columns([1.2, 2.0, 1.2])

# --- LEFT COLUMN ---
with left_col:
    st.subheader("Overview")

    today = date.today().strftime("%B %d, %Y")

    st.markdown(
        """
        Washington’s bridge network includes more than 56 million square feet of deck area, much of it aging and increasingly expensive to maintain. Recent closures, including the Carbon River Bridge on SR 165 and the Wishkah River Bridge in Aberdeen, highlight the consequences of deferred preservation and the growing challenge of prioritizing limited maintenance dollars.

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
    st.subheader("Model Inputs & Strategy Selection")

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
        min_value=5000,
        max_value=40000,
        value=20000,
        step=1000,
    )

    replacement_share = st.slider(
        "Replacement Share of Annual Budget (Balanced Strategy)",
        min_value=0.0,
        max_value=1.0,
        value=0.5,
        step=0.1,
    )

    pres_cost = 125
    repl_cost = 2500

    init_good = 20425507
    init_fair = 30359189
    init_poor = 5341995
    init_closed = 31292

    det_good_to_fair = 1 / 35.21867687
    det_fair_to_poor = 1 / 57.92504134
    det_poor_to_closed = 1 / 54.95117

    strategy_label_to_key = {
        "Rehab Fair Condition First": "fair_first",
        "Rehab Poor Condition First": "poor_first",
        "Replace Closed Bridges First": "replace_closed_first",
        "Balanced Strategy (Slider-Controlled)": "balanced",
    }

    strategy_label = st.selectbox(
        "Select a Policy Strategy:",
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
            init_closed=init_closed,
            det_good_to_fair=det_good_to_fair,
            det_fair_to_poor=det_fair_to_poor,
            det_poor_to_closed=det_poor_to_closed,
            replacement_share=replacement_share,
        )

        df_bridges = df / avg_deck_area
        closed_bridges = closed_series / avg_deck_area

        st.subheader("Condition Trajectories Over Time (Number of Bridges)")

        chart_df = df_bridges.reset_index().rename(columns={"index": "Year"})
        melted = chart_df.melt(
            id_vars="Year",
            value_vars=[GOOD, FAIR, POOR, CLOSED],
            var_name="Condition",
            value_name="Bridges",
        )

        color_scale = alt.Scale(
            domain=[GOOD, FAIR, POOR, CLOSED],
            range=["#007b3e", "#ffd700", "#d62728", "#000000"],
        )

        cond_chart = (
            alt.Chart(melted)
            .mark_line()
            .encode(
                x=alt.X("Year:Q", title="Year"),
                y=alt.Y("Bridges:Q", title="Number of Bridges"),
                color=alt.Color("Condition:N", scale=color_scale),
            )
            .properties(height=350)
            .configure_axis(
                labelColor='black',
                titleColor='black',
                gridColor='lightgray'
            )
            .configure_view(
                fill='white'
            )
        )

        st.altair_chart(cond_chart, use_container_width=True)

        st.markdown("**Summary at End of Horizon**")
        st.table(pd.DataFrame({
            "Condition": ["Good", "Fair", "Poor", "Closed"],
            "Share of Bridges": [
                fmt_pct(stats["final_share_good"]),
                fmt_pct(stats["final_share_fair"]),
                fmt_pct(stats["final_share_poor"]),
                fmt_pct(stats["final_share_closed"]),
            ],
            "Number of Bridges": [
                fmt_num(df_bridges[GOOD].iloc[-1]),
                fmt_num(df_bridges[FAIR].iloc[-1]),
                fmt_num(df_bridges[POOR].iloc[-1]),
                fmt_num(df_bridges[CLOSED].iloc[-1]),
            ],
        }))

        st.markdown(
            f"**Total Bridges Preserved:** {fmt_num(stats['total_preserved'] / avg_deck_area)}  \n"
            f"**Total Bridges Replaced:** {fmt_num(stats['total_replaced'] / avg_deck_area)}"
        )

        st.markdown("---")
        st.subheader("Closed Bridges Over Time")

        closed_df = pd.DataFrame({
            "Year": closed_bridges.index.astype(int),
            "Closed Bridges": closed_bridges.values,
        })

        closed_chart = (
            alt.Chart(closed_df)
            .mark_line(color="#000000")
            .encode(
                x=alt.X("Year:Q", title="Year"),
                y=alt.Y("Closed Bridges:Q", title="Number of Closed Bridges"),
            )
            .properties(height=300)
            .configure_axis(
                labelColor='black',
                titleColor='black',
                gridColor='lightgray'
            )
            .configure_view(
                fill='white'
            )
        )

        st.altair_chart(closed_chart, use_container_width=True)

# --- RIGHT COLUMN ---
with right_col:
    st.subheader("Policy Strategy Definitions")

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
        **Balanced Strategy (Slider-Controlled)**  
        Splits the annual budget between preserving Fair bridges and replacing Closed/Poor bridges. The slider controls the share of the annual budget allocated to replacement; the remainder is used for Fair preservation.
        """
    )
