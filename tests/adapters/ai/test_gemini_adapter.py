"""Unit tests for Gemini adapter internals."""

from backend.adapters.ai.gemini_adapter import GeminiExtractor


def test_detect_image_mime_type_png() -> None:
    """Detect PNG signatures."""
    mime_type = GeminiExtractor._detect_image_mime_type(b"\x89PNG\r\n\x1a\nabc")
    assert mime_type == "image/png"


def test_detect_image_mime_type_jpeg() -> None:
    """Detect JPEG signatures."""
    mime_type = GeminiExtractor._detect_image_mime_type(b"\xff\xd8\xff\xe0abc")
    assert mime_type == "image/jpeg"


def test_detect_image_mime_type_unknown_returns_none() -> None:
    """Return None for unsupported image signatures."""
    mime_type = GeminiExtractor._detect_image_mime_type(b"not-an-image")
    assert mime_type is None
