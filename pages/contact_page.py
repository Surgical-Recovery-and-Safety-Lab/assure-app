"""
contact_page.py

Streamlit ASSURE app contact page.
"""

import streamlit as st

from src.app_fn import reserve_send_slot, send_email, validate_feedback
from src.constants import MAX_EMAIL_LENGTH, MAX_MESSAGE_LENGTH, MAX_SUBJECT_LENGTH

contact_col1, _ = st.columns([0.7, 0.3])

with contact_col1:
    st.header("Contact us", divider="rainbow")
    st.write("""Get in touch with us to report an issue, ask a question, or provide some
        feedback by filling out the form below.
        """)
    with st.form("contact_form", enter_to_submit=False):
        st.subheader("Contact form")
        email = st.text_input("Email address", max_chars=MAX_EMAIL_LENGTH)
        subject = st.text_input("Subject", max_chars=MAX_SUBJECT_LENGTH)
        message = st.text_area("Message", max_chars=MAX_MESSAGE_LENGTH)

        submitted = st.form_submit_button("Send message")

        if submitted:
            email, subject = email.strip(), subject.strip()
            message = message.strip()
            error = validate_feedback(email, subject, message) or reserve_send_slot()
            if error:
                st.error(error)
            else:
                with st.spinner("Sending..."):
                    success = send_email(email, subject, message)
                    if success:
                        st.success("Thank you, your message has been sent!")
                    else:
                        st.error(
                            "Sorry, your message could not be sent. Please try "
                            "again later."
                        )
