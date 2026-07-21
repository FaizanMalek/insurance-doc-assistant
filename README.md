# Insurance Document Assistant

A private, retrieval-augmented (RAG) assistant that answers staff questions about
insurance policy and benefits documents. Every answer cites its source passage, and
the assistant refuses to answer when the documents do not cover the question.

Built to demonstrate a production-minded, Microsoft-stack AI solution: document
automation, retrieval, grounded generation, secure integration, and measured
reliability.

> Note: uses only public sample documents. No confidential data.

## Why this exists

Corporate teams waste hours searching policy PDFs. This assistant grounds a language
model in an organisation's own documents so answers are accurate, cited, and safe to
trust, with a human always able to verify the source.

## Architecture

```
User -> Chat UI -> API
                    |-- embed question
                    |-- retrieve top-k chunks (Azure AI Search vector index)
                    |-- grounded prompt + context -> chat model (Azure AI Foundry)
                    |-- answer + citations
Logging + Content Safety wrap every call.
```

Model access is behind a single adapter, so the same code runs on Azure AI Foundry or
on the OpenAI / Anthropic APIs by changing one config value.

## Stack

- Python 3.11, FastAPI
- Azure AI Foundry (chat + embeddings)
- Azure AI Search (vector index)
- Streamlit chat UI
- Azure AI Content Safety (guardrails)
- LLM-as-judge evaluation harness (custom)

## Repo layout

```
data/     public sample PDFs
ingest/   load, chunk, embed, index
api/      FastAPI app (retrieve + generate)
eval/     question set + LLM-as-judge scorer
ui/       Streamlit chat
```

## Quickstart

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # add your Azure or model keys
python ingest/build_index.py
uvicorn api.main:app --reload
streamlit run ui/app.py
```

## Evaluation

The assistant is scored on a held-out question set for:

- **Groundedness**: is every claim supported by a retrieved source?
- **Correctness**: does the answer match the expected answer?

| Change | Groundedness | Correctness |
|---|---|---|
| Baseline (chunk 500, top-k 3) | _fill in_ | _fill in_ |
| After tuning (chunk 300, top-k 5) | _fill in_ | _fill in_ |

Run: `python eval/run_eval.py`

## Responsible AI

See [RESPONSIBLE_AI.md](RESPONSIBLE_AI.md). Summary: answers are grounded and cited,
the assistant refuses out-of-scope questions, inputs and outputs pass content safety,
and no confidential data is used. Not for final underwriting or any decision requiring
guaranteed accuracy without human review.

## Status

- [ ] M1 ingest and chunk
- [ ] M2 embed and index
- [ ] M3 retrieve and generate with citations
- [ ] M4 chat UI + API
- [ ] M5 evaluation harness
- [ ] M6 guardrails, logging, responsible-AI note

Built by Faizan Malek.
