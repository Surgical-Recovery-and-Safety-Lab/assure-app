"""Tests for the risk status shown in the charts and tables."""

from unittest import mock

import numpy as np
import pandas as pd
import streamlit as st

from src.constants import LABEL_MAP, LEGEND_MEDIAN, LEGEND_PATIENT
from src.visualisation import (
    _add_regressor_status,
    _add_risk_status,
    _build_chart,
    _build_classifier_plot_df,
    _build_regressor_chart,
    _build_regressor_plot_df,
    _format_average,
)


def test_classifier_status_compares_at_displayed_precision():
    plot_df = pd.DataFrame(
        {
            "Risk percentage": [5.004, 5.2, 4.0],
            "Similar-operation mean": [5.0, 5.0, 5.0],
        }
    )
    status = _add_risk_status(plot_df)["Risk status"].tolist()
    assert status == ["Equal", "Higher", "Lower"]


def test_regressor_status_and_favourable():
    labels = LABEL_MAP["HEALTH_OUTCOMES"]
    plot_df = pd.DataFrame(
        {
            "Complications": [labels["DAOH_90"]] * 2 + [labels["POSTOP_LOS"]] * 2,
            "Median prediction": [80, 70, 5, 3],
            "Similar-operation mean": [75, 75, 5, 4],
        }
    )
    result = _add_regressor_status(plot_df)
    assert result["Risk status"].tolist() == ["Higher", "Lower", "Equal", "Lower"]
    # More days alive and out of hospital is good, a longer stay is not
    assert result["Favourable"].tolist()[:2] == [True, False]
    assert result["Favourable"].iloc[3]  # Fewer days of stay than the average


def test_format_average_decimals():
    row = pd.Series(
        {"Similar-operation mean": 5.1234, "Lower CI": 4.5, "Upper CI": 6.789}
    )
    assert _format_average(row, decimals=2) == "5.12 (95% CI 4.50-6.79)"
    row["Lower CI"] = float("nan")
    assert _format_average(row, decimals=2) == "5.12, 95% CI not available"
    assert _format_average(row, decimals=0) == "5, 95% CI not available"


def test_format_average_integers():
    row = pd.Series({"Similar-operation mean": 5.0, "Lower CI": 4.0, "Upper CI": 6.0})
    assert _format_average(row, decimals=0) == "5 (95% CI 4-6)"


class FakeState(dict):
    """Session state that can also be read through attributes."""

    def __getattr__(self, name):
        return self[name]


def test_regressor_plot_df_with_missing_confidence_interval():
    # The bounds are None when there were too few samples to compute them
    dist = mock.Mock()
    dist.median.return_value = np.array([5.2])
    dist.interval.return_value = (np.array([2.1]), np.array([9.4]))
    state = FakeState(POSTOP_LOS=True, output_dists={"POSTOP_LOS": dist})
    labels = {"POSTOP_LOS": "Length of stay"}

    with mock.patch.object(st, "session_state", state):
        missing = _build_regressor_plot_df(labels, {"POSTOP_LOS": (5.4, None, None)})
        present = _build_regressor_plot_df(labels, {"POSTOP_LOS": (5.4, 3.6, 7.2)})

    assert missing[["Lower CI", "Upper CI"]].isna().all(axis=None)
    assert missing["Similar-operation mean"].iloc[0] == 5
    assert present[["Lower CI", "Upper CI"]].iloc[0].tolist() == [4, 7]


# --------------------------------------------------------------------------- #
# Operations without similar-operation averages
# --------------------------------------------------------------------------- #
def _mock_dist(median, lower, upper):
    dist = mock.Mock()
    dist.median.return_value = np.array([median])
    dist.interval.return_value = (np.array([lower]), np.array([upper]))
    return dist


def test_plot_dfs_without_averages_keep_patient_results():
    state = FakeState(
        SHOCK=True,
        POSTOP_LOS=True,
        output_proba={"SHOCK": 0.31},
        output_dists={"POSTOP_LOS": _mock_dist(5.2, 2.1, 9.4)},
    )
    labels = {"SHOCK": "Shock", "POSTOP_LOS": "Length of stay"}

    with (
        mock.patch.object(st, "session_state", state),
        mock.patch.object(st, "warning") as warning,
    ):
        classifier = _build_classifier_plot_df(labels, None)
        regressor = _build_regressor_plot_df(labels, None)

    warning.assert_not_called()  # The outcomes have results, just no mean
    assert classifier["Risk percentage"].tolist() == [0.3]
    assert regressor["Median prediction"].tolist() == [6]
    for df in (classifier, regressor):
        assert (
            df[["Similar-operation mean", "Lower CI", "Upper CI"]].isna().all(axis=None)
        )


def test_status_without_average():
    classifier = _add_risk_status(
        pd.DataFrame({"Risk percentage": [5.0], "Similar-operation mean": [np.nan]})
    )
    assert classifier["Risk status"].tolist() == ["Unavailable"]
    assert classifier["Status label"].tolist() == ["Not available"]

    labels = LABEL_MAP["HEALTH_OUTCOMES"]
    regressor = _add_regressor_status(
        pd.DataFrame(
            {
                "Complications": [labels["DAOH_90"], labels["POSTOP_LOS"]],
                "Median prediction": [80.0, 5.0],
                "Similar-operation mean": [np.nan, np.nan],
            }
        )
    )
    assert regressor["Risk status"].tolist() == ["Unavailable"] * 2
    assert not regressor["Favourable"].any()  # Nothing to compare to


def test_format_average_without_mean():
    row = pd.Series(
        {"Similar-operation mean": np.nan, "Lower CI": np.nan, "Upper CI": np.nan}
    )
    assert _format_average(row, decimals=1, unit="%") == "Not available"


def _layer_marks(chart):
    spec = chart.to_dict()  # Also checks the chart is a valid Vega-Lite spec
    marks = [layer["mark"]["type"] for layer in spec["layer"]]
    domains = [
        layer["encoding"]["color"]["scale"]["domain"]
        for layer in spec["layer"]
        if "scale" in layer["encoding"].get("color", {})
    ]
    return marks, domains, spec["title"]


def test_classifier_chart_without_average_has_no_mean_layers():
    plot_df = _add_risk_status(
        pd.DataFrame(
            {
                "Complications": ["Shock"],
                "Risk percentage": [0.3],
                "Similar-operation mean": [np.nan],
                "Lower CI": [np.nan],
                "Upper CI": [np.nan],
            }
        )
    )
    marks, domains, title = _layer_marks(_build_chart(plot_df))
    assert marks == ["point", "text"]  # No grey interval, mean tick or status
    assert domains == [[LEGEND_PATIENT]]
    assert title == "Patient risk"

    plot_df["Similar-operation mean"] = 0.1
    marks, _, _ = _layer_marks(_build_chart(_add_risk_status(plot_df)))
    assert marks == ["rect", "tick", "point", "text", "text"]


def test_regressor_chart_without_average_has_no_mean_layers():
    plot_df = _add_regressor_status(
        pd.DataFrame(
            {
                "Complications": ["Length of stay"],
                "Median prediction": [6.0],
                "Lower PI": [3.0],
                "Upper PI": [10.0],
                "Similar-operation mean": [np.nan],
                "Lower CI": [np.nan],
                "Upper CI": [np.nan],
            }
        )
    )
    marks, domains, _ = _layer_marks(_build_regressor_chart(plot_df))
    assert marks == ["point", "errorbar", "text"]  # Patient prediction and PI only
    assert domains == [[LEGEND_MEDIAN]]
