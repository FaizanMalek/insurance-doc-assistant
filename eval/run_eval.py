"""M5: LLM-as-judge evaluation (parallel).
Runs questions concurrently (default 3 at a time) with retry on rate limits,
prints a pass/fail line per question and the total run time, and writes
eval/eval_results.md with a summary table plus a "Failure details" section.

Run:            python eval/run_eval.py
Change workers: set EVAL_WORKERS in .env (1 = sequential, 3 = default, 5 = faster/riskier)
"""
import os, sys, json, time, datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from ragcore.rag import answer

WORKERS = int(os.getenv("EVAL_WORKERS", "3"))

JUDGE = (
    "You are a strict evaluator. Given a QUESTION, the ASSISTANT_ANSWER, its "
    "SOURCES, and an EXPECTED description, return a JSON object: "
    '{"grounded": true/false, "correct": true/false, "reason": "one sentence why"}. '
    "grounded = every claim is supported by the sources (a correct refusal counts). "
    "correct = the answer matches the expected description (a correct refusal on "
    "an out-of-scope question counts as correct)."
)


def _retry(fn, tries=4):
    """Call fn(); retry with backoff on rate-limit / transient errors."""
    for i in range(tries):
        try:
            return fn()
        except Exception as e:
            if i == tries - 1:
                raise
            time.sleep(2 ** i)  # 1s, 2s, 4s


def judge(q, ans, sources, expected):
    src = "\n".join(f"[{s['source']} p.{s['page']}] {s['content']}" for s in sources)
    user = (f"QUESTION: {q}\nASSISTANT_ANSWER: {ans}\nSOURCES:\n{src}\n"
            f"EXPECTED: {expected}\nReturn only the JSON.")
    raw = _retry(lambda: config.chat(JUDGE, user))
    try:
        return json.loads(raw[raw.find("{"):raw.rfind("}") + 1])
    except Exception:
        return {"grounded": False, "correct": False, "reason": "unparseable judge output: " + raw[:120]}


def process(idx, it):
    try:
        res = _retry(lambda: answer(it["question"]))
        v = judge(it["question"], res["answer"], res["sources"], it["expected"])
        return idx, {"q": it["question"], "expected": it["expected"], "answer": res["answer"],
                     "sources": res["sources"], "grounded": bool(v.get("grounded")),
                     "correct": bool(v.get("correct")), "reason": v.get("reason", "")}
    except Exception as e:
        return idx, {"q": it["question"], "expected": it["expected"], "answer": "",
                     "sources": [], "grounded": False, "correct": False,
                     "reason": f"error: {e}"}


def main():
    with open("eval/questions.jsonl") as f:
        items = [json.loads(l) for l in f if l.strip()]
    n = len(items)
    results = [None] * n
    start = time.time()
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futs = [ex.submit(process, i, it) for i, it in enumerate(items)]
        for fut in as_completed(futs):
            idx, row = fut.result()
            results[idx] = row
            ok = row["grounded"] and row["correct"]
            print(f"[{'OK ' if ok else 'XX '}] {row['q'][:55]}")
    elapsed = time.time() - start

    g = sum(r["grounded"] for r in results); c = sum(r["correct"] for r in results)
    gp, cp = 100 * g // n, 100 * c // n

    L = ["# Evaluation results", "",
         f"Run: {datetime.datetime.now():%Y-%m-%d %H:%M}  |  Questions: {n}  |  "
         f"Workers: {WORKERS}  |  Time: {elapsed:.1f}s", "",
         f"**Groundedness: {g}/{n} ({gp}%)  |  Correctness: {c}/{n} ({cp}%)**", "",
         "| Question | Grounded | Correct |", "|---|---|---|"]
    for r in results:
        L.append(f"| {r['q']} | {'yes' if r['grounded'] else 'no'} | {'yes' if r['correct'] else 'no'} |")
    fails = [r for r in results if not (r["grounded"] and r["correct"])]
    if fails:
        L += ["", "## Failure details", ""]
        for r in fails:
            srcs = ", ".join(f"{s['source']} p.{s['page']}" for s in r["sources"])
            L += [f"### {r['q']}",
                  f"- Grounded: {r['grounded']}  |  Correct: {r['correct']}",
                  f"- Judge reason: {r['reason']}",
                  f"- Expected: {r['expected']}",
                  f"- Sources retrieved: {srcs}",
                  f"- Assistant answer: {r['answer'][:700]}", ""]
    with open("eval/eval_results.md", "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")

    print(f"\nGroundedness: {g}/{n} ({gp}%)   Correctness: {c}/{n} ({cp}%)")
    print(f"Ran {n} questions with {WORKERS} workers in {elapsed:.1f}s")
    print("Wrote eval/eval_results.md")


if __name__ == "__main__":
    main()
