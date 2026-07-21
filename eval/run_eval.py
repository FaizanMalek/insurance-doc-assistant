"""M5: LLM-as-judge evaluation.
Scores each answer for groundedness + correctness, prints a table, and writes
eval/eval_results.md so you can screenshot or attach it.
Run:  python eval/run_eval.py
"""
import os, sys, json, datetime
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from ragcore.rag import answer

JUDGE = (
    "You are a strict evaluator. Given a QUESTION, the ASSISTANT_ANSWER, its "
    "SOURCES, and an EXPECTED description, return a JSON object: "
    '{"grounded": true/false, "correct": true/false, "reason": "..."}. '
    "grounded = every claim is supported by the sources (a correct refusal counts). "
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
    with open("eval/questions.jsonl") as f:
        items = [json.loads(l) for l in f if l.strip()]
    rows, g, c = [], 0, 0
    for it in items:
        res = answer(it["question"])
        v = judge(it["question"], res["answer"], res["sources"], it["expected"])
        g += bool(v.get("grounded")); c += bool(v.get("correct"))
        rows.append((it["question"], v.get("grounded"), v.get("correct")))
        print(f"[{'OK ' if v.get('correct') else 'XX '}] {it['question'][:55]}")
    n = len(items)
    gp, cp = 100 * g // n, 100 * c // n
    lines = ["# Evaluation results", "",
             f"Run: {datetime.datetime.now():%Y-%m-%d %H:%M}  |  Questions: {n}", "",
             f"**Groundedness: {g}/{n} ({gp}%)  |  Correctness: {c}/{n} ({cp}%)**", "",
             "| Question | Grounded | Correct |", "|---|---|---|"]
    for q, gr, co in rows:
        lines.append(f"| {q} | {'yes' if gr else 'no'} | {'yes' if co else 'no'} |")
    with open("eval/eval_results.md", "w") as f:
        f.write("\n".join(lines) + "\n")
    print(f"\nGroundedness: {g}/{n} ({gp}%)   Correctness: {c}/{n} ({cp}%)")
    print("Wrote eval/eval_results.md")


if __name__ == "__main__":
    main()
