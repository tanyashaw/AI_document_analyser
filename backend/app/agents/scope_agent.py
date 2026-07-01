from app.core.llm import client, GROQ_MODEL
from app.utils.json_parser import parse_llm_json


def scope_agent(state):

    text = state["text"]

    prompt = f"""
    Extract ONLY the scope of work / project scope from this document
    (what work, goods, or services are being requested or covered).

    This applies regardless of document type (RFP, RFQ, ITB, RFI,
    SOW, contract, etc.) — use whatever section describes the
    work/goods/services involved.

    For EACH scope item, return a structured object with these exact fields:
    - "item": a clear one-sentence description of the scope item
    - "page_ref": the page number where this item appears, e.g. "Page 3"
                  or "Page 3-4". If the page cannot be determined, use "N/A".

    If no scope information is present, return an empty list.

    Return ONLY valid JSON in this exact format:
    {{
        "project_scope": [
            {{
                "item": "...",
                "page_ref": "..."
            }}
        ]
    }}

    DOCUMENT:
    {text}
    """

    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )

    content = response.choices[0].message.content
    parsed = parse_llm_json(content)
    state["scope"] = parsed
    return state