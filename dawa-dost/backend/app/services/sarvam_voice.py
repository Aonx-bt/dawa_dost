"""Integration with the existing, externally-deployed Sarvam Samvaad voice agent.

This module is the ONLY place that knows Samvaad's HTTP payload shape.
Everything else in the app calls trigger_call()/get_call_context() and deals
with plain Python types.

We do not build or run the voice agent itself here - it is assumed to already
be deployed and configured (SARVAM_AGENT_ID / SARVAM_DEPLOYMENT_ID) to call
back into this backend's /api/voice/* and /api/webhooks/sarvam endpoints.
"""
import logging
from typing import Any

import httpx

from app.config import get_settings

logger = logging.getLogger("dawa_dost.sarvam_voice")

settings = get_settings()

SAMVAAD_BASE_URL = "https://api.sarvam.ai"


class VoiceCallError(Exception):
    pass


class SarvamVoiceService:
    """Thin client for triggering and inspecting Samvaad voice calls."""

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {settings.sarvam_api_key}",
            "Content-Type": "application/json",
        }

    def is_configured(self) -> bool:
        return bool(
            settings.sarvam_api_key and settings.sarvam_agent_id and settings.sarvam_deployment_id
        )

    def trigger_call(self, phone: str, context: dict[str, Any]) -> str:
        """Ask Samvaad to place an outbound call. Returns Sarvam's interaction id.

        `context` should be the minimal payload described in the product spec
        (reminder_id, medication_id, medication_name, dose, food_instruction,
        scheduled_time) - never the full patient record.
        """
        if not self.is_configured():
            raise VoiceCallError(
                "Sarvam Samvaad is not configured (missing SARVAM_API_KEY / "
                "SARVAM_AGENT_ID / SARVAM_DEPLOYMENT_ID)."
            )

        payload = {
            "agent_id": settings.sarvam_agent_id,
            "deployment_id": settings.sarvam_deployment_id,
            "to_number": phone,
            "context": context,
        }
        try:
            with httpx.Client(timeout=15.0) as client:
                resp = client.post(
                    f"{SAMVAAD_BASE_URL}/samvaad/calls",
                    json=payload,
                    headers=self._headers(),
                )
            resp.raise_for_status()
            data = resp.json()
        except httpx.HTTPStatusError as exc:
            raise VoiceCallError(f"Samvaad rejected the call request: {exc.response.text}") from exc
        except httpx.HTTPError as exc:
            raise VoiceCallError(f"Could not reach Samvaad: {exc}") from exc

        interaction_id = data.get("interaction_id") or data.get("call_id") or data.get("id")
        if not interaction_id:
            raise VoiceCallError("Samvaad did not return an interaction id.")
        return interaction_id

    def get_call_context(self, interaction_id: str) -> dict[str, Any]:
        """Look up a call's status from Sarvam (used for polling/debugging)."""
        if not self.is_configured():
            raise VoiceCallError("Sarvam Samvaad is not configured.")
        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.get(
                    f"{SAMVAAD_BASE_URL}/samvaad/calls/{interaction_id}",
                    headers=self._headers(),
                )
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError as exc:
            raise VoiceCallError(f"Could not fetch call context: {exc}") from exc

    def verify_webhook(self, provided_secret: str | None) -> bool:
        """Validate an inbound webhook using the shared secret.

        Samvaad is expected to send the configured SARVAM_WEBHOOK_SECRET back
        (e.g. as a header or query param) so we can reject spoofed calls.
        """
        if not settings.sarvam_webhook_secret:
            # No secret configured (local/demo) - allow through but log loudly.
            logger.warning("SARVAM_WEBHOOK_SECRET not set; accepting webhook unverified.")
            return True
        return provided_secret == settings.sarvam_webhook_secret


sarvam_voice_service = SarvamVoiceService()
