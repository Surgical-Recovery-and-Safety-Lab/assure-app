#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
contact_page.py

Streamlit ASSuRE app contact page.
"""

import streamlit as st

st.header("Contact us", divider="rainbow")
st.write("""Get in touch with us to report an issue, ask a question, or provide some
    feedback by filling out the form below.
    """)
with st.form("contact_form"):
    st.subheader("Contact form")
    name = st.text_input("Name")
    email = st.text_input("Email address")
    message = st.text_area("Message")

    submitted = st.form_submit_button("Send message")

    if submitted:
        if email and name and message:
            st.success("Thank you, your message has been sent!")
        else:
            st.error("Please fill out all fields.")
