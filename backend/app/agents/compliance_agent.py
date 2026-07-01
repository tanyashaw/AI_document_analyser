from app.core.llm import client, GROQ_MODEL
from app.utils.json_parser import parse_llm_json


def compliance_agent(state):

    text = state["text"]

    prompt = f"""
    Extract ALL compliance, legal, regulatory, certification, eligibility,
    or submission requirements mentioned in this document, regardless of
    document type.

    For EACH requirement, return a structured object with these exact fields:
    - "requirement": the specific requirement described in one clear sentence
    - "category": one of — Certification | Legal | Regulatory | Insurance |
                  Financial | Technical | Submission | Eligibility | Other
    - "page_ref": the page number where this requirement appears, e.g. "Page 4"
                  or "Page 4-5". If the page cannot be determined, use "N/A".
    - "mandatory": true if this is mandatory/required, false if optional

    If no compliance information is present, return an empty list.

    Return ONLY valid JSON in this exact format:
    {{
        "compliance_requirements": [
            {{
                "requirement": "...",
                "category": "...",
                "page_ref": "...",
                "mandatory": true
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
    state["compliance"] = parsed
    return state