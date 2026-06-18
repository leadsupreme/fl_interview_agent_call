import streamlit as st
import requests

st.set_page_config(page_title="Sir Llama - AI Interviewer", page_icon="🦙")

# ================== SECURELY FETCHED FROM SECRETS ==================
# This reads the URL from Streamlit Cloud's Advanced Settings
if "FLOWISE_API_URL" in st.secrets:
    FLOWISE_API_URL = st.secrets["FLOWISE_API_URL"]
else:
    st.error("Missing FLOWISE_API_URL secret in Streamlit Cloud settings.")
    st.stop()

st.title("🦙 Sir Llama - AI Engineer Interview")
st.caption("Medium Difficulty | 10 Questions")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "access_granted" not in st.session_state:
    st.session_state.access_granted = False
if "access_key" not in st.session_state:
    st.session_state.access_key = None

# Sidebar
with st.sidebar:
    st.header("🔐 Access Control")
    access_key_input = st.text_input("Enter your Flowise API Key", type="password")
    
    if st.button("Validate Key"):
        if not access_key_input.strip():
            st.error("Please enter the key")
        else:
            with st.spinner("Validating key..."):
                try:
                    test_payload = {"question": "Test connection please"}
                    headers = {
                        "Authorization": f"Bearer {access_key_input.strip()}",
                        "Content-Type": "application/json"
                    }
                    
                    st.info(f"Calling: {FLOWISE_API_URL}")   # Debug line
                    
                    response = requests.post(FLOWISE_API_URL, json=test_payload, headers=headers, timeout=20)
                    
                    st.write(f"Status Code: {response.status_code}")  # Debug
                    
                    if response.status_code == 200:
                        st.success("✅ Key is valid!")
                        st.session_state.access_granted = True
                        st.session_state.access_key = access_key_input.strip()
                        st.session_state.messages.append({"role": "assistant", "content": "Access granted! Let's begin the interview."})
                    else:
                        st.error(f"❌ Failed. Status: {response.status_code}")
                        st.error(response.text[:300])  # Show error message
                except Exception as e:
                    st.error(f"Connection Error: {str(e)}")

# Main Chat Area
if st.session_state.access_granted:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Your response..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Sir Llama thinking..."):
                try:
                    payload = {"question": prompt}
                    headers = {
                        "Authorization": f"Bearer {st.session_state.access_key}",
                        "Content-Type": "application/json"
                    }
                    response = requests.post(FLOWISE_API_URL, json=payload, headers=headers, timeout=60)
                    
                    if response.status_code == 200:
                        answer = response.json().get("text", "No response received.")
                        st.markdown(answer)
                        st.session_state.messages.append({"role": "assistant", "content": answer})
                    else:
                        st.error("Error communicating with agent.")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
else:
    st.info("Enter your Flowise API Key in the sidebar to start.")

st.caption("Protected by Flowise")
