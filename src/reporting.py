import base64
import time

import vl_convert as vlc
from weasyprint import HTML


def _chart_to_base64(chart):
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


def _empty_section_html(title):
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
        <div class="section-title">{title}</div>
        <div class="box">
            <strong>No outcomes were selected</strong>
        </div>
    </div>
    <hr style="border: 1px solid #eee; margin: 40px 0;">
    """


def _classifier_rows_html(df):
    """Build the HTML table rows for the classifier results.

    Parameters
    ----------
    df : pandas.DataFrame
        Table with 'Complications', 'Risk percentage', 'Population average' and
        'Risk status' columns.

    Returns
    -------
    str
        HTML ``<tr>`` rows.
    """
    return "".join(
        f"""
        <tr>
            <td>{r.get("Complications", r.get("Outcome", "N/A"))}</td>
            <td>{r["Risk percentage"]:.1f}</td>
            <td>{r["Population average"]}</td>
            <td class="status-{"higher" if r["Risk status"] == "Higher" else "lower"}">{r["Risk status"]}</td>
        </tr>
        """
        for _, r in df.iterrows()
    )


def _regressor_rows_html(df):
    """Build the HTML table rows for the regressor results.

    Parameters
    ----------
    df : pandas.DataFrame
        Table with 'Complications' and 'Prediction' columns.

    Returns
    -------
    str
        HTML ``<tr>`` rows.
    """
    return "".join(
        f"""
        <tr>
            <td>{r["Complications"]}</td>
            <td>{r["Prediction"]}</td>
        </tr>
        """
        for _, r in df.iterrows()
    )


def _section_html(title, chart, headers, table_rows):
    """Build the HTML for a report section with a chart and a table.

    Parameters
    ----------
    title : str
        Section title.
    chart : altair.Chart | altair.LayerChart
        Chart to embed as an image.
    headers : list[str]
        Table column headers.
    table_rows : str
        HTML ``<tr>`` rows for the table body.

    Returns
    -------
    str
        HTML for the section.
    """
    header_cells = "".join(f"<th>{header}</th>" for header in headers)
    return f"""
    <div class="report-section" style="page-break-inside: avoid;">
        <div class="section-title">{title}</div>
        <div style="text-align: center; margin-bottom: 20px;">
            <img src="data:image/png;base64,{_chart_to_base64(chart)}"
                 style="width: 100%; max-width: 650px;">
        </div>
        <table>
            <thead>
                <tr>{header_cells}</tr>
            </thead>
            <tbody>
                {table_rows}
            </tbody>
        </table>
    </div>
    <hr style="border: 1px solid #eee; margin: 40px 0;">
    """


def create_pdf_report(charts, tables):
    """Create a pdf report from the plots and tables.

    Assumes the order is mortality, complications, health service use
    (classifier) and health service use (regressor). The regressor table is
    recognised by its 'Prediction' column.

    Parameters
    ----------
    charts : list[altair.Chart | None]
        List of charts plotting the outcome graph results.
    tables : list[pandas.DataFrame | None]
        List of tables displaying the outcomes. A ``None`` or empty table
        produces a "No outcomes were selected" section.

    Returns
    -------
    bytes
        Pdf report.
    """
    # Headers aligned with the indices of charts/tables
    section_titles = [
        "Mortality outcomes",
        "Complications",
        "Health Service use",
        "Health Service use",
    ]

    sections_html = ""
    for title, chart, df in zip(section_titles, charts, tables, strict=True):
        if df is None or df.empty:
            sections_html += _empty_section_html(title)
        elif "Prediction" in df.columns:
            sections_html += _section_html(
                title,
                chart,
                ["Outcome", "Patient median prediction"],
                _regressor_rows_html(df),
            )
        else:
            sections_html += _section_html(
                title,
                chart,
                ["Outcome", "Patient Risk (%)", "Population Avg (%)", "Status"],
                _classifier_rows_html(df),
            )

    date = time.strftime("%B %d, %Y", time.localtime())

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
        .box {{
        background-color: #e8f4fd;
        border-radius: 5px;
        padding: 15px;
        font-size: 10pt;
        margin-top: 30px;
        }}
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
