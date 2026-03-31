#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
app_fn.py

Streamlit NZ Risk Score app helper functions.
"""

from io import BytesIO

import altair as alt
import joblib
import streamlit as st
import vl_convert as vlc
from fpdf import FPDF
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
    st.session_state.COMPLICATIONS = True
    st.session_state.GLOBAL_OUTCOMES = True
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
    * the processing of your uploaded data by our AI model.
    * acknowledging that the model output is for informational purposes only.
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
            dx=10,
            fontWeight="bold",
        )
        .encode(
            x=alt.datum(100),  # Fixed pixel position
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

    # Create table in column 2
    st.write("**Risk summary**")
    # Format the dataframe for display
    display_df = plot_df.copy()

    # Adding a 'Risk status' column for a quick visual cue
    display_df["Risk status"] = display_df.apply(
        lambda x: (
            "Higher" if x["Risk percentage"] > x["Population average"] else "Lower"
        ),
        axis=1,
    )

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
                "Complications": "Complications",
                "Risk percentage": "Patient risk",
                "Population average": "Population average (95% CI)",
                "Risk status": "Risk status",
            },
            hide_index=True,
            width="stretch",
        )
        st.info("Sort the table columns by clicking on the column name")
    else:
        st.altair_chart(chart, width=600)
        with st.expander("See graph interpretation"):
            st.write("""
                     The chart above shows the current patient's risk relative to the
                     average population risk for the selected operation.
                     """)
            st.write("""The black circle
                     and horizontal bars represent the average population risk and 95% 
                     confidence intervals.
                     """)
            st.write("""The vertical bars represent the current patient's
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

    Assumes the global chart and tables are first.

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
    # Define some constant values
    graph_headers = ["Global outcomes graph", "Specific complication graph"]
    table_headers = ["Global outcomes table", "Specific complication table"]

    pdf = FPDF()
    pdf.add_font("DejaVu", "", "assets/fonts/DejaVuSans.ttf")
    pdf.add_font("DejaVu", "B", "assets/fonts/DejaVuSans-Bold.ttf")
    pdf.add_page()
    pdf.set_font("DejaVu", "B", 16)

    # --- Title ---
    pdf.cell(0, 10, "Patient Risk Assessment Report", align="C")
    pdf.ln(20)  # Line break

    # --- Convert Altair Chart to PNG Bytes ---
    # This turns the interactive web chart into a static image for the PDF
    for i, chart in enumerate(charts):
        png_data = vlc.vegalite_to_png(chart.to_dict(), scale=2)
        chart_img = BytesIO(png_data)

        # --- Insert Chart ---
        pdf.set_font("DejaVu", "B", 12)
        pdf.cell(40, 10, graph_headers[i])
        pdf.ln(10)
        # image(source, x, y, width)
        pdf.image(chart_img, x=10, y=None, w=180)
        pdf.ln(10)

    pdf.add_page()  # Add new page for table views

    # --- Insert Table Data ---
    for i, table in enumerate(tables):
        pdf.set_font("DejaVu", "B", 12)
        pdf.cell(40, 10, table_headers[i])
        pdf.ln(10)

        # Table Header
        pdf.set_font("DejaVu", "B", 10)
        pdf.cell(60, 10, "Complications", border=1, align="C")
        pdf.cell(35, 10, "Patient risk", border=1, align="C")
        pdf.cell(60, 10, "Population average (95% CI)", border=1, align="C")
        pdf.cell(35, 10, "Risk status", border=1, align="C")
        pdf.ln()

        # Table Rows
        pdf.set_font("DejaVu", "", 10)  # Reset to normal font
        for _, row in table.iterrows():
            # Write first three columns in normal black font
            pdf.cell(60, 10, str(row["Complications"]), border=1)
            pdf.cell(35, 10, f"{row['Risk percentage']:.1f}%", border=1)
            pdf.cell(60, 10, f"{row['Population average']}", border=1)

            # Set font and colour for Risk status
            pdf.set_font("DejaVu", "B", 10)  # Set bold font
            if row["Risk status"] == "Higher":
                pdf.set_text_color(200, 0, 0)  # Red font
            else:
                pdf.set_text_color(0, 128, 0)  # Green font

            pdf.cell(35, 10, f"{row['Risk status']}", border=1)
            pdf.ln()

            pdf.set_font("DejaVu", "", 10)  # Reset to normal font
            pdf.set_text_color(0, 0, 0)  # Reset to black

    return bytes(pdf.output())
