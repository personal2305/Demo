import os
from typing import List, Dict

import streamlit as st

# ------------------------
# Placeholder Answer Engine
# ------------------------

def get_answer(question: str, chat_history: List[Dict[str, str]]) -> str:
    """Return an answer to the user's question.

    This is currently a stub. In a future iteration this function will:
        1. Retrieve relevant context from a MOSDAC knowledge graph / vector store.
        2. Feed the context plus the conversation history into an LLM (e.g. OpenAI, LLama-cpp).
    """
    # TODO: Replace with real retrieval-augmented generation pipeline
    # For now, we return a canned response so the chat UI can be demonstrated.
    return (
        "🚧 This is a placeholder response. In the full system, this area will "
        "call the knowledge-graph-powered LLM to provide an accurate answer "
        "to your MOSDAC query."
    )


# ------------------------
# Streamlit Chat UI
# ------------------------

st.set_page_config(page_title="MOSDAC AI Help Bot", page_icon="🛰️", layout="centered")
st.title("🛰️ MOSDAC AI Help Bot")

st.markdown(
    """
    **Welcome!** Ask me anything about the data, services, or documentation hosted on the **[MOSDAC](https://www.mosdac.gov.in)** portal.

    _This is an early prototype showcasing the interactive chat interface. The backend answering logic will evolve to use advanced NLP and a knowledge graph built from MOSDAC content._
    """,
    help="The rendered answer quality will improve as the knowledge graph and retrieval pipeline are implemented.",
)

# Initialise chat history structure: a list of {role, content}
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Render existing messages
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input widget at the bottom of the page
if user_query := st.chat_input("Type your question and press Enter…"):
    # Append the user's message to history and display
    st.session_state.chat_history.append({"role": "user", "content": user_query})
    with st.chat_message("user"):
        st.markdown(user_query)

    # Generate assistant response
    assistant_response = get_answer(user_query, st.session_state.chat_history)

    # Display assistant response
    with st.chat_message("assistant"):
        st.markdown(assistant_response)

    # Append assistant message to history
    st.session_state.chat_history.append({"role": "assistant", "content": assistant_response})