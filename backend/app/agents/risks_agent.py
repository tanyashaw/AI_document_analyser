from app.core.llm import client, GROQ_MODEL
from app.utils.json_parser import parse_llm_json


def risks_agent(state):
    text = state["text"]

    prompt = f"""
    Identify and extract ALL risks associated with this document — both risks
    explicitly mentioned in the document AND key risks that can be INFERRED
    from its requirements (e.g. tight timelines, complex technical scope,
    regulatory exposure, financial penalties, ambiguous requirements, resource
    constraints, etc.).

    For EACH risk, return a structured object:
    - "risk": description of the risk in one clear sentence
    - "severity": "High", "Medium", or "Low" based on potential impact
    - "type": one of — Schedule | Technical | Financial | Compliance | Resource | Scope | Legal | Other
    - "source": "Explicit" if stated in document, "Inferred" if derived from analysis
    - "page_ref": page number if explicitly mentioned, e.g. "Page 11". Use "N/A" for inferred risks.

    Return ONLY valid JSON:
    {{
        "risks": [
            {{
                "risk": "...",
                "severity": "...",
                "type": "...",
                "source": "...",
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
    state["risks"] = parsed
    return state
