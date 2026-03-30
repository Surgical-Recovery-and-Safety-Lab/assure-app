#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
app_fn.py

Streamlit NZ Risk Score app helper functions.
"""

import altair as alt
import joblib
import streamlit as st
from medpipe.models.core import load_pipeline
from pandas import DataFrame, to_numeric

from constants import AVERAGES, LABEL_MAP, MODEL


@st.cache_resource(show_spinner=False)
def app_load_pipeline():
    """Load the pipeline"""
    pipeline = load_pipeline(MODEL)
    return pipeline


@st.cache_resource(show_spinner=False)
def app_load_averages():
    """Load operation averages"""
    op_averages = joblib.load(AVERAGES)
    return op_averages


def convert_dtypes(data):
    """Convert datatypes to fit requirements"""
    for column in data.columns:
        if column in ["AGE", "M3_SCORE", "OP_SEVERITY", "DEP18_ORIGINAL"]:
            data[column] = to_numeric(data[column])
        if column in ["PRIOR_CANCER", "TRAUMA"]:
            data[column] = data[column].astype(bool)
    return data


def sync_global_outcome_toggles():
    """Sync the global outcome toggles based on the all toggle"""
    for key in LABEL_MAP["GLOBAL_OUTCOMES"].keys():
        st.session_state[key] = st.session_state.GLOBAL_OUTCOMES


def sync_complication_toggles():
    """Sync the complication toggles based on the all toggle"""
    for key in LABEL_MAP["COMPLICATIONS"].keys():
        st.session_state[key] = st.session_state.COMPLICATIONS


def reset_app():
    """Reset all session state variables"""
    st.session_state.COMPLICATIONS = False
    st.session_state.GLOBAL_OUTCOMES = False
    st.session_state.consent = False
    st.session_state.model_run = False

    # Reset all toggles to False
    sync_complication_toggles()
    sync_global_outcome_toggles()


def show_consent_page():
    """Show consent page to user"""
    st.title("Data Usage & Model Consent")
    st.warning("Please read the following carefully before proceeding.")

    st.write("""
    By using this tool, you agree to:
    * The processing of your uploaded data by our AI model.
    * Acknowledging that the model output is for informational purposes only.
    """)
    st.write("""
    Your information is not stored and is deleted after the window is closed.
    """)

    if st.button("I Agree and Accept"):
        st.session_state.consent = True
        st.rerun()  # Rerun to immediately switch to the main app


def data_visualisation(complications_dict, op_average, display="graph"):
    """
    Visualise data in the web app.

    Parameters
    ----------
    complications_dict : dict[str: str]
        Dictionary containing the complications and the corresponding plot label.
    op_average : dict[str: float]
        Dictionary containing the operation averages for each complication.
    display : str, {"graph", "table"}
        Flag to plot the graph rather than the table, default: graph.

    Returns
    -------
    None
        Nothing is returned.

    """
    # Empty list to store complications to plot
    comp_labels = []
    comp_outcomes_proba = []
    comp_average = []
    comp_lower = []
    comp_upper = []

    for key in complications_dict.keys():
        if st.session_state[key]:
            if key == "COMPLICATIONS" or key == "GLOBAL_OUTCOMES":
                continue
            comp_labels.append(complications_dict[key])
            comp_outcomes_proba.append(st.session_state.output_proba[key])
            comp_average.append(op_average[key][0] * 100)
            comp_lower.append(op_average[key][1] * 100)
            comp_upper.append(op_average[key][2] * 100)
    plot_df = DataFrame(
        {
            "Complications": comp_labels,
            "Risk percentage": comp_outcomes_proba,
            "Population average": comp_average,
            "Lower CI": comp_lower,
            "Upper CI": comp_upper,
        }
    )

    # 1. The Confidence Interval Layer (The horizontal "whisker")
    error_bars = (
        alt.Chart(plot_df)
        .mark_errorbar()
        .encode(
            x=alt.X(
                "Lower CI:Q",
                title="Risk percentage (%)",
                scale=alt.Scale(domain=[0, 95]),
            ),
            x2="Upper CI:Q",
            y=alt.Y("Complications:N", sort=None),
        )
    )

    # 2. The Average Layer (A circle representing the population mean)
    avg_point = (
        alt.Chart(plot_df)
        .mark_point(filled=True, color="black", size=100)
        .encode(
            x="Population average:Q",
            y="Complications:N",
            tooltip=["Complications", "Population average", "Lower CI", "Upper CI"],
        )
    )

    # 3. The Patient Risk Layer (A vertical tick that changes color)
    # We use a conditional color: Red if > Avg, Green if <= Avg
    patient_tick = (
        alt.Chart(plot_df)
        .mark_tick(thickness=3, size=12)  # Height of the tick
        .encode(
            x="Risk percentage:Q",
            y="Complications:N",
            color=alt.condition(
                alt.datum["Risk percentage"] > alt.datum["Population average"],
                alt.value("red"),  # Higher than average
                alt.value("green"),  # Lower than average
            ),
            tooltip=["Complications", "Risk percentage"],
        )
    )

    # This places the percentage value at the end of the chart for readability
    text_labels = (
        alt.Chart(plot_df)
        .mark_text(
            align="left",
            baseline="middle",
            dx=10,  # Shifts text to the right of the anchor point
            fontWeight="bold",
        )
        .encode(
            x=alt.value(500),  # Fixed pixel position
            y=alt.Y("Complications:N", sort=None),
            text=alt.Text(
                "Risk percentage:Q", format=".1f"
            ),  # Formats to 1 decimal place
            color=alt.condition(
                alt.datum["Risk percentage"] > alt.datum["Population average"],
                alt.value("red"),
                alt.value("green"),
            ),
        )
    )

    # Combine layers
    chart = (error_bars + avg_point + patient_tick + text_labels).properties(
        title="Patient risk vs. Population average (95% CI)"
    )

    if display == "table":
        # Create table in column 2
        st.write("**Risk summary**")
        # Format the dataframe for display
        display_df = plot_df.copy()

        # Adding a 'Status' column for a quick visual cue
        display_df["Status"] = display_df.apply(
            lambda x: (
                "⚠️ Higher"
                if x["Risk percentage"] > x["Population average"]
                else "✅ Lower"
            ),
            axis=1,
        )

        display_df["Population average"] = display_df.apply(
            lambda x: f"{x["Population average"]:.1f}, 95% CI [{x["Lower CI"]:.1f}, {x["Upper CI"]:.1f}]",
            axis=1,
        )

        table_to_display = display_df[
            ["Complications", "Risk percentage", "Population average", "Status"]
        ]

        # Use st.dataframe or st.table for a clean look
        st.dataframe(
            table_to_display.style.format({"Risk percentage": "{:.1f}%"}),
            column_config={
                "Complications": "Complications",
                "Risk percentage": "Patient risk",
                "Population average": "Population average (95% CI)",
                "Status": "Status",
            },
            hide_index=True,
            width="stretch",
        )
        st.info("Sort the table columns by clicking on the column name")
    else:
        st.altair_chart(chart)
        with st.expander("See graph interpretation"):
            st.write("""
                     The chart above shows the current patient's risk relative to the
                     average population risk for the selected operation. The black circle
                     and horizontal bars represent the average population risk and 95% 
                     confidence intervals. The vertical bars represent the current patient's
                     risk, with the exact value specified on the right side of the graph.
                     If the risk is lower than the population average the bars are green,
                     otherwise, they are red.
            """)
