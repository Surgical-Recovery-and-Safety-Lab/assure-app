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


@st.cache_resource
def app_load_pipeline():
    """Load the pipeline"""
    pipeline = load_pipeline(MODEL)
    return pipeline


@st.cache_resource
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


def data_visualisation():
    """
    Visualise data in the web app.

    Parameters
    ----------
    arg
        arg description.

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
        if st.session_state[key] and key != "COMPLICATIONS":
            comp_labels.append(complications_dict[key])
            comp_outcomes_proba.append(st.session_state.output_proba[key])
            comp_average.append(op_average[key][0] * 100)
            comp_lower.append(op_average[key][1] * 100)
            comp_upper.append(op_average[key][2] * 100)
    plot_df = DataFrame(
        {
            "Complications": comp_labels,
            "Risk percentage": comp_outcomes_proba,
            "Average risk": comp_average,
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
                scale=alt.Scale(domain=[0, 100]),
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
            x="Average risk:Q",
            y="Complications:N",
            tooltip=["Complications", "Average risk", "Lower CI", "Upper CI"],
        )
    )

    # 3. The Patient Risk Layer (A vertical tick that changes color)
    # We use a conditional color: Red if > Avg, Green if <= Avg
    patient_tick = (
        alt.Chart(plot_df)
        .mark_tick(thickness=4, size=30)  # Height of the tick
        .encode(
            x="Risk percentage:Q",
            y="Complications:N",
            color=alt.condition(
                alt.datum["Risk percentage"] > alt.datum["Average risk"],
                alt.value("red"),  # Higher than average
                alt.value("green"),  # Lower than average
            ),
            tooltip=["Complications", "Risk percentage"],
        )
    )

    # Combine layers
    chart = (error_bars + avg_point + patient_tick).properties(
        width=600, title="Patient Risk vs. Population Average (95% CI)"
    )

    st.altair_chart(chart)
