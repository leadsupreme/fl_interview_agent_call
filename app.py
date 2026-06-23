import streamlit as st
import requests
import hashlib
import time

st.set_page_config(page_title="Sir Llama - AI Interviewer", page_icon="🦙")

# ── Secrets (server side only) ─────────────────────────────────────────────────
FLOWISE_API_URL = st.secrets["FLOWISE_API_URL"]
FLOWISE_API_KEY = st.secrets["FLOWISE_API_KEY"]  # YOUR Flowise key, hidden here

# Valid user keys — store hashes only, never plain keys
# Generate with: hashlib.sha256("sk-userkey123".encode()).hexdigest()
VALID_KEY_HASHES = {
    hashlib.sha256(k.encode()).hexdigest()
    for k in st.secrets["VALID_USER_KEYS"].split(",")
}

# ── Rate limiting (in-memory, simple) ─────────────────────────────────────────
if "attempt_count" not in st.session_state:
    st.session_state.attempt_count = 0
if "lockout_until" not in st.session_state:
    st.session_state.lockout_until = 0

# ── Session state ──────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "access_granted" not in st.session_state:
    st.session_state.access_granted = False

st.title("🦙 Sir Llama - AI Engineer Interview")
st.caption("Medium Difficulty | 10 Questions")

# ── Sidebar auth ───────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("🔐 Access Control")

    if not st.session_state.access_granted:
        # Check lockout
        if time.time() < st.session_state.lockout_until:
            wait = int(st.session_state.lockout_until - time.time())
            st.error(f"Too many attempts. Try again in {wait}s.")
        else:
            access_key_input = st.text_input("Enter your Access Key", type="password")

            if st.button("Validate Key"):
                if not access_key_input.strip():
                    st.error("Please enter your key.")
                else:
                    # Rate limit: max 5 attempts then 10 min lockout
                    st.session_state.attempt_count += 1
                    if st.session_state.attempt_count > 5:
                        st.session_state.lockout_until = time.time() + 600
                        st.error("Too many attempts. Locked for 10 minutes.")
                    else:
                        # Validate against hash — key never sent to Flowise
                        input_hash = hashlib.sha256(
                            access_key_input.strip().encode()
                        ).hexdigest()

                        if input_hash in VALID_KEY_HASHES:
                            st.session_state.access_granted = True
                            st.session_state.attempt_count = 0
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

# ── Chat (only YOUR Flowise key used here, user never sees it) ─────────────────
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
                        # YOUR key from secrets — user's key not used here at all
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
                        st.error("Unable to reach interview agent. Try again.")
                except Exception as e:
                    st.error("Connection error. Please try again.")
else:
    st.info("Enter your Access Key in the sidebar to start.")

st.caption("Sir Llama — AI Interview Coach")
