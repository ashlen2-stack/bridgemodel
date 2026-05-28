import streamlit as st
import pandas as pd
import altair as alt
from datetime import date

from model import simulate_network, GOOD, FAIR, POOR, CLOSED

# ---------------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------------
st.set_page_config(
    page_title="Washington State Bridge Network Strategy Simulator",
    layout="wide",
)

# ---------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------
AVG_DECK_AREA = 16300   # ft² per bridge (55.8M ft² / 3,420 bridges)
TOTAL_BRIDGES = 3420

PRES_COST = 125
REPL_COST = 2500

# ---------------------------------------------------------
# HELPERS
# ---------------------------------------------------------
def fmt_pct(x):
    return f"{x*100:.1f}%"

def fmt_num(x):
    return f"{x:,.0f}"

def fmt_money(x):
    return f"${x/1_000_000:,.1f}M"

# ---------------------------------------------------------
# CSS (NO BOLDING ANYWHERE)
# ---------------------------------------------------------
st.markdown(
    """
    <style>
    div[data-baseweb="slider"] > div > div {
        background-color: #007b3e !important;
        height: 6px !important;
    }
    div[data-baseweb="slider"] > div > div > div {
        background-color: #007b3e !important;
    }
    label[data-testid="stWidgetLabel"] {
        font-size: 1.05rem !important;
        font-weight: 400 !important;
    }
    div.stButton > button:first-child {
        background-color: #fa8072;
        color: white;
        border-radius: 6px;
        border: none;
        padding: 0.5rem 1.5rem;
        font-weight: 500;
    }
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

# ---------------------------------------------------------
# TITLE + TABS
# ---------------------------------------------------------
st.markdown(
    "<h2 style='text-align:center; margin-top:-55px;'>Washington State Bridge Network Strategy Simulator</h2>",
    unsafe_allow_html=True,
)

tab_home, tab_methods, tab_more = st.tabs(["Home", "Methods", "More Plots"])
# =========================================================
# HOME TAB
# =========================================================
with tab_home:

    # -----------------------------------------------------
    # LAYOUT: LEFT, MIDDLE, RIGHT COLUMNS
    # -----------------------------------------------------
    left_col, middle_col, right_col = st.columns([1.2, 2.0, 1.2])

    # -----------------------------------------------------
    # LEFT COLUMN — OVERVIEW (NO BOLDING)
    # -----------------------------------------------------
    with left_col:
        st.subheader("Overview")

        today = date.today().strftime("%B %d, %Y")

        st.markdown(
            """
            Washington’s bridge network includes approximately 55.8 million square feet of deck area 
            across 3,420 bridges, much of it aging and increasingly expensive to maintain. Recent closures, 
            including the Carbon River Bridge on SR 165 and the Wishkah River Bridge in Aberdeen, highlight 
            the consequences of deferred preservation and the growing challenge of prioritizing limited 
            maintenance dollars.

            This simulator provides a system-level view of how different preservation and replacement 
            strategies influence long-term bridge conditions under constrained budgets. It is not designed 
            to predict the future of any specific structure. Instead, it illustrates how funding levels, 
            prioritization rules, and preservation timing shape statewide outcomes over time.

            Users can adjust key parameters, explore alternative strategies, and compare the long-term 
            implications of preventive versus reactive investment approaches. The goal is to support 
            decision-makers by making the tradeoffs between strategies visible, intuitive, and grounded 
            in the structure of Washington’s bridge network.
            """
        )

        st.markdown(
            f"""
            Developed by: Ashley Carle, WSDOT Fellow  
            Published: {today}  
            Data Used: WSDOT Bridge Inventory and Condition Data (2024)
            """
        )

    # -----------------------------------------------------
    # MIDDLE COLUMN — MODEL INPUTS
    # -----------------------------------------------------
    with middle_col:
        st.subheader("Model Inputs and Strategy Selection")

        st.markdown(
            """
            The annual budget applies to all strategies.  
            Strategies differ only in how they prioritize preservation and replacement.
            """
        )

        # Annual Budget Slider
        annual_budget_m = st.slider(
            "Annual Budget (million dollars)",
            min_value=50,
            max_value=400,
            value=150,
            step=10,
        )
        annual_budget = annual_budget_m * 1_000_000

        # Balanced Strategy Slider (must appear before strategy dropdown)
        replacement_share = st.slider(
            "Replacement Share of Annual Budget (Balanced Strategy Only)",
            min_value=0.0,
            max_value=1.0,
            value=0.5,
            step=0.1,
            help="For the Balanced strategy, this is the share of the annual budget allocated to replacement. The remaining share is used for preservation.",
        )

        # Strategy Dropdown (now placed after both sliders)
        strategy_label_to_key = {
            "Rehab Fair Condition First": "fair_first",
            "Rehab Poor Condition First": "poor_first",
            "Replace Closed Bridges First": "replace_closed_first",
            "Balanced Strategy (Slider-Controlled)": "balanced",
        }

        strategy_label = st.selectbox(
            "Select a Policy Strategy",
            options=list(strategy_label_to_key.keys()),
            index=0,
        )
        strategy_key = strategy_label_to_key[strategy_label]

        # Run Button
        run_col1, run_col2, run_col3 = st.columns([1, 1, 1])
        with run_col2:
            run = st.button("Run Model")

        st.markdown("---")

    # -----------------------------------------------------
    # RIGHT COLUMN — STRATEGY DEFINITIONS (RESTORED)
    # -----------------------------------------------------
    with right_col:
        st.subheader("Strategy Definitions")

        st.markdown(
            """
            Rehab Fair Condition First  
            • Preserve Fair deck area first  
            • Then preserve Poor deck area  
            • Replace bridges only if budget remains  

            Rehab Poor Condition First  
            • Preserve Poor deck area first  
            • Then preserve Fair deck area  
            • Replace bridges only if budget remains  

            Replace Closed Bridges First  
            • Replace Closed bridges first  
            • Then preserve Fair deck area  
            • Then preserve Poor deck area  

            Balanced Strategy  
            • Budget is split between preservation and replacement  
            • Replacement share is controlled by the slider  
            • Preservation typically prioritizes Fair then Poor  
            """
        )
    # -----------------------------------------------------
    # MODEL EXECUTION (RUN BUTTON)
    # -----------------------------------------------------
    
    if run:

        # Run the model
        df, closed_series, stats, flows = simulate_network(
            years=30,
            strategy=strategy_key,
            annual_budget=annual_budget,
            pres_cost=PRES_COST,
            repl_cost=REPL_COST,
            init_good=20425507,
            init_fair=30359189,
            init_poor=5341995,
            init_closed=31292,
            det_good_to_fair=1 / 35.21867687,
            det_fair_to_poor=1 / 57.92504134,
            det_poor_to_closed=1 / 54.95117,
            replacement_share=replacement_share,
        )

        # Convert deck area to bridge-equivalent units
        df_bridges = df / AVG_DECK_AREA
        closed_bridges = closed_series / AVG_DECK_AREA

        # -------------------------------------------------
        # CONDITION TRAJECTORIES PLOT
        # -------------------------------------------------
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
            .properties(width=650, height=420)
        )

        st.altair_chart(cond_chart, use_container_width=False)

        # -------------------------------------------------
        # SUMMARY TABLE
        # -------------------------------------------------
        st.markdown("Summary at End of Horizon")

        summary_df = pd.DataFrame({
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
        })

        st.table(summary_df)

        st.markdown(
            f"Total Bridges in System: {TOTAL_BRIDGES}"
        )

        st.markdown(
            f"Total Bridges Preserved (cumulative): {fmt_num(stats.get('total_preserved', 0) / AVG_DECK_AREA)}"
        )
        st.markdown(
            f"Total Bridges Replaced (cumulative): {fmt_num(stats.get('total_replaced', 0) / AVG_DECK_AREA)}"
        )

        st.markdown("---")

        # -------------------------------------------------
        # PERCENT FAIR OR BETTER (UPDATED COLORS + LEGEND)
        # -------------------------------------------------
        st.subheader("Percent of Bridges in Fair or Better Condition")

        fair_better = (df_bridges[GOOD] + df_bridges[FAIR]) / (
            df_bridges[GOOD] + df_bridges[FAIR] + df_bridges[POOR] + df_bridges[CLOSED]
        )

        fb_df = pd.DataFrame({
            "Year": df_bridges.index.astype(int),
            "Fair or Better": fair_better.values,
            "Target": [0.9] * len(fair_better),
        })

        fair_line = (
            alt.Chart(fb_df)
            .mark_line(color="#ffd700", strokeWidth=2)
            .encode(
                x=alt.X("Year:Q", title="Year"),
                y=alt.Y("Fair or Better:Q", title="Share of Bridges", axis=alt.Axis(format='%')),
                color=alt.value("#ffd700"),
            )
        )

        target_line = (
            alt.Chart(fb_df)
            .mark_line(color="black", strokeDash=[4, 4], strokeWidth=2)
            .encode(
                x="Year:Q",
                y="Target:Q",
                color=alt.value("black"),
            )
        )

        fb_chart = alt.layer(fair_line, target_line).resolve_scale(
            color="independent"
        ).properties(width=650, height=420)

        st.altair_chart(fb_chart, use_container_width=False)

        st.markdown(
            """
            The yellow line shows the share of bridges in Fair or Good condition.  
            The black dotted line marks a 90 percent Fair-or-better target.
            """
        )

        st.markdown("---")
        # -------------------------------------------------
        # CLOSED BRIDGES + BACKLOG COST (CLEANED)
        # -------------------------------------------------
        st.subheader("Closed Bridges and Replacement Backlog Cost Over Time")

        closed_df = pd.DataFrame({
            "Year": closed_bridges.index.astype(int),
            "Closed Bridges": closed_bridges.values,
        })

        # Always compute backlog cost
        closed_df["Backlog Cost"] = (
            closed_df["Closed Bridges"] * AVG_DECK_AREA * REPL_COST
        )
        closed_df["Backlog Cost (Millions)"] = closed_df["Backlog Cost"] / 1_000_000

        # Always compute required budget (needed for More Plots tab)
        closed_df["Required Budget"] = (
            closed_df["Closed Bridges"] * AVG_DECK_AREA * REPL_COST
        )


        # Black line = closed bridges
        line_closed = (
            alt.Chart(closed_df)
            .mark_line(color="black", strokeWidth=2)
            .encode(
                x=alt.X("Year:Q", title="Year"),
                y=alt.Y("Closed Bridges:Q", title="Closed Bridges"),
            )
        )

        # Blue line = backlog cost (right axis)
        line_cost = (
            alt.Chart(closed_df)
            .mark_line(color="#1f77b4", strokeWidth=2)
            .encode(
                x="Year:Q",
                y=alt.Y(
                    "Backlog Cost (Millions):Q",
                    title="Replacement Backlog Cost (Million dollars)",
                    axis=alt.Axis(titleColor="#1f77b4", labelPadding=10)
                )
            )
        )

        closed_chart = (
            alt.layer(line_closed, line_cost)
            .resolve_scale(y="independent")
            .properties(width=650, height=420)
        )

        st.altair_chart(closed_chart, use_container_width=False)

        st.markdown(
            """
            The black line shows the number of closed bridges.  
            The blue line shows the replacement backlog cost in millions of dollars.  
            Removing shading clarifies the relationship between closures and long-term financial pressure.
            """
        )

        st.markdown("---")

        # -------------------------------------------------
        # REPLACE-FIRST: BUDGET SUFFICIENCY (TEXT + BAR + TIME SERIES)
        # -------------------------------------------------
        if strategy_key == "replace_closed_first":
            st.subheader("Budget Sufficiency for Replacing Closed Bridges")

            # Required budget each year to replace all closed bridges
            closed_df["Required Budget"] = (
                closed_df["Closed Bridges"] * AVG_DECK_AREA * REPL_COST
            )

            max_required = closed_df["Required Budget"].max()

            st.markdown(
                f"Annual budget selected: {fmt_money(annual_budget)}"
            )

            if max_required <= annual_budget:
                st.markdown(
                    f"The current budget is sufficient to replace all closed bridges in the year with the highest backlog."
                )
            else:
                st.markdown(
                    st.markdown(
    f"The maximum annual budget required to replace all closed bridges in a single year is {fmt_money(max_required)}. "
    f"The current budget would need to increase by {fmt_money(max_required - annual_budget)} to fully clear the backlog in that peak year."
)

                )

            # -----------------------------
            # BAR CHART: MAX REQUIRED VS AVAILABLE
            # -----------------------------
            bar_df = pd.DataFrame({
                "Type": ["Available Budget", "Max Required Budget"],
                "Amount": [annual_budget / 1_000_000, max_required / 1_000_000],
            })

            bar_chart = (
                alt.Chart(bar_df)
                .mark_bar()
                .encode(
                    x=alt.X("Type:N", title=""),
                    y=alt.Y("Amount:Q", title="Million dollars"),
                    color=alt.Color("Type:N", scale=alt.Scale(range=["#1f77b4", "#d62728"])),
                )
                .properties(width=650,height=420)
            )

            st.altair_chart(bar_chart, use_container_width=False)

            # -----------------------------
            # TIME SERIES: REQUIRED VS AVAILABLE
            # -----------------------------
            ts_df = pd.DataFrame({
                "Year": closed_df["Year"],
                "Required Budget (M)": closed_df["Required Budget"] / 1_000_000,
                "Available Budget (M)": [annual_budget / 1_000_000] * len(closed_df),
            })

            required_line = (
                alt.Chart(ts_df)
                .mark_line(color="#d62728", strokeWidth=2)
                .encode(
                    x="Year:Q",
                    y=alt.Y("Required Budget (M):Q", title="Million dollars"),
                )
            )

            available_line = (
                alt.Chart(ts_df)
                .mark_line(color="black", strokeDash=[4, 4], strokeWidth=2)
                .encode(
                    x="Year:Q",
                    y="Available Budget (M):Q",
                )
            )

            ts_chart = (
                alt.layer(required_line, available_line)
                .properties(width=650, height=420)
            )

            st.altair_chart(ts_chart, use_container_width=False)

            st.markdown(
                """
                The red line shows the annual budget required to replace all closed bridges.  
                The black dotted line shows the available annual budget.  
                When the red line exceeds the black line, the backlog cannot be cleared within that year.
                """
            )

            st.markdown("---")
# =========================================================
# METHODS TAB
# =========================================================
with tab_methods:
    st.subheader("Methods")

    st.markdown(
        """
        Model Purpose  
        This model is designed to explore how different preservation and replacement strategies affect 
        the long-term condition of Washington State’s bridge network under constrained budgets. It is a 
        system-level deck-area model, not a structure-by-structure forecast.

        Data and Network Representation  
        The model represents the statewide bridge network using total deck area rather than individual 
        bridges. This allows preservation and replacement actions to be modeled consistently across 
        structures of different sizes.

        Total bridges: 3,420  
        Total deck area: 55.8 million square feet  
        Average deck area per bridge: 16,300 square feet  

        Deck area is tracked in four condition states: Good, Fair, Poor, and Closed. All flows, costs, 
        and outcomes are modeled in terms of deck area and then converted into bridge-equivalent units 
        using the average deck area.

        Deterioration Structure  
        The model assumes a unidirectional deterioration pathway:

        Good → Fair → Poor → Closed

        Annual deterioration rates are derived from observed age and condition patterns in the WSDOT 
        inventory:

        Good to Fair: 1 / 35.2 years  
        Fair to Poor: 1 / 57.9 years  
        Poor to Closed: 1 / 55.0 years  

        These rates are applied to the deck area in each condition state to estimate annual deterioration 
        flows.

        Cost Assumptions  
        Costs are specified per square foot of deck area:

        Preservation cost: 125 dollars per square foot  
        Replacement cost: 2,500 dollars per square foot  

        Annual spending is constrained by the annual budget slider, which applies to all strategies.

        Strategy Logic  
        Strategies differ only in how they prioritize preservation and replacement actions. The annual 
        budget is the same across all strategies.

        Rehab Fair Condition First  
        Preserve Fair deck area first, then Poor, then replace bridges if budget remains.

        Rehab Poor Condition First  
        Preserve Poor deck area first, then Fair, then replace bridges if budget remains.

        Replace Closed Bridges First  
        Replace Closed bridges first, then preserve Fair deck area, then Poor.

        Balanced Strategy  
        A user-defined share of the annual budget is allocated to replacement. The remaining share is 
        allocated to preservation, typically prioritizing Fair then Poor.

        Simulation Horizon  
        The model simulates 30 years of annual transitions, deterioration, preservation, and replacement 
        under the selected strategy and budget.

        Outputs  
        The app reports:

        • Condition trajectories in bridge-equivalent units  
        • Summary condition shares at the end of the horizon  
        • Cumulative bridges preserved and replaced  
        • Closed bridges and replacement backlog cost over time  
        • Percent of bridges in Fair or better condition with a 90 percent target line  
        • Additional diagnostic plots in the More Plots tab  

        Limitations  
        The model is not a structure-specific forecast and does not represent individual bridges. 
        Deterioration rates are assumed constant over time and do not respond to climate, traffic, or 
        design changes. Preservation and replacement effects are modeled at the deck-area level and may 
        not capture all structural nuances. The model is intended for scenario exploration and 
        communication, not for project-level decision-making.
        """
    )
# =========================================================
# MORE PLOTS TAB
# =========================================================
with tab_more:
    st.subheader(f"Additional Plots - {strategy_label}")

    st.markdown(
        """
        These plots provide additional diagnostic views of how the system behaves under the selected 
        strategy and budget. They are intended to complement the main results shown on the Home tab.
        """
    )

       # Require that the model has been run
    if not run:
        st.info("Run the model on the Home tab to view additional plots.")
    else:

        # --------------------------------------------------
        # BUILD FLOWS DATAFRAME
        # --------------------------------------------------
        flows_df = pd.DataFrame({
            "Year": range(len(flows["det_gf"])),
            "Deterioration G→F": flows["det_gf"],
            "Deterioration F→P": flows["det_fp"],
            "Deterioration P→C": flows["det_pc"],
            "Preservation F→G": flows["pres_fair"],
            "Preservation P→F": flows["pres_poor"],
            "Replacement C→G": flows["repl_closed"],
        })

        # --------------------------------------------------
        # 1. DETERIORATION FLOWS
        # --------------------------------------------------
        st.markdown("### Deterioration Flows Over Time")

        det_df = flows_df[[
            "Year",
            "Deterioration G→F",
            "Deterioration F→P",
            "Deterioration P→C"
        ]]
        det_melt = det_df.melt(id_vars="Year", var_name="Flow", value_name="Deck Area")

        det_chart = (
            alt.Chart(det_melt)
            .mark_line(strokeWidth=2)
            .encode(
                x="Year:Q",
                y=alt.Y("Deck Area:Q", title="Square feet"),
                color=alt.Color(
                    "Flow:N",
                    scale=alt.Scale(range=["#007b3e", "#ffd700", "#d62728"])
                ),
            )
            .properties(width=650, height=420)
        )
        st.altair_chart(det_chart, use_container_width=False)

        # Text summary
        avg_det = det_df.mean()
        peak_det = det_df.max()
        final_det = det_df.iloc[-1]

        st.markdown(
            f"""
            **Average annual deterioration (bridges):**  
            • Good → Fair: {avg_det['Deterioration G→F'] / AVG_DECK_AREA:.1f}  
            • Fair → Poor: {avg_det['Deterioration F→P'] / AVG_DECK_AREA:.1f}  
            • Poor → Closed: {avg_det['Deterioration P→C'] / AVG_DECK_AREA:.1f}  

            **Peak deterioration year (bridges):**  
            • Good → Fair: {peak_det['Deterioration G→F'] / AVG_DECK_AREA:.1f}  
            • Fair → Poor: {peak_det['Deterioration F→P'] / AVG_DECK_AREA:.1f}  
            • Poor → Closed: {peak_det['Deterioration P→C'] / AVG_DECK_AREA:.1f}  

            **Final year deterioration (bridges):**  
            • Good → Fair: {final_det['Deterioration G→F'] / AVG_DECK_AREA:.1f}  
            • Fair → Poor: {final_det['Deterioration F→P'] / AVG_DECK_AREA:.1f}  
            • Poor → Closed: {final_det['Deterioration P→C'] / AVG_DECK_AREA:.1f}  
            """
        )

        st.markdown("---")

        # --------------------------------------------------
        # 2. PRESERVATION FLOWS
        # --------------------------------------------------
        st.markdown("### Preservation Flows Over Time")

        pres_df = flows_df[[
            "Year",
            "Preservation F→G",
            "Preservation P→F"
        ]]
        pres_melt = pres_df.melt(id_vars="Year", var_name="Flow", value_name="Deck Area")

        pres_chart = (
            alt.Chart(pres_melt)
            .mark_line(strokeWidth=2)
            .encode(
                x="Year:Q",
                y=alt.Y("Deck Area:Q", title="Square feet"),
                color=alt.Color(
                    "Flow:N",
                    scale=alt.Scale(range=["#1f77b4", "#9467bd"])
                ),
            )
            .properties(width=650, height=300)
        )
        st.altair_chart(pres_chart, use_container_width=False)

        # Text summary
        avg_pres = pres_df.mean()
        peak_pres = pres_df.max()
        final_pres = pres_df.iloc[-1]

        st.markdown(
            f"""
            **Average annual preservation (bridges):**  
            • Fair → Good: {avg_pres['Preservation F→G'] / AVG_DECK_AREA:.1f}  
            • Poor → Fair: {avg_pres['Preservation P→F'] / AVG_DECK_AREA:.1f}  

            **Peak preservation year (bridges):**  
            • Fair → Good: {peak_pres['Preservation F→G'] / AVG_DECK_AREA:.1f}  
            • Poor → Fair: {peak_pres['Preservation P→F'] / AVG_DECK_AREA:.1f}  

            **Final year preservation (bridges):**  
            • Fair → Good: {final_pres['Preservation F→G'] / AVG_DECK_AREA:.1f}  
            • Poor → Fair: {final_pres['Preservation P→F'] / AVG_DECK_AREA:.1f}  
            """
        )

        st.markdown("---")

        # --------------------------------------------------
        # 3. REPLACEMENT FLOWS
        # --------------------------------------------------
        st.markdown("### Replacement Flows Over Time")

        repl_df = flows_df[[
            "Year",
            "Replacement C→G"
        ]]
        repl_melt = repl_df.melt(id_vars="Year", var_name="Flow", value_name="Deck Area")

        repl_chart = (
            alt.Chart(repl_melt)
            .mark_line(strokeWidth=2)
            .encode(
                x="Year:Q",
                y=alt.Y("Deck Area:Q", title="Square feet"),
                color=alt.Color(
                    "Flow:N",
                    scale=alt.Scale(range=["#2ca02c", "#000000"])
                ),
            )
            .properties(width=650, height=300)
        )
        st.altair_chart(repl_chart, use_container_width=False)

        # Text summary
        avg_repl = repl_df.mean()
        peak_repl = repl_df.max()
        final_repl = repl_df.iloc[-1]

        st.markdown(
            f"""
            **Average annual replacement (bridges):**         
            • Closed → Good: {avg_repl['Replacement C→G'] / AVG_DECK_AREA:.1f}  

            **Peak replacement year (bridges):**              
            • Closed → Good: {peak_repl['Replacement C→G'] / AVG_DECK_AREA:.1f}  

            **Final year replacement (bridges):**              
            • Closed → Good: {final_repl['Replacement C→G'] / AVG_DECK_AREA:.1f}  
            """
        )

        st.markdown("---")
	
        # -------------------------------------------------
        # FULL-WIDTH CHART 1: REQUIRED VS AVAILABLE (TIME SERIES)
        # -------------------------------------------------
        st.markdown("Annual Required Budget vs Available Budget")

        ts_df = pd.DataFrame({
            "Year": closed_df["Year"],
            "Required Budget (M)": closed_df["Required Budget"] / 1_000_000,
            "Available Budget (M)": [annual_budget / 1_000_000] * len(closed_df),
        })

        req_line = (
            alt.Chart(ts_df)
            .mark_line(color="#d62728", strokeWidth=2)
            .encode(
                x="Year:Q",
                y=alt.Y("Required Budget (M):Q", title="Million dollars"),
            )
        )

        avail_line = (
            alt.Chart(ts_df)
            .mark_line(color="black", strokeDash=[4, 4], strokeWidth=2)
            .encode(
                x="Year:Q",
                y="Available Budget (M):Q",
            )
        )

        ts_chart = alt.layer(req_line, avail_line).properties(wideth=650, height=420)
        st.altair_chart(ts_chart, use_container_width=False)

        st.markdown("---")

               # -------------------------------------------------
        # FULL-WIDTH CHART 3: ANNUAL BACKLOG COST
        # -------------------------------------------------
        st.markdown("Annual Replacement Backlog Cost (Millions)")

        backlog_ts = (
            alt.Chart(closed_df)
            .mark_line(color="#1f77b4", strokeWidth=2)
            .encode(
                x="Year:Q",
                y=alt.Y("Backlog Cost (Millions):Q", title="Million dollars"),
            )
            .properties(width=650, height=420)
        )

        st.altair_chart(backlog_ts, use_container_width=False)

        st.markdown("---")

        # -------------------------------------------------
        # TWO-COLUMN LAYOUT
        # -------------------------------------------------
        col_left, col_right = st.columns(2)

     
        # -------------------------------------------------
        # PLACEHOLDER FOR FUTURE FLOW-BASED PLOTS
        # -------------------------------------------------
        st.markdown(
            """
            Flow-based plots (preservation, replacement, and deterioration 
) will be added in a 
            future version once the model outputs annual flow series.
            """
        )
# =========================================================
# END OF APP
# =========================================================

# The app ends here. All tabs, plots, and logic are defined above.
# Streamlit will automatically handle reruns when inputs change.
