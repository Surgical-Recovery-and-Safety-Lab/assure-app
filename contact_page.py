#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
contact_page.py

Streamlit ASSuRE app contact page.
"""

import streamlit as st

from app_fn import send_email

st.header("Contact us", divider="rainbow")
st.write("""Get in touch with us to report an issue, ask a question, or provide some
    feedback by filling out the form below.
    """)
with st.form("contact_form", enter_to_submit=False):
    st.subheader("Contact form")
    email = st.text_input("Email address")
    subject = st.text_input("Subject")
    message = st.text_area("Message")

    submitted = st.form_submit_button("Send message")

    if submitted:
        if email and subject and message:
            with st.spinner("Sending..."):
                success = send_email(email, subject, message)
                if success:
                    st.success("Thank you, your message has been sent!")
        else:
            st.error("Please fill out all fields.")
