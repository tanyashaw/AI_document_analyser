import json

from app.core.llm import client, GROQ_MODEL
from app.utils.json_parser import parse_llm_json


def _flatten(items):
    """Flatten whatever shape an upstream agent returned into a list of strings."""
    if not items:
        return []
    if isinstance(items, dict):
        items = list(items.values())
    flat = []
    for item in items:
        if isinstance(item, (list, tuple)):
            flat.extend(_flatten(item))
        elif isinstance(item, dict):
            flat.append(str(next(iter(item.values()), item)))
        elif item:
            flat.append(str(item))
    return flat


def summary_agent(state):

    text = state["text"]

    doc_type = state.get("document_type", {}).get(
        "document_type_label",
        state.get("document_type", {}).get("document_type", "document")
    )

    already_extracted = {
        "project_scope": _flatten(state.get("scope", {}).get("project_scope")),
        "deadlines": _flatten(state.get("deadlines", {}).get("deadlines")),
        "staffing_requirements": _flatten(state.get("staffing", {}).get("staffing_requirements")),
        "compliance_requirements": _flatten(state.get("compliance", {}).get("compliance_requirements")),
        "deliverables": _flatten(state.get("deliverables", {}).get("deliverables")),
        "technical_requirements": _flatten(state.get("technical", {}).get("technical_requirements")),
        "commercial_requirements": _flatten(state.get("commercial", {}).get("commercial_requirements")),
        "risks": _flatten(state.get("risks", {}).get("risks")),
    }

    prompt = f"""
    You are analyzing a {doc_type}.

    The following information has ALREADY been extracted into dedicated sections.
    Do NOT repeat or paraphrase any of it in your outputs:

    ALREADY EXTRACTED:
    {json.dumps(already_extracted, indent=2)}

    Now produce THREE outputs from the full document below.

    1. "executive_summary":
       Write a COMPREHENSIVE, DETAILED multi-paragraph executive summary.
       It MUST cover ALL of the following aspects that are present in the document:
       - The issuing organisation, its mandate, and the background/context
       - Why this document is being issued and what problem it is solving
       - The primary strategic objectives the issuer is trying to achieve
       - A high-level narrative of the overall scope and nature of the work
       - Key eligibility criteria and who can respond
       - The evaluation/selection approach in brief
       - Any notable financial signals, budget context, or pricing structure
       - Overall timeline, contract period, and key phases at a high level
       - Any unique, unusual, or critical contextual factors a reader must know
       - Anything else that is important and not captured in the dedicated sections

       Write AT LEAST 8-10 well-structured sentences in flowing prose paragraphs.
       Be SPECIFIC — reference actual numbers, names, dates, and facts from the document.
       Do NOT bullet-point the summary. Write it as professional prose.
       Do NOT repeat anything that is in ALREADY EXTRACTED above.

    2. "objectives":
       A list of the document's stated GOALS or PURPOSE — why this document exists,
       what the issuer wants to achieve strategically. Do NOT include scope line items,
       deadlines, staffing, compliance, deliverables, technical, commercial, or risk details.

    3. "key_highlights":
       A list of IMPORTANT ADDITIONAL points not covered in objectives or in the
       ALREADY EXTRACTED sections (e.g. evaluation criteria weights, unusual contract
       clauses, key stakeholders, bidding restrictions, special conditions).

    Return ONLY valid JSON:
    {{
        "executive_summary": "...",
        "objectives": [],
        "key_highlights": []
    }}

    DOCUMENT:
    {text}
    """

    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        max_tokens=800,  # needs more room than extraction agents since it writes prose
    )

    content = response.choices[0].message.content
    parsed = parse_llm_json(content)
    state["summary"] = parsed
    return state