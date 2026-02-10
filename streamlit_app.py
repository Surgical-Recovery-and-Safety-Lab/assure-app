#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
streamlit_app.py

Streamlit NZ Risk Score app.
"""

import altair as alt
import streamlit as st
from numpy import array, expand_dims
from pandas import DataFrame, to_numeric
from pyrisk.models.core import load_pipeline

from constants import CATEGORIES, COLUMNS, ETHCNICITIES, GCH, LABEL_MAP


@st.cache_resource
def app_load_pipeline():
    """Load the pipeline"""
    pipeline = load_pipeline("models/ai_risk_HGB-v0.3.1.3-d.1.3.2.pkl")
    return pipeline


def convert_dtypes(data):
    """Convert datatypes to fit requirements"""
    for column in data.columns:
        if column in ["AGE", "M3_SCORE", "OP_SEVERITY", "DEP18_ORIGINAL"]:
            data[column] = to_numeric(data[column])
        if column in ["PRIOR_CANCER", "TRAUMA"]:
            data[column] = data[column].astype(bool)
    return data


def sync_toggles():
    """Sync the toggles based on the all toggle"""
    for key in LABEL_MAP.keys():
        st.session_state[key] = st.session_state.ALL


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


# Define session state variables
if "model_run" not in st.session_state:
    # Session state flag to check if model has run at least once
    st.session_state.model_run = False
if "output_proba" not in st.session_state:
    # Session state variable to keep output probabilities
    st.session_state.output_proba = array([])
if "consent" not in st.session_state:
    # Session state varible for consent
    st.session_state.consent = False

if not st.session_state.consent:
    show_consent_page()
else:
    st.title("NZ AI Risk Score")
    st.logo("assets/logo.png", size="large")

    st.header("Surgical risk score calculator", divider="rainbow")
    st.write(
        "The NZ AI Risk Score Calculator uses artificial intelligence to predict the risk of mortality and complications post-surgery. Input the patient information below and click on 'Run model' to generate the results."
    )
    st.write("Click on the 'Reset' button below if you do not want to continue.")
    st.button("Reset", on_click=lambda: st.session_state.update({"consent": False}))

    st.header("Data input", divider="rainbow")

    # Age input
    age = st.number_input(
        "**Age**",
        min_value=18,
        max_value=122,
        step=1,
        help="Patient age",
        value=None,
        placeholder="Age",
    )

    # Ethnicity selectbox
    ethnicity = st.selectbox(
        "**Ethnicity**",
        ETHCNICITIES,
        help="Patient ethnicity",
        index=None,
        placeholder="Select ethnicity",
    )

    # Sex radio buttons
    sex_map = {"M": "Male", "F": "Female"}
    sex = st.radio(
        "**Sex**",
        options=sex_map.keys(),
        format_func=lambda x: sex_map[x],
        index=None,
        help="Patient sex at birth",
    )

    # Cancer radio buttons
    cancer = st.radio(
        "**Prior cancer**",
        options=[True, False],
        format_func=lambda x: "Yes" if x else "No",
        index=1,
        help="Did the patient have cancer?",
    )

    # Acuity radio buttons
    acuity = st.radio(
        "**Admission acuity**",
        ["Elective", "Acute"],
        index=0,
        help="Is the surgery elective or acute?",
    )

    # Source radio buttons
    source = st.radio(
        "**Admission source**",
        ["Routine", "Transfer"],
        index=0,
        help="Is the patient transfered from another hospital?",
    )

    # Traum radio buttons
    trauma = st.radio(
        "**Trauma**",
        index=1,
        help="Trauma",
        options=[True, False],
        format_func=lambda x: "Yes" if x else "No",
    )

    # DEP slider
    dep = st.slider(
        "**NZDep**", min_value=1, max_value=10, step=1, help="NZ Index of Depravation"
    )

    # GCH selectbox
    gch = st.selectbox(
        "**GCH**",
        GCH,
        help="NZ Geographical Classification of Health",
        index=None,
        placeholder="Select GCH",
    )

    # M3 score input
    m3_score = st.number_input(
        "**M3 score**",
        min_value=0.0,
        step=0.001,
        help="Multimorbidity index",
        format="%.3f",
        value=None,
        placeholder="M3 score",
    )

    # Category L1 selectbox
    category_l1_options = [key for key in CATEGORIES.keys() if key is not None]
    category_l1 = st.selectbox(
        "**Surgical specialty**",
        category_l1_options,
        help="Surgical specialty of the operation",
        index=None,
        placeholder="Specialty",
    )

    # Category L2 selectbox (depends on L1)
    category_l2_disabled = True
    if category_l1:
        category_l2_disabled = False
    category_l2 = st.selectbox(
        "**Surgical sub-specialty**",
        CATEGORIES[category_l1],
        help="Surgical sub-specialty, select a specialty to see options",
        index=None,
        placeholder="Sub-specialty",
        disabled=category_l2_disabled,
    )

    # Op severity slider
    op_severity = st.slider(
        "**Operation severity**",
        min_value=1,
        max_value=5,
        help="Operation severity",
        step=1,
    )

    input_features = [
        age,
        ethnicity,
        sex,
        dep,
        gch,
        m3_score,
        cancer,
        "Auckland City Hospital",
        acuity,
        source,
        category_l1,
        category_l2,
        op_severity,
        trauma,
    ]
    is_ready = None not in input_features  # Define the is_ready flag

    run_model_col, run_info_col = st.columns(2, vertical_alignment="center")
    with run_model_col:
        run = st.button("Run model", disabled=not is_ready)
    with run_info_col:
        if is_ready:
            if run:
                # Your model code here
                pipeline = app_load_pipeline()
                label_list = pipeline.label_list
                data = DataFrame(expand_dims(input_features, 1).T, columns=COLUMNS)
                input_data = pipeline.transform(convert_dtypes(data))
                output_proba = pipeline.predict_proba(
                    input_data, idx=-1, model_type="predictor"
                )
                st.session_state.output_proba = array(output_proba)[
                    :, 0, 1
                ]  # Reshape to only get positives
                st.session_state.model_run = True
            st.info(
                "To generate results with new data, please click on 'Run model' again."
            )
        else:
            st.info("Please fill out all fields to enable the 'Run model' button.")

    st.divider()
    if st.session_state.model_run:
        st.header("Results", divider="rainbow")
        st.subheader("Outcomes")
        st.write(
            "Please select the outcomes to visualise. There is no need to re-run the model to view different outcomes."
        )
        col1, col2, col3 = st.columns(3)
        selected_labels = []
        with col1:
            for i, key in enumerate(LABEL_MAP.keys()):
                if i >= len(LABEL_MAP) / 3:
                    # Break after passing the first third
                    break

                if key == "ALL":
                    toggle = st.toggle(LABEL_MAP[key], key=key, on_change=sync_toggles)
                else:
                    toggle = st.toggle(LABEL_MAP[key], key=key)
                selected_labels.append(toggle)
        with col2:
            for i, key in enumerate(LABEL_MAP.keys()):
                if i >= 2 * len(LABEL_MAP) / 3:
                    # Break after passing the second third
                    break

                if i >= len(LABEL_MAP) / 3:
                    selected_labels.append(st.toggle(LABEL_MAP[key], key=key))
        with col3:
            for i, key in enumerate(LABEL_MAP.keys()):
                if i >= 2 * len(LABEL_MAP) / 3:
                    selected_labels.append(st.toggle(LABEL_MAP[key], key=key))

        with st.container():
            labels = [
                LABEL_MAP[key]
                for key in LABEL_MAP.keys()
                if st.session_state[key] and key != "ALL"
            ]
            probabilities = st.session_state.output_proba[selected_labels[1:]]
            plot_df = DataFrame(
                {"Predicted outcomes": labels, "Probability": probabilities}
            )

            chart = (
                alt.Chart(plot_df)
                .mark_bar()
                .encode(
                    # Fix the X axis from 0 to 1
                    x=alt.X("Probability:Q", scale=alt.Scale(domain=[0, 1])),
                    # Sort by probability so the highest is at the top
                    y=alt.Y("Predicted outcomes:N", sort="-x"),
                    # Optional: Change color based on value
                    color=alt.Color("Probability:Q", scale=alt.Scale()),
                    tooltip=["Predicted outcomes", "Probability"],
                )
            )
            st.altair_chart(chart)
