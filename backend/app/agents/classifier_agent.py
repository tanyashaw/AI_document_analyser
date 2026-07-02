from app.core.llm import client, GROQ_MODEL
from app.utils.json_parser import parse_llm_json


DOCUMENT_TYPES = [
    "RFP",      # Request for Proposal
    "RFQ",      # Request for Quotation
    "RFI",      # Request for Information
    "ITB",      # Invitation to Bid
    "SOW",      # Statement of Work
    "Contract",
    "NDA",
    "Proposal",
    "Policy Document",
    "Report",
    "Other"
]


def classifier_agent(state):

    # Document type is almost always evident from the opening of the doc;
    # no need to burn tokens sending the whole thing to this call.
    text = state["text"][:2000]

    prompt = f"""
    You are a document classification expert.

    Identify what TYPE of document the text below is.

    Choose the single best match from this list:
    {", ".join(DOCUMENT_TYPES)}

    If it doesn't clearly match a procurement/business document type,
    classify it as "Other" and describe what it actually is in
    "document_type_label".

    Return ONLY valid JSON in this exact format:
    {{
        "document_type": "<one value from the list above>",
        "document_type_label": "<short human-readable label, e.g. 'Request for Proposal (RFP)'>",
        "confidence": "<High | Medium | Low>",
        "reasoning": "<one short sentence explaining why>"
    }}

    DOCUMENT:
    {text}
    """

    response = client.chat.completions.create(

        model=GROQ_MODEL,

        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],

        temperature=0,
        max_tokens=150,  # this response is a small fixed-shape JSON object
    )

    content = response.choices[0].message.content

    parsed = parse_llm_json(content)

    state["document_type"] = parsed

    return state