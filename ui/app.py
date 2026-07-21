"""Streamlit chat UI for the Insurance Document Assistant.
Local:  reads .env (via config).
Cloud:  reads Streamlit secrets, copied into the environment before config loads.
Run:    streamlit run ui/app.py
"""
import os, sys
import streamlit as st

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# On Streamlit Cloud there is no .env, so copy any provided secrets into the
# environment BEFORE importing config (config reads os.environ at import time).
_KEYS = ["PROVIDER", "AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_KEY",
         "AZURE_CHAT_DEPLOYMENT", "AZURE_EMBED_DEPLOYMENT",
         "AZURE_SEARCH_ENDPOINT", "AZURE_SEARCH_KEY", "AZURE_SEARCH_INDEX",
         "EMBED_DIM", "TOP_K", "CHUNK_WORDS", "CHUNK_OVERLAP"]
try:
    for k in _KEYS:
        if k in st.secrets:
            os.environ[k] = str(st.secrets[k])
except Exception:
    pass  # no secrets file locally; config falls back to .env

from ragcore.rag import answer  # noqa: E402

MAX_QUESTIONS = 25  # per-visitor cap to protect the demo budget

# (button label, full question sent to the assistant)
SUGGESTED = [
    ("Change a beneficiary", "How do I change the beneficiary on my policy?"),
    ("Submit a death claim", "What is required to submit a death claim?"),
    ("Waiver of premium", "What does the waiver of premium benefit cover?"),
    ("Available riders", "What riders are available and what do they cover?"),
    ("No-medical product", "Do I need a medical exam for the No Medical Life product?"),
]

st.set_page_config(page_title="Insurance Document Assistant", page_icon="📄")
st.title("Insurance Document Assistant")
st.caption("Ask about the policy and claim documents. Every answer cites its source "
           "document and page, and it refuses when the documents do not cover the "
           "question. Built by Faizan Malek over publicly available documents.")

if "history" not in st.session_state:
    st.session_state.history = []
if "count" not in st.session_state:
    st.session_state.count = 0
if "pending" not in st.session_state:
    st.session_state.pending = None

st.write("**Try one of these, or type your own below:**")
cols = st.columns(len(SUGGESTED))
for i, (label, q) in enumerate(SUGGESTED):
    if cols[i].button(label, key=f"s{i}", use_container_width=True):
        st.session_state.pending = q

typed = st.chat_input("Ask about the documents...")
question = typed or st.session_state.pending
st.session_state.pending = None

for role, msg in st.session_state.history:
    st.chat_message(role).write(msg)

if question:
    if st.session_state.count >= MAX_QUESTIONS:
        st.warning("Demo limit reached for this session. Reload to start over.")
    else:
        st.session_state.count += 1
        st.chat_message("user").write(question)
        st.session_state.history.append(("user", question))
        with st.spinner("Searching the documents..."):
            res = answer(question)
        st.chat_message("assistant").write(res["answer"])
        with st.expander("Sources"):
            for s in res["sources"]:
                st.markdown(f"**{s['source']} (p.{s['page']})** — {s['content'][:300]}...")
        st.session_state.history.append(("assistant", res["answer"]))
