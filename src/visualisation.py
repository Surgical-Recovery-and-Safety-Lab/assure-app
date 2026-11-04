"""Risk visualisation (chart and table) for the web app."""

from collections.abc import Callable
from typing import Literal

import altair as alt
import numpy as np
import streamlit as st
from pandas import DataFrame, Series, isna

from .constants import (
    CAPPED_OUTCOMES_NOTE,
    COLOR_BLACK,
    COLOR_BLUE,
    COLOR_GREEN,
    COLOR_GREY,
    COLOR_RED,
    EXCLUDED_KEYS,
    LABEL_MAP,
    LEGEND_AVERAGE,
    LEGEND_MEDIAN,
    LEGEND_PATIENT,
    REGRESSOR_KEYS,
    REGRESSOR_X_MAX,
    RISK_DECIMALS,
    SIMILAR_OPERATION_NOTE,
)

# Pixels reserved for the y axis labels, wide enough for the longest outcome name
Y_AXIS_EXTENT = 210


# --------------------------------------------------------------------------- #
# Data preparation
# --------------------------------------------------------------------------- #
def _ci_value(value: float | None, transform: Callable[[float], float]) -> float:
    """Transform a confidence interval bound, keeping missing bounds as NaN.

    The bounds are None when there were too few samples to compute them.

    Parameters
    ----------
    value : float | None
        Confidence interval bound.
    transform : Callable[[float], float]
        Transformation applied to a bound that is available.

    Returns
    -------
    float
        The transformed bound, or NaN if it is missing.
    """
    return np.nan if value is None else transform(value)


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
        if key not in op_average or key not in st.session_state.output_proba:
            st.warning(f"No results are available for {label}.")
            continue
        labels.append(label)
        patient_risk.append(np.round(st.session_state.output_proba[key], RISK_DECIMALS))
        average.append(np.round(op_average[key][0] * 100, RISK_DECIMALS))
        lower.append(
            _ci_value(op_average[key][1], lambda v: np.round(v * 100, RISK_DECIMALS))
        )
        upper.append(
            _ci_value(op_average[key][2], lambda v: np.round(v * 100, RISK_DECIMALS))
        )

    return DataFrame(
        {
            "Complications": labels,
            "Risk percentage": patient_risk,
            "Similar-operation mean": average,
            "Lower CI": lower,
            "Upper CI": upper,
        }
    )


def _build_regressor_plot_df(
    complications_dict: dict[str, str],
    op_average: dict[str, tuple[float, float, float]],
) -> DataFrame:
    """Collect the selected regressor complications into a DataFrame.

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
    labels, prediction, pi_lower, pi_upper, average, lower, upper = (
        [],
        [],
        [],
        [],
        [],
        [],
        [],
    )
    for key, label in complications_dict.items():
        if not st.session_state[key] or key not in REGRESSOR_KEYS:
            continue
        if key not in op_average or key not in st.session_state.output_dists:
            st.warning(f"No results are available for {label}.")
            continue
        labels.append(label)
        dist = st.session_state.output_dists[key]
        prediction.append(np.ceil(dist.median()[0]))  # To get an integer
        l, u = dist.interval(0.95)
        pi_lower.append(np.ceil(l[0]) + 0.0)  # To get an integer
        pi_upper.append(np.ceil(u[0]))  # To get an integer
        average.append(int(np.round(op_average[key][0])))
        # Whole days, or NaN if there were too few samples to compute the interval
        lower.append(_ci_value(op_average[key][1], lambda v: int(np.round(v))))
        upper.append(_ci_value(op_average[key][2], lambda v: int(np.round(v))))

    return DataFrame(
        {
            "Complications": labels,
            "Median prediction": prediction,
            "Lower PI": pi_lower,
            "Upper PI": pi_upper,
            "Similar-operation mean": average,
            "Lower CI": lower,
            "Upper CI": upper,
        }
    )


def _status_label(value: float, average: float, status: str) -> str:
    """Build the status text with the ratio between the value and the average.

    The ratio is always at least one, taking the larger value over the smaller
    one, so a status of "Lower" reads for example ``"×1.20 lower"``.

    Parameters
    ----------
    value : float
        Patient risk or median prediction.
    average : float
        Similar-operation mean.
    status : {"Higher", "Lower", "Equal"}
        How the value compares to the similar-operation mean.

    Returns
    -------
    str
        For example ``"×1.50 higher"``. Just the status if the ratio is undefined,
        which happens when the smaller of the two values is zero.
    """
    if status == "Equal":
        return status

    smaller, larger = sorted([value, average])
    if smaller == 0:
        return status

    return f"×{larger / smaller:.{RISK_DECIMALS}f} {status.lower()}"


def _add_risk_status(plot_df: DataFrame) -> DataFrame:
    """Add the 'Risk status' and 'Status label' columns for a quick visual cue.

    Parameters
    ----------
    plot_df : pandas.DataFrame
        Data returned by `_build_classifier_plot_df`.

    Returns
    -------
    pandas.DataFrame
        The same DataFrame with a 'Risk status' column ("Higher", "Lower" or "Equal")
        and a 'Status label' column that adds the ratio to the similar-operation mean.
    """
    # Compare at the displayed precision, so equal looking values are not "Higher"
    risk = plot_df["Risk percentage"].round(RISK_DECIMALS)
    average = plot_df["Similar-operation mean"].round(RISK_DECIMALS)
    plot_df["Risk status"] = np.select(
        [risk > average, risk < average], ["Higher", "Lower"], default="Equal"
    )
    plot_df["Status label"] = [
        _status_label(*args) for args in zip(risk, average, plot_df["Risk status"])
    ]
    return plot_df


def _add_regressor_status(plot_df: DataFrame) -> DataFrame:
    """Add the 'Risk status', 'Status label' and 'Favourable' columns.

    A prediction above the similar-operation mean is "Higher", below it "Lower" and
    the same as it "Equal". More days alive and out of hospital is favourable,
    while a longer stay is not. An equal prediction is neither.

    Parameters
    ----------
    plot_df : pandas.DataFrame
        Data returned by `_build_regressor_plot_df`.

    Returns
    -------
    pandas.DataFrame
        The same DataFrame with 'Risk status', 'Status label' (which adds the ratio
        to the similar-operation mean) and 'Favourable' columns.
    """
    prediction = plot_df["Median prediction"]
    average = plot_df["Similar-operation mean"]
    higher = prediction > average
    daoh = plot_df["Complications"] == LABEL_MAP["HEALTH_OUTCOMES"]["DAOH_90"]
    plot_df["Risk status"] = np.select(
        [higher, prediction < average], ["Higher", "Lower"], default="Equal"
    )
    plot_df["Status label"] = [
        _status_label(*args)
        for args in zip(prediction, average, plot_df["Risk status"])
    ]
    plot_df["Favourable"] = higher == daoh  # higher is good for DAOH only
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
            domain=[LEGEND_AVERAGE, LEGEND_PATIENT],
            range=[COLOR_BLACK, COLOR_BLUE],
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
            domain=[LEGEND_AVERAGE, LEGEND_MEDIAN],
            range=[COLOR_BLACK, COLOR_BLUE],
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
            minExtent=Y_AXIS_EXTENT,  # same label width, so the plots start aligned
        ),
    )


def _regressor_status_color():
    """Create the red / green condition used by the regressor text layers.

    Returns
    -------
    altair.Then
        Black if the prediction equals the similar-operation mean, green if it is
        favourable compared to it, else red.
    """
    return (
        alt.when(alt.datum["Risk status"] == "Equal")
        .then(alt.value(COLOR_BLACK))
        .when(alt.datum["Favourable"])
        .then(alt.value(COLOR_GREEN))
        .otherwise(alt.value(COLOR_RED))
    )


def _status_color():
    """Create the red / green condition used by the text layers.

    Returns
    -------
    altair.Then
        Black if the patient risk equals the similar-operation mean, red if it is above,
        else green.
    """
    return (
        alt.when(alt.datum["Risk status"] == "Equal")
        .then(alt.value(COLOR_BLACK))
        .when(alt.datum["Risk status"] == "Higher")
        .then(alt.value(COLOR_RED))
        .otherwise(alt.value(COLOR_GREEN))
    )


# --------------------------------------------------------------------------- #
# Chart layers (one helper per element)
# --------------------------------------------------------------------------- #
def _error_bars_layer(plot_df: DataFrame, y_enc: alt.Y) -> alt.Chart:
    """Build the horizontal 95% CI whiskers.

    Parameters
    ----------
    plot_df : pandas.DataFrame
        Data to plot.
    y_enc : altair.Y
        Shared y encoding.

    Returns
    -------
    altair.Chart
        Error bar layer.
    """
    return (
        alt.Chart(plot_df)
        .mark_rect(color=COLOR_GREY, opacity=0.75, cornerRadius=25, height=15)
        .encode(
            x="Lower CI:Q",
            x2="Upper CI:Q",
            y=y_enc,
        )
    )


def _average_point_layer(
    plot_df: DataFrame, y_enc: alt.Y, legend_color: alt.Color
) -> alt.Chart:
    """Build the tick marking the similar-operation mean.

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
        Similar-operation mean layer.
    """
    return (
        alt.Chart(plot_df)
        .transform_calculate(Legend=f"'{LEGEND_AVERAGE}'")
        .mark_tick(
            bandSize=10, thickness=2, height=15, opacity=0.75
        )  # colour comes from the encoding
        .encode(
            x="Similar-operation mean:Q",
            y=y_enc,
            color=legend_color,
            tooltip=["Complications", "Similar-operation mean", "Lower CI", "Upper CI"],
        )
    )


def _patient_diamond_layer(
    plot_df: DataFrame, y_enc: alt.Y, legend_color: alt.Color, x_max
) -> alt.Chart:
    """Build the diamond marking the patient risk.

    Parameters
    ----------
    plot_df : pandas.DataFrame
        Data to plot.
    y_enc : altair.Y
        Shared y encoding.
    legend_color : altair.Color
        Shared legend colour encoding.
    x_max : float
        Upper limit of the x axis.

    Returns
    -------
    altair.Chart
        Patient risk layer.
    """
    return (
        alt.Chart(plot_df)
        .transform_calculate(Legend=f"'{LEGEND_PATIENT}'")
        .mark_point(filled=True, shape="diamond", size=250, opacity=1)
        .encode(
            x=alt.X(
                "Risk percentage:Q",
                title="Risk percentage (%)",
                scale=alt.Scale(domain=[0, x_max]),
            ),
            y=y_enc,
            color=legend_color,
            tooltip=["Complications", "Risk percentage"],
        )
    )


def _risk_value_text_layer(plot_df: DataFrame, y_enc: alt.Y, x_max: float) -> alt.Chart:
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
            text=alt.Text("Risk percentage:Q", format=f".{RISK_DECIMALS}f"),
            color=_status_color(),
        )
    )


def _risk_status_text_layer(
    plot_df: DataFrame, y_enc: alt.Y, x_max: float
) -> alt.Chart:
    """Build the status label shown next to the risk value, e.g. '×1.50 higher'.

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
            text="Status label:N",
            color=_status_color(),
        )
    )


def _median_prediction_layer(
    plot_df: DataFrame, y_enc: alt.Y, legend_color: alt.Color
) -> alt.Chart:
    """Build the diamond marking the patient's median prediction.

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
        .mark_point(filled=True, shape="diamond", size=250, opacity=1)
        .encode(
            x="Median prediction:Q",
            y=y_enc,
            color=legend_color,
            tooltip=["Complications", "Median prediction", "Lower PI", "Upper PI"],
        )
    )


def _prediction_bars_layer(plot_df: DataFrame, y_enc: alt.Y, x_max: float) -> alt.Chart:
    """Build the horizontal 95% PI whiskers.

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
        Prediction interval error bar layer.
    """
    return (
        alt.Chart(plot_df)
        .mark_errorbar(
            color=COLOR_BLUE, thickness=2, opacity=1
        )  # explicit, since it isn't colour-encoded
        .encode(
            x=alt.X(
                "Lower PI:Q",
                title="Prediction (days)",
                scale=alt.Scale(domain=[0, x_max]),
            ),
            x2="Upper PI:Q",
            y=y_enc,
        )
    )


def _prediction_value_text_layer(
    plot_df: DataFrame, y_enc: alt.Y, x_max: float
) -> alt.Chart:
    """Build the patient prediction shown at the right-hand end of each row.

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
            x=alt.datum(x_max),
            y=y_enc,
            text=alt.Text("Median prediction:Q", format=".0f"),
            color=_regressor_status_color(),
        )
    )


def _prediction_status_text_layer(
    plot_df: DataFrame, y_enc: alt.Y, x_max: float
) -> alt.Chart:
    """Build the status label shown next to the prediction, e.g. '×1.50 higher'.

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
        Prediction status text layer.
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
            text="Status label:N",
            color=_regressor_status_color(),
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
    x_max = max(plot_df.max(numeric_only=True).max() * 1.1, 1)  # Never a 0 width axis
    y_enc = _y_encoding()
    legend_color = _legend_color()

    layers = (
        _error_bars_layer(plot_df, y_enc)
        + _average_point_layer(plot_df, y_enc, legend_color)
        + _patient_diamond_layer(plot_df, y_enc, legend_color, x_max)
        + _risk_value_text_layer(plot_df, y_enc, x_max)
        + _risk_status_text_layer(plot_df, y_enc, x_max)
    )

    return (
        layers.properties(
            height=alt.Step(30),  # consistent breathing room per row
            title="Patient risk vs. Similar-operation mean (95% CI)",
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

    Both outcomes are capped at 90 days, so they share one chart and one axis.

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
    x_max = REGRESSOR_X_MAX
    y_enc = _y_encoding()
    legend_color = _regressor_legend_color()

    layers = (
        _error_bars_layer(plot_df, y_enc)
        + _prediction_bars_layer(plot_df, y_enc, x_max)
        + _average_point_layer(plot_df, y_enc, legend_color)
        + _median_prediction_layer(plot_df, y_enc, legend_color)
        + _prediction_value_text_layer(plot_df, y_enc, x_max)
        + _prediction_status_text_layer(plot_df, y_enc, x_max)
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
def _format_average(row: Series, decimals: int = 1) -> str:
    """Format the similar-operation mean with its confidence interval.

    Parameters
    ----------
    row : pandas.Series
        Row with 'Similar-operation mean', 'Lower CI' and 'Upper CI'.
    decimals : int, default 1
        Number of decimals to display.

    Returns
    -------
    str
        For example ``"12.3, 95% CI [10.1, 14.5]"``, or ``"12.3, 95% CI not
        available"`` if the interval could not be computed.
    """
    if isna(row["Lower CI"]) or isna(row["Upper CI"]):
        return f"{row['Similar-operation mean']:.{decimals}f}, 95% CI not available"

    return (
        f"{row['Similar-operation mean']:.{decimals}f}, "
        f"95% CI [{row['Lower CI']:.{decimals}f}, {row['Upper CI']:.{decimals}f}]"
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
        Table with the outcome, patient risk, similar-operation mean and risk status.
    """
    display_df = plot_df.copy()
    display_df["Similar-operation mean"] = display_df.apply(
        _format_average, axis=1, decimals=RISK_DECIMALS
    )
    return display_df[
        [
            "Complications",
            "Risk percentage",
            "Similar-operation mean",
            "Risk status",
            "Status label",
        ]
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
    display_df["Similar-operation mean"] = display_df.apply(
        _format_average, axis=1, decimals=0
    )
    return display_df[
        [
            "Complications",
            "Prediction",
            "Similar-operation mean",
            "Risk status",
            "Status label",
            "Favourable",
        ]
    ]


# --------------------------------------------------------------------------- #
# Streamlit rendering
# --------------------------------------------------------------------------- #
def hide_chart_toolbar() -> None:
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


def _highlight_regressor_status(row: Series) -> list[str]:
    """Highlight the regressor status in green if favourable, else red.

    Parameters
    ----------
    row : pandas.Series
        Table row containing 'Risk status' and 'Favourable' entries.

    Returns
    -------
    list[str]
        CSS style for each cell in the row.
    """
    styles = ["color: black"] * len(row)
    if row["Risk status"] == "Equal":
        colour = COLOR_BLACK
    else:
        colour = COLOR_GREEN if row["Favourable"] else COLOR_RED
    styles[row.index.get_loc("Status label")] = f"color: {colour}; font-weight: bold"
    return styles


def _highlight_medical_risk(row: Series) -> list[str]:
    """Highlight the risk status in red, green or black and bold font.

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

    risk_col_index = row.index.get_loc("Status label")
    colours = {"Higher": COLOR_RED, "Lower": COLOR_GREEN, "Equal": COLOR_BLACK}
    styles[risk_col_index] = f"color: {colours[row['Risk status']]}; font-weight: bold"

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
            classifier_table.style.format(
                {"Risk percentage": f"{{:.{RISK_DECIMALS}f}}%"}
            ).apply(_highlight_medical_risk, axis=1),
            column_config={
                "Complications": "Outcome",
                "Risk percentage": "Patient risk",
                "Similar-operation mean": "Similar-operation mean",
                "Risk status": None,  # only used for the colours
                "Status label": "Risk status",
            },
            hide_index=True,
            width="stretch",
        )
    if regressor_table is not None:
        st.dataframe(
            regressor_table.style.apply(_highlight_regressor_status, axis=1),
            column_config={
                "Complications": "Outcome",
                "Prediction": "Patient median prediction",
                "Similar-operation mean": "Similar-operation mean",
                "Risk status": None,  # only used for the colours
                "Status label": "Risk status",
                "Favourable": None,  # only used for the colours
            },
            hide_index=True,
            width="stretch",
        )
    if classifier_table is not None or regressor_table is not None:
        st.info("Sort the table columns by clicking on the column name")


def _render_chart(
    classifier_chart: alt.LayerChart | None,
    regressor_chart: alt.LayerChart | None,
) -> None:
    """Display the chart with its explanatory text.

    Parameters
    ----------
    classifier_chart : altair.LayerChart
        Chart returned by `_build_chart`.
    regressor_chart : altair.LayerChart
        Days alive and out of hospital and length of stay chart returned by
        `_build_regressor_chart`.
    """
    show_help = False
    if classifier_chart is not None:
        st.altair_chart(classifier_chart)
        show_help = True
    if regressor_chart is not None:
        st.altair_chart(regressor_chart)
        show_help = True

    if show_help:
        with st.popover(
            "How to read the charts", type="tertiary", icon=":material/help:"
        ):
            st.write(
                "The charts above show the current patient's risk relative to the "
                "similar-operation mean for the selected operation."
            )
            st.write(SIMILAR_OPERATION_NOTE)
            st.write(
                "The grey bar and shading represent the similar-operation mean "
                "and its 95% confidence interval."
            )
            st.write(
                "The blue diamond represent the current patient's risk, with the "
                "exact value specified on the right side of the graph. If the "
                "patient's outcome is better than the similar-operation mean, the "
                "text will be green, otherwise, it will be red."
            )
            st.write(
                "For days alive and out of hospital and length of stay, the blue "
                "bars around the diamond represent the 95% prediction interval. "
                "There is a 95% chance that the true value will be between the "
                "two values. If there are none, they are the same as the median "
                "prediction."
            )
            st.write(CAPPED_OUTCOMES_NOTE)


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
        Chart plotting the days alive and out of hospital and length of stay
        predictions.
    regressor_table : pandas.DataFrame | None
        Table displayed for regressors.
    """
    plot_df = _build_classifier_plot_df(complications_dict, op_average)
    regressor_plot_df = _build_regressor_plot_df(complications_dict, op_average)

    # Set default values
    classifier_chart = None
    classifier_table = None
    regressor_table = None
    regressor_chart = None

    st.write("**Risk summary**")
    if not plot_df.empty:  # all labels are unticked
        plot_df = _add_risk_status(plot_df)

        classifier_chart = _build_chart(plot_df)

        classifier_table = _build_table(plot_df)

    if not regressor_plot_df.empty:
        regressor_plot_df = _add_regressor_status(regressor_plot_df)
        regressor_table = _build_regressor_table(regressor_plot_df)
        regressor_chart = _build_regressor_chart(regressor_plot_df)

    if display == "table":
        _render_table(classifier_table, regressor_table)
    else:
        _render_chart(classifier_chart, regressor_chart)

    return classifier_chart, classifier_table, regressor_chart, regressor_table
