#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
constants.py

Constants for the app.
"""

ETHCNICITIES = ["Asian", "European", "Māori", "MELAA/Other", "Pacific Peoples"]
GCH = ["U1", "U2", "R1", "R2", "R3"]
CATEGORIES = {
    None: "Placeholder",
    "Obstetrics & Gynaecology": [
        "Cervical & Vulval",
        "Obstetrics",
        "Hysterectomy & Uterus",
        "Ovarian & Adnexal",
        "Other Gynaecology",
        "Pelvic Floor & Prolapse",
    ],
    "General Surgery": [
        "Colorectal",
        "Miscellaneous Abdominal / Peritoneal",
        "Breast",
        "Hernia/Abdominal Wall",
        "HPB",
        "Endocrine",
        "Upper GI",
    ],
    "Plastics": [
        "Other Soft Tissue",
        "Hand Surgery",
        "Flaps & Reconstructions",
        "Burns",
        "Scar Revision & Cosmetic",
    ],
    "Orthopaedics": [
        "Fracture / Trauma Fixation",
        "Other Orthopaedics",
        "Joint Replacement",
        "Spine",
        "Arthroscopy",
        "Amputations",
    ],
    "Ophthalmology": ["Ophthalmology"],
    "ENT": [
        "Throat / Larynx / Airway",
        "Nasal / Sinus Surgery",
        "Ear Surgery",
        "Head & Neck Tumour / Resection",
        "Other ENT",
    ],
    "Oral & Maxillofacial": ["Oral & Maxillofacial"],
    "Neurosurgery": ["Cranial", "Spine", "Peripheral Nerve", "Other Neurosurgery"],
    "Urology": [
        "Bladder",
        "Testis / Scrotum / Penis",
        "Ureter",
        "Prostate",
        "Kidney",
        "Other Urology",
    ],
    "Vascular": [
        "Peripheral Arterial",
        "Aortic",
        "Carotid",
        "Venous",
        "Other Vascular",
        "Mesenteric / Visceral",
    ],
    "Cardiac": [
        "Coronary Artery Bypass (CABG)",
        "Valve Surgery",
        "Aortic Root / Ascending Aorta",
        "Other Cardiac",
    ],
    "Thoracic": [
        "Pleural Procedures",
        "Lung Resection",
        "Mediastinal",
        "Other Thoracic",
    ],
    "Transplant": ["Kidney", "Liver", "Heart", "Lung", "Pancreas"],
    "Other": ["Other"],
}
COLUMNS = [
    "AGE",
    "ETHNICITY_ORIGINAL",
    "SEX_ORIGINAL",
    "DEP18_ORIGINAL",
    "GCH2018_ORIGINAL",
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
    "ALL": "All",
    "MORTALITY_30D": "30-day mortality",
    "MORTALITY_90D": "90-day mortality",
    "MORTALITY_1Y": "1-year mortality",
    "READMIT_ACUTE_30D": "30-day acute readmission",
    "READMIT_ACUTE_90D": "90-day acute readmission",
    "ANY_COMP": "Any complications",
    "SSI": "SSI",
    "VTE": "VTE",
    "CARDIAC_ARREST": "Cardiac arrest",
    "SEPSIS": "Sepsis",
    "RESPIRATORY_FAILURE": "Respiratory failure",
    "SHOCK": "Shock",
    "STROKE": "Stroke",
    "AKI": "AKI",
    "CARDIAC_ARRHYTHMIA": "Cardiac arrhythmia",
    "DELIRIUM": "Delirium",
    "GI_BLEEDING": "GI bleeding",
    "HAEMORRHAGE": "Haemorrhage",
    "IMPLANT_GRAFT": "Implant / graft complications",
    "MYOCARDIAL_INFARCTION": "Myocardial infarction",
    "PNEUMONIA": "Pneumonia",
    "UTI": "UTI",
}
