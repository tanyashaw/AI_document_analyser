from app.core.llm import client, GROQ_MODEL
from app.utils.json_parser import parse_llm_json


def commercial_agent(state):
    text = state["text"]

    prompt = f"""
    Extract ALL commercial requirements from this document — these include:
    pricing structures, payment terms, budget limits/ranges, bid/proposal bond
    requirements, performance guarantees, contract duration, warranty terms,
    penalty clauses, insurance requirements (commercial), and any financial
    conditions of the engagement.

    For EACH commercial requirement, return a structured object:
    - "item": clear description of the commercial requirement in one sentence
    - "page_ref": page number where mentioned, e.g. "Page 9". Use "N/A" if unknown.

    If no commercial requirements are present, return an empty list.

    Return ONLY valid JSON:
    {{
        "commercial_requirements": [
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
    state["commercial"] = parsed
    return state