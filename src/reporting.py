"""PDF report of the patient results for the web app."""

import base64
import time
from html import escape
from pathlib import Path

import altair as alt
import pandas as pd
import vl_convert as vlc
from weasyprint import HTML

from .constants import (
    CAPPED_OUTCOMES_NOTE,
    COLOR_BLACK,
    COLOR_GREEN,
    COLOR_RED,
    COMPLICATIONS_WARNING,
    COMPLICATIONS_WARNING_EMPHASIS,
    COPYRIGHT,
    ETHNICITY_LABELS,
    RISK_DECIMALS,
    SEX_LABELS,
    SIMILAR_OPERATION_NOTE,
    VERSION,
)

FONTS_DIR = Path(__file__).resolve().parents[1] / "assets" / "fonts"


def _chart_to_base64(chart: alt.Chart | alt.LayerChart) -> str:
    """Render an Altair chart to a base64-encoded PNG.

    Parameters
    ----------
    chart : altair.Chart | altair.LayerChart
        Chart to render.

    Returns
    -------
    str
        Base64-encoded PNG image.
    """
    png_data = vlc.vegalite_to_png(chart.to_dict(), scale=2)
    return base64.b64encode(png_data).decode("utf-8")


def _empty_section_html(title: str) -> str:
    """Build the HTML for a report section with no selected outcomes.

    Parameters
    ----------
    title : str
        Section title.

    Returns
    -------
    str
        HTML for the section.
    """
    return f"""
    <div class="report-section" style="page-break-inside: avoid;">
        <div class="section-title">{escape(title)}</div>
        <div class="box">
            <strong>No outcomes were selected</strong>
        </div>
    </div>
    """


def _classifier_rows_html(df: pd.DataFrame) -> str:
    """Build the HTML table rows for the classifier results.

    Parameters
    ----------
    df : pandas.DataFrame
        Table with 'Complications', 'Risk percentage', 'Similar-operation mean',
        'Risk status' and 'Status label' columns.

    Returns
    -------
    str
        HTML ``<tr>`` rows.
    """
    return "".join(
        f"""
        <tr>
            <td>{escape(str(r.get("Complications", r.get("Outcome", "N/A"))))}</td>
            <td>{r["Risk percentage"]:.{RISK_DECIMALS}f}%</td>
            <td>{escape(str(r["Similar-operation mean"]))}</td>
            <td class="status-{escape(r["Risk status"].lower())}">{escape(r["Status label"])}</td>
        </tr>
        """
        for _, r in df.iterrows()
    )


def _regressor_status_class(row: pd.Series) -> str:
    """Pick the CSS class colouring the regressor status in the report.

    Parameters
    ----------
    row : pandas.Series
        Table row with 'Risk status' and 'Favourable' entries.

    Returns
    -------
    str
        "lower" (green) if favourable, "higher" (red) if not, else the status
        itself in lower case ("equal" or "unavailable").
    """
    if row["Risk status"] not in ("Higher", "Lower"):
        return row["Risk status"].lower()
    return "lower" if row["Favourable"] else "higher"


def _regressor_rows_html(df: pd.DataFrame) -> str:
    """Build the HTML table rows for the regressor results.

    Parameters
    ----------
    df : pandas.DataFrame
        Table with 'Complications', 'Prediction', 'Similar-operation mean',
        'Risk status', 'Status label' and 'Favourable' columns.

    Returns
    -------
    str
        HTML ``<tr>`` rows.
    """
    return "".join(
        f"""
        <tr>
            <td>{escape(str(r["Complications"]))}</td>
            <td>{escape(str(r["Prediction"]))}</td>
            <td>{escape(str(r["Similar-operation mean"]))}</td>
            <td class="status-{_regressor_status_class(r)}">{escape(r["Status label"])}</td>
        </tr>
        """
        for _, r in df.iterrows()
    )


def _block_html(
    charts: list[alt.Chart | alt.LayerChart], headers: list[str], table_rows: str
) -> str:
    """Build the HTML for one or more charts and their table.

    Parameters
    ----------
    charts : list[altair.Chart | altair.LayerChart]
        Charts to embed as images, in order, above the table.
    headers : list[str]
        Table column headers.
    table_rows : str
        HTML ``<tr>`` rows for the table body.

    Returns
    -------
    str
        HTML for the chart and table.
    """
    header_cells = "".join(f"<th>{escape(header)}</th>" for header in headers)
    images = "".join(
        f"""
        <div style="text-align: center; margin-bottom: 20px; break-inside: avoid;">
            <img src="data:image/png;base64,{_chart_to_base64(chart)}"
                 style="max-width: 650px; max-height: 175mm; width: auto; height: auto;">
        </div>
        """
        for chart in charts
    )
    return f"""
    <div>
        {images}
        <table>
            <thead>
                <tr>{header_cells}</tr>
            </thead>
            <tbody>
                {table_rows}
            </tbody>
        </table>
    </div>
    """


def _section_html(title: str, blocks: list[str], css_class: str = "") -> str:
    """Build the HTML for a report section made of one or more blocks.

    Parameters
    ----------
    title : str
        Section title.
    blocks : list[str]
        HTML blocks, such as those returned by `_block_html`.
    css_class : str, default ""
        Extra CSS class added to the section.

    Returns
    -------
    str
        HTML for the section.
    """
    return f"""
    <div class="report-section {css_class}">
        <div class="section-title">{escape(title)}</div>
        {"".join(blocks)}
    </div>
    """


def _patient_summary_html(inputs: pd.DataFrame, operation: str | None) -> str:
    """Build the HTML text summary of the patient and the operation.

    Parameters
    ----------
    inputs : pandas.DataFrame
        One-row input features the model was run with, as returned by
        `convert_input_features`.
    operation : str | None
        Description of the selected operation. Left out if missing.

    Returns
    -------
    str
        HTML for the patient summary section.
    """
    row = inputs.iloc[0]
    sex = SEX_LABELS.get(row["SEX_ORIGINAL"], row["SEX_ORIGINAL"]).lower()
    ethnicity = ETHNICITY_LABELS.get(
        row["ETHNICITY_ORIGINAL"], row["ETHNICITY_ORIGINAL"]
    )
    cancer = "with" if row["PRIOR_CANCER"] else "without"
    patient = (
        f"{int(row['AGE'])}-year-old {ethnicity} {sex} with an ASA score "
        f"{int(row['ASA_ORIGINAL'])} and {cancer} prior cancer."
    )

    source = (
        "transferred from another hospital"
        if row["ADMISSION_SOURCE"] == "Transfer"
        else "routine admission source"
    )
    trauma = "related to trauma" if row["TRAUMA"] else "not related to trauma"
    category = (
        f"{row['CATEGORY_LEVEL_1']}, {row['CATEGORY_LEVEL_2']}, "
        f"severity {row['OP_SEVERITY']}"
    )
    name = f"{operation} ({category})" if operation else category.capitalize()
    surgery = f"{name}. {row['ADMISSION_ACUITY']} surgery, {source}, {trauma}."

    blocks = [
        f"""
        <div class="subsection-title">Patient information</div>
        <p>{escape(patient)}</p>
        <div class="subsection-title">Operation information</div>
        <p>{escape(surgery)}</p>
        """
    ]
    return _section_html("ASSURE inputs summary", blocks, css_class="patient-summary")


def create_pdf_report(
    charts: list[alt.Chart | alt.LayerChart | None],
    tables: list[pd.DataFrame | None],
    regressor_chart: alt.Chart | alt.LayerChart | None = None,
    regressor_table: pd.DataFrame | None = None,
    report_date: str | None = None,
    with_average: bool = True,
    patient_inputs: pd.DataFrame | None = None,
    operation: str | None = None,
) -> bytes:
    """Create a pdf report from the plots and tables.

    Assumes the order is mortality, complications and health service use. The
    regressor results are added to the end of the health service use section.

    Parameters
    ----------
    charts : list[altair.Chart]
        Classifier charts for mortality, complications and health service use.
    tables : list[pandas.DataFrame]
        Classifier tables for mortality, complications and health service use.
        An empty table produces no chart or table for that section.
    regressor_chart : altair.Chart | None, default None
        Chart of the regressor results, shown above the regressor table in the
        health service use section. Skipped if missing.
    regressor_table : pandas.DataFrame | None, default None
        Table of the regressor results, with 'Complications' and 'Prediction'
        columns.

    report_date : str | None, default None
        Date shown in the report header. Defaults to today's date on the server.
    with_average : bool, default True
        Whether the similar-operation means are available for the operation. If
        not, the report says so in its notes.
    patient_inputs : pandas.DataFrame | None, default None
        One-row input features the model was run with, summarised after the
        notes. The summary is left out if missing.
    operation : str | None, default None
        Description of the selected operation, shown in the patient summary.

    Returns
    -------
    bytes
        Pdf report.
    """
    section_titles = ["Mortality outcomes", "Complications", "Health Service use"]
    # Regressor results only belong to the last section
    reg_charts = [] if regressor_chart is None else [regressor_chart]
    regressors = [None, None, (reg_charts, regressor_table)]

    sections_html = ""
    for title, chart, df, regressor in zip(
        section_titles, charts, tables, regressors, strict=True
    ):
        blocks = []

        if chart is not None and df is not None and not df.empty:
            blocks.append(
                _block_html(
                    [chart],
                    [
                        "Outcome",
                        "Patient Risk (%)",
                        "Similar-operation mean (%)",
                        "Status",
                    ],
                    _classifier_rows_html(df),
                )
            )

        if regressor is not None:
            reg_charts, reg_df = regressor
            if reg_df is not None and not reg_df.empty:
                blocks.append(
                    _block_html(
                        reg_charts,
                        [
                            "Outcome",
                            "Patient median prediction (days)",
                            "Similar-operation mean (days)",
                            "Status",
                        ],
                        _regressor_rows_html(reg_df),
                    )
                )

        if blocks:
            sections_html += _section_html(title, blocks)
        else:
            sections_html += _empty_section_html(title)

    # The complications warning only matters if complications are in the report
    complications_df = tables[1]
    warning_html = ""
    if complications_df is not None and not complications_df.empty:
        warning_html = (
            f"<li><strong>Warning:</strong> {escape(COMPLICATIONS_WARNING)} "
            f"<strong>{escape(COMPLICATIONS_WARNING_EMPHASIS)}</strong></li>"
        )

    average_html = ""
    if not with_average:
        average_html = (
            "<li><strong>Similar-operation means are not available for this "
            "operation category.</strong> The report only shows the patient's "
            "predictions.</li>"
        )

    summary_html = ""
    if patient_inputs is not None and not patient_inputs.empty:
        summary_html = _patient_summary_html(patient_inputs, operation)

    date = escape(report_date or time.strftime("%B %d, %Y", time.localtime()))

    # --- Final HTML Assembly ---
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
        @font-face {{ font-family: 'DejaVu Sans'; font-weight: normal;
            src: url('{(FONTS_DIR / "DejaVuSans.ttf").as_uri()}'); }}
        @font-face {{ font-family: 'DejaVu Sans'; font-weight: bold;
            src: url('{(FONTS_DIR / "DejaVuSans-Bold.ttf").as_uri()}'); }}
        @page {{
            size: A4;
            margin: 15mm;
            @bottom-center {{
                content: "ASSURE {COPYRIGHT}";
                font-family: 'DejaVu Sans', sans-serif;
                font-size: 8pt;
                color: #7f8c8d;
            }}
        }}
        body {{ font-family: 'DejaVu Sans', sans-serif; color: #2c3e50; }}
        .report-header {{ border-bottom: 3px solid #3498db; padding-bottom: 10px; margin-bottom: 30px; }}
        .section-title {{ font-size: 16pt; color: #2980b9; border-left: 5px solid #3498db; padding-left: 10px; margin: 20px 0; }}
        table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; font-size: 9pt; }}
        th {{ background-color: #3498db; color: white; text-align: left; padding: 12px; }}
        td {{ padding: 10px; border-bottom: 1px solid #ecf0f1; }}
        td:first-child {{ font-weight: bold; }}
        thead {{ display: table-header-group; }}  /* repeat on each page */
        tr {{ break-inside: avoid; }}
        .section-title {{ break-after: avoid; }}
        tr:nth-child(even) {{ background-color: #f9f9f9; }}
        .status-higher {{ color: {COLOR_RED}; font-weight: bold; }}
        .status-lower {{ color: {COLOR_GREEN}; font-weight: bold; }}
        .status-equal {{ color: {COLOR_BLACK}; font-weight: bold; }}
        .status-unavailable {{ color: {COLOR_BLACK}; }}
        .box {{
        background-color: #e8f4fd;
        border-radius: 5px;
        padding: 15px;
        font-size: 10pt;
        margin: 0 0 30px 0;
        }}
        /* Every results section after the first starts on a new page */
        .report-section:not(.patient-summary) ~ .report-section {{ break-before: page; }}
        .subsection-title {{ font-size: 12pt; font-weight: bold; color: #2980b9; margin: 12px 0 6px 0; }}
        .patient-summary p {{ font-size: 10pt; margin: 0 0 10px 0; }}
        .notes p {{ margin: 0 0 6px 0; }}
        .notes ul {{ margin: 0; padding-left: 18px; }}
        .notes li {{ margin-bottom: 4px; }}
    </style>
    </head>
    <body>
        <div class="report-header">
            <h1>Clinical Risk Assessment Report</h1>
            <p><strong>Comprehensive Patient Summary</strong> | Date: {date} | Version: {escape(VERSION)}</p>
        </div>
        <div class="box notes">
            <p><strong>How to read this report</strong></p>
            <ul>
                <li>{escape(SIMILAR_OPERATION_NOTE)}</li>
                <li>{escape(CAPPED_OUTCOMES_NOTE)}</li>
                {average_html}
                {warning_html}
                <li>The 95% CI is the confidence interval of the similar-operation
                mean. The 95% PI is the range in which the patient's true value is
                expected to fall with 95% probability.</li>
            </ul>
        </div>
        {summary_html}
        {sections_html}
    </body>
    </html>
    """

    # Return the PDF as bytes
    return HTML(string=html_content).write_pdf()
