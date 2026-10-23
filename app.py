"""
app.py

Streamlit ASSURE app.
"""

import streamlit as st

st.set_page_config(page_title="ASSURE", page_icon="assets/srs-mark.svg", layout="wide")

# Define session state variables
if "model_run" not in st.session_state:
    # Session state flag to check if model has run at least once
    st.session_state.model_run = False
if "output_proba" not in st.session_state:
    # Session state variable to keep output probabilities
    st.session_state.output_proba = {}
if "output_dists" not in st.session_state:
    # Session state variable to keep output distributions of the regressors
    st.session_state.output_dists = {}
if "run_inputs" not in st.session_state:
    # Session state variables for the inputs and operation category of the last run
    st.session_state.run_inputs = None
    st.session_state.run_category = None
if "consent" not in st.session_state:
    # Session state varible for consent
    st.session_state.consent = False

st.logo("assets/srs-logo.svg", size="large", icon_image="assets/srs-mark.svg")
home_page = st.Page("pages/home_page.py", title="Home", icon="🏠")
about_page = st.Page("pages/about_page.py", title="About", icon="📖")
calc_page = st.Page("pages/main_page.py", title="Calculator", icon="🎯")
contact_page = st.Page("pages/contact_page.py", title="Contact us", icon="📤")
pg = st.navigation([home_page, about_page, calc_page, contact_page])
if pg.title != "Calculator":
    # The calculator inputs are reset when leaving the page, so the results
    # computed from them must be discarded too
    st.session_state.model_run = False
pg.run()
