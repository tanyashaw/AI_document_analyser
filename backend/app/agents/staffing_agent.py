from app.core.llm import client, GROQ_MODEL
from app.utils.json_parser import parse_llm_json


def staffing_agent(state):

    text = state["text"]

    prompt = f"""
    Extract ONLY staffing, personnel, roles, or resourcing requirements
    mentioned in this document (required roles, headcount, qualifications,
    certifications, team structure, key personnel), regardless of document type.

    For EACH staffing requirement, return a structured object with these exact fields:
    - "role": the job title or role name (e.g. "Project Manager", "Senior Developer")
    - "details": key requirements for this role in one or two sentences
    - "page_ref": the page number where this requirement appears, e.g. "Page 8"
                  or "Page 8-9". If the page cannot be determined, use "N/A".

    If no staffing information is present, return an empty list.

    Return ONLY valid JSON in this exact format:
    {{
        "staffing_requirements": [
            {{
                "role": "...",
                "details": "...",
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
        max_tokens=500,  # bound output tokens to control per-call cost
    )

    content = response.choices[0].message.content
    parsed = parse_llm_json(content)
    state["staffing"] = parsed
    return state