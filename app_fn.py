#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
app_fn.py

Streamlit ASSURE helper functions.
"""

import base64
from datetime import datetime

import altair as alt
import joblib
import requests
import streamlit as st
import vl_convert as vlc
from pandas import DataFrame, to_numeric
from weasyprint import HTML

from constants import AVERAGES, CATEGORIES, LABEL_MAP, MODEL


@st.cache_resource(show_spinner=False)
def load_pipeline():
    """Load pipeline"""

    return joblib.load(MODEL)


@st.cache_resource(show_spinner=False)
def load_averages():
    """Load operation averages"""

    return joblib.load(AVERAGES)


def convert_dtypes(data):
    """Convert datatypes to fit requirements"""
    for column in data.columns:
        if column in [
            "AGE",
            "ASA",
            "OP_SEVERITY",
            "PRIOR_CANCER",
            "TRAUMA",
            "OP_SEVERITY",
        ]:
            data[column] = to_numeric(data[column], downcast="unsigned")
    return data


def sync_mortality_outcome_toggles():
    """Sync the mortality outcome toggles based on the all toggle"""
    for key in LABEL_MAP["MORTALITY_OUTCOMES"].keys():
        if key == "MORTALITY_OUTCOMES":
            continue
        st.session_state[key] = st.session_state.MORTALITY_OUTCOMES


def sync_health_outcome_toggles():
    """Sync the health service outcome toggles based on the all toggle"""
    for key in LABEL_MAP["HEALTH_OUTCOMES"].keys():
        if key in ["HEALTH_OUTCOMES", "FTR", "LOS", "DAOH"]:
            continue
        st.session_state[key] = st.session_state.HEALTH_OUTCOMES


def sync_complication_toggles():
    """Sync the complication toggles based on the all toggle"""
    for key in LABEL_MAP["COMPLICATIONS"].keys():
        if key == "COMPLICATIONS":
            continue
        st.session_state[key] = st.session_state.COMPLICATIONS


def init_outcome_toggles():
    """Initialise the keys used for the outcome toggles"""
    for master_key in ["MORTALITY_OUTCOMES", "COMPLICATIONS", "HEALTH_OUTCOMES"]:
        if master_key not in st.session_state:
            st.session_state[master_key] = True

        # Initialize all SUB-TOGGLES in that group to True as well
        for sub_key in LABEL_MAP[master_key].keys():
            if sub_key not in st.session_state:
                if sub_key in ["FTR", "DAOH", "LOS"]:
                    continue
                st.session_state[sub_key] = True


def show_consent_page():
    """Show consent page to user"""
    st.header("Disclaimer", divider="rainbow")
    st.warning("Please read the following carefully before proceeding.")

    st.write("""
    By using this tool, you agree to having the data you enter into the calculator
    processed by our AI model. Your information is not stored and is deleted after
    the window is closed.
    """)
    st.write("""
    The model outputs are for informational purposes only and should not be used in
    isolation to make clinical decisions.
    """)
    st.write("""
    ASSURE and the Surgical Recovery and Safety Lab are not responsible for decisions
    made by health care professionals or patients based on the information provided by
    this tool.
    """)
    if st.button("I Agree and Accept"):
        st.session_state.consent = True
        st.rerun()  # Rerun to immediately switch to the main app


def main_page_layout():
    """
    Main page layout for user input.

    Parameters
    ----------
    None
        No arguments are provided.

    Returns
    -------
    input_features : list
        List of the input features extracted from the user inputs.

    """
    st.header("Aotearoa's Smart SUrgical Risk Estimator")

    st.header("Data input", divider="rainbow")

    # Age input
    age_col1, _ = st.columns([3, 1], vertical_alignment="bottom", gap="medium")
    with age_col1:
        age = st.number_input(
            "**Age**",
            min_value=18,
            max_value=122,
            step=1,
            value=None,
            placeholder="Age",
        )

    # Sex radio buttons
    sex_map = {"M": "Male", "F": "Female"}
    sex = st.radio(
        "**Sex at birth**",
        options=sex_map.keys(),
        format_func=lambda x: sex_map[x],
        index=None,
        help="Patient sex **at birth**",
        horizontal=True,
    )

    # Ethnicity selectbox
    ethnicity_map = {
        "Asian": "Asian",
        "European": "NZ European",
        "Māori": "Māori",
        "MELAA/Other": "MELAA/Other",
        "Pacific peoples": "Pacific",
    }
    ethnicity_col1, _ = st.columns([3, 1], vertical_alignment="bottom", gap="medium")
    with ethnicity_col1:
        ethnicity = st.selectbox(
            "**Ethnicity**",
            options=ethnicity_map.keys(),
            format_func=lambda x: ethnicity_map[x],
            index=None,
            placeholder="Select ethnicity",
        )

    # Cancer radio buttons
    cancer = st.radio(
        "**Prior cancer**",
        options=[1, 0],
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
        options=[1, 0],
        format_func=lambda x: "Yes" if x else "No",
        horizontal=True,
    )

    # M3 score input
    asa_col1, asa_col2 = st.columns([3, 1], vertical_alignment="bottom", gap="medium")
    with asa_col1:
        asa_score = st.slider(
            "**ASA score**",
            min_value=1,
            max_value=5,
            value=1,
        )
    with asa_col2:
        with st.popover("Help", type="tertiary", icon=":material/help:"):
            st.write("**Amercian Society of Anaesthesiology -- Physical Status Score**")
            st.markdown("""
                1. Normal healthy patient
                2. Patient with mild systemic disease
                3. Patient with severe systemic disease
                4. Patient with severe systemic disease that is a constant threat to life
                5. Patient who is moribund and not suspected to survive without
                the operation
                """)
            st.page_link(
                "https://www.openanesthesia.org/keywords/asa-physical-status-classification/",
                label="More information",
                icon=":material/info:",
            )

    # Category L1 selectbox
    catl1_col1, _ = st.columns([3, 1], vertical_alignment="bottom", gap="medium")
    category_l1_options = [key for key in CATEGORIES.keys() if key is not None]

    with catl1_col1:
        category_l1 = st.selectbox(
            "**Surgical specialty**",
            category_l1_options,
            help="Surgical specialty of the operation",
            index=None,
            placeholder="Specialty",
        )

    # Category L2 selectbox (depends on L1)
    catl2_col1, _ = st.columns([3, 1], vertical_alignment="bottom", gap="medium")

    with catl2_col1:
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
    op_sev_col1, op_sev_col2 = st.columns(
        [3, 1], vertical_alignment="bottom", gap="medium"
    )
    with op_sev_col1:
        op_severity = st.slider(
            "**Operation severity**",
            min_value=1,
            max_value=5,
            step=1,
        )
    with op_sev_col2:
        with st.popover("Help", type="tertiary", icon=":material/help:"):
            st.write("**Operation severity**")
            st.write("""
                The operation severity score varies between 1 and 5.
                1 represents operation that have a low severity score, while 5 represents
                those with high severity.""")

    input_features = [
        age,
        ethnicity,
        sex,
        asa_score,
        cancer,
        acuity,
        source,
        category_l1,
        category_l2,
        op_severity,
        trauma,
    ]
    return input_features


def data_visualisation(complications_dict, op_average, display="graph"):
    """
    Visualise data in the web app.

    Returing chart and table to be able to download them later.

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
    chart : altair.Chart
        Chart plotting the graph results.
    table_to_display : pandas.DataFrame
        Table displayed.

    """
    # Empty list to store complications to plot
    comp_labels = []
    comp_outcomes_proba = []
    comp_average = []
    comp_lower = []
    comp_upper = []

    for key in complications_dict.keys():
        if st.session_state[key]:
            if key in ["COMPLICATIONS", "MORTALITY_OUTCOMES", "HEALTH_OUTCOMES"]:
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

    if plot_df.empty:
        # If all labels are unticked
        return alt.Chart(plot_df), plot_df

    x_max = plot_df.max(numeric_only=True).max() * 1.1

    # Adding a 'Risk status' column for a quick visual cue
    plot_df["Risk status"] = plot_df.apply(
        lambda x: (
            "Higher" if x["Risk percentage"] > x["Population average"] else "Lower"
        ),
        axis=1,
    )

    st.markdown(  # Hide table view and zoom options
        """
        <style>
        [data-testid="stElementToolbar"] {
            display: none !important;
        }
        </style>
    """,
        unsafe_allow_html=True,
    )
    # 1. The Confidence Interval Layer (The horizontal "whisker")
    error_bars = (
        alt.Chart(plot_df)
        .mark_errorbar()
        .encode(
            x=alt.X(
                "Lower CI:Q",
                title="Risk percentage (%)",
                scale=alt.Scale(domain=[0, x_max]),
            ),
            x2="Upper CI:Q",
            y=alt.Y("Complications:N", sort=None),
        )
    )

    # 2. The Average Layer (A circle representing the population mean)
    avg_point = (
        alt.Chart(plot_df)
        .mark_point(filled=True, color="black", size=50)
        .encode(
            x="Population average:Q",
            y="Complications:N",
            tooltip=["Complications", "Population average", "Lower CI", "Upper CI"],
        )
    )

    # 3. The Patient Risk Layer (A vertical tick that changes color)
    # We use a conditional color: Red if > Avg, Green if <= Avg
    patient_bars = (
        alt.Chart(plot_df)
        .mark_bar(cornerRadiusEnd=25, opacity=0.5)  # Bar graph
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
            dx=10,
            fontWeight="bold",
            clip=False,
        )
        .encode(
            x=alt.datum(x_max),  # Fixed pixel position
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

    status_text = (
        alt.Chart(plot_df)
        .mark_text(
            align="left",
            baseline="middle",
            dx=40,
            fontWeight="bold",
            clip=False,
        )
        .encode(
            y=alt.Y("Complications:N", sort=None),
            x=alt.datum(x_max),  # Anchored to the same spot, but shifted right via dx
            text="Risk status:N",
            color=alt.condition(
                alt.datum["Risk percentage"] > alt.datum["Population average"],
                alt.value("red"),
                alt.value("green"),
            ),
        )
    )

    # Combine layers
    chart = (
        (patient_bars + error_bars + avg_point + text_labels + status_text)
        .properties(
            height=alt.Step(30),  # Gives every row consistent breathing room
            title="Patient risk vs. Population average (95% CI)",
        )
        .configure_axis(
            grid=False,  # Remove distracting lines
            domain=False,  # Remove the 'L' shape axis lines
            labelFontSize=12,
        )
        .configure_view(strokeWidth=0)  # Remove the border box
        .configure_title(fontSize=16, anchor="middle")
    )

    # Create table in column 2
    st.write("**Risk summary**")
    # Format the dataframe for display
    display_df = plot_df.copy()

    display_df["Population average"] = display_df.apply(
        lambda x: f"{x["Population average"]:.1f}, 95% CI [{x["Lower CI"]:.1f}, {x["Upper CI"]:.1f}]",
        axis=1,
    )

    table_to_display = display_df[
        ["Complications", "Risk percentage", "Population average", "Risk status"]
    ]

    if display == "table":
        # Use st.dataframe or st.table for a clean look
        st.dataframe(
            table_to_display.style.format({"Risk percentage": "{:.1f}%"}).apply(
                highlight_medical_risk, axis=1
            ),
            column_config={
                "Complications": "Outcome",
                "Risk percentage": "Patient risk",
                "Population average": "Population average (95% CI)",
                "Risk status": "Risk status",
            },
            hide_index=True,
            width="stretch",
        )
        st.info("Sort the table columns by clicking on the column name")
    else:
        st.altair_chart(chart)
        st.write("""
                 The chart above shows the current patient's risk relative to the
                 average population risk for the selected operation.
                 """)
        st.write("""The black circle and horizontal bars
                 represent the average population risk and 95% 
                 confidence intervals.
                 """)
        st.write("""The red / green bars represent the current patient's
                 risk, with the exact value specified on the right side of the graph.
                 If the risk is lower than the population average the bars are green,
                 otherwise, they are red.
        """)

    return chart, table_to_display


def highlight_medical_risk(row):
    """Highlight the risk status in red or green and bold font."""
    # Create a list of styles for the whole row (defaulting to black)
    styles = ["color: black"] * len(row)

    risk_col_index = row.index.get_loc("Risk status")
    if row["Risk status"] == "Higher":
        # Find the index of the column you want to color
        styles[risk_col_index] = "color: red; font-weight: bold"
    else:
        styles[risk_col_index] = "color: green; font-weight: bold"

    return styles


def create_pdf_report(charts, tables):
    """
    Create a pdf report from the plots and tables.

    Assumes the mortality chart and tables are first.

    Parameters
    ----------
    charts : list[altair.Chart]
        List of charts plotting the outcome graph results.
    table : list[pandas.DataFrame]
        List of tables displaying the outcomes.

    Returns
    -------
    pdf : pdf bytes
        Pdf report.

    """
    # Headers aligned with the indices of charts/tables
    section_titles = ["Mortality outcomes", "Complications", "Health Service use"]

    # --- Generate the Sections Dynamically ---
    sections_html = ""

    # We zip everything together to iterate in one go
    for title, chart, df in zip(section_titles, charts, tables):
        png_data = vlc.vegalite_to_png(chart.to_dict(), scale=2)
        chart_b64 = base64.b64encode(png_data).decode("utf-8")

        # Build the table rows for this specific dataframe
        table_rows = "".join([f"""
            <tr>
                <td>{r.get("Complications", r.get("Outcome", "N/A"))}</td>
                <td>{r["Risk percentage"]:.1f}</td>
                <td>{r["Population average"]}</td>
                <td class="status-{"higher" if r["Risk status"] == "Higher" else "lower"}">{r["Risk status"]}</td>
            </tr>
        """ for _, r in df.iterrows()])

        # Create the HTML block for this section
        sections_html += f"""
        <div class="report-section" style="page-break-inside: avoid;">
            <div class="section-title">{title}</div>
            <div style="text-align: center; margin-bottom: 20px;">
                <img src="data:image/png;base64,{chart_b64}" style="width: 100%; max-width: 650px;">
            </div>
            <table>
                <thead>
                    <tr>
                        <th>Outcome</th>
                        <th>Patient Risk (%)</th>
                        <th>Population Avg (%)</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    {table_rows}
                </tbody>
            </table>
        </div>
        <hr style="border: 1px solid #eee; margin: 40px 0;">
        """

    date = datetime.now().strftime("%B %d, %Y")

    # --- Final HTML Assembly ---
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
        @page {{ size: A4; margin: 15mm; }}
        body {{ font-family: 'Segoe UI', sans-serif; color: #2c3e50; }}
        .report-header {{ border-bottom: 3px solid #3498db; padding-bottom: 10px; margin-bottom: 30px; }}
        .section-title {{ font-size: 16pt; color: #2980b9; border-left: 5px solid #3498db; padding-left: 10px; margin: 20px 0; }}
        table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; }}
        th {{ background-color: #3498db; color: white; text-align: left; padding: 12px; }}
        td {{ padding: 10px; border-bottom: 1px solid #ecf0f1; }}
        tr:nth-child(even) {{ background-color: #f9f9f9; }}
        .status-higher {{ color: #e74c3c; font-weight: bold; }}
        .status-lower {{ color: #27ae60; font-weight: bold; }}
    </style>
    </head>
    <body>
        <div class="report-header">
            <h1>Clinical Risk Assessment Report</h1>
            <p><strong>Comprehensive Patient Summary</strong> | Date: {date}</p>
        </div>
        {sections_html}
    </body>
    </html>
    """

    # Return the PDF as bytes
    return HTML(string=html_content).write_pdf()


def send_email(sender_email, subject, message) -> bool:
    """Send email from user feedback"""
    url = st.secrets["url"]
    data = {"email": sender_email, "subject": subject, "message": message}
    response = requests.post(url, data=data)
    return response.status_code == 200
