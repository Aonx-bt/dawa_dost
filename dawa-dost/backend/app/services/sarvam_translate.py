"""Text translation via Sarvam's translation API (client.text.translate).

Used to let the patient view their prescription/medication/symptom content
in their preferred language, independent of whichever language it was
originally written or extracted in.
"""
import logging

from sarvamai import SarvamAI

from app.config import get_settings

logger = logging.getLogger("dawa_dost.sarvam_translate")

settings = get_settings()

SUPPORTED_LANGUAGES = {
    "en-IN", "hi-IN", "bn-IN", "gu-IN", "kn-IN", "ml-IN", "mr-IN",
    "od-IN", "pa-IN", "ta-IN", "te-IN", "ur-IN",
}


class TranslationError(Exception):
    pass


class SarvamTranslateService:
    def __init__(self) -> None:
        self._client: SarvamAI | None = None

    def _get_client(self) -> SarvamAI:
        if not settings.sarvam_api_key:
            raise TranslationError("SARVAM_API_KEY is not configured on the server.")
        if self._client is None:
            self._client = SarvamAI(api_subscription_key=settings.sarvam_api_key)
        return self._client

    def translate_batch(
        self, texts: list[str], target_language_code: str, source_language_code: str = "auto"
    ) -> list[str]:
        """Translate a list of short strings, preserving order and blanks.

        Empty/whitespace-only entries are passed through unchanged (nothing
        useful to translate, and it saves an API call).
        """
        if target_language_code not in SUPPORTED_LANGUAGES:
            raise TranslationError(f"Unsupported target language: {target_language_code}")

        client = self._get_client()
        results: list[str] = []
        for text in texts:
            if not text or not text.strip():
                results.append(text)
                continue
            try:
                resp = client.text.translate(
                    input=text,
                    source_language_code=source_language_code,
                    target_language_code=target_language_code,
                )
                results.append(resp.translated_text)
            except Exception as exc:  # noqa: BLE001 - isolate all Sarvam SDK errors here
                logger.error("Translation failed for %r: %s", text, exc)
                results.append(text)  # fall back to original rather than failing the whole page
        return results


sarvam_translate_service = SarvamTranslateService()
