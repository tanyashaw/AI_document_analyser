from app.core.llm import client, GROQ_MODEL
import json
import re


def clean_json_response(content: str):

    # Remove markdown json formatting
    content = re.sub(r"```json", "", content)
    content = re.sub(r"```", "", content)

    # Remove extra whitespace
    content = content.strip()

    return content


def extract_rfp_info(chunk: str):

    prompt = f"""
    You are an expert RFP analysis system.

    Extract the following information STRICTLY in valid JSON format.

    IMPORTANT RULES:
    - Return ONLY JSON
    - No markdown
    - No explanations
    - Use lowercase snake_case keys
    - Always follow this schema exactly

    REQUIRED JSON SCHEMA:

    {{
        "project_scope": [],
        "deadlines": [],
        "staffing_requirements": [],
        "compliance_requirements": []
    }}

    DOCUMENT:
    {chunk}
    """

    try:

        response = client.chat.completions.create(

            model=GROQ_MODEL,

            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],

            temperature=0
        )

        content = response.choices[0].message.content

        cleaned_content = clean_json_response(content)

        parsed_json = json.loads(cleaned_content)

        return parsed_json

    except Exception as e:

        return {
            "error": str(e),
            "raw_response": content if 'content' in locals() else None
        }