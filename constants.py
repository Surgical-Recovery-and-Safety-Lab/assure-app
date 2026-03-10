#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
constants.py

Constants for the app.
"""

MODEL = "assets/ai_risk_HGBc-v0.5.1.5-d.1.3.2.joblib"
AVERAGES = "assets/op_averages.joblib"
ETHCNICITIES = ["Asian", "European", "Māori", "MELAA/Other", "Pacific Peoples"]
GCH = ["U1", "U2", "R1", "R2", "R3"]
CATEGORIES = {
    None: "Placeholder",
    "Cardiac": [
        "Aortic Root / Ascending Aorta",
        "Coronary Artery Bypass (CABG)",
        "Other Cardiac",
        "Valve Surgery",
    ],
    "ENT": [
        "Ear Surgery",
        "Head & Neck Tumour / Resection",
        "Nasal / Sinus Surgery",
        "Other ENT",
        "Throat / Larynx / Airway",
    ],
    "General Surgery": [
        "Breast",
        "Colorectal",
        "Endocrine",
        "HPB",
        "Hernia/Abdominal Wall",
        "Miscellaneous Abdominal / Peritoneal",
        "Upper GI",
    ],
    "Neurosurgery": ["Cranial", "Other Neurosurgery", "Peripheral Nerve", "Spine"],
    "Obstetrics & Gynaecology": [
        "Cervical & Vulval",
        "Hysterectomy & Uterus",
        "Obstetrics",
        "Other Gynaecology",
        "Ovarian & Adnexal",
        "Pelvic Floor & Prolapse",
    ],
    "Ophthalmology": ["Ophthalmology"],
    "Oral & Maxillofacial": ["Oral & Maxillofacial"],
    "Orthopaedics": [
        "Amputations",
        "Arthroscopy",
        "Fracture / Trauma Fixation",
        "Joint Replacement",
        "Other Orthopaedics",
        "Spine",
    ],
    "Other": ["Other"],
    "Plastics": [
        "Burns",
        "Flaps & Reconstructions",
        "Hand Surgery",
        "Other Soft Tissue",
        "Scar Revision & Cosmetic",
    ],
    "Thoracic": [
        "Lung Resection",
        "Mediastinal",
        "Other Thoracic",
        "Pleural Procedures",
    ],
    "Transplant": ["Heart", "Kidney", "Liver", "Lung", "Pancreas"],
    "Urology": [
        "Bladder",
        "Kidney",
        "Other Urology",
        "Prostate",
        "Testis / Scrotum / Penis",
        "Ureter",
    ],
    "Vascular": [
        "Aortic",
        "Carotid",
        "Mesenteric / Visceral",
        "Other Vascular",
        "Peripheral Arterial",
        "Venous",
    ],
}
COLUMNS = [
    "AGE",
    "ETHNICITY",
    "SEX",
    "DEP18",
    "GCH2018",
    "M3_SCORE",
    "PRIOR_CANCER",
    "ADMISSION_ACUITY",
    "ADMISSION_SOURCE",
    "CATEGORY_LEVEL_1",
    "CATEGORY_LEVEL_2",
    "OP_SEVERITY",
    "TRAUMA",
]
LABEL_MAP = {
    "GLOBAL_OUTCOMES": {
        "GLOBAL_OUTCOMES": "All global outcomes",
        "MORTALITY_30D": "30-day mortality",
        "MORTALITY_90D": "90-day mortality",
        "MORTALITY_1Y": "1-year mortality",
        "READMIT_ACUTE_30D": "30-day acute readmission",
        "READMIT_ACUTE_90D": "90-day acute readmission",
        "ANY_COMP": "Any complication",
    },
    "COMPLICATIONS": {
        "COMPLICATIONS": "All complications",
        "AKI": "AKI",
        "CARDIAC_ARREST": "Cardiac arrest",
        "CARDIAC_ARRHYTHMIA": "Cardiac arrhythmia",
        "DELIRIUM": "Delirium",
        "GI_BLEEDING": "GI bleeding",
        "HAEMORRHAGE": "Haemorrhage",
        "IMPLANT_GRAFT": "Implant / graft complications",
        "MYOCARDIAL_INFARCTION": "Myocardial infarction",
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
