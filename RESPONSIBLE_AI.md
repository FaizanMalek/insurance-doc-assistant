# Responsible AI note

**What it does:** answers staff questions using only the organisation's own
documents, retrieved at query time (RAG), and cites the source of every claim.

**How it avoids harm**
- Grounding + citations: answers are drawn from retrieved passages and cite
  file and page, so a human can verify.
- Refusal: if the documents do not contain the answer, the assistant says so
  instead of guessing.
- Content safety: inputs and outputs can be screened with Azure AI Content Safety.
- Logging: every question and the sources used are logged for review.
- Privacy: uses only public sample documents here; a real deployment would
  respect PIPEDA and document-level permissions (e.g. via Microsoft Graph).

**Where it should NOT be used**
- Final underwriting, claims, or pricing decisions.
- Anything requiring guaranteed accuracy without a human in the loop.
- Personal or regulated data without proper access controls and DPIA.

**Known limits:** retrieval quality depends on chunking and the document set;
the model can still misread context, which is why every answer is cited and the
system is evaluated (see eval/).
