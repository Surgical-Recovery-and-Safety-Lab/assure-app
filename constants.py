#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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
        "FTR": "Failure to rescue (coming soon)",
        "DAOH": "DAOH (coming soon)",
        "LOS": "Length of stay (coming soon)",
    },
    "COMPLICATIONS": {
        "COMPLICATIONS": "Toggle all complications",
        "AKI": "AKI",
        "ANY_COMP": "Any complication",
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
MODEL_MAP = {
    "MORTALITY_30D": "recalibrator",
    "MORTALITY_90D": "predictor",
    "MORTALITY_1Y": "recalibrator",
    "READMIT_ACUTE_30D": "predictor",
    "READMIT_ACUTE_90D": "predictor",
    "ANY_COMP": "predictor",
    "SSI": "predictor",
    "VTE": "predictor",
    "SEPSIS": "predictor",
    "RESPIRATORY_FAILURE": "recalibrator",
    "SHOCK": "predictor",
    "STROKE": "recalibrator",
    "AKI": "predictor",
    "CARDIAC_ARRHYTHMIA": "predictor",
    "DELIRIUM": "predictor",
    "GI_BLEEDING": "predictor",
    "HAEMORRHAGE": "recalibrator",
    "IMPLANT_GRAFT": "predictor",
    "MYOCARDIAL_EVENT": "predictor",
    "PNEUMONIA": "predictor",
    "UTI": "recalibrator",
}
