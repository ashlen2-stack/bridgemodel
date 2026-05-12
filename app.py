# app.py

import streamlit as st
from model import run_model

st.title("WSDOT Bridge Condition Model")

Preservation_Budget = st.slider("Preservation Budget", 1_000_000, 20_000_000, 5_000_000)
Replacement_Share = st.slider("Replacement Share", 0.0, 1.0, 0.10)
Avg_Deck_Area = st.slider("Average Deck Area (ft²)", 5000, 20000, 12000)

scenario = st.selectbox("Scenario", ["poor_first", "fair_first", "balanced"])

if st.button("Run Model"):
    df = run_model(
        Preservation_Budget=Preservation_Budget,
        Replacement_Share=Replacement_Share,
        Avg_Deck_Area=Avg_Deck_Area,
        scenario=scenario
    )

    st.line_chart(df.set_index("year"))



