from app.core.llm import client, GROQ_MODEL
from app.utils.json_parser import parse_llm_json


def deliverables_agent(state):
    text = state["text"]

    prompt = f"""
    Extract ALL deliverables from this document — these are the specific outputs,
    products, reports, documents, or services that must be produced or handed over
    as part of this engagement.

    For EACH deliverable, return a structured object:
    - "item": clear description of the deliverable in one sentence
    - "page_ref": page number where mentioned, e.g. "Page 5". Use "N/A" if unknown.

    If no deliverables are present, return an empty list.

    Return ONLY valid JSON:
    {{
        "deliverables": [
            {{"item": "...", "page_ref": "..."}}
        ]
    }}

    DOCUMENT:
    {text}
    """

    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        max_tokens=500,  # bound output tokens to control per-call cost
    )
    content = response.choices[0].message.content
    parsed = parse_llm_json(content)
    state["deliverables"] = parsed
    return state