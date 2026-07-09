import os

import requests
import streamlit as st

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:5000").rstrip("/") + "/api/reviews"

st.set_page_config(page_title="Patient Experience Feedback", page_icon="🏥")
st.title("Patient Experience Feedback")

st.subheader("Share your experience")
with st.form("review_form", clear_on_submit=True):
    patient_name = st.text_input("Your name")
    service = st.text_input("Service received (e.g. Cardiology Checkup)")
    rating = st.slider("Rating", min_value=1, max_value=5, value=5)
    comment = st.text_area("Comments (optional)")
    submitted = st.form_submit_button("Submit review")

if submitted:
    if not patient_name or not service:
        st.error("Please fill in your name and the service received.")
    else:
        try:
            response = requests.post(
                BACKEND_URL,
                json={
                    "patient_name": patient_name,
                    "service": service,
                    "rating": rating,
                    "comment": comment,
                },
                timeout=5,
            )
            if response.status_code == 201:
                st.success("Thank you for your feedback!")
            else:
                st.error(response.json().get("error", "Something went wrong."))
        except requests.exceptions.ConnectionError:
            st.error("Could not reach the backend. Is it running on port 5000?")

st.divider()
st.subheader("Recent reviews")
try:
    reviews = requests.get(BACKEND_URL, timeout=5).json()
    summary = requests.get(f"{BACKEND_URL}/summary", timeout=5).json()

    if summary["count"]:
        st.metric(
            "Average rating",
            f"{summary['average_rating']} / 5",
            help=f"Based on {summary['count']} review(s)",
        )

    for review in reversed(reviews):
        st.markdown(f"**{review['service']}** — {'⭐' * int(review['rating'])} ({review['rating']}/5)")
        st.caption(f"{review['patient_name']} · {review['submitted_at']}")
        if review["comment"]:
            st.write(review["comment"])
        st.divider()
except requests.exceptions.ConnectionError:
    st.warning("Could not reach the backend to load reviews.")
