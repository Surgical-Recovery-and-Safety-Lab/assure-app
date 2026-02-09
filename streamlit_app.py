import altair as alt
import streamlit as st
from numpy import arange, expand_dims, zeros
from pandas import DataFrame, to_numeric
from pyrisk.models.core import load_pipeline


@st.cache_resource
def app_load_pipeline():
    """Load the pipeline"""
    pipeline = load_pipeline("models/ai_risk_HGB-v0.3.1.3-d.1.3.2.pkl")
    return pipeline


def convert_dtypes(data):
    """Convert datatypes to fit requirements"""
    for column in data.columns:
        if column in ["AGE", "M3_SCORE", "OP_SEVERITY", "DEP18_ORIGINAL"]:
            data[column] = to_numeric(data[column])
        if column in ["PRIOR_CANCER", "TRAUMA"]:
            data[column] = data[column].astype(bool)
    return data


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
    "Ophthalmology": "Ophthalmology",
    "ENT": [
        "Throat / Larynx / Airway",
        "Nasal / Sinus Surgery",
        "Ear Surgery",
        "Head & Neck Tumour / Resection",
        "Other ENT",
    ],
    "Oral & Maxillofacial": "Oral & Maxillofacial",
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
    "Other": "Other",
}
COLUMNS = [
    "AGE",
    "ETHNICITY_ORIGINAL",
    "SEX_ORIGINAL",
    "DEP18_ORIGINAL",
    "GCH2018_ORIGINAL",
    "M3_SCORE",
    "PRIOR_CANCER",
    "FACILITY",
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
    "IMPLANT_GRAFT": "Implant graft",
    "MYOCARDIAL_INFARCTION": "Myocardial infarction",
    "PNEUMONIA": "Pneumonia",
    "UTI": "UTI",
}

if "model_run" not in st.session_state:
    # Session state flag to check if model has run at least once
    st.session_state.model_run = False

st.title("NZ AI Risk Score")
st.logo("assets/logo.png", size="large")

st.header("Surgical risk score calculator", divider="rainbow")
st.markdown("Explanation / introduction")

st.header("Data input", divider="rainbow")

# Age input
age = st.number_input(
    "**Age**",
    min_value=18,
    max_value=122,
    step=1,
    help="Patient age",
    value=None,
    placeholder="Age",
)

# Ethnicity selectbox
ethnicity = st.selectbox(
    "**Ethnicity**",
    ETHCNICITIES,
    help="Patient ethnicity",
    index=None,
    placeholder="Select ethnicity",
)

# Sex radio buttons
sex_map = {"M": "Male", "F": "Female"}
sex = st.radio(
    "**Sex**",
    options=sex_map.keys(),
    format_func=lambda x: sex_map[x],
    index=None,
    help="Patient sex at birth",
)

# Cancer radio buttons
cancer = st.radio(
    "**Prior cancer**",
    options=[True, False],
    format_func=lambda x: "Yes" if x else "No",
    index=1,
    help="Did the patient have cancer?",
)

# Acuity radio buttons
acuity = st.radio(
    "**Admission acuity**",
    ["Elective", "Acute"],
    index=0,
    help="Is the surgery elective or acute?",
)

# Source radio buttons
source = st.radio(
    "**Admission source**",
    ["Routine", "Transfer"],
    index=0,
    help="Is the patient transfered from another hospital?",
)

# Traum radio buttons
trauma = st.radio(
    "**Trauma**",
    index=1,
    help="Trauma",
    options=[True, False],
    format_func=lambda x: "Yes" if x else "No",
)

# DEP slider
dep = st.slider(
    "**NZDep**", min_value=1, max_value=10, step=1, help="NZ Index of Depravation"
)

# GCH selectbox
gch = st.selectbox(
    "**GCH**",
    GCH,
    help="NZ Geographical Classification of Health",
    index=None,
    placeholder="Select GCH",
)

# M3 score input
m3_score = st.number_input(
    "**M3 score**",
    min_value=0.0,
    step=0.001,
    help="Multimorbidity index",
    format="%.3f",
    value=None,
    placeholder="M3 score",
)

# Category L1 selectbox
category_l1_options = [key for key in CATEGORIES.keys() if key is not None]
category_l1 = st.selectbox(
    "**Surgical specialty**",
    category_l1_options,
    help="Surgical specialty of the operation",
    index=None,
    placeholder="Specialty",
)

# Category L2 selectbox (depends on L1)
category_l2_disabled = True
if category_l1:
    category_l2_disabled = False
category_l2 = st.selectbox(
    "**Surgical sub-specialty**",
    CATEGORIES[category_l1],
    help="Surgical sub-specialty, select a specialty to see options",
    index=None,
    placeholder="Sub-specialty",
    disabled=category_l2_disabled,
)

# Op severity slider
op_severity = st.slider(
    "**Operation severity**",
    min_value=1,
    max_value=5,
    help="Operation severity",
    step=1,
)

input_features = [
    age,
    ethnicity,
    sex,
    dep,
    gch,
    m3_score,
    cancer,
    "Auckland City Hospital",
    acuity,
    source,
    category_l1,
    category_l2,
    op_severity,
    trauma,
]
is_ready = None not in input_features  # Define the is_ready flag

run = st.button("Run model", disabled=not is_ready)

if is_ready:
    if run:
        # Your model code here
        pipeline = app_load_pipeline()
        label_list = pipeline.label_list
        data = DataFrame(expand_dims(input_features, 1).T, columns=COLUMNS)
        input_data = pipeline.transform(convert_dtypes(data))
        output_proba = pipeline.predict_proba(
            input_data, idx=-1, model_type="predictor"
        )
        pos_proba = array(output_proba)[:, 0, 1]  # Reshape to only get positives
        st.session_state.model_run = True

else:
    st.info("Please fill out all fields to enable the 'Run model' button.")

st.header("Results", divider="rainbow")
if computed:
    with st.container():
        labels = [LABEL_MAP[label_list[idx]] for idx in idx_list]
        plot_df = DataFrame({"Predicted outcomes": labels, "Probability": output_proba})

        chart = (
            alt.Chart(plot_df)
            .mark_bar()
            .encode(
                # Fix the X axis from 0 to 1
                x=alt.X("Probability:Q", scale=alt.Scale(domain=[0, 1])),
                # Sort by probability so the highest is at the top
                y=alt.Y("Predicted outcomes:N", sort="-x"),
                # Optional: Change color based on value
                color=alt.Color("Probability:Q", scale=alt.Scale()),
                tooltip=["Predicted outcomes", "Probability"],
            )
        )
        st.altair_chart(chart)
