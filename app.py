# app.py
import os
import tempfile
import streamlit as st
from streamlit_chat import message
from main import ChatPDF

st.set_page_config(page_title="ChatPDF ETS")

# Initialize session state
if "assistant" not in st.session_state:
    st.session_state.assistant = ChatPDF()
    st.session_state.messages = []
    st.session_state.uploaded_filenames = set()

st.title("ChatPDF ETS")

# Upload PDFs and JSONs (only new ones)
uploaded_files = st.file_uploader("Upload PDFs or JSONs", type=["pdf", "json"], accept_multiple_files=True)

if uploaded_files:
    new_files = [f for f in uploaded_files if f.name not in st.session_state.uploaded_filenames]

    if new_files:
        for file in new_files:
            suffix = os.path.splitext(file.name)[-1]  # preserve extension for temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tf:
                tf.write(file.getbuffer())
                file_path = tf.name
            try:
                if file.name.endswith(".pdf"):
                    st.session_state.assistant.ingest(file_path)
                elif file.name.endswith(".json"):
                    st.session_state.assistant.ingest_json(file_path)
                else:
                    raise ValueError("Unsupported file type.")
                st.session_state.uploaded_filenames.add(file.name)
            except Exception as e:
                st.error(f"Failed to ingest {file.name}: {e}")
            finally:
                os.remove(file_path)

# Show uploaded files from this session
if st.session_state.uploaded_filenames:
    st.markdown("**Uploaded Files (This Session):**")
    for f in st.session_state.uploaded_filenames:
        st.markdown(f"- {f}")

# 🗑️ Clear chat + delete DB
if st.button("🗑️ Delete All Data"):
    st.session_state.assistant.clear()
    st.session_state.assistant.delete_all_data()
    st.session_state.messages.clear()
    st.session_state.uploaded_filenames.clear()
    st.success("All data deleted.")

# Display chat history
for i, (msg, is_user) in enumerate(st.session_state.messages):
    message(msg, is_user=is_user, key=f"chat_{i}")

# Ask a question using a form
with st.form("chat_form", clear_on_submit=True):
    user_input = st.text_input("Ask a question", key="chat_input")
    submitted = st.form_submit_button("Send")

if submitted and user_input:
    with st.spinner("Thinking..."):
        response = st.session_state.assistant.ask(user_input)
    st.session_state.messages.append((user_input, True))
    st.session_state.messages.append((response, False))
    st.rerun()