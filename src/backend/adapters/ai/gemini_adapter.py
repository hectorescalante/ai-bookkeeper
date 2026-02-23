"""Gemini 3 Pro adapter for AI invoice extraction.

Implements the AIExtractor port using the Google Gen AI SDK.
Supports both text-based and scanned (image) PDFs.
"""

import json
import logging
from typing import Any, Never

from google import genai
from google.genai import types

from backend.domain.entities.configuration import DEFAULT_AI_MODEL
from backend.ports.output.ai_extractor import (
    AIAuthError,
    AIExtractionError,
    AIExtractor,
    AIRateLimitError,
    AITimeoutError,
    ExtractionResult,
    PDFContent,
)

logger = logging.getLogger(__name__)

# Timeout for AI requests in seconds
REQUEST_TIMEOUT = 60

# System prompt for invoice extraction
SYSTEM_PROMPT = (
    "You are an invoice data extraction assistant for a commercial shipping agent. "
    "Your task is to extract structured data from invoice PDFs (either text-based or "
    "scanned images). Return ONLY valid JSON, no markdown or explanation."
)


class GeminiExtractor(AIExtractor):
    """Gemini 3 Pro implementation of AIExtractor.
    Uses the google-genai SDK to send PDF content to Gemini 3 Pro and receive
    structured invoice data.
    and receive structured invoice data.
    """

    def __init__(self, api_key: str, model_name: str = DEFAULT_AI_MODEL) -> None:
        """Initialize Gemini extractor.

        Args:
            api_key: Google Gemini API key
            model_name: Model identifier (default: gemini-3-pro)
        """
        self._api_key = api_key
        self._model_name = model_name
        self._client = genai.Client(api_key=api_key)

    def extract_invoice_data(
        self,
        pdf_content: PDFContent,
        company_nif: str,
        extraction_prompt: str,
    ) -> ExtractionResult:
        """Extract structured invoice data from PDF content using Gemini 3.

        Args:
            pdf_content: The PDF content (text and/or images)
            company_nif: Company NIF for invoice classification
            extraction_prompt: The prompt template to use

        Returns:
            ExtractionResult with parsed data

        Raises:
            AITimeoutError: If the request times out (60s)
            AIRateLimitError: If rate limited (429)
            AIAuthError: If API key is invalid (401/403)
            AIExtractionError: For other errors
        """
        # Build the user prompt with company NIF substitution
        user_prompt = extraction_prompt.replace("{{company_nif}}", company_nif)

        # Build request contents
        contents: list[Any] = []

        # Add text content if available
        if pdf_content.has_text:
            contents.append(
                f"{user_prompt}\n\n--- PDF Text Content ---\n{pdf_content.text_content}"
            )
        else:
            contents.append(user_prompt)

        # Add page images for scanned PDFs
        for image_bytes in pdf_content.page_images:
            contents.append(
                types.Part.from_bytes(
                    data=image_bytes,
                    mime_type="image/png",
                )
            )

        try:
            logger.info(
                "Sending extraction request to Gemini",
                extra={
                    "model": self._model_name,
                    "filename": pdf_content.filename,
                    "has_text": pdf_content.has_text,
                    "has_images": pdf_content.has_images,
                    "page_count": pdf_content.page_count,
                },
            )

            response = self._client.models.generate_content(
                model=self._model_name,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    temperature=1.0,
                    response_mime_type="application/json",
                    http_options=types.HttpOptions(timeout=REQUEST_TIMEOUT * 1000),
                ),
            )

            # Extract the text response
            raw_json = response.text

            if not raw_json:
                raise AIExtractionError("Empty response from Gemini")

            # Parse JSON response
            parsed_data = self._parse_response(raw_json)

            logger.info(
                "Extraction completed successfully",
                extra={
                    "document_type": parsed_data.get("document_type"),
                    "filename": pdf_content.filename,
                },
            )

            return ExtractionResult(
                raw_json=raw_json,
                parsed_data=parsed_data,
                model_used=self._model_name,
            )

        except Exception as e:
            self._handle_error(e)

    def test_connection(self, api_key: str) -> bool:
        """Test that the API key is valid by making a simple request.

        Args:
            api_key: The API key to test

        Returns:
            True if the connection is successful
        """
        try:
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model=self._model_name,
                contents="Respond with exactly: OK",
                config=types.GenerateContentConfig(
                    http_options=types.HttpOptions(timeout=15000)
                ),
            )
            client.close()
            return bool(response.text)
        except Exception as e:
            logger.warning("API key test failed: %s", str(e))
            return False

    def _parse_response(self, raw_json: str) -> dict[str, Any]:
        """Parse and validate the JSON response from Gemini.

        Args:
            raw_json: Raw JSON string from the model

        Returns:
            Parsed dict

        Raises:
            AIExtractionError: If response is not valid JSON
        """
        # Clean up response — sometimes models wrap in markdown code blocks
        cleaned = raw_json.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        try:
            data: dict[str, Any] = json.loads(cleaned)
        except json.JSONDecodeError as e:
            raise AIExtractionError(f"Invalid JSON response from AI: {e}") from e

        # Basic structure validation
        if "document_type" not in data:
            raise AIExtractionError(
                "AI response missing required field: document_type"
            )

        return data

    def _handle_error(self, error: Exception) -> Never:
        """Convert SDK exceptions to domain exceptions.

        Args:
            error: The original exception

        Raises:
            AITimeoutError: For timeout errors
            AIRateLimitError: For 429 rate limit errors
            AIAuthError: For 401/403 auth errors
            AIExtractionError: For all other errors
        """
        error_str = str(error)
        error_type = type(error).__name__
        error_code = getattr(error, "code", None)

        logger.error(
            "Gemini API error: %s: %s",
            error_type,
            error_str,
        )

        # Already a domain exception, re-raise
        if isinstance(error, AIExtractionError):
            raise error

        # Timeout detection
        if "timeout" in error_str.lower() or "deadline" in error_str.lower():
            raise AITimeoutError(
                f"AI request timed out after {REQUEST_TIMEOUT}s"
            ) from error

        # Rate limit detection (429)
        if (
            error_code == 429
            or "429" in error_str
            or "resource_exhausted" in error_str.lower()
            or "rate limit" in error_str.lower()
            or "quota" in error_str.lower()
        ):
            raise AIRateLimitError(retry_after_minutes=5) from error

        # Auth error detection (401, 403)
        if (
            error_code in {401, 403}
            or
            "401" in error_str
            or "403" in error_str
            or "api_key" in error_str.lower()
            or "permission" in error_str.lower()
            or "invalid" in error_str.lower() and "key" in error_str.lower()
        ):
            raise AIAuthError("Invalid or expired Gemini API key") from error

        # Generic error
        raise AIExtractionError(f"AI extraction failed: {error_str}") from error
