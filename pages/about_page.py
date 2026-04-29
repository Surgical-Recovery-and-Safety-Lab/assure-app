#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
about_page.py

Streamlit ASSURE app about page.
"""

import streamlit as st

st.header("About ASSURE", divider="rainbow")
st.write("""Aotearoa's Smart SUrgical Risk Estimator (ASSURE) uses artificial
    intelligence to predict the risk of mortality, readmission, and
    complications that may occur post-surgery.
    """)
st.write("""
    This tool is designed to inform clinicians and patients about the surgical risks.
    The data is **not** collected to train models and is **not** saved anywhere.
    """)

button = st.button(type="primary", label="Calculate", icon="🎯")
if button:
    st.switch_page("pages/main_page.py")

st.header("About the SRS Lab", divider="rainbow")
st.write("""The Surigical Recovery and Safety (SRS) Lab is part of the Department of 
    Surgery at the University of Auckland. Started in 2025, the lab focuses on reducing
    complications after surgery and improving post-operative care.
    """)
st.write("""Check out our other projects or get in touch with us!""")
container = st.container(horizontal=True)
container.link_button(
    url="https://github.com/Surgical-Recovery-and-Safety-Lab?view_as=public",
    type="secondary",
    label="Our projects",
    icon="📁",
)
contact = container.button("Contact us", type="secondary", icon="📤")
if contact:
    st.switch_page("pages/contact_page.py")
