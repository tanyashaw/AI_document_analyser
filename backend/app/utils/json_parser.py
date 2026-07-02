import json
import re


def _fix_trailing_commas(text: str) -> str:
    """Remove trailing commas before ] or } — common model mistake."""
    text = re.sub(r",\s*}", "}", text)
    text = re.sub(r",\s*]", "]", text)
    return text


def parse_llm_json(content: str):
    """
    Robustly extract and parse JSON from LLM output that may contain:
    - Preamble text ("Here are the deliverables extracted...")
    - Markdown code fences (```json ... ```)
    - Trailing commas (common model mistake)
    - Extra whitespace
    """
    if not content or not content.strip():
        return {"error": "empty response", "raw_content": ""}

    # Step 1: strip markdown code fences
    cleaned = re.sub(r"```json", "", content)
    cleaned = re.sub(r"```", "", cleaned).strip()

    # Step 2: try direct parse first (fastest path)
    try:
        return json.loads(cleaned)
    except Exception:
        pass

    # Step 3: fix trailing commas and retry
    try:
        return json.loads(_fix_trailing_commas(cleaned))
    except Exception:
        pass

    # Step 4: extract JSON object or array from surrounding text
    # Finds the first { ... } or [ ... ] block in the response
    for pattern in [r"(\{[\s\S]*\})", r"(\[[\s\S]*\])"]:
        match = re.search(pattern, cleaned)
        if match:
            candidate = match.group(1)
            try:
                return json.loads(candidate)
            except Exception:
                # Try with trailing comma fix
                try:
                    return json.loads(_fix_trailing_commas(candidate))
                except Exception:
                    pass

    # Step 5: give up — log and return error dict
    print(f"[parse_llm_json] All parse attempts failed")
    print(f"[parse_llm_json] Raw content was: {content[:500]}")
    return {
        "error": "json_parse_failed",
        "raw_content": content[:500]
    }