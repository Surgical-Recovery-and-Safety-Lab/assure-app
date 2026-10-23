"""
app_fn.py

Streamlit ASSURE helper functions.
"""

import re
import threading
import time
from collections import deque
from datetime import datetime
from typing import Any, Literal
from zoneinfo import ZoneInfo

import joblib
import requests
import streamlit as st
from pandas import DataFrame, read_csv

from medpipe import MedpipeClassifier, MedpipeRegressor

from .constants import (
    AVERAGES,
    CLASSIFIER,
    COLUMNS,
    LABEL_MAP,
    MAX_EMAIL_LENGTH,
    MAX_MESSAGE_LENGTH,
    MAX_SENDS_PER_HOUR,
    MAX_SUBJECT_LENGTH,
    OPERATIONS,
    REGRESSOR,
    SEND_COOLDOWN,
    SEND_EMAIL_TIMEOUT,
    UNAVAILABLE_KEYS,
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
        if key == "HEALTH_OUTCOMES" or key in UNAVAILABLE_KEYS:
            continue
        st.session_state[key] = st.session_state.HEALTH_OUTCOMES


def sync_complication_toggles() -> None:
    """Sync the complication toggles with the 'all' toggle."""
    for key in LABEL_MAP["COMPLICATIONS"]:
        if key == "COMPLICATIONS":
            continue
        st.session_state[key] = st.session_state.COMPLICATIONS


def sync_master_toggle(master_key: str) -> None:
    """Sync an 'all' toggle with the toggles it controls.

    The 'all' toggle is on only if every toggle it controls is on.

    Parameters
    ----------
    master_key : str
        Session state key of the 'all' toggle, also the key of its group in the
        label map.
    """
    sub_keys = [
        key
        for key in LABEL_MAP[master_key]
        if key != master_key and key not in UNAVAILABLE_KEYS
    ]
    st.session_state[master_key] = all(st.session_state[key] for key in sub_keys)


def init_outcome_toggles() -> None:
    """Initialise the session state keys used for the outcome toggles."""
    for master_key in ["MORTALITY_OUTCOMES", "COMPLICATIONS", "HEALTH_OUTCOMES"]:
        if master_key not in st.session_state:
            st.session_state[master_key] = True

        # Initialize all SUB-TOGGLES in that group to True as well
        for sub_key in LABEL_MAP[master_key]:
            if sub_key not in st.session_state:
                if sub_key in UNAVAILABLE_KEYS:
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


def main_page_layout() -> DataFrame | None:
    """Lay out the main page and collect the user inputs.

    Returns
    -------
    pandas.DataFrame | None
        Input features extracted from the user inputs, with correct types. None
        if some of the required fields have not been filled out.
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
        "Pacific Peoples": "Pacific",
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
    with asa_col2, st.popover("Help", type="tertiary", icon=":material/help:"):
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

    with op_col2, st.popover("Help", type="tertiary", icon=":material/help:"):
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

    required = [age, ethnicity, sex, selected_operation]
    if any(value is None for value in required) or not category_l2:
        return None  # Not all fields have been filled out

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
    # One row built from the list keeps each value's own type. Going through a
    # numpy array would turn everything into strings, and bool("False") is True.
    data = DataFrame([input_features], columns=COLUMNS)
    data["AGE"] = data["AGE"].astype(int)
    data["OP_SEVERITY"] = data["OP_SEVERITY"].astype(str)  # Categorical in the model
    data["ASA_ORIGINAL"] = data["ASA_ORIGINAL"].astype(float)
    data["TRAUMA"] = data["TRAUMA"].astype(bool)
    data["PRIOR_CANCER"] = data["PRIOR_CANCER"].astype(bool)

    return data


EMAIL_PATTERN = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")
CONTROL_CHARACTERS = re.compile(r"[\x00-\x1f\x7f]")  # Includes line breaks
_send_lock = threading.Lock()


@st.cache_resource(show_spinner=False)
def _send_times() -> deque:
    """Return the send times shared by all sessions, as monotonic seconds."""
    return deque()


def validate_feedback(sender_email: str, subject: str, message: str) -> str | None:
    """Check the feedback form fields.

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
    str | None
        Message describing what is wrong, or None if the fields are valid.
    """
    if not (sender_email and subject and message):
        return "Please fill out all fields."
    if len(sender_email) > MAX_EMAIL_LENGTH or not EMAIL_PATTERN.fullmatch(sender_email):
        return "Please enter a valid email address."
    if len(subject) > MAX_SUBJECT_LENGTH:
        return f"The subject must be at most {MAX_SUBJECT_LENGTH} characters."
    if len(message) > MAX_MESSAGE_LENGTH:
        return f"The message must be at most {MAX_MESSAGE_LENGTH} characters."
    # Line breaks in these fields could be used to inject email headers
    if CONTROL_CHARACTERS.search(sender_email) or CONTROL_CHARACTERS.search(subject):
        return "The email address and subject cannot contain line breaks."
    return None


def reserve_send_slot() -> str | None:
    """Reserve the right to send a message, if the rate limits allow it.

    A session has to wait between two messages, and the number of messages from
    all the sessions together is capped per hour. A reserved slot is used up even
    if the message then fails to send, so failures cannot be retried in a loop.

    Returns
    -------
    str | None
        Message explaining why the message cannot be sent now, or None if a slot
        was reserved.
    """
    now = time.monotonic()
    last_send = st.session_state.get("last_send")
    if last_send is not None and now - last_send < SEND_COOLDOWN:
        wait = int(SEND_COOLDOWN - (now - last_send)) + 1
        return f"Please wait {wait} seconds before sending another message."

    with _send_lock:
        send_times = _send_times()
        while send_times and now - send_times[0] > 3600:
            send_times.popleft()
        if len(send_times) >= MAX_SENDS_PER_HOUR:
            return "We are receiving a lot of messages. Please try again later."
        send_times.append(now)

    st.session_state.last_send = now
    return None


def get_report_date() -> str:
    """Return today's date in the timezone of the user's browser.

    Returns
    -------
    str
        Date formatted for the report, for example "October 24, 2026". The server
        timezone is used if the one of the browser is not available.
    """
    try:
        now = datetime.now(ZoneInfo(st.context.timezone))
    except Exception:  # Unknown or unavailable timezone
        now = datetime.now()
    return now.strftime("%B %d, %Y")


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
        True if the request was successful, False otherwise, including if the
        url is not configured or the request could not be sent.
    """
    try:
        url = st.secrets["url"]
        data = {"email": sender_email, "subject": subject, "message": message}
        response = requests.post(url, data=data, timeout=SEND_EMAIL_TIMEOUT)
    except (KeyError, FileNotFoundError, requests.RequestException):
        # Do not let the exception propagate, as its message can contain the url
        return False

    return response.status_code == 200
