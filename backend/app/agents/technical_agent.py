from app.core.llm import client, GROQ_MODEL
from app.utils.json_parser import parse_llm_json


def technical_agent(state):
    text = state["text"]

    prompt = f"""
    Extract ALL technical requirements from this document — these are specifications
    about technology, systems, platforms, standards, methodologies, certifications,
    or technical capabilities that a vendor/bidder must have or implement.

    For EACH technical requirement, return a structured object:
    - "item": clear description of the technical requirement in one sentence
    - "page_ref": page number where mentioned, e.g. "Page 7". Use "N/A" if unknown.

    If no technical requirements are present, return an empty list.

    Return ONLY valid JSON:
    {{
        "technical_requirements": [
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
    state["technical"] = parsed
    return state