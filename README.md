# Insurance Document Assistant

A private, retrieval-augmented (RAG) assistant that answers staff questions about
insurance policy and claim documents. Every answer cites the exact source file and
page, and the assistant refuses when the documents do not contain the answer.

Built on the Microsoft stack (Azure AI Foundry + Azure AI Search) to show a
production-minded, trustworthy AI solution: document automation, grounded
generation with citations, and a self-built evaluation harness.

> Uses only publicly available sample documents. No confidential data. The `data/`
> folder is gitignored, so source PDFs are not committed.

## What it does

Ask a plain-language question ("How do I change a beneficiary?", "What is required
to submit a death claim?"). The assistant retrieves the most relevant passages from
the document set and answers using only those, citing file and page for each claim.
If nothing relevant is found (for example an off-topic question), it says so instead
of guessing.

## How it works

Two phases:

1. Ingest (once): read PDFs, split into ~400-word chunks, embed each chunk with
   `text-embedding-3-small`, and store the vectors in an Azure AI Search index.
2. Answer (per question): embed the question, retrieve the top-k nearest chunks from
   Azure AI Search, then send those passages plus the question to `gpt-5-mini` with a
   grounding prompt that requires citations and a refusal when unsupported.

```
Question -> embed -> Azure AI Search (vector top-k) -> grounded prompt -> gpt-5-mini
         -> cited answer  (+ logging, content-safety, refusal-when-unsure)
```

## Stack

- Python, FastAPI, Streamlit
- Azure AI Foundry: `gpt-5-mini` (chat), `text-embedding-3-small` (embeddings)
- Azure AI Search (vector index)
- LLM-as-judge evaluation harness (custom)
- Model access behind one adapter, so the same code runs on Azure or the OpenAI API

## Quickstart

```bash
python -m venv .venv && source .venv/Scripts/activate   # Windows Git Bash
pip install -r requirements.txt
cp .env.example .env        # fill in your Azure keys and endpoints
python ingest/build_index.py    # build the search index (once)
streamlit run ui/app.py         # chat UI
python eval/run_eval.py         # evaluation
```

## Evaluation

The assistant is scored by an LLM-as-judge harness on a held-out question set for
**groundedness** (is every claim supported by a retrieved source?) and
**correctness** (does it match the expected answer, including correctly refusing
out-of-scope questions?). Run `python eval/run_eval.py`; results are written to
`eval/eval_results.md`.

Two findings from building the evaluation, both worth more than the final number:

1. **The evaluation itself was buggy.** Groundedness first came back at 41%, which
   looked alarming. The cause was in the harness, not the model: the judge was only
   shown the first 400 characters of each source, so it could not verify answers that
   were actually correct and cited. Giving the judge the full passage raised
   groundedness to the 90s. Lesson: test the test.
2. **The assistant was over-refusing.** The eval then revealed the model sometimes
   appended "I don't have that information" after a correct answer, and refused on
   form-style documents it had actually retrieved. Tightening the grounding prompt
   (answer when context is relevant, never append a refusal, only refuse when nothing
   relevant is retrieved) fixed both.

After both fixes, runs land up to 12/12 (100%) on groundedness and correctness,
typically in the low-to-mid 90s. Scores wobble slightly run to run because the judge
is itself an LLM at temperature 1 (nondeterministic); a production setup would use a
deterministic temperature-0 judge and average several runs.

The eval also runs the questions concurrently (bounded, default 3 workers, with retry
on rate limits): a 12-case run drops from about 85s at 3 workers to about 60s at 5,
with identical scores. Set `EVAL_WORKERS` in `.env`.

## Responsible AI

See [RESPONSIBLE_AI.md](RESPONSIBLE_AI.md). In short: answers are grounded and cited,
the assistant refuses when unsure, inputs and outputs can be screened with content
safety, and it is designed so a human can verify every answer. Not for final
underwriting or any decision requiring guaranteed accuracy without review.

## Repo layout

```
data/       source PDFs (gitignored)
ingest/     load, chunk, embed, index  (+ download_docs.py helper)
ragcore/    retrieval + grounded generation
api/        FastAPI app
ui/         Streamlit chat
eval/       LLM-as-judge harness + question set + results
```

Built by Faizan Malek.
