from app.core.llm import client, GROQ_MODEL
from app.utils.json_parser import parse_llm_json


def _call_llm(prompt: str, max_tokens: int) -> str:
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content


def summary_agent(state):

    text = state["text"][:5000]  # cap input tokens

    doc_type = state.get("document_type", {}).get(
        "document_type_label",
        state.get("document_type", {}).get("document_type", "document")
    )

    # Primary prompt — descriptions are OUTSIDE the JSON, not as placeholder values
    prompt = f"""You are analyzing a {doc_type}. Read the document and extract:

1. executive_summary: 2-4 sentences covering who issued it, what it is about, what they need, and any key financial/timeline context.
2. objectives: Up to 6 short bullet points — the issuer's stated goals/purpose. Each under 15 words.
3. key_highlights: Up to 8 short bullet points — important details NOT in scope/deadlines/staffing/compliance (e.g. evaluation criteria, eligibility, budget signals, special conditions). Each under 20 words.

Be specific: use real names, numbers, dates from the document. Do not invent anything.

Return ONLY this JSON and nothing else:
{{
  "executive_summary": "...",
  "objectives": ["...", "..."],
  "key_highlights": ["...", "..."]
}}

DOCUMENT:
{text}"""

    content = _call_llm(prompt, max_tokens=700)
    parsed = parse_llm_json(content)

    # If JSON parse failed, retry once with an even simpler prompt
    if "error" in parsed:
        print("[summary_agent] Primary parse failed, retrying with simpler prompt")
        simple_prompt = f"""Analyze this {doc_type} and return ONLY valid JSON:
{{
  "executive_summary": "one paragraph summary of what this document is about",
  "objectives": ["goal 1", "goal 2"],
  "key_highlights": ["highlight 1", "highlight 2"]
}}

DOCUMENT:
{text[:3000]}"""
        content2 = _call_llm(simple_prompt, max_tokens=500)
        parsed = parse_llm_json(content2)

    # Last-resort fallback: build a minimal summary from the text itself
    if "error" in parsed or not isinstance(parsed, dict):
        print("[summary_agent] Both attempts failed — using text fallback")
        parsed = {
            "executive_summary": text[:400].strip() + "…" if len(text) > 400 else text.strip(),
            "objectives": [],
            "key_highlights": [],
        }

    state["summary"] = parsed
    return state