"""
main_page.py

Streamlit ASSURE app main page.
"""

import streamlit as st
from numpy import array, zeros

from src.app_fn import (
    get_report_date,
    init_outcome_toggles,
    load_averages,
    load_pipeline,
    main_page_layout,
    show_consent_page,
    sync_complication_toggles,
    sync_health_outcome_toggles,
    sync_master_toggle,
    sync_mortality_outcome_toggles,
)
from src.constants import LABEL_MAP, UNAVAILABLE_KEYS
from src.reporting import create_pdf_report
from src.visualisation import data_visualisation, hide_chart_toolbar

main_col1, _ = st.columns([0.7, 0.3])

with main_col1:
    if not st.session_state.consent:
        show_consent_page()
    else:
        input_features = main_page_layout()
        is_ready = input_features is not None  # Define the is_ready flag

        with st.spinner("Loading model and data..."):
            pipeline = load_pipeline()
            regressor_pipeline = load_pipeline("regressor")
            averages = load_averages()

        run = st.button("Run model", disabled=not is_ready)
        info_col, _ = st.columns([3, 1], vertical_alignment="bottom", gap="medium")
        if input_features is not None:
            if run:
                # Run classifier
                outcomes = pipeline.mp_config.data.outcomes
                output_proba = zeros((len(outcomes), 1, 2))
                for i, outcome in enumerate(outcomes):
                    output_proba[i, :, :] = pipeline.predict_proba(
                        input_features, outcome=outcome
                    )[0]

                st.session_state.output_proba = {
                    outcomes[i]: 100 * array(output_proba)[i, 0, 1]
                    for i in range(len(outcomes))
                }  # Reshape to create dictionary with only positive probas

                # Run regressor
                outcomes = regressor_pipeline.mp_config.data.outcomes
                st.session_state.output_dists = {}

                for outcome in outcomes:
                    st.session_state.output_dists[outcome] = (
                        regressor_pipeline.predict_dist(
                            input_features,
                            outcome=outcome,
                        )
                    )

                # Keep what the results were computed from, so they stay consistent
                # if the inputs are edited afterwards
                st.session_state.run_inputs = input_features
                st.session_state.run_category = input_features["CATEGORY_LEVEL_2"].iloc[
                    0
                ]
                st.session_state.model_run = True  # Models have now been run
            with info_col:
                st.info(
                    "To generate results with new data, please click on 'Run model' again."
                )
        else:
            with info_col:
                st.info("Please fill out all fields to enable the 'Run model' button.")

    if (
        st.session_state.model_run
        and st.session_state.consent
        and st.session_state.run_category is not None
    ):
        cat_l2 = st.session_state.run_category  # Category the model was run with

        # If the model has been run
        st.header("Results", divider="rainbow")
        hide_chart_toolbar()
        if input_features is None or not input_features.equals(
            st.session_state.run_inputs
        ):
            st.warning(
                "The inputs have changed since the model was last run. The results "
                "below are for the previous inputs."
            )
        st.write("""Select one of the tabs below to view the desired results.""")
        st.write("""
                 The outcomes can be toggled on and off using the switches. The
                 model does **not** need to be re-run to view different
                 outcomes.

                 """)
        st.write("""
                The results can be viewed as a graph or as a table. Select the desired 
                visualisation by selecting the display type.
                """)

        op_average = averages.get(cat_l2)
        if op_average is None:
            st.error(
                "Population averages are not available for this operation category."
            )
            st.stop()
        display_options = {"graph": "Graph", "table": "Table"}
        init_outcome_toggles()
        mortality_tab, comp_tab, health_tab = st.tabs(
            [
                "**Mortality**",
                "**Postoperative complications**",
                "**Health service use**",
            ]
        )

        mortality_outcomes_dict = LABEL_MAP["MORTALITY_OUTCOMES"]
        complications_dict = LABEL_MAP["COMPLICATIONS"]
        health_outcomes_dict = LABEL_MAP["HEALTH_OUTCOMES"]

        with mortality_tab:
            st.subheader("Mortality outcomes")

            # Create mortality outcomes layout
            st.toggle(
                mortality_outcomes_dict["MORTALITY_OUTCOMES"],
                key="MORTALITY_OUTCOMES",
                on_change=sync_mortality_outcome_toggles,
            )

            with st.container(horizontal=False):
                for key in mortality_outcomes_dict:
                    if key == "MORTALITY_OUTCOMES":
                        continue
                    st.toggle(
                        mortality_outcomes_dict[key],
                        key=key,
                        on_change=sync_master_toggle,
                        args=("MORTALITY_OUTCOMES",),
                    )

            # Create the graph/table toggle
            st.pills(
                "**Display type**",
                key="mortality_display_option",
                options=display_options.keys(),
                format_func=lambda option: display_options[option],
                selection_mode="single",
                default="graph",
            )

            mortality_chart, mortality_table, *_mortality_regressors = (
                data_visualisation(
                    mortality_outcomes_dict,
                    op_average,
                    display=st.session_state.mortality_display_option,
                )
            )

        with comp_tab:
            # Create complications layout
            st.subheader("Postoperative complications")

            st.toggle(
                complications_dict["COMPLICATIONS"],
                key="COMPLICATIONS",
                on_change=sync_complication_toggles,
            )

            with st.container():
                comp_col1, comp_col2, comp_col3, comp_col4 = st.columns(4)
                comp_len = len(complications_dict)
                for i, key in enumerate(complications_dict.keys()):
                    if i >= 3 * comp_len / 4:
                        col = comp_col4
                    elif i >= 2 * comp_len / 4:
                        col = comp_col3
                    elif i >= comp_len / 4:
                        col = comp_col2
                    else:
                        col = comp_col1
                    with col:
                        if key == "COMPLICATIONS":
                            continue
                        else:
                            st.toggle(
                                complications_dict[key],
                                key=key,
                                on_change=sync_master_toggle,
                                args=("COMPLICATIONS",),
                            )

                # Create the graph/table toggle
                st.pills(
                    "**Display type**",
                    key="comp_display_option",
                    options=display_options.keys(),
                    format_func=lambda option: display_options[option],
                    selection_mode="single",
                    default="graph",
                )

                comp_chart, comp_table, *_comp_regressors = data_visualisation(
                    complications_dict,
                    op_average,
                    display=st.session_state.comp_display_option,
                )

        with health_tab:
            st.subheader("Health Service use")

            # Create health outcomes layout
            st.toggle(
                health_outcomes_dict["HEALTH_OUTCOMES"],
                key="HEALTH_OUTCOMES",
                on_change=sync_health_outcome_toggles,
            )

            with st.container():
                health_outcomes_col1, health_outcomes_col2 = st.columns(2)
                for i, key in enumerate(health_outcomes_dict.keys()):
                    if i >= len(health_outcomes_dict) / 2:
                        col = health_outcomes_col2
                    else:
                        col = health_outcomes_col1

                    with col:
                        if key == "HEALTH_OUTCOMES":
                            continue
                        if key in UNAVAILABLE_KEYS:
                            st.toggle(  # Disable because coming soon
                                health_outcomes_dict[key], key=key, disabled=True
                            )
                        else:
                            st.toggle(
                                health_outcomes_dict[key],
                                key=key,
                                on_change=sync_master_toggle,
                                args=("HEALTH_OUTCOMES",),
                            )

                # Create the graph/table toggle
                st.pills(
                    "**Display type**",
                    key="health_display_option",
                    options=display_options.keys(),
                    format_func=lambda option: display_options[option],
                    selection_mode="single",
                    default="graph",
                )

                (
                    health_chart,
                    health_table,
                    daoh_chart,
                    los_chart,
                    regressor_table,
                ) = data_visualisation(
                    health_outcomes_dict,
                    op_average,
                    display=st.session_state.health_display_option,
                )

        # The report is only generated when the button is clicked, since rendering
        # the charts is slow and the script reruns on every interaction
        report_date = get_report_date()

        def build_report() -> bytes:
            return create_pdf_report(
                [mortality_chart, comp_chart, health_chart],
                [mortality_table, comp_table, health_table],
                regressor_charts=[daoh_chart, los_chart],
                regressor_table=regressor_table,
                report_date=report_date,
            )

        st.download_button(
            label="Download PDF report",
            data=build_report,
            file_name="patient_risk_report.pdf",
            mime="application/pdf",
            icon=":material/download:",
        )
