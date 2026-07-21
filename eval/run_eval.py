"""M5: LLM-as-judge evaluation. Scores each answer for groundedness + correctness.
Run:  python eval/run_eval.py   (writes results and prints a summary table)"""
import os, sys, json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from app.rag import answer

JUDGE = (
    "You are a strict evaluator. Given a QUESTION, the ASSISTANT_ANSWER, its "
    "SOURCES, and an EXPECTED description, return a JSON object: "
    '{"grounded": true/false, "correct": true/false, "reason": "..."}. '
    "grounded = every claim is supported by the sources (or a correct refusal). "
    "correct = the answer matches the expected description (a correct refusal on "
    "an out-of-scope question counts as correct)."
)


def judge(q, ans, sources, expected):
    src = "\n".join(f"[{s['source']} p.{s['page']}] {s['content'][:400]}" for s in sources)
    user = (f"QUESTION: {q}\nASSISTANT_ANSWER: {ans}\nSOURCES:\n{src}\n"
            f"EXPECTED: {expected}\nReturn only the JSON.")
    raw = config.chat(JUDGE, user)
    try:
        return json.loads(raw[raw.find("{"):raw.rfind("}") + 1])
    except Exception:
        return {"grounded": False, "correct": False, "reason": "unparseable: " + raw[:120]}


def main():
    rows, g, c = [], 0, 0
    with open("eval/questions.jsonl") as f:
        items = [json.loads(l) for l in f if l.strip()]
    for it in items:
        res = answer(it["question"])
        v = judge(it["question"], res["answer"], res["sources"], it["expected"])
        g += bool(v.get("grounded")); c += bool(v.get("correct"))
        rows.append((it["question"][:45], v.get("grounded"), v.get("correct")))
    n = len(items)
    print(f"\n{'QUESTION':47} GROUNDED  CORRECT")
    for q, gr, co in rows:
        print(f"{q:47} {str(gr):8} {str(co)}")
    print(f"\nGroundedness: {g}/{n} ({100*g//n}%)   Correctness: {c}/{n} ({100*c//n}%)")


if __name__ == "__main__":
    main()
