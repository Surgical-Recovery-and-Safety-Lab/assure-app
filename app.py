#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
app.py

Streamlit ASSuRE app.
"""

import streamlit as st
from numpy import array

st.set_page_config(page_title="ASSuRE")

# Define session state variables
if "model_run" not in st.session_state:
    # Session state flag to check if model has run at least once
    st.session_state.model_run = False
if "output_proba" not in st.session_state:
    # Session state variable to keep output probabilities
    st.session_state.output_proba = array([])
if "consent" not in st.session_state:
    # Session state varible for consent
    st.session_state.consent = False

st.logo("assets/logo.png", size="large")
home_page = st.Page("home_page.py", title="Home", icon="🏠")
about_page = st.Page("about_page.py", title="About")
calc_page = st.Page("main_page.py", title="Calculator", icon="🎯")
pg = st.navigation([home_page, about_page, calc_page])
pg.run()
