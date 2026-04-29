#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
home_page.py

Streamlit ASSURE app home page.
"""

import streamlit as st

st.header("Welcome to ASSURE", divider="rainbow")
st.write(
    """Aotearoa's Smart SUrgical Risk Estimator (ASSURE) uses artificial intelligence
    to predict the risk of mortality, readmission, and complications that may occur 
    post-surgery.
    """
)
st.write("""
    This tool is designed to inform clinicians and patients about the surgical risks.
    The data is **not** collected to train models and is **not** saved anywhere.
    """)

button = st.button(type="primary", label="Calculate", icon="🎯")
if button:
    st.switch_page("pages/main_page.py")
