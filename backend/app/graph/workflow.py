import time

from app.agents.classifier_agent import classifier_agent
from app.agents.summary_agent import summary_agent
from app.agents.combined_extraction_agent import extract_all_fields

from app.services.batcher import create_batches


# Which field inside each item is the "text" of that item — used to spot
# near-duplicate items that overlapping batches both picked up.
_DEDUPE_TEXT_FIELD = {
    "project_scope": "item",
    "deadlines": "event",
    "staffing_requirements": "role",
    "compliance_requirements": "requirement",
    "deliverables": "item",
    "technical_requirements": "item",
    "commercial_requirements": "item",
    "risks": "risk",
}

# Pause between batches. Worst case, one combined-extraction call costs
# roughly 3,000 tokens (input text + instructions + max output). To
# strictly never exceed 6,000 TPM at that worst case, calls would need to
# be ~30 seconds apart -- which makes a long document take a long time.
# In practice most batches use noticeably fewer tokens than the worst
# case (max_tokens is a ceiling, not a guarantee), so this is set lower
# as a practical middle ground: it cuts down how often we need to fall
# back to the retry-with-backoff already built into core/llm.py, without
# making every document analysis take 10+ minutes. If you see repeated
# "[llm] Rate limited, retrying in ...s" messages in your logs, that's
# the retry logic doing its job -- raise this value if it happens a lot.
_SECONDS_BETWEEN_BATCHES = 8.0


def _normalize(value) -> str:
    return " ".join(str(value).lower().split())


def _dedupe(items: list, text_field: str) -> list:
    """
    Overlapping batches can both extract the same item. This keeps the
    first occurrence of each distinct item (by its normalized text) and
    drops repeats.
    """
    seen = set()
    deduped = []
    for item in items:
        if not isinstance(item, dict):
            continue
        key = _normalize(item.get(text_field, ""))
        if not key or key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped


class _ParallelWorkflow:
    """
    Map-reduce extraction pipeline. Drop-in replacement for a compiled
    LangGraph app — exposes the same .invoke(state) interface.

    Execution order:
      1. classifier_agent + summary_agent run ONCE, on the start of the
         document (document type and an executive summary are reliably
         evident from the opening section, so there's no need to batch
         these two — each does its own internal truncation already).
      2. The FULL document text is split into batches (services/batcher.py).
      3. For EACH batch, ONE combined LLM call extracts all 8 categories
         at once (see agents/combined_extraction_agent.py) — this is the
         key difference from the 8-separate-calls-per-batch version: the
         document text for a batch is only sent to the model once, not 8
         times, which is what keeps this within Groq's free-tier TPM
         budget while still covering the whole document.
      4. Results from every batch are merged and de-duplicated, so an
         item on page 40 is found just as reliably as one on page 2 — not
         just whatever fit in the first ~8,000 characters.
    """

    def invoke(self, state: dict) -> dict:
        full_text = state["text"]

        # Step 1: classification + summary.
        state = classifier_agent(state)
        state = summary_agent(state)

        # Step 2: split the FULL document into batches for extraction.
        batches = create_batches(full_text)

        merged = {key: [] for key in _DEDUPE_TEXT_FIELD}

        # Step 3: one combined call per batch, run sequentially (not in
        # parallel) — with only 1 call per batch there's no per-batch
        # parallelism left to exploit, and staying sequential is what
        # lets the pacing delay below actually do its job.
        for i, batch_text in enumerate(batches):
            result = extract_all_fields(batch_text)
            for key in merged:
                merged[key].extend(result.get(key, []))

            is_last_batch = i == len(batches) - 1
            if not is_last_batch:
                time.sleep(_SECONDS_BETWEEN_BATCHES)

        # Step 4: drop near-duplicate items picked up by overlapping batches.
        for key, items in merged.items():
            text_field = _DEDUPE_TEXT_FIELD[key]
            merged[key] = _dedupe(items, text_field)

        state["scope"] = {"project_scope": merged["project_scope"]}
        state["deadlines"] = {"deadlines": merged["deadlines"]}
        state["staffing"] = {"staffing_requirements": merged["staffing_requirements"]}
        state["compliance"] = {"compliance_requirements": merged["compliance_requirements"]}
        state["deliverables"] = {"deliverables": merged["deliverables"]}
        state["technical"] = {"technical_requirements": merged["technical_requirements"]}
        state["commercial"] = {"commercial_requirements": merged["commercial_requirements"]}
        state["risks"] = {"risks": merged["risks"]}

        return state


# Public name — imported by rfp.py as `app_graph`
app_graph = _ParallelWorkflow()