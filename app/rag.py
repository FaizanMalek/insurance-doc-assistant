"""M3: retrieve top-k chunks and generate a grounded, cited answer."""
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery
import config

_search = SearchClient(config.SEARCH_ENDPOINT, config.SEARCH_INDEX,
                       AzureKeyCredential(config.SEARCH_KEY))

SYSTEM = (
    "You are an internal assistant for insurance staff. Answer ONLY using the "
    "CONTEXT below. For every claim, cite the source as [file, p.PAGE]. If the "
    "answer is not in the context, reply exactly: 'I don't have that information "
    "in the provided documents.' Do not use outside knowledge."
)


def retrieve(question, k=None):
    k = k or config.TOP_K
    qvec = config.embed([question])[0]
    results = _search.search(
        search_text=None,
        vector_queries=[VectorizedQuery(vector=qvec, k_nearest_neighbors=k, fields="vector")],
        select=["content", "source", "page"], top=k,
    )
    return [{"content": r["content"], "source": r["source"], "page": r["page"]} for r in results]


def answer(question, k=None):
    hits = retrieve(question, k)
    context = "\n\n".join(f"[{h['source']}, p.{h['page']}]\n{h['content']}" for h in hits)
    reply = config.chat(SYSTEM, f"CONTEXT:\n{context}\n\nQUESTION: {question}")
    return {"answer": reply, "sources": hits}


if __name__ == "__main__":
    import json
    q = " ".join(sys.argv[1:]) or "What is the grace period for premium payment?"
    print(json.dumps(answer(q), indent=2)[:2000])
