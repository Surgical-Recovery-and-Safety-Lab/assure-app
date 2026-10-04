"""
constants.py

Constants for the app.
"""

MODEL_NAME = "assure_v0.1.1.joblib"
MODEL = "assets/models/" + MODEL_NAME
AVERAGES_NAME = "op-averages.joblib"
OPERATIONS = "assets/operations.csv"
AVERAGES = "assets/models/" + AVERAGES_NAME
COLUMNS = [
    "AGE",
    "ETHNICITY",
    "SEX",
    "ASA",
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
        "DAOH": "Days alive and out of hospital",
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
