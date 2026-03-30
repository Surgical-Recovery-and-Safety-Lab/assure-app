#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
app.py

Streamlit NZ Risk Score app.
"""

import altair as alt
import streamlit as st
from numpy import array, expand_dims
from pandas import DataFrame

from app_fn import (
    app_load_averages,
    app_load_pipeline,
    convert_dtypes,
    data_visualisation,
    reset_app,
    show_consent_page,
    sync_complication_toggles,
    sync_global_outcome_toggles,
)
from constants import AVERAGES, CATEGORIES, COLUMNS, ETHCNICITIES, GCH, LABEL_MAP, MODEL

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
if "GLOBAL_OUTCOMES" not in st.session_state:
    # Session state variable for all global outcomes
    st.session_state.GLOBAL_OUTCOMES = False
if "COMPLICATIONS" not in st.session_state:
    # Session state variable for all global outcomes
    st.session_state.COMPLICATIONS = False


if not st.session_state.consent:
    show_consent_page()
else:
    st.title("PAIRS ANZ")
    st.logo("assets/logo.png", size="large")

    st.header("Surgical risk score calculator", divider="rainbow")
    st.write(
        "The PAIRS ANZ (Patient AI Risk Score Aotearoa New Zealand) uses artificial intelligence to predict the risk of mortality and complications post-surgery. Input the patient information below and click on 'Run model' to generate the results."
    )
    st.write("Click on the 'Reset' button below if you do not want to continue.")
    st.button("Reset", on_click=reset_app)

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
        horizontal=True,
    )

    # Cancer radio buttons
    cancer = st.radio(
        "**Prior cancer**",
        options=[True, False],
        format_func=lambda x: "Yes" if x else "No",
        index=1,
        help="Did the patient have cancer?",
        horizontal=True,
    )

    # Acuity radio buttons
    acuity = st.radio(
        "**Admission acuity**",
        ["Elective", "Acute"],
        index=0,
        help="Is the surgery elective or acute?",
        horizontal=True,
    )

    # Source radio buttons
    source = st.radio(
        "**Admission source**",
        ["Routine", "Transfer"],
        index=0,
        help="Is the patient transfered from another hospital?",
        horizontal=True,
    )

    # Traum radio buttons
    trauma = st.radio(
        "**Trauma**",
        index=1,
        help="Trauma",
        options=[True, False],
        format_func=lambda x: "Yes" if x else "No",
        horizontal=True,
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
    index = None
    if category_l1:
        category_l2_disabled = False
        if len(CATEGORIES[category_l1]) == 1:
            index = 0

    category_l2 = st.selectbox(
        "**Surgical sub-specialty**",
        CATEGORIES[category_l1],
        help="Surgical sub-specialty, select a specialty to see options",
        index=index,
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
                pipeline = app_load_pipeline()
                label_list = pipeline.label_list
                data = DataFrame(expand_dims(input_features, 1).T, columns=COLUMNS)
                input_data = pipeline.transform(convert_dtypes(data))
                output_proba = pipeline.predict_proba(
                    input_data, label_list="all", model_type="predictor"
                )
                st.session_state.output_proba = {
                    label_list[i]: 100 * array(output_proba)[i, 0, 1]
                    for i in range(len(label_list))
                }
                # Reshape to create dictionary with only positive probas
                st.session_state.model_run = True
            st.info(
                "To generate results with new data, please click on 'Run model' again."
            )
        else:
            st.info("Please fill out all fields to enable the 'Run model' button.")

    if st.session_state.model_run:
        # If the model has been run
        st.header("Results", divider="rainbow")

        averages = app_load_averages()
        op_average = averages[category_l2]

        st.subheader("Global outcomes")
        st.write(
            "Please select the global outcomes to visualise. There is no need to re-run the model to view different outcomes."
        )
        # Get global outcome and complication dictionaries
        global_outcomes_dict = LABEL_MAP["GLOBAL_OUTCOMES"]
        complications_dict = LABEL_MAP["COMPLICATIONS"]

        # Create global outcomes layout
        all_toggle = st.toggle(
            global_outcomes_dict["GLOBAL_OUTCOMES"],
            key="GLOBAL_OUTCOMES",
            on_change=sync_global_outcome_toggles,
        )

        with st.container():
            global_outcomes_col1, global_outcomes_col2 = st.columns(2)
            for i, key in enumerate(global_outcomes_dict.keys()):
                if i >= len(global_outcomes_dict) / 2:
                    col = global_outcomes_col2
                else:
                    col = global_outcomes_col1

                with col:
                    if key == "GLOBAL_OUTCOMES":
                        continue
                    else:
                        toggle = st.toggle(global_outcomes_dict[key], key=key)

            # Empty list to store global outcomes to plot
            global_labels = []
            global_outcomes_proba = []
            global_average = []
            global_lower = []
            global_upper = []

            for key in global_outcomes_dict.keys():
                if st.session_state[key] and key != "GLOBAL_OUTCOMES":
                    global_labels.append(global_outcomes_dict[key])
                    global_outcomes_proba.append(st.session_state.output_proba[key])
                    global_average.append(op_average[key][0] * 100)
                    global_lower.append(op_average[key][1] * 100)
                    global_upper.append(op_average[key][2] * 100)

            plot_df = DataFrame(
                {
                    "Complications": global_labels,
                    "Risk percentage": global_outcomes_proba,
                    "Average risk": global_average,
                    "Lower CI": global_lower,
                    "Upper CI": global_upper,
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

        # Create complications layout
        st.subheader("Complications")
        st.write(
            "Please select the complications to visualise. There is no need to re-run the model to view different outcomes."
        )

        all_toggle = st.toggle(
            complications_dict["COMPLICATIONS"],
            key="COMPLICATIONS",
            on_change=sync_complication_toggles,
        )

        with st.container():
            comp_col1, comp_col2, comp_col3, comp_col4 = st.columns(4)
            for i, key in enumerate(complications_dict.keys()):
                if i >= 3 * len(complications_dict) / 4:
                    col = comp_col4
                elif i >= 2 * len(complications_dict) / 4:
                    col = comp_col3
                elif i >= len(complications_dict) / 4:
                    col = comp_col2
                else:
                    col = comp_col1
                with col:
                    if key == "COMPLICATIONS":
                        continue
                    else:
                        toggle = st.toggle(complications_dict[key], key=key)

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
