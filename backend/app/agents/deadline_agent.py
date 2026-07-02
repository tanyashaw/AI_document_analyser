from app.core.llm import client, GROQ_MODEL
from app.utils.json_parser import parse_llm_json


def deadline_agent(state):

    text = state["text"]

    prompt = f"""
    Extract ALL dates, deadlines, and milestones from this document
    (submission dates, Q&A cut-offs, award dates, contract start/end,
    validity periods, milestones, etc.), regardless of document type.

    For EACH deadline, return a structured object with these exact fields:
    - "event": a clear description of what this date/deadline is for
    - "date": the date or date range as stated in the document (e.g. "15 August 2025")
    - "page_ref": the page number where this date appears, e.g. "Page 6"
                  or "Page 6-7". If the page cannot be determined, use "N/A".

    If no dates are present, return an empty list.

    Return ONLY valid JSON in this exact format:
    {{
        "deadlines": [
            {{
                "event": "...",
                "date": "...",
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
    state["deadlines"] = parsed
    return state