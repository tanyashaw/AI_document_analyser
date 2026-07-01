import json
import re


def parse_llm_json(content: str):

    try:

        # Remove markdown formatting
        content = re.sub(r"```json", "", content)
        content = re.sub(r"```", "", content)

        # Remove extra spaces
        content = content.strip()

        # Convert string to JSON
        parsed = json.loads(content)

        return parsed

    except Exception as e:

        return {
            "error": str(e),
            "raw_content": content
        }