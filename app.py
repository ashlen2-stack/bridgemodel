import streamlit as st
import pandas as pd
import altair as alt
from datetime import date

from model import simulate_network, GOOD, FAIR, POOR, CLOSED

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Washington State Bridge Network Strategy Simulator",
    layout="wide",
)

# --- CONSTANTS ---
AVG_DECK_AREA = 16300  # ft² per bridge (55.8M ft² / 3,420 bridges)
TOTAL_BRIDGES = 3420

# --- CORE UI CSS ---
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

def fmt_pct(x):
    return f"{x*100:.1f}%"

def fmt_num(x):
    return f"{x:,.0f}"

def fmt_money(x):
    return f"${x/1_000_000:,.1f}M"

# --- TITLE ---
st.markdown(
    "<h2 style='text-align:center; margin-top:-55px;'>Washington State Bridge Network Strategy Simulator</h2>",
    unsafe_allow_html=True,
)

tab_home, tab_methods, tab_more = st.tabs(["Home", "Methods", "More Plots"])

# =========================================================
# HOME TAB
# =========================================================
with tab_home:
    left_col, middle_col, right_col = st.columns([1.2, 2.0, 1.2])

    # --- LEFT COLUMN: OVERVIEW ---
    with left_col:
        st.subheader("Overview")

        today = date.today().strftime("%B %d, %Y")

        st.markdown(
            """
            Washington’s bridge network includes approximately **55.8 million square feet** of deck area across **3,420 bridges**, much of it aging and increasingly expensive to maintain. Recent closures, including the Carbon River Bridge on SR 165 and the Wishkah River Bridge in Aberdeen, highlight the consequences of deferred preservation and the growing challenge of prioritizing limited maintenance dollars.

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

    # --- MIDDLE COLUMN: INPUTS ---
    with middle_col:
        st.subheader("Model Inputs & Strategy Selection")

        st.markdown(
            """
            The **annual budget** applies to **all strategies**.  
            Strategies differ only in **how they prioritize preservation and replacement**, not in total dollars available.
            """
        )

        annual_budget_m = st.slider(
            "Annual Budget (million $) – applies to all strategies",
            min_value=50,
            max_value=400,
            value=150,
            step=10,
        )
        annual_budget = annual_budget_m * 1_000_000

        # Costs per ft²
        pres_cost = 125
        repl_cost = 2500

        # Initial deck area by condition (ft²)
        init_good = 20425507
        init_fair = 30359189
        init_poor = 5341995
        init_closed = 31292

        # Deterioration rates (1 / expected years in condition)
        det_good_to_fair = 1 / 35.21867687
        det_fair_to_poor = 1 / 57.92504134
        det_poor_to_closed = 1 / 54.95117

        # Strategy mapping
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

        replacement_share = st.slider(
            "Replacement Share of Annual Budget (Balanced Strategy Only)",
            min_value=0.0,
            max_value=1.0,
            value=0.5,
            step=0.1,
            help="For the Balanced strategy, this is the share of the annual budget allocated to replacement. The remaining share is used for preservation.",
        )

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

            # Convert deck area to bridges using fixed average deck area
            df_bridges = df / AVG_DECK_AREA
            closed_bridges = closed_series / AVG_DECK_AREA

            # --- MAIN CONDITION TRAJECTORIES ---
            st.subheader(f"{strategy_label} – Condition Trajectories Over Time")

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

            # --- SUMMARY TABLE ---
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
                f"**Total Bridges Preserved (over 30 years):** {fmt_num(stats.get('total_preserved', 0) / AVG_DECK_AREA)}  \n"
                f"**Total Bridges Replaced (over 30 years):** {fmt_num(stats.get('total_replaced', 0) / AVG_DECK_AREA)}"
            )

            st.markdown("---")

            # --- % FAIR OR BETTER WITH 90% TARGET ---
            st.subheader("Percent of Bridges in Fair or Better Condition")

            fair_better = (df_bridges[GOOD] + df_bridges[FAIR]) / (
                df_bridges[GOOD] + df_bridges[FAIR] + df_bridges[POOR] + df_bridges[CLOSED]
            )

            fb_df = pd.DataFrame({
                "Year": df_bridges.index.astype(int),
                "Fair or Better": fair_better.values,
            })

            fb_chart = (
                alt.Chart(fb_df)
                .mark_line(color="#007b3e", strokeWidth=2)
                .encode(
                    x=alt.X("Year:Q", title="Year"),
                    y=alt.Y("Fair or Better:Q", title="Share of Bridges", axis=alt.Axis(format='%')),
                )
            )

            target_line = (
                alt.Chart(pd.DataFrame({"y": [0.9]}))
                .mark_rule(color="red", strokeDash=[4, 4])
                .encode(y="y:Q")
            )

            fb_final = (fb_chart + target_line).properties(height=250)

            st.altair_chart(fb_final, use_container_width=True)

            st.markdown(
                """
                The green line shows the share of bridges in **Fair or Good** condition.  
                The red dashed line marks a **90% Fair‑or‑better target**, consistent with WSDOT’s statewide goal.
                """
            )

            st.markdown("---")

            # --- CLOSED BRIDGES + BACKLOG COST (DUAL AXIS) ---
            st.subheader("Closed Bridges and Replacement Backlog Cost Over Time")

            closed_df = pd.DataFrame({
                "Year": closed_bridges.index.astype(int),
                "Closed Bridges": closed_bridges.values,
            })

            closed_df["Increasing"] = (closed_df["Closed Bridges"].diff() > 0).astype(int)

            closed_df["Backlog Cost"] = (
                closed_df["Closed Bridges"] * AVG_DECK_AREA * repl_cost
            )
            closed_df["Backlog Cost (Millions)"] = closed_df["Backlog Cost"] / 1_000_000

            shaded = (
                alt.Chart(closed_df)
                .mark_area(color="lightgray")
                .encode(
                    x="Year:Q",
                    y="Closed Bridges:Q",
                    y2=alt.value(0),
                    opacity=alt.Opacity(
                        "Increasing:Q",
                        scale=alt.Scale(domain=[0,1], range=[0,0.35])
                    )
                )
            )

            line_closed = (
                alt.Chart(closed_df)
                .mark_line(color="black", strokeWidth=2)
                .encode(
                    x=alt.X("Year:Q", title="Year"),
                    y=alt.Y("Closed Bridges:Q", title="Closed Bridges"),
                )
            )

            line_cost = (
                alt.Chart(closed_df)
                .mark_line(color="#1f77b4", strokeWidth=2)
                .encode(
                    x="Year:Q",
                    y=alt.Y(
                        "Backlog Cost (Millions):Q",
                        title="Replacement Backlog Cost (Million $)",
                        axis=alt.Axis(titleColor="#1f77b4")
                    )
                )
            )

            closed_chart = alt.layer(shaded, line_closed, line_cost).resolve_scale(
                y='independent'
            ).properties(height=350)

            st.altair_chart(closed_chart, use_container_width=True)

            st.markdown(
                """
                **How to interpret this chart:**  
                • The **black line** shows the number of closed bridges.  
                • The **blue line** shows the **replacement backlog cost** in millions of dollars.  
                • **Gray shading** highlights years where closures increase — periods where the system is falling behind.  
                • When shading and the blue line rise together, it signals **accelerating long‑term financial pressure**.  
                • This is the essence of *“mortgaging the future”*: delaying preservation today increases the cost burden tomorrow.
                """
            )

            st.markdown("---")

            # --- REPLACE-FIRST BUDGET SUFFICIENCY (TEXT + BAR CHART) ---
            if strategy_key == "replace_closed_first":
                st.subheader("Budget Sufficiency for Replacing Closed Bridges (Replace-First Strategy)")

                # Required budget each year to replace all closed bridges
                closed_df["Required Budget"] = closed_df["Closed Bridges"] * AVG_DECK_AREA * repl_cost
                max_required = closed_df["Required Budget"].max()

                st.markdown(
                    f"""
                    With the current annual budget of **{fmt_money(annual_budget)}**, the model compares this to the  
                    **maximum annual budget that would be required to replace all closed bridges in a single year**.
                    """
                )

                if max_required <= annual_budget:
                    st.markdown(
                        f"""
                        ✅ Under this strategy and trajectory, the current budget of **{fmt_money(annual_budget)}**  
                        is sufficient to replace all closed bridges in the year with the highest closure backlog.
                        """
                    )
                else:
                    st.markdown(
                        f"""
                        ⚪ Under this strategy, the **maximum annual budget required** to replace all closed bridges in the  
                        worst year is approximately **{fmt_money(max_required)}**.  
                        The current budget of **{fmt_money(annual_budget)}** would need to increase by about  
                        **{fmt_money(max_required - annual_budget)}** to fully clear the backlog in that peak year.
                        """
                    )

                budget_comp_df = pd.DataFrame({
                    "Type": ["Available Budget", "Max Required Budget"],
                    "Amount": [annual_budget / 1_000_000, max_required / 1_000_000],
                })

                budget_chart = (
                    alt.Chart(budget_comp_df)
                    .mark_bar()
                    .encode(
                        x=alt.X("Type:N", title=""),
                        y=alt.Y("Amount:Q", title="Million $"),
                        color=alt.Color("Type:N", scale=alt.Scale(range=["#1f77b4", "#d62728"])),
                    )
                    .properties(height=250)
                )

                st.altair_chart(budget_chart, use_container_width=True)

# =========================================================
# METHODS TAB
# =========================================================
with tab_methods:
    st.subheader("Methods")

    st.markdown(
        """
        ### Model Purpose

        This model is designed to explore how different preservation and replacement strategies affect the long‑term condition of Washington State’s bridge network under constrained budgets. It is a **system‑level deck‑area model**, not a structure‑by‑structure forecast.

        ### Data and Network Representation

        • **Total bridges:** 3,420  
        • **Total deck area:** 55.8 million ft²  
        • **Average deck area per bridge:** 16,300 ft²  

        The model tracks deck area in four condition states:

        • **Good**  
        • **Fair**  
        • **Poor**  
        • **Closed**

        All flows, costs, and outcomes are modeled in terms of **deck area**, then converted into **bridge‑equivalent units** using the average deck area.

        ### Deterioration Structure

        The model assumes a unidirectional deterioration pathway:

        Good → Fair → Poor → Closed

        Annual deterioration rates are derived from observed age and condition patterns in the WSDOT inventory:

        • Good → Fair: 1 / 35.2 years  
        • Fair → Poor: 1 / 57.9 years  
        • Poor → Closed: 1 / 55.0 years  

        These rates are applied to the deck area in each condition state to estimate annual deterioration flows.

        ### Cost Assumptions

        Costs are specified per square foot of deck area:

        • **Preservation cost:** $125 per ft²  
        • **Replacement cost:** $2,500 per ft²  

        Annual spending is constrained by the **annual budget slider**, which applies to **all strategies**.

        ### Strategies and Priority Rules

        All strategies share the same annual budget but differ in how they prioritize preservation and replacement:

        **Rehab Fair Condition First**  
        1. Preserve **Fair** deck area  
        2. Preserve **Poor** deck area (if budget remains)  
        3. Replace bridges (if budget remains)  

        **Rehab Poor Condition First**  
        1. Preserve **Poor** deck area  
        2. Preserve **Fair** deck area (if budget remains)  
        3. Replace bridges (if budget remains)  

        **Replace Closed Bridges First**  
        1. Replace **Closed** bridges  
        2. Preserve **Fair** deck area (if budget remains)  
        3. Preserve **Poor** deck area (if budget remains)  

        **Balanced Strategy (Slider‑Controlled)**  
        • A user‑defined share of the annual budget is allocated to **replacement**.  
        • The remaining share is allocated to **preservation**, typically prioritizing Fair and Poor deck area.  

        ### Simulation Horizon

        The model simulates **30 years** of annual transitions, deterioration, preservation, and replacement under the selected strategy and budget.

        ### Outputs

        The app reports:

        • Condition trajectories (Good, Fair, Poor, Closed) in bridge‑equivalent units  
        • Summary condition shares at the end of the horizon  
        • Total bridges preserved and replaced  
        • Closed bridges and replacement backlog cost over time  
        • Percent of bridges in Fair or better condition, with a 90% target line  

        Additional plots (flows and spending by action) are provided in the **More Plots** tab as diagnostic views.

        ### Limitations

        • The model is **not** a structure‑specific forecast and does not represent individual bridges.  
        • Deterioration rates are assumed constant over time and do not respond to climate, traffic, or design changes.  
        • Preservation and replacement effects are modeled at the deck‑area level and may not capture all structural nuances.  
        • The model is intended for **scenario exploration and communication**, not for project‑level decision‑making.

        """
    )

# =========================================================
# MORE PLOTS TAB
# =========================================================
with tab_more:
    st.subheader("Additional Plots")

    st.markdown(
        """
        These plots provide additional diagnostic views of how the system behaves under the selected strategy and budget.
        """
    )

    # We need access to the model outputs; re-run only if user has run the model on Home.
    # To keep things simple and robust, we ask the user to re-run here if needed.
    st.info("To view additional plots, please ensure you have run the model on the Home tab with your desired settings.")

    # In a more advanced version, you could refactor the code to share state across tabs.
