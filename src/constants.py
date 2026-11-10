"""
constants.py

Constants for the app.
"""

import tomllib
from pathlib import Path


def _read_version() -> str:
    """Read the app version from pyproject.toml, the single source of truth."""
    with open(Path(__file__).parent.parent / "pyproject.toml", "rb") as f:
        return str(tomllib.load(f)["project"]["version"])


VERSION = _read_version()
CHANGELOG_URL = "https://github.com/Surgical-Recovery-and-Safety-Lab/assure-app/blob/main/CHANGELOG.md"
CLASSIFIER = "assets/models/classifier/v3"
REGRESSOR = "assets/models/regressor/v3"
AVERAGES_NAME = "op-averages.joblib"
OPERATIONS = "assets/operations.csv"
AVERAGES = "assets/models/" + AVERAGES_NAME
SEND_EMAIL_TIMEOUT = 10  # Seconds to wait for the feedback service
MAX_EMAIL_LENGTH = 254
MAX_SUBJECT_LENGTH = 150
MAX_MESSAGE_LENGTH = 2000
SEND_COOLDOWN = 60  # Seconds a session must wait between two messages
MAX_SENDS_PER_HOUR = 20  # Messages accepted from all sessions together
COLUMNS = [
    "AGE",
    "ETHNICITY_ORIGINAL",
    "SEX_ORIGINAL",
    "ASA_ORIGINAL",
    "PRIOR_CANCER",
    "ADMISSION_ACUITY",
    "ADMISSION_SOURCE",
    "CATEGORY_LEVEL_1",
    "CATEGORY_LEVEL_2",
    "OP_SEVERITY",
    "TRAUMA",
]
LABEL_MAP = {
    "MORTALITY_OUTCOMES": {
        "MORTALITY_OUTCOMES": "Toggle all mortality outcomes",
        "MORTALITY_30D": "30-day mortality",
        "MORTALITY_90D": "90-day mortality",
        "MORTALITY_1Y": "1-year mortality",
    },
    "HEALTH_OUTCOMES": {
        "HEALTH_OUTCOMES": "Toggle all",
        "READMIT_ACUTE_30D": "30-day acute readmission",
        "READMIT_ACUTE_90D": "90-day acute readmission",
        "DAOH_90": "Days alive and out of hospital (90 days)",
        "POSTOP_LOS": "Length of stay",
        "FTR": "Failure to rescue (coming soon)",
    },
    "COMPLICATIONS": {
        "COMPLICATIONS": "Toggle all complications",
        "ANY_COMP": "Any complication",
        "REOP": "Reoperation",
        "AKI": "AKI",
        "CARDIAC_ARRHYTHMIA": "Cardiac arrhythmia",
        "DELIRIUM": "Delirium",
        "GI_BLEEDING": "GI bleeding",
        "HAEMORRHAGE": "Haemorrhage",
        "IMPLANT_GRAFT": "Implant/graft complication",
        "MYOCARDIAL_EVENT": "Myocardial event",
        "PNEUMONIA": "Pneumonia",
        "RESPIRATORY_FAILURE": "Respiratory failure",
        "SEPSIS": "Sepsis",
        "SHOCK": "Shock",
        "SSI": "SSI",
        "STROKE": "Stroke",
        "UTI": "UTI",
        "VTE": "VTE",
    },
}
SIMILAR_OPERATION_NOTE = (
    "The similar-operation mean is the average outcome of patients who "
    "underwent an operation in the same sub-specialty with the same operation "
    "severity as the planned operation. It describes the type of operation, not "
    "the individual patient."
)
CAPPED_OUTCOMES_NOTE = (
    "Days alive and out of hospital and postoperative length of stay "
    " are both capped at 90 days, so no value can exceed 90 days."
)
COMPLICATIONS_WARNING = (
    "The data collection methods may have caused individual complications to be "
    "underrepresented in the training data. This can lead to predicted rates being "
    "lower than the expected clinical risk."
)
COMPLICATIONS_WARNING_EMPHASIS = "Results must be interpreted with care."
LEGEND_AVERAGE = "Similar-operation mean (95% CI)"
LEGEND_PATIENT = "Patient risk"
LEGEND_MEDIAN = "Median prediction (95% PI)"
EXCLUDED_KEYS = ["COMPLICATIONS", "MORTALITY_OUTCOMES", "HEALTH_OUTCOMES"]
REGRESSOR_X_MAX = 90  # Days, both regressor outcomes are capped at 90
REGRESSOR_KEYS = ["DAOH_90", "POSTOP_LOS"]
# Tall, narrow diamond (SVG path in a [-1, 1] box): width is 0.4x the height, so it
# stays easy to spot without covering the interval and the mean tick
PATIENT_MARKER_SHAPE = "M0,-1.5L0.6,0L0,1.5L-0.6,0Z"
PATIENT_MARKER_SIZE = 100  # Scales the whole shape, tune together with the shape
RISK_DECIMALS = 1  # Decimals of the classifier percentages that are plotted and shown
UNAVAILABLE_KEYS = ["FTR"]  # Outcomes that are coming soon, their toggle is disabled
# Hex values rather than names, since Streamlit remaps colour names to its theme
COLOR_RED = "#ff0000"
COLOR_GREEN = "#008000"
COLOR_GREY = "#808080"
COLOR_BLUE = "#0000ff"
COLOR_BLACK = "#000000"
