# © 2025 Brendan Fox. All Rights Reserved.
# This software is proprietary and not licensed for public use or modification.
# For licensing inquiries, contact: brendan12fox@gmail.com

import streamlit as st
import requests
import csv
import os
from datetime import datetime

# --- PAGE CONFIG ---
st.set_page_config(page_title="Community Resource Guide", layout="centered")

# --- CUSTOM STYLES ---
st.markdown("""
<style>
body {
    background-color: #f0f2f5;
}
.block-container {
    padding-top: 2rem;
    max-width: 800px;
    margin: auto;
    font-family: 'Segoe UI', sans-serif;
    color: #1e1e1e;
}
h1, h3 {
    color: #001f3f;
    font-weight: 600;
}
.app-header {
    text-align: center;
    margin-bottom: 2rem;
}
.card {
    background-color: #f7f9fc;
    padding: 2rem;
    border-radius: 12px;
    box-shadow: 0 2px 6px rgba(0,0,0,0.1);
    border: 1px solid #d0d4da;
    margin-bottom: 2rem;
}
.stButton > button {
    background-color: #003366;
    color: white;
    border-radius: 6px;
    padding: 0.5rem 1rem;
}
</style>
""", unsafe_allow_html=True)

# --- HEADER ---
st.markdown("<div class='app-header'><h1>Community Resource Finder</h1><p>Find verified local help near you</p></div>", unsafe_allow_html=True)

# --- INPUTS ---
category = st.selectbox("What type of help are you looking for?", [
    "Food assistance", "Housing or shelter", "Medical care", 
    "Mental health support", "Legal aid", "Employment services", 
    "Addiction recovery", "Transportation assistance", "Elder care", "Other"
])

zip_code = st.text_input("Enter ZIP Code", placeholder="e.g. 14201")

# --- PROMPT BUILDER ---
def build_prompt(category, zip_code):
    return f"""
You are acting as a clinical social work assistant helping a healthcare provider identify free or low-cost hyperlocal community resources for vulnerable adults.

Return a list of 3 to 5 unique, verifiable services that provide assistance in the category of **{category}**, specifically located in **ZIP Code {zip_code}** (and surrounding neighborhoods if necessary).

Requirements:
- Only include local or regional nonprofits, public agencies, health systems, or government-run services.
- Each entry must include:
  • Service Name  
  • One-sentence description  
  • Contact Info: Address (with ZIP), phone (if available), website (if available)

Strict Guidelines:
- Avoid listing national hotlines or broad advice like “try local churches.”
- Do not list duplicate organizations.
- If no services are found, return: “No appropriate services found.”

Present results as a clean numbered list or table, readable for both patients and care staff.
"""

# --- GPT REQUEST via Backend Proxy ---
def get_resources_from_gpt(prompt):
    messages = [{"role": "user", "content": prompt}]
    try:
        response = requests.post("https://ai-resource-guide.fly.dev/chat", json={"messages": messages})
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        raise RuntimeError(f"Failed to get response from proxy: {e}")

# --- LOGGING FUNCTIONS ---
import gspread
from oauth2client.service_account import ServiceAccountCredentials

def record_feedback(zip_code, category, resource_id, helpful, gpt_response):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["google_service_account"], scope)
    client = gspread.authorize(creds)

    sheet = client.open("Feedback_Log").sheet1
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sheet.append_row([timestamp, zip_code, category, resource_id, helpful, gpt_response])

def record_search(zip_code, category):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["google_service_account"], scope)
    client = gspread.authorize(creds)

    sheet = client.open("Search_Log").sheet1
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sheet.append_row([timestamp, zip_code, category])

# --- DISPLAY RESULTS ---
if 'results' not in st.session_state:
    st.session_state.results = None
if 'show_feedback' not in st.session_state:
    st.session_state.show_feedback = False

if st.button("Find Resources"):
    if not zip_code.strip():
        st.error("Please enter a ZIP code.")
    else:
        with st.spinner("Searching hyperlocal services..."):
            try:
                prompt = build_prompt(category, zip_code)
                record_search(zip_code, category)
                results = get_resources_from_gpt(prompt)
                st.session_state.results = results
                st.session_state.show_feedback = True
            except Exception as e:
                st.error(str(e))

if st.session_state.results:
    st.markdown(f"<div class='card'>{st.session_state.results}</div>", unsafe_allow_html=True)

    if st.session_state.show_feedback:
        st.markdown("**Which resource (1-5) did you use or want to rate?**")
        resource_number = st.selectbox("Select a number", ["1", "2", "3", "4", "5"])

        if resource_number:
            col1, col2 = st.columns(2)
            with col1:
                if st.button("👍 Helpful"):
                    record_feedback(zip_code, category, resource_number, True, st.session_state.results)
                    st.success("Thanks for your feedback!")
                    st.session_state.show_feedback = False
            with col2:
                if st.button("👎 Not Helpful"):
                    record_feedback(zip_code, category, resource_number, False, st.session_state.results)
                    st.info("Thanks for your feedback!")
                    st.session_state.show_feedback = False