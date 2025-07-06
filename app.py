import os
from typing import List, Dict

import streamlit as st

from mosdac_bot.qa_engine import QABot


# ------------------------
# Placeholder Answer Engine
# ------------------------

# Initialise QABot singleton and cache with Streamlit
@st.cache_resource(allow_output_mutation=True)
def _load_qa_bot():
    try:
        bot = QABot(
            neo4j_uri=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
            neo4j_user=os.getenv("NEO4J_USER", "neo4j"),
            neo4j_password=os.getenv("NEO4J_PASSWORD"),
            vector_index_dir=os.getenv("VECTOR_INDEX_DIR", "vector_index"),
            openai_model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
        )
        return bot
    except Exception as e:
        st.error(f"Failed to load QA engine: {e}")
        raise


def get_answer(question: str, chat_history: List[Dict[str, str]]) -> str:
    qa_bot = _load_qa_bot()
    return qa_bot.answer(question, chat_history)


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