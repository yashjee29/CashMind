"""
Moderation Reason Rewriter Engine
Handles prompt execution, LLM invocation, and output validation for moderation actions.
"""

from typing import Tuple
from app.core.exceptions import OutputValidationError
from app.core.providers.groq_provider import GroqProvider, get_groq_provider
from app.core.responses import ResponseMetadata
from app.modules.generate.moderation.prompts import PROMPT_VERSION, build_moderation_prompt
from app.modules.generate.moderation.schemas import (
    ModerationRewriteData,
    ModerationRewriteRequest,
)
from app.modules.generate.moderation.validators import (
    sanitize_moderation_output,
    validate_moderation_input,
)


class ModerationRewriter:
    """Executes moderation reason rewriting via Groq LLM with strict invariant checks."""

    def __init__(self, provider: GroqProvider | None = None) -> None:
        self._provider = provider

    @property
    def provider(self) -> GroqProvider:
        return self._provider or get_groq_provider()

    async def rewrite(
        self,
        request: ModerationRewriteRequest,
    ) -> Tuple[ModerationRewriteData, ResponseMetadata]:
        """Validates input, generates rewritten reason, and verifies response invariants."""
        # 1. Pre-validation
        validate_moderation_input(request)

        # 2. Build secure prompt
        messages = build_moderation_prompt(
            action=request.action,
            reason=request.reason,
            language=request.language,
            additional_context=request.additional_context,
            max_length=request.max_length or 500,
        )

        # 3. Call Groq
        result = await self.provider.generate_completion(
            task="moderation_rewrite",
            messages=messages,
        )

        parsed_json = result.get("parsed_json")
        if not isinstance(parsed_json, dict) or "rewritten_reason" not in parsed_json:
            raise OutputValidationError(
                "Model failed to return expected JSON with 'rewritten_reason'.",
                details={"raw_content": result.get("content")},
            )

        raw_rewritten = str(parsed_json["rewritten_reason"]).strip()
        if not raw_rewritten:
            raise OutputValidationError("Model returned an empty rewritten reason.")

        # 4. Post-generation sanitization and length check
        clean_rewritten = sanitize_moderation_output(
            raw_rewritten,
            max_length=request.max_length or 500,
        )

        data = ModerationRewriteData(
            action=request.action.value,
            original_reason=request.reason,
            rewritten_reason=clean_rewritten,
            language=request.language,
        )

        metadata = ResponseMetadata(
            model=result.get("model", "unknown"),
            provider="groq",
            prompt_version=PROMPT_VERSION,
        )

        return data, metadata
