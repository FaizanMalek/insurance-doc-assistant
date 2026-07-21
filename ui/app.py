"""Streamlit chat UI for the Insurance Document Assistant.
Local:  reads .env (via config).  Cloud: reads Streamlit secrets.
Run:    streamlit run ui/app.py
Standard top-to-bottom chat; suggested questions live in the sidebar so they are
always reachable without scrolling.
"""
import os, sys
import streamlit as st

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

_KEYS = ["PROVIDER", "AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_KEY",
         "AZURE_CHAT_DEPLOYMENT", "AZURE_EMBED_DEPLOYMENT",
         "AZURE_SEARCH_ENDPOINT", "AZURE_SEARCH_KEY", "AZURE_SEARCH_INDEX",
         "EMBED_DIM", "TOP_K", "CHUNK_WORDS", "CHUNK_OVERLAP"]
try:
    for k in _KEYS:
        if k in st.secrets:
            os.environ[k] = str(st.secrets[k])
except Exception:
    pass

from ragcore.rag import answer  # noqa: E402

MAX_QUESTIONS = 25

SUGGESTED = [
    ("Change a beneficiary", "How do I change the beneficiary on my policy?"),
    ("Submit a death claim", "What is required to submit a death claim?"),
    ("Waiver of premium", "What does the waiver of premium benefit cover?"),
    ("Available riders", "What riders are available and what do they cover?"),
    ("No-medical product", "Do I need a medical exam for the No Medical Life product?"),
]

st.set_page_config(page_title="Insurance Document Assistant", page_icon="📄", layout="centered")

if "messages" not in st.session_state:
    st.session_state.messages = []   # {role, content, sources?}
if "count" not in st.session_state:
    st.session_state.count = 0
if "pending" not in st.session_state:
    st.session_state.pending = None

# --- Sidebar: always-visible suggestions ---
with st.sidebar:
    st.header("Insurance Document Assistant")
    st.caption("Answers are grounded in the documents and cite their source. "
               "Built by Faizan Malek over publicly available documents.")
    st.write("**Try a question:**")
    for i, (label, q) in enumerate(SUGGESTED):
        if st.button(label, key=f"s{i}", use_container_width=True):
            st.session_state.pending = q
    st.divider()
    if st.button("Clear chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.count = 0
        st.rerun()

st.title("Insurance Document Assistant")
if not st.session_state.messages:
    st.caption("Ask a question below, or pick one from the sidebar. Every answer "
               "cites its source document and page, and refuses when the documents "
               "do not cover the question.")

def render(m):
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        if m.get("sources"):
            with st.expander("Sources"):
                for s in m["sources"]:
                    st.markdown(f"**{s['source']} (p.{s['page']})** — {s['content'][:300]}...")

# existing conversation, oldest to newest
for m in st.session_state.messages:
    render(m)

typed = st.chat_input("Ask about the documents...")
question = typed or st.session_state.pending
st.session_state.pending = None

if question:
    if st.session_state.count >= MAX_QUESTIONS:
        st.warning("Demo limit reached for this session. Reload to start over.")
    else:
        st.session_state.count += 1
        user_msg = {"role": "user", "content": question}
        render(user_msg)
        st.session_state.messages.append(user_msg)
        with st.chat_message("assistant"):
            with st.spinner("Searching the documents..."):
                res = answer(question)
            st.markdown(res["answer"])
            with st.expander("Sources"):
                for s in res["sources"]:
                    st.markdown(f"**{s['source']} (p.{s['page']})** — {s['content'][:300]}...")
        st.session_state.messages.append({"role": "assistant", "content": res["answer"],
                                          "sources": res["sources"]})
