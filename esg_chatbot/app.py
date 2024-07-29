import os

import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from langchain_core.tracers.context import collect_runs
from langsmith import Client
from streamlit_feedback import streamlit_feedback

from esg_bot.chain.rag_chain import ESGReportRAGChain
from esg_bot.data_handler.utils.lc_callback_handler import RetrieveCallbackHandler

# Load the .env file
load_dotenv()

file_list_df = pd.read_csv("./data/reports.csv")
target = "SK텔레콤"  ##"LG에너지솔루션"
row = file_list_df[file_list_df.company_name == target].iloc[0]
company_name = row["company_name"]
year = row["year"]


chain = ESGReportRAGChain(company_name=company_name, year=year)

# Langsmith project change
os.environ["LANGCHAIN_PROJECT"] = "LogBlack Chatbot Tracing & Feedback"

client = Client()

st.set_page_config(
    page_title="Capturing User Feedback",
    page_icon="🦜️️🛠️",
)

st.subheader("🦜🛠️ Chatbot with Feedback in LangSmith")

st.sidebar.info(
    """
An example of a Streamlit Chat UI capturing user feedback.

- [LangSmith Documentation](https://docs.smith.langchain.com/)
- Streamlit's [chat elements Documentation](https://docs.streamlit.io/library/api-reference/chat)
- Trubrics' [Streamlit-Feedback](https://github.com/trubrics/streamlit-feedback) component
"""
)

st.sidebar.markdown("## Feedback Scale")
feedback_option = "thumbs" if st.sidebar.toggle(label="`Faces` ⇄ `Thumbs`", value=False) else "faces"

rcb = RetrieveCallbackHandler()

with st.form("form"):
    text = st.text_area("Enter text:", "Ask me a question!")
    submitted = st.form_submit_button("Submit")
    if submitted:
        # get run_id from chain or lanchain run
        with collect_runs() as cb:
            st.info(chain.invoke(text, callbacks=[rcb]))
            st.session_state.run_id = cb.traced_runs[0].id

if st.session_state.get("run_id"):
    run_id = st.session_state.run_id
    feedback = streamlit_feedback(
        feedback_type=feedback_option,
        optional_text_label="[Optional] Please provide an explanation",
        key=f"feedback_{run_id}",
    )

    # Define score mappings for both "thumbs" and "faces" feedback systems
    score_mappings = {
        "thumbs": {"👍": 1, "👎": 0},
        "faces": {"😀": 1, "🙂": 0.75, "😐": 0.5, "🙁": 0.25, "😞": 0},
    }

    # Get the score mapping based on the selected feedback option
    scores = score_mappings[feedback_option]

    if feedback:
        # Get the score from the selected feedback option's score mapping
        score = scores.get(feedback["score"])

        if score is not None:
            # Formulate feedback type string incorporating the feedback option
            # and score value
            feedback_type_str = f"{feedback_option} {feedback['score']}"

            # Record the feedback with the formulated feedback type string
            # and optional comment
            feedback_record = client.create_feedback(
                run_id,
                feedback_type_str,
                score=score,
                comment=feedback.get("text"),
            )
            st.session_state.feedback = {
                "feedback_id": str(feedback_record.id),
                "score": score,
            }
        else:
            st.warning("Invalid feedback score.")
