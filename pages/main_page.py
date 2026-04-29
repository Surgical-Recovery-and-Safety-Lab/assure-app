#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
main_page.py

Streamlit ASSuRE app main page.
"""

import streamlit as st
from numpy import array, expand_dims
from pandas import DataFrame

from app_fn import (
    convert_dtypes,
    create_pdf_report,
    data_visualisation,
    init_outcome_toggles,
    load_averages,
    load_pipeline,
    main_page_layout,
    show_consent_page,
    sync_complication_toggles,
    sync_global_outcome_toggles,
)
from constants import COLUMNS, LABEL_MAP

if not st.session_state.consent:
    show_consent_page()
else:
    input_features = main_page_layout()
    is_ready = None not in input_features  # Define the is_ready flag

    with st.spinner("Loading model and data..."):
        pipeline = load_pipeline()
        averages = load_averages()

    run = st.button("Run model", disabled=not is_ready)
    info_col, _ = st.columns([3, 1], vertical_alignment="bottom", gap="medium")
    if is_ready:
        if run:
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
        with info_col:
            st.info(
                "To generate results with new data, please click on 'Run model' again."
            )
    else:
        with info_col:
            st.info("Please fill out all fields to enable the 'Run model' button.")

    if st.session_state.model_run and input_features[8]:
        # If the model has been run
        st.header("Results", divider="rainbow")
        st.write("""Select one of the tabs to view the desired results.""")
        st.write("""
                 The outcomes can be toggled on and off using the switches. The All 
                 button in each tab activates or deactivates all the outcomes within 
                 that tab. The model does **not** need to be re-run to view different
                 outcomes.

                 """)
        st.write("""
                The results can be viewed as a graph or as a table. Select the desired 
                visualisation by selecting the display type.
                """)
        op_average = averages[input_features[8]]
        display_options = {"graph": "Graph", "table": "Table"}
        init_outcome_toggles()
        global_tab, comp_tab = st.tabs(["Global outcomes", "Specific complications"])

        with global_tab:
            st.subheader("Global outcomes")
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
                            toggle = st.toggle(
                                global_outcomes_dict[key],
                                key=key,
                            )

                # Empty list to store global outcomes to plot
                global_labels = []
                global_outcomes_proba = []
                global_average = []
                global_lower = []
                global_upper = []

                # Create the graph/table toggle
                global_display_option = st.pills(
                    "**Display type**",
                    key="global_display_option",
                    options=display_options.keys(),
                    format_func=lambda option: display_options[option],
                    selection_mode="single",
                    default="graph",
                )

                global_chart, global_table = data_visualisation(
                    global_outcomes_dict,
                    op_average,
                    display=st.session_state.global_display_option,
                )

        with comp_tab:
            # Create complications layout
            st.subheader("Specific complications")
            all_toggle = st.toggle(
                complications_dict["COMPLICATIONS"],
                key="COMPLICATIONS",
                on_change=sync_complication_toggles,
            )

            with st.container():
                comp_col1, comp_col2, comp_col3 = st.columns(3)
                for i, key in enumerate(complications_dict.keys()):
                    if i >= 2 * len(complications_dict) / 3:
                        col = comp_col3
                    elif i >= len(complications_dict) / 3:
                        col = comp_col2
                    else:
                        col = comp_col1
                    with col:
                        if key == "COMPLICATIONS":
                            continue
                        else:
                            toggle = st.toggle(
                                complications_dict[key],
                                key=key,
                            )

                # Empty list to store complications to plot
                comp_labels = []
                comp_outcomes_proba = []
                comp_average = []
                comp_lower = []
                comp_upper = []

                # Create the graph/table toggle
                comp_display_option = st.pills(
                    "**Display type**",
                    key="comp_display_option",
                    options=display_options.keys(),
                    format_func=lambda option: display_options[option],
                    selection_mode="single",
                    default="graph",
                )

                comp_chart, comp_table = data_visualisation(
                    complications_dict,
                    op_average,
                    display=st.session_state.comp_display_option,
                )

        pdf_bytes = create_pdf_report(
            [global_chart, comp_chart], [global_table, comp_table]
        )
        st.download_button(
            label="Download PDF report",
            data=pdf_bytes,
            file_name="patient_risk_report.pdf",
            mime="application/octet-stream",
            icon=":material/download:",
        )
