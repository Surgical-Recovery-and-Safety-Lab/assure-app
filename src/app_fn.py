"""
app_fn.py

Streamlit ASSURE helper functions.
"""

from typing import Any, Literal

import joblib
import numpy as np
import requests
import streamlit as st
from medpipe import MedpipeClassifier, MedpipeRegressor
from pandas import DataFrame, Series, read_csv

from .constants import (
    AVERAGES,
    CLASSIFIER,
    COLUMNS,
    LABEL_MAP,
    OPERATIONS,
    REGRESSOR,
)


@st.cache_resource(show_spinner=False)
def load_pipeline(
    pipeline_type: Literal["classifier", "regressor"] = "classifier",
) -> MedpipeClassifier | MedpipeRegressor:
    """Load a MedpipeClassifier or MedpipeRegressor pipeline.

    Parameters
    ----------
    pipeline_type : {"classifier", "regressor"}, default "classifier"
        Pipeline type to load.

    Returns
    -------
    MedpipeClassifier | MedpipeRegressor
        The loaded pipeline.
    """
    if pipeline_type == "classifier":
        return MedpipeClassifier.load(CLASSIFIER)

    else:
        return MedpipeRegressor.load(REGRESSOR)


@st.cache_resource(show_spinner=False)
def load_averages() -> dict:
    """Load the operation averages.

    Returns
    -------
    dict
        Operation averages, as loaded from the averages file.
    """
    return joblib.load(AVERAGES)


@st.cache_resource(show_spinner=False)
def load_operations() -> DataFrame:
    """Load the operations table.

    Returns
    -------
    pandas.DataFrame
        Table of operations.
    """
    return read_csv(OPERATIONS)


def sync_mortality_outcome_toggles() -> None:
    """Sync the mortality outcome toggles with the 'all' toggle."""
    for key in LABEL_MAP["MORTALITY_OUTCOMES"]:
        if key == "MORTALITY_OUTCOMES":
            continue
        st.session_state[key] = st.session_state.MORTALITY_OUTCOMES


def sync_health_outcome_toggles() -> None:
    """Sync the health service outcome toggles with the 'all' toggle."""
    for key in LABEL_MAP["HEALTH_OUTCOMES"]:
        if key in ["HEALTH_OUTCOMES", "FTR", "LOS", "DAOH"]:
            continue
        st.session_state[key] = st.session_state.HEALTH_OUTCOMES


def sync_complication_toggles() -> None:
    """Sync the complication toggles with the 'all' toggle."""
    for key in LABEL_MAP["COMPLICATIONS"]:
        if key == "COMPLICATIONS":
            continue
        st.session_state[key] = st.session_state.COMPLICATIONS


def init_outcome_toggles() -> None:
    """Initialise the session state keys used for the outcome toggles."""
    for master_key in ["MORTALITY_OUTCOMES", "COMPLICATIONS", "HEALTH_OUTCOMES"]:
        if master_key not in st.session_state:
            st.session_state[master_key] = True

        # Initialize all SUB-TOGGLES in that group to True as well
        for sub_key in LABEL_MAP[master_key]:
            if sub_key not in st.session_state:
                if sub_key in ["FTR", "DAOH", "LOS"]:
                    continue
                st.session_state[sub_key] = True


def show_consent_page() -> None:
    """Show the consent page to the user."""
    st.header("Disclaimer", divider="rainbow")
    st.warning("Please read the following carefully before proceeding.")

    st.write("""
    By using this tool, you agree to having the data you enter into the calculator
    processed by our AI model. Your information is not stored and is deleted after
    the window is closed.
    """)
    st.write("""
    The model outputs are for informational purposes only and should not be used in
    isolation to make clinical decisions.
    """)
    st.write("""
    ASSURE and the Surgical Recovery and Safety Lab are not responsible for decisions
    made by health care professionals or patients based on the information provided by
    this tool.
    """)
    if st.button("I Agree and Accept"):
        st.session_state.consent = True
        st.rerun()  # Rerun to immediately switch to the main app


def main_page_layout() -> DataFrame:
    """Lay out the main page and collect the user inputs.

    Returns
    -------
    pandas.DataFrame
        Input features extracted from the user inputs, with correct types.
    """
    st.header("Aotearoa's Smart SUrgical Risk Estimator")

    st.header("Data input", divider="rainbow")

    # Age input
    age_col1, _ = st.columns([3, 1], vertical_alignment="bottom", gap="medium")
    with age_col1:
        age = st.number_input(
            "**Age**",
            min_value=18,
            max_value=122,
            step=1,
            value=None,
            placeholder="Age",
        )

    # Sex radio buttons
    sex_map = {"M": "Male", "F": "Female"}
    sex = st.radio(
        "**Sex at birth**",
        options=sex_map.keys(),
        format_func=lambda x: sex_map[x],
        index=None,
        help="Patient sex **at birth**",
        horizontal=True,
    )

    # Ethnicity selectbox
    ethnicity_map = {
        "Asian": "Asian",
        "European": "NZ European",
        "Māori": "Māori",
        "MELAA/Other": "MELAA/Other",
        "Pacific peoples": "Pacific",
    }
    ethnicity_col1, _ = st.columns([3, 1], vertical_alignment="bottom", gap="medium")
    with ethnicity_col1:
        ethnicity = st.selectbox(
            "**Ethnicity**",
            options=ethnicity_map.keys(),
            format_func=lambda x: ethnicity_map[x],
            index=None,
            placeholder="Select ethnicity",
        )

    # Cancer radio buttons
    cancer = st.radio(
        "**Prior cancer**",
        options=[True, False],
        format_func=lambda x: "Yes" if x else "No",
        index=1,
        help="Did the patient have cancer?",
        horizontal=True,
    )

    # Acuity radio buttons
    acuity = st.radio(
        "**Admission acuity**",
        ["Elective", "Acute"],
        index=0,
        help="Is the surgery elective or acute?",
        horizontal=True,
    )

    # Source radio buttons
    source = st.radio(
        "**Admission source**",
        ["Routine", "Transfer"],
        index=0,
        help="Is the patient transfered from another hospital?",
        horizontal=True,
    )

    # Traum radio buttons
    trauma = st.radio(
        "**Trauma**",
        index=1,
        options=[True, False],
        format_func=lambda x: "Yes" if x else "No",
        horizontal=True,
    )

    # ASA score input
    asa_col1, asa_col2 = st.columns([3, 1], vertical_alignment="bottom", gap="medium")
    with asa_col1:
        asa_score = st.slider(
            "**ASA score**",
            min_value=1,
            max_value=5,
            value=1,
        )
    with asa_col2 and st.popover("Help", type="tertiary", icon=":material/help:"):
        st.write("**Amercian Society of Anaesthesiology -- Physical Status Score**")
        st.markdown("""
                1. Normal healthy patient
                2. Patient with mild systemic disease
                3. Patient with severe systemic disease
                4. Patient with severe systemic disease that is a constant threat to life
                5. Patient who is moribund and not suspected to survive without
                the operation
                """)
        st.page_link(
            "https://www.openanesthesia.org/keywords/asa-physical-status-classification/",
            label="More information",
            icon=":material/info:",
        )

    operations_df = load_operations()  # Load operations dataframe

    # Define placeholder values to avoid error
    category_l1 = ""
    category_l2 = ""
    op_severity = 0

    search_options = operations_df["OP_DESC"].tolist()

    op_col1, op_col2 = st.columns([3, 1], vertical_alignment="bottom", gap="medium")

    with op_col1:
        selected_operation = st.selectbox(
            "**Operation**",
            options=search_options,
            index=None,
            placeholder="Type to search...",
        )

        if selected_operation:
            row = operations_df[operations_df["OP_DESC"] == selected_operation].iloc[0]

            # Extract specialty, sub-specialty, and severity
            category_l1 = row["CATEGORY_LEVEL_1"]
            category_l2 = row["CATEGORY_LEVEL_2"]
            op_severity = int(row["OP_SEVERITY"])

    with op_col2 and st.popover("Help", type="tertiary", icon=":material/help:"):
        st.write("**Operation search bar**")
        st.write("""
                Start typing the operation name or description in the search bar to filter
                the operation list. Once the correct operation is find select it from the
                list. The surgical specialty, sub-specialty, and the operation severity
                will be automatically filled for you.
                If the operation name is too long leaving the cursor hovering over it
                will display the entire operation description.
                """)

    st.markdown("**Selected operation**")
    st.markdown(f"{selected_operation}")
    col1, col2, col3, _ = st.columns(4)

    with col1:
        st.markdown("**Surgical Specialty**")
        st.markdown(f"{category_l1}")
    with col2:
        st.markdown("**Sub-specialty**")
        st.markdown(f"{category_l2}")
    with col3:
        st.markdown("**Operation severity**")
        st.markdown(f"{op_severity}")

    st.markdown("---")

    input_features = [
        age,
        ethnicity,
        sex,
        float(asa_score),
        cancer,
        acuity,
        source,
        category_l1,
        category_l2,
        op_severity,
        trauma,
    ]
    return convert_input_features(input_features)


def convert_input_features(input_features: list[Any]) -> DataFrame:
    """Convert the input feature list to a data frame with correct types.

    Parameters
    ----------
    input_features : list
        List of input features from the user.

    Returns
    -------
    pandas.DataFrame
        Converted features into a data frame with correct typings.
    """
    data = DataFrame(np.expand_dims(input_features, 1).T, columns=Series(COLUMNS))
    data["ASA"] = data["ASA"].astype(float)
    data["TRAUMA"] = data["TRAUMA"].astype(bool)
    data["PRIOR_CANCER"] = data["PRIOR_CANCER"].astype(bool)

    return data


def send_email(sender_email: str, subject: str, message: str) -> bool:
    """Send an email from the user feedback.

    Parameters
    ----------
    sender_email : str
        Email address of the sender.
    subject : str
        Subject of the email.
    message : str
        Body of the email.

    Returns
    -------
    bool
        True if the request was successful, False otherwise.
    """
    url = st.secrets["url"]
    data = {"email": sender_email, "subject": subject, "message": message}
    response = requests.post(url, data=data)
    return response.status_code == 200
