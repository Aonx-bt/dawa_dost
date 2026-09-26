from pydantic import BaseModel, Field

from fastapi import APIRouter

from app.services.sarvam_translate import SUPPORTED_LANGUAGES, TranslationError, sarvam_translate_service
from app.utils.errors import bad_request, upstream_failure

router = APIRouter(prefix="/api/translate", tags=["translate"])


class TranslateRequest(BaseModel):
    texts: list[str] = Field(max_length=100)
    target_language_code: str
    source_language_code: str = "auto"


class TranslateResponse(BaseModel):
    translated_texts: list[str]


@router.post("", response_model=TranslateResponse)
def translate(body: TranslateRequest):
    if body.target_language_code not in SUPPORTED_LANGUAGES:
        raise bad_request(f"Unsupported target language: {body.target_language_code}")
    try:
        translated = sarvam_translate_service.translate_batch(
            body.texts, body.target_language_code, body.source_language_code
        )
    except TranslationError as exc:
        raise upstream_failure("Sarvam Translate", str(exc))
    return TranslateResponse(translated_texts=translated)
