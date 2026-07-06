"""
Extracts ALL 8 requirement categories from one batch of document text in a
SINGLE LLM call, instead of one call per category (8 calls).

Why this matters specifically for Groq's free tier:
The binding constraint on Groq's free tier isn't the daily request cap —
it's TPM (tokens per minute), and it's tight: llama-3.1-8b-instant gets
6,000 TPM, shared across your whole account. That budget is consumed by
INPUT tokens too, and the input (the document text) was previously being
re-sent 8 times per batch — once per agent — even though it's the exact
same text every time. Combining 8 agents into 1 call means the document
text for a batch is only paid for once, which is roughly an 8x cut in
token usage for the same document coverage.

Accuracy fixes in this version (added after reviewing real output):
  1. Every item must now include an "evidence" field — a short direct
     quote from the document backing it up. If the model can't produce a
     real quote, it's instructed to drop the item instead of guessing.
     This also gives you something concrete to spot-check results against.
  2. Deadlines with no findable date use "Not specified" instead of "N/A",
     and are only included at all if the milestone is explicitly named in
     the text — no more free-floating page numbers attached to items the
     model couldn't actually verify.
  3. The model is told not to output a generic/summary version of a
     requirement (e.g. "Minimum Insurance Requirements") when it's also
     extracting the specific itemized version of the same requirement
     (e.g. the actual dollar amounts) — this was showing up as duplicate-
     looking rows in the compliance table.
  4. compliance_requirements categories now each have a short example, so
     the same kind of requirement doesn't get filed under different
     categories in different batches.
"""

from app.core.llm import client, GROQ_MODEL
from app.utils.json_parser import parse_llm_json

# Every category this single call extracts, and the exact field shape for
# each item — matches what the old 8 separate agents used to return, so
# nothing downstream (merging, dedup, the final response builder) needs
# to change.
_RESULT_SHAPE = {
    "project_scope": [],
    "deadlines": [],
    "staffing_requirements": [],
    "compliance_requirements": [],
    "deliverables": [],
    "technical_requirements": [],
    "commercial_requirements": [],
    "risks": [],
}


def extract_all_fields(text: str) -> dict:
    """
    Extract every category from ONE batch of document text in one call.
    Returns a dict with all 8 keys (each a list, possibly empty) — never
    raises; a parsing failure just comes back as all-empty lists so one
    bad batch can't take down the whole document's analysis.
    """

    prompt = f"""
    You are an expert document analyst. Read the document excerpt below
    and extract every relevant item for EACH of these 8 categories.
    If a category has nothing in this excerpt, return an empty list for
    it — do not guess or invent items that aren't actually there.

    GROUNDING RULE (applies to every item in every category):
    Every item must include an "evidence" field: a short direct quote
    (no more than 20 words) copied from the DOCUMENT EXCERPT below that
    actually supports this item. If you cannot find real, quotable text
    to support an item, DO NOT include that item — do not guess, and do
    not invent something just to fill out a category.

    NO DUPLICATE GRANULARITY RULE:
    If the same requirement appears BOTH as a general/summary statement
    (e.g. a section heading like "Minimum Insurance Requirements") AND as
    specific itemized details (e.g. the actual dollar amounts and coverage
    types), extract ONLY the specific version. Do not also add a separate
    generic item that just restates what the specific items already cover.

    1. project_scope — the work/goods/services being requested or covered.
       Fields: "item" (one clear sentence), "page_ref" (e.g. "Page 3", or
       "N/A" if unknown), "evidence".

    2. deadlines — dates, deadlines, milestones (submission dates, Q&A
       cut-offs, award dates, contract start/end, validity periods).
       Fields: "event", "date", "page_ref", "evidence".
       - Only include a milestone if it is explicitly named somewhere in
         this excerpt. Do not infer deadlines that aren't actually named.
       - If the milestone is named but no specific date/timeframe is
         given for it, set "date" to "Not specified" (never "N/A") — and
         "evidence" must quote the sentence that names the milestone, so
         there's still a real reason page_ref is included.

    3. staffing_requirements — required roles, headcount, qualifications,
       certifications, team structure, key personnel.
       Fields: "role", "details" (one or two sentences), "page_ref",
       "evidence".

    4. compliance_requirements — legal, regulatory, certification,
       eligibility, or submission requirements.
       Fields: "requirement", "category", "page_ref", "mandatory" (true or
       false), "evidence".
       "category" must be exactly one of, using these as a guide:
         - Certification: licenses, required qualifications, training
           (e.g. "guards must be licensed to carry firearms")
         - Legal: contract law terms, indemnification, liability clauses
         - Regulatory: government/industry codes and regulations
         - Insurance: required coverage types and minimum amounts
         - Financial: bonding, financial statements, minimum revenue
         - Technical: required technical standards or specifications
         - Submission: required forms, formatting, submission process
           (e.g. "submit forms in the exact sequence provided")
         - Eligibility: who is allowed to bid (business type, certified
           status required to qualify at all)
         - Other: anything that genuinely doesn't fit the above

    5. deliverables — specific outputs, products, reports, or services
       that must be produced or handed over.
       Fields: "item", "page_ref", "evidence".

    6. technical_requirements — technology, systems, platforms, standards,
       methodologies, or technical capabilities required.
       Fields: "item", "page_ref", "evidence".

    7. commercial_requirements — pricing, payment terms, budget, bonds,
       guarantees, contract duration, warranty, penalties, insurance
       (commercial), financial conditions.
       Fields: "item", "page_ref", "evidence".

    8. risks — risks explicitly stated OR reasonably inferred (tight
       timelines, complex scope, regulatory exposure, penalties,
       ambiguous requirements, resource constraints).
       Fields: "risk", "severity" (High | Medium | Low), "type" (Schedule |
       Technical | Financial | Compliance | Resource | Scope | Legal |
       Other), "source" (Explicit | Inferred), "page_ref" ("N/A" for
       inferred risks), "evidence" (for Inferred risks, quote the text
       that made you infer it, e.g. the tight-timeline sentence).

    Return ONLY valid JSON in exactly this shape, with no extra text
    before or after it:
    {{
        "project_scope": [{{"item": "...", "page_ref": "...", "evidence": "..."}}],
        "deadlines": [{{"event": "...", "date": "...", "page_ref": "...", "evidence": "..."}}],
        "staffing_requirements": [{{"role": "...", "details": "...", "page_ref": "...", "evidence": "..."}}],
        "compliance_requirements": [{{"requirement": "...", "category": "...", "page_ref": "...", "mandatory": true, "evidence": "..."}}],
        "deliverables": [{{"item": "...", "page_ref": "...", "evidence": "..."}}],
        "technical_requirements": [{{"item": "...", "page_ref": "...", "evidence": "..."}}],
        "commercial_requirements": [{{"item": "...", "page_ref": "...", "evidence": "..."}}],
        "risks": [{{"risk": "...", "severity": "...", "type": "...", "source": "...", "page_ref": "...", "evidence": "..."}}]
    }}

    DOCUMENT EXCERPT:
    {text}
    """

    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            # Slightly lower than before (was 1000) to offset the extra
            # "evidence" field now required on every item — keeps total
            # per-call token cost in a similar range to the pre-evidence
            # version instead of growing on top of it.
            max_tokens=900,
        )
        content = response.choices[0].message.content
        parsed = parse_llm_json(content)
        if not isinstance(parsed, dict):
            return dict(_RESULT_SHAPE)
        # Make sure every expected key exists, even if the model omitted one.
        return {key: parsed.get(key, []) or [] for key in _RESULT_SHAPE}
    except Exception as e:
        print(f"[combined_extraction_agent] failed on a batch, skipping just that batch: {e}")
        return dict(_RESULT_SHAPE)