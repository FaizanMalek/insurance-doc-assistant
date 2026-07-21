"""M4: FastAPI wrapper.  Run:  uvicorn api.main:app --reload"""
import os, sys, logging
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fastapi import FastAPI
from pydantic import BaseModel
from ragcore.rag import answer

logging.basicConfig(filename="assistant.log", level=logging.INFO,
                    format="%(asctime)s %(message)s")
app = FastAPI(title="Insurance Document Assistant")


class Query(BaseModel):
    question: str


@app.post("/chat")
def chat(q: Query):
    result = answer(q.question)
    logging.info("Q=%s | sources=%s", q.question,
                 [f"{s['source']} p.{s['page']}" for s in result["sources"]])
    return result


@app.get("/health")
def health():
    return {"ok": True}
