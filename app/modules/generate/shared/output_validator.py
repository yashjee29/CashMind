"""
Shared Output Validation Utilities
Common text sanitization and structure verification across generative tasks.
"""

import json
from typing import Any, Dict
from app.core.exceptions import OutputValidationError


def parse_and_validate_json_dict(raw_content: str, required_keys: list[str]) -> Dict[str, Any]:
    """Parses JSON content and verifies required top-level keys."""
    try:
        data = json.loads(raw_content)
    except json.JSONDecodeError as e:
        raise OutputValidationError(f"Invalid JSON returned by LLM: {str(e)}", details={"raw": raw_content})

    if not isinstance(data, dict):
        raise OutputValidationError("Expected JSON object from LLM, got non-object.", details={"raw": raw_content})

    for key in required_keys:
        if key not in data:
            raise OutputValidationError(f"Missing required key '{key}' in LLM output.", details={"keys": list(data.keys())})

    return data
