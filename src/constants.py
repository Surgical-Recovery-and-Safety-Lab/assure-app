"""
constants.py

Constants for the app.
"""

CLASSIFIER = "assets/models/classifier/v2"
REGRESSOR = "assets/models/regressor/v2"
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
        "DAOH_90": "Days alive and out of hospital",
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
LEGEND_AVERAGE = "Population average (95% CI)"
LEGEND_PATIENT = "Patient risk"
LEGEND_MEDIAN = "Median prediction (95% PI)"
EXCLUDED_KEYS = ["COMPLICATIONS", "MORTALITY_OUTCOMES", "HEALTH_OUTCOMES"]
REGRESSOR_KEYS = ["DAOH_90", "POSTOP_LOS"]
UNAVAILABLE_KEYS = ["FTR"]  # Outcomes that are coming soon, their toggle is disabled
# Hex values rather than names, since Streamlit remaps colour names to its theme
COLOR_RED = "#ff0000"
COLOR_GREEN = "#008000"
COLOR_GREY = "#808080"
COLOR_BLUE = "#0000ff"
COLOR_BLACK = "#000000"
