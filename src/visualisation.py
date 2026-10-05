"""Risk visualisation (chart and table) for the web app."""

from typing import Literal

import altair as alt
import streamlit as st
from pandas import DataFrame, Series

from .constants import (
    EXCLUDED_KEYS,
    LEGEND_AVERAGE,
    LEGEND_HIGHER,
    LEGEND_LOWER,
    LEGEND_MEDIAN,
    REGRESSOR_KEYS,
)


# --------------------------------------------------------------------------- #
# Data preparation
# --------------------------------------------------------------------------- #
def _build_classifier_plot_df(
    complications_dict: dict[str, str],
    op_average: dict[str, tuple[float, float, float]],
) -> DataFrame:
    """Collect the selected classifier complications into a DataFrame.

    Parameters
    ----------
    complications_dict : dict[str, str]
        Dictionary containing the complications and the corresponding plot label.
    op_average : dict[str, tuple[float, float, float]]
        Operation averages (mean, lower CI, upper CI) for each complication,
        expressed as proportions.

    Returns
    -------
    pandas.DataFrame
        One row per ticked complication. Empty if nothing is ticked.
    """
    labels, patient_risk, average, lower, upper = [], [], [], [], []

    for key, label in complications_dict.items():
        if not st.session_state[key] or key in EXCLUDED_KEYS + REGRESSOR_KEYS:
            continue
        labels.append(label)
        patient_risk.append(st.session_state.output_proba[key])
        average.append(op_average[key][0] * 100)
        lower.append(op_average[key][1] * 100)
        upper.append(op_average[key][2] * 100)

    return DataFrame(
        {
            "Complications": labels,
            "Risk percentage": patient_risk,
            "Population average": average,
            "Lower CI": lower,
            "Upper CI": upper,
        }
    )


def _build_regressor_plot_df(complications_dict: dict[str, str]) -> DataFrame:
    """Collect the selected regressor complications into a DataFrame.

    Parameters
    ----------
    complications_dict : dict[str, str]
        Dictionary containing the complications and the corresponding plot label.

    Returns
    -------
    pandas.DataFrame
        One row per ticked complication. Empty if nothing is ticked.
    """
    labels, prediction, lower, upper = [], [], [], []

    for key, label in complications_dict.items():
        if not st.session_state[key] or key not in REGRESSOR_KEYS:
            continue
        labels.append(label)
        dist = st.session_state.output_dists[key]
        prediction.append(round(dist.median()[0]))  # To get an integer
        l, u = dist.interval(0.95)
        lower.append(round(l[0]))  # To get an integer
        upper.append(round(u[0]))  # To get an integer

    return DataFrame(
        {
            "Complications": labels,
            "Median prediction": prediction,
            "Lower PI": lower,
            "Upper PI": upper,
        }
    )


def _add_risk_status(plot_df: DataFrame) -> DataFrame:
    """Add a 'Risk status' column for a quick visual cue.

    Parameters
    ----------
    plot_df : pandas.DataFrame
        Data returned by `_build_classifier_plot_df`.

    Returns
    -------
    pandas.DataFrame
        The same DataFrame with a 'Risk status' column ("Higher" or "Lower").
    """
    plot_df["Risk status"] = plot_df.apply(
        lambda row: (
            "Higher" if row["Risk percentage"] > row["Population average"] else "Lower"
        ),
        axis=1,
    )
    return plot_df


# --------------------------------------------------------------------------- #
# Shared chart encodings
# --------------------------------------------------------------------------- #
def _legend_color() -> alt.Color:
    """Create the colour encoding shared by the layers that feed the legend.

    The same field name and scale across layers merges them into one legend.

    Returns
    -------
    altair.Color
        Colour encoding on the ``Legend`` field.
    """
    return alt.Color(
        "Legend:N",
        scale=alt.Scale(
            domain=[LEGEND_AVERAGE, LEGEND_LOWER, LEGEND_HIGHER],
            range=["black", "green", "red", "black"],
        ),
        legend=alt.Legend(
            title=None,
            orient="top",
            direction="horizontal",
            labelFontSize=12,
        ),
    )


def _regressor_legend_color() -> alt.Color:
    """Create the regressor colour encoding shared by the layers feeding the legend.

    The same field name and scale across layers merges them into one legend.

    Returns
    -------
    altair.Color
        Colour encoding on the ``Legend`` field.
    """
    return alt.Color(
        "Legend:N",
        scale=alt.Scale(
            domain=["Median prediction (95% PI)"],
            range=["black"],
        ),
        legend=alt.Legend(
            title=None,
            orient="top",
            direction="horizontal",
            labelFontSize=12,
        ),
    )


def _y_encoding() -> alt.Y:
    """Create the y encoding shared by all layers.

    Returns
    -------
    altair.Y
        Complication names, in data order, with truncation disabled.
    """
    return alt.Y(
        "Complications:N",
        sort=None,
        axis=alt.Axis(
            labelLimit=0,  # 0 disables truncation
            labelLineHeight=14,  # spacing between the two lines
            labelFontSize=12,
            title=None,
        ),
    )


def _status_color() -> dict:
    """Create the red / green condition used by the text layers.

    Returns
    -------
    altair.condition
        Red if the patient risk is above the population average, else green.
    """
    return alt.condition(
        alt.datum["Risk percentage"] > alt.datum["Population average"],
        alt.value("red"),
        alt.value("green"),
    )


# --------------------------------------------------------------------------- #
# Chart layers (one helper per element)
# --------------------------------------------------------------------------- #
def _error_bars_layer(plot_df: DataFrame, y_enc: alt.Y, x_max: float) -> alt.Chart:
    """Build the horizontal 95% CI whiskers.

    Parameters
    ----------
    plot_df : pandas.DataFrame
        Data to plot.
    y_enc : altair.Y
        Shared y encoding.
    x_max : float
        Upper limit of the x axis.

    Returns
    -------
    altair.Chart
        Error bar layer.
    """
    return (
        alt.Chart(plot_df)
        .mark_errorbar(color="black")  # explicit, since it isn't colour-encoded
        .encode(
            x=alt.X(
                "Lower CI:Q",
                title="Risk percentage (%)",
                scale=alt.Scale(domain=[0, x_max]),
            ),
            x2="Upper CI:Q",
            y=y_enc,
        )
    )


def _average_point_layer(
    plot_df: DataFrame, y_enc: alt.Y, legend_color: alt.Color
) -> alt.Chart:
    """Build the circle marking the population average.

    Parameters
    ----------
    plot_df : pandas.DataFrame
        Data to plot.
    y_enc : altair.Y
        Shared y encoding.
    legend_color : altair.Color
        Shared legend colour encoding.

    Returns
    -------
    altair.Chart
        Population average layer.
    """
    return (
        alt.Chart(plot_df)
        .transform_calculate(Legend=f"'{LEGEND_AVERAGE}'")
        .mark_point(filled=True, size=50)  # colour comes from the encoding
        .encode(
            x="Population average:Q",
            y=y_enc,
            color=legend_color,
            tooltip=["Complications", "Population average", "Lower CI", "Upper CI"],
        )
    )


def _patient_bars_layer(
    plot_df: DataFrame, y_enc: alt.Y, legend_color: alt.Color
) -> alt.Chart:
    """Build the patient risk bars, red if above average and green otherwise.

    Parameters
    ----------
    plot_df : pandas.DataFrame
        Data to plot.
    y_enc : altair.Y
        Shared y encoding.
    legend_color : altair.Color
        Shared legend colour encoding.

    Returns
    -------
    altair.Chart
        Patient risk layer.
    """
    return (
        alt.Chart(plot_df)
        .transform_calculate(
            Legend=(
                "datum['Risk percentage'] > datum['Population average'] "
                f"? '{LEGEND_HIGHER}' : '{LEGEND_LOWER}'"
            )
        )
        .mark_bar(cornerRadiusEnd=25, opacity=0.5)
        .encode(
            x="Risk percentage:Q",
            y=y_enc,
            color=legend_color,
            tooltip=["Complications", "Risk percentage"],
        )
    )


def _risk_value_text_layer(
    plot_df: DataFrame, y_enc: alt.Y, x_max: float
) -> alt.Chart:
    """Build the patient risk value shown at the right-hand end of each row.

    Parameters
    ----------
    plot_df : pandas.DataFrame
        Data to plot.
    y_enc : altair.Y
        Shared y encoding.
    x_max : float
        Upper limit of the x axis, used to anchor the text.

    Returns
    -------
    altair.Chart
        Risk value text layer.
    """
    return (
        alt.Chart(plot_df)
        .mark_text(
            align="left",
            baseline="middle",
            dx=10,
            fontWeight="bold",
            clip=False,
        )
        .encode(
            x=alt.datum(x_max),
            y=y_enc,
            text=alt.Text("Risk percentage:Q", format=".1f"),
            color=_status_color(),
        )
    )


def _risk_status_text_layer(
    plot_df: DataFrame, y_enc: alt.Y, x_max: float
) -> alt.Chart:
    """Build the 'Higher' / 'Lower' label shown next to the risk value.

    Parameters
    ----------
    plot_df : pandas.DataFrame
        Data to plot.
    y_enc : altair.Y
        Shared y encoding.
    x_max : float
        Upper limit of the x axis, used to anchor the text.

    Returns
    -------
    altair.Chart
        Risk status text layer.
    """
    return (
        alt.Chart(plot_df)
        .mark_text(
            align="left",
            baseline="middle",
            dx=40,  # same anchor as the value text, shifted right
            fontWeight="bold",
            clip=False,
        )
        .encode(
            x=alt.datum(x_max),
            y=y_enc,
            text="Risk status:N",
            color=_status_color(),
        )
    )


def _median_prediction_layer(
    plot_df: DataFrame, y_enc: alt.Y, legend_color: alt.Color
) -> alt.Chart:
    """Build the circle marking the patient's median prediction.

    Parameters
    ----------
    plot_df : pandas.DataFrame
        Data to plot.
    y_enc : altair.Y
        Shared y encoding.
    legend_color : altair.Color
        Shared legend colour encoding.

    Returns
    -------
    altair.Chart
        Median prediction layer.
    """
    return (
        alt.Chart(plot_df)
        .transform_calculate(Legend=f"'{LEGEND_MEDIAN}'")
        .mark_point(filled=True, size=50)
        .encode(
            x="Median prediction:Q",
            y=y_enc,
            color=legend_color,
            tooltip=["Complications", "Median prediction", "Lower PI", "Upper PI"],
        )
    )


def _prediction_bars_layer(plot_df: DataFrame, y_enc: alt.Y) -> alt.Chart:
    """Build the horizontal 95% PI whiskers.

    Parameters
    ----------
    plot_df : pandas.DataFrame
        Data to plot.
    y_enc : altair.Y
        Shared y encoding.

    Returns
    -------
    altair.Chart
        Prediction interval error bar layer.
    """
    return (
        alt.Chart(plot_df)
        .mark_errorbar(color="black")  # explicit, since it isn't colour-encoded
        .encode(
            x=alt.X(
                "Lower PI:Q",
                title="Prediction (days)",
                scale=alt.Scale(domain=[0, 90]),
            ),
            x2="Upper PI:Q",
            y=y_enc,
        )
    )


def _prediction_value_text_layer(plot_df: DataFrame, y_enc: alt.Y) -> alt.Chart:
    """Build the patient prediction shown at the right-hand end of each row.

    Parameters
    ----------
    plot_df : pandas.DataFrame
        Data to plot.
    y_enc : altair.Y
        Shared y encoding.

    Returns
    -------
    altair.Chart
        Prediction value text layer.
    """
    return (
        alt.Chart(plot_df)
        .mark_text(
            align="left",
            baseline="middle",
            dx=10,
            fontWeight="bold",
            clip=False,
        )
        .encode(
            x=alt.datum(90),
            y=y_enc,
            text=alt.Text("Median prediction:Q", format=".0f"),
        )
    )


def _build_chart(plot_df: DataFrame) -> alt.LayerChart:
    """Combine all layers into the final chart.

    Parameters
    ----------
    plot_df : pandas.DataFrame
        Non-empty data to plot, including the 'Risk status' column.

    Returns
    -------
    altair.LayerChart
        The configured layered chart.
    """
    x_max = plot_df.max(numeric_only=True).max() * 1.1
    y_enc = _y_encoding()
    legend_color = _legend_color()

    layers = (
        _patient_bars_layer(plot_df, y_enc, legend_color)
        + _error_bars_layer(plot_df, y_enc, x_max)
        + _average_point_layer(plot_df, y_enc, legend_color)
        + _risk_value_text_layer(plot_df, y_enc, x_max)
        + _risk_status_text_layer(plot_df, y_enc, x_max)
    )

    return (
        layers.properties(
            height=alt.Step(30),  # consistent breathing room per row
            title="Patient risk vs. Population average (95% CI)",
        )
        .configure_axis(
            grid=False,  # remove distracting lines
            domain=False,  # remove the 'L' shape axis lines
            labelFontSize=12,
        )
        .configure_view(strokeWidth=0)  # remove the border box
        .configure_title(anchor="middle")
    )


def _build_regressor_chart(plot_df: DataFrame) -> alt.LayerChart:
    """Combine all layers for the regressor plot into the final chart.

    Parameters
    ----------
    plot_df : pandas.DataFrame
        Non-empty data to plot, including the 'Median prediction', 'Lower PI'
        and 'Upper PI' columns.

    Returns
    -------
    altair.LayerChart
        The configured layered chart.
    """
    y_enc = _y_encoding()
    legend_color = _regressor_legend_color()

    layers = (
        _prediction_bars_layer(plot_df, y_enc)
        + _median_prediction_layer(plot_df, y_enc, legend_color)
        + _prediction_value_text_layer(plot_df, y_enc)
    )

    return (
        layers.properties(
            height=alt.Step(30),  # consistent breathing room per row
            title="Patient median prediction (95% PI)",
        )
        .configure_axis(
            grid=False,  # remove distracting lines
            domain=False,  # remove the 'L' shape axis lines
            labelFontSize=12,
        )
        .configure_view(strokeWidth=0)  # remove the border box
        .configure_title(anchor="middle")
    )


# --------------------------------------------------------------------------- #
# Table
# --------------------------------------------------------------------------- #
def _format_average(row: Series) -> str:
    """Format the population average with its confidence interval.

    Parameters
    ----------
    row : pandas.Series
        Row with 'Population average', 'Lower CI' and 'Upper CI'.

    Returns
    -------
    str
        For example ``"12.3, 95% CI [10.1, 14.5]"``.
    """
    return (
        f"{row['Population average']:.1f}, "
        f"95% CI [{row['Lower CI']:.1f}, {row['Upper CI']:.1f}]"
    )


def _format_prediction(row: Series) -> str:
    """Format the median prediction with prediction intervals.

    Parameters
    ----------
    row : pandas.Series
        Row with 'Median prediction', 'Lower PI' and 'Upper PI'.

    Returns
    -------
    str
        For example ``"12.3, 95% PI [10.1, 14.5]"``.
    """
    return (
        f"{row['Median prediction']:.0f}, "
        f"95% PI [{row['Lower PI']:.0f}, {row['Upper PI']:.0f}] days"
    )


def _build_table(plot_df: DataFrame) -> DataFrame:
    """Build the table of results to display and download.

    Parameters
    ----------
    plot_df : pandas.DataFrame
        Non-empty data to plot, including the 'Risk status' column.

    Returns
    -------
    pandas.DataFrame
        Table with the outcome, patient risk, population average and risk status.
    """
    display_df = plot_df.copy()
    display_df["Population average"] = display_df.apply(_format_average, axis=1)
    return display_df[
        ["Complications", "Risk percentage", "Population average", "Risk status"]
    ]


def _build_regressor_table(plot_df: DataFrame) -> DataFrame:
    """Build the table of regressor results to display and download.

    Parameters
    ----------
    plot_df : pandas.DataFrame
        Non-empty data to display.

    Returns
    -------
    pandas.DataFrame
        Table with the outcome, median prediction, upper and lower prediction
        intervals.
    """
    display_df = plot_df.copy()
    display_df["Prediction"] = display_df.apply(_format_prediction, axis=1)
    return display_df[["Complications", "Prediction"]]


# --------------------------------------------------------------------------- #
# Streamlit rendering
# --------------------------------------------------------------------------- #
def _hide_chart_toolbar() -> None:
    """Hide the table view and zoom options on Streamlit elements."""
    st.markdown(
        """
        <style>
        [data-testid="stElementToolbar"] {
            display: none !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _highlight_medical_risk(row: Series) -> list[str]:
    """Highlight the risk status in red or green and bold font.

    Parameters
    ----------
    row : pandas.Series
        Table row containing a 'Risk status' entry.

    Returns
    -------
    list[str]
        CSS style for each cell in the row.
    """
    # Create a list of styles for the whole row (defaulting to black)
    styles = ["color: black"] * len(row)

    risk_col_index = row.index.get_loc("Risk status")
    if row["Risk status"] == "Higher":
        # Find the index of the column you want to color
        styles[risk_col_index] = "color: red; font-weight: bold"
    else:
        styles[risk_col_index] = "color: green; font-weight: bold"

    return styles


def _render_table(
    classifier_table: DataFrame | None, regressor_table: DataFrame | None
) -> None:
    """Display the results table.

    Parameters
    ----------
    classifier_table : pandas.DataFrame
        Table with classifier results returned by `_build_table`.
    regressor_table : pandas.DataFrame
        Table with regressor results returned by `_build_regressor_table`.
    """
    if classifier_table is not None:
        st.dataframe(
            classifier_table.style.format({"Risk percentage": "{:.1f}%"}).apply(
                _highlight_medical_risk, axis=1
            ),
            column_config={
                "Complications": "Outcome",
                "Risk percentage": "Patient risk",
                "Population average": "Population average",
                "Risk status": "Risk status",
            },
            hide_index=True,
            width="stretch",
        )
    if regressor_table is not None:
        st.dataframe(
            regressor_table,
            column_config={
                "Complications": "Outcome",
                "Prediction": "Patient median prediction",
            },
            hide_index=True,
            width="stretch",
        )
    st.info("Sort the table columns by clicking on the column name")


def _render_chart(
    classifier_chart: alt.LayerChart | None, regressor_chart: alt.LayerChart | None
) -> None:
    """Display the chart with its explanatory text.

    Parameters
    ----------
    classifier_chart : altair.LayerChart
        Chart returned by `_build_chart`.
    regressor_chart : altair.LayerChart
        Chart returned by `_build_regressor_chart`.
    """
    if classifier_chart is not None:
        st.altair_chart(classifier_chart)
        with st.popover("Help", type="tertiary", icon=":material/help:"):
            st.write(
                "The chart above shows the current patient's risk relative to the "
                "average population risk for the selected operation."
            )
            st.write(
                "The black circle and horizontal bars represent the average population "
                "risk and 95% confidence intervals."
            )
            st.write(
                "The red / green bars represent the current patient's risk, with the "
                "exact value specified on the right side of the graph. If the risk is "
                "lower than the population average the bars are green, otherwise, they "
                "are red."
            )
    if regressor_chart is not None:
        st.altair_chart(regressor_chart)


# --------------------------------------------------------------------------- #
# Public entry point
# --------------------------------------------------------------------------- #
def data_visualisation(
    complications_dict: dict[str, str],
    op_average: dict[str, tuple[float, float, float]],
    display: Literal["graph", "table"] = "graph",
) -> tuple[
    alt.LayerChart | None,
    DataFrame | None,
    alt.LayerChart | None,
    DataFrame | None,
]:
    """Visualise data in the web app.

    Returning chart and table to be able to download them later.

    Parameters
    ----------
    complications_dict : dict[str, str]
        Dictionary containing the complications and the corresponding plot label.
    op_average : dict[str, tuple[float, float, float]]
        Dictionary containing the operation averages for each complication.
    display : {"graph", "table"}, default "graph"
        Flag to plot the graph rather than the table.

    Returns
    -------
    classifier_chart : altair.Chart | None
        Chart plotting the graph results for classifiers.
    classifier_table : pandas.DataFrame | None
        Table displayed for classifiers.
    regressor_chart : altair.Chart | None
        Chart plotting the graph results for regressors.
    regressor_table : pandas.DataFrame | None
        Table displayed for regressors.
    """
    plot_df = _build_classifier_plot_df(complications_dict, op_average)
    regressor_plot_df = _build_regressor_plot_df(complications_dict)

    # Set default values
    classifier_chart = None
    classifier_table = None
    regressor_table = None
    regressor_chart = None

    st.write("**Risk summary**")
    if not plot_df.empty:  # all labels are unticked
        plot_df = _add_risk_status(plot_df)

        _hide_chart_toolbar()
        classifier_chart = _build_chart(plot_df)

        classifier_table = _build_table(plot_df)

    if not regressor_plot_df.empty:
        regressor_table = _build_regressor_table(regressor_plot_df)
        regressor_chart = _build_regressor_chart(regressor_plot_df)

    if display == "table":
        _render_table(classifier_table, regressor_table)
    else:
        _render_chart(classifier_chart, regressor_chart)

    return classifier_chart, classifier_table, regressor_chart, regressor_table
