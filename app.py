import streamlit as st
import requests
import hashlib
import time
import os

st.set_page_config(page_title="Sir Llama - AI Interviewer", page_icon="🦙")

# ── Secrets — works on both Streamlit Cloud (st.secrets) and Render (env vars) ─
def get_secret(key):
    """Read from st.secrets first, fall back to environment variable."""
    try:
        return st.secrets[key]
    except (KeyError, FileNotFoundError):
        value = os.environ.get(key)
        if not value:
            st.error(f"Missing required secret: {key}. Set it in Render's Environment panel.")
            st.stop()
        return value

FLOWISE_API_URL  = get_secret("FLOWISE_API_URL")
FLOWISE_API_KEY  = get_secret("FLOWISE_API_KEY")
VALID_USER_KEYS  = get_secret("VALID_USER_KEYS")   # comma-separated plain keys

# Build hash set from comma-separated keys
VALID_KEY_HASHES = {
    hashlib.sha256(k.strip().encode()).hexdigest()
    for k in VALID_USER_KEYS.split(",")
    if k.strip()
}

# ── Rate limiting (in-memory, per session) ─────────────────────────────────────
if "attempt_count"  not in st.session_state:
    st.session_state.attempt_count  = 0
if "lockout_until"  not in st.session_state:
    st.session_state.lockout_until  = 0

# ── Session state ──────────────────────────────────────────────────────────────
if "messages"       not in st.session_state:
    st.session_state.messages       = []
if "access_granted" not in st.session_state:
    st.session_state.access_granted = False

# ── UI ─────────────────────────────────────────────────────────────────────────
st.title("🦙 Sir Llama - AI Engineer Interview")
st.caption("Medium Difficulty | 10 Questions")

# ── Sidebar auth ───────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("🔐 Access Control")

    if not st.session_state.access_granted:
        if time.time() < st.session_state.lockout_until:
            wait = int(st.session_state.lockout_until - time.time())
            st.error(f"Too many attempts. Try again in {wait}s.")
        else:
            access_key_input = st.text_input("Enter your Access Key", type="password")

            if st.button("Validate Key"):
                if not access_key_input.strip():
                    st.error("Please enter your key.")
                else:
                    st.session_state.attempt_count += 1

                    if st.session_state.attempt_count > 5:
                        st.session_state.lockout_until = time.time() + 600
                        st.error("Too many attempts. Locked for 10 minutes.")
                    else:
                        input_hash = hashlib.sha256(
                            access_key_input.strip().encode()
                        ).hexdigest()

                        if input_hash in VALID_KEY_HASHES:
                            st.session_state.access_granted = True
                            st.session_state.attempt_count  = 0
                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": "Access granted! Let's begin the interview."
                            })
                            st.rerun()
                        else:
                            st.error("❌ Invalid key.")
    else:
        st.success("✅ Access granted")
        if st.button("End Session"):
            st.session_state.clear()
            st.rerun()

# ── Chat ───────────────────────────────────────────────────────────────────────
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
                        "Authorization": f"Bearer {FLOWISE_API_KEY}",
                        "Content-Type": "application/json"
                    }
                    response = requests.post(
                        FLOWISE_API_URL, json=payload,
                        headers=headers, timeout=60
                    )
                    if response.status_code == 200:
                        answer = response.json().get("text", "No response received.")
                        st.markdown(answer)
                        st.session_state.messages.append({
                            "role": "assistant", "content": answer
                        })
                    else:
                        st.error("Unable to reach interview agent. Please try again.")
                except Exception as e:
                    st.error("Connection error. Please try again.")
else:
    st.info("Enter your Access Key in the sidebar to start.")

st.caption("Sir Llama — AI Interview Coach")
