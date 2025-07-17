import streamlit as st
import requests

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
        response = requests.post("http://localhost:8000/chat", json={"messages": messages})
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        raise RuntimeError(f"Failed to get response from proxy: {e}")

# --- DISPLAY RESULTS ---
if st.button("Find Resources"):
    if not zip_code.strip():
        st.error("Please enter a ZIP code.")
    else:
        with st.spinner("Searching hyperlocal services..."):
            try:
                prompt = build_prompt(category, zip_code)
                results = get_resources_from_gpt(prompt)
                st.markdown(f"<div class='card'>{results.replace('\\n', '<br>')}</div>", unsafe_allow_html=True)
            except Exception as e:
                st.error(str(e))