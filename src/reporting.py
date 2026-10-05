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


def _block_html(chart, headers, table_rows):
    """Build the HTML for one chart and its table.

    Parameters
    ----------
    chart : altair.Chart | altair.LayerChart
        Chart to embed as an image.
    headers : list[str]
        Table column headers.
    table_rows : str
        HTML ``<tr>`` rows for the table body.

    Returns
    -------
    str
        HTML for the chart and table.
    """
    header_cells = "".join(f"<th>{header}</th>" for header in headers)
    return f"""
    <div style="page-break-inside: avoid;">
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
    """


def _section_html(title, blocks):
    """Build the HTML for a report section made of one or more blocks.

    Parameters
    ----------
    title : str
        Section title.
    blocks : list[str]
        HTML blocks returned by `_block_html`.

    Returns
    -------
    str
        HTML for the section.
    """
    return f"""
    <div class="report-section">
        <div class="section-title">{title}</div>
        {"".join(blocks)}
    </div>
    <hr style="border: 1px solid #eee; margin: 40px 0;">
    """


def create_pdf_report(
    charts,
    tables,
    regressor_chart=None,
    regressor_table=None,
):
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
        Chart of the regressor results, shown in the health service use section.
    regressor_table : pandas.DataFrame | None, default None
        Table of the regressor results, with 'Complications' and 'Prediction'
        columns.

    Returns
    -------
    bytes
        Pdf report.
    """
    section_titles = ["Mortality outcomes", "Complications", "Health Service use"]
    # Regressor results only belong to the last section
    regressors = [None, None, (regressor_chart, regressor_table)]

    sections_html = ""
    for title, chart, df, regressor in zip(
        section_titles, charts, tables, regressors, strict=True
    ):
        blocks = []

        if df is not None and not df.empty:
            blocks.append(
                _block_html(
                    chart,
                    ["Outcome", "Patient Risk (%)", "Population Avg (%)", "Status"],
                    _classifier_rows_html(df),
                )
            )

        if regressor is not None:
            reg_chart, reg_df = regressor
            if reg_df is not None and not reg_df.empty:
                blocks.append(
                    _block_html(
                        reg_chart,
                        ["Outcome", "Patient median prediction"],
                        _regressor_rows_html(reg_df),
                    )
                )

        if blocks:
            sections_html += _section_html(title, blocks)
        else:
            sections_html += _empty_section_html(title)

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
