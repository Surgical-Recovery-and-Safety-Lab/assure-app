#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
about_page.py

Streamlit ASSuRE app about page.
"""

import streamlit as st

st.header("About ASSuRE", divider="rainbow")
st.write("""ASSuRE uses artificial intelligence to predict the risk of
    mortality, readmission, and complications that may occur post-surgery.
    """)
st.write("""
    This tool is designed to inform clinicians and patients about the surgical risks.
    The data is **not** collected to train models and is **not** saved anywhere.
    """)
st.write("""
    To use the calculator, input the patient information below and
    click on 'Run model' to generate the results.
""")
