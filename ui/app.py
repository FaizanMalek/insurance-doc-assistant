"""M4 UI: minimal Streamlit chat.  Run:  streamlit run ui/app.py"""
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import streamlit as st
from ragcore.rag import answer

st.set_page_config(page_title="Insurance Document Assistant", page_icon="📄")
st.title("Insurance Document Assistant")
st.caption("Answers grounded in your documents, with citations. Refuses when unsure.")

if "history" not in st.session_state:
    st.session_state.history = []

q = st.chat_input("Ask about the policy documents...")
for role, msg in st.session_state.history:
    st.chat_message(role).write(msg)

if q:
    st.chat_message("user").write(q)
    st.session_state.history.append(("user", q))
    with st.spinner("Searching documents..."):
        res = answer(q)
    st.chat_message("assistant").write(res["answer"])
    with st.expander("Sources"):
        for s in res["sources"]:
            st.markdown(f"**{s['source']} (p.{s['page']})** — {s['content'][:300]}...")
    st.session_state.history.append(("assistant", res["answer"]))
