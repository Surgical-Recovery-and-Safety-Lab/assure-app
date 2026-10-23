"""Tests for the risk status shown in the charts and tables."""

import pandas as pd

from src.constants import LABEL_MAP
from src.visualisation import _add_regressor_status, _add_risk_status


def test_classifier_status_compares_at_displayed_precision():
    plot_df = pd.DataFrame(
        {
            "Risk percentage": [5.04, 5.2, 4.0],
            "Population average": [5.0, 5.0, 5.0],
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
            "Population average": [75, 75, 5, 4],
        }
    )
    result = _add_regressor_status(plot_df)
    assert result["Risk status"].tolist() == ["Higher", "Lower", "Equal", "Lower"]
    # More days alive and out of hospital is good, a longer stay is not
    assert result["Favourable"].tolist()[:2] == [True, False]
    assert result["Favourable"].iloc[3]  # Fewer days of stay than the average
