"""Integration with the existing, externally-deployed Sarvam Voice Agent
(Samvaad), using Sarvam's documented Instant Outbound Call API:
https://docs.sarvam.ai/conversations/api/instant-outbound/create
https://docs.sarvam.ai/conversations/api/instant-outbound/webhook-payload

This module is the ONLY place that knows Samvaad's HTTP payload shape.
Everything else in the app calls trigger_call()/verify_webhook() and deals
with plain Python types.

We do not build or run the voice agent itself here - it is assumed to
already be deployed in the Sarvam dashboard (app_id/app_version/
connection_id/agent_phone_number identify it).
"""
import logging
from typing import Any

import httpx

from app.config import get_settings

logger = logging.getLogger("dawa_dost.sarvam_voice")

settings = get_settings()

VOICE_API_BASE_URL = "https://apps.sarvam.ai/api"


class VoiceCallError(Exception):
    pass


class SarvamVoiceService:
    """Thin client for triggering Samvaad instant outbound calls."""

    def _headers(self) -> dict[str, str]:
        return {
            "X-API-Key": settings.sarvam_voice_api_key,
            "Content-Type": "application/json",
        }

    def is_configured(self) -> bool:
        return bool(
            settings.sarvam_voice_api_key
            and settings.sarvam_org_id
            and settings.sarvam_workspace_id
            and settings.sarvam_app_id
            and settings.sarvam_connection_id
            and settings.sarvam_agent_phone_number
            and settings.public_backend_url
        )

    def trigger_call(self, phone: str, agent_variables: dict[str, Any], metadata: dict[str, Any]) -> str:
        """Places an instant outbound call via Sarvam Voice Agents.

        `agent_variables` are passed into the agent's conversation context
        (e.g. medication_name, dose, scheduled_time) - never the full
        patient record. `metadata` is opaque data we want echoed back on the
        webhook (e.g. reminder_id) so we can correlate the outcome.

        Returns Sarvam's `attempt_id`, used as our idempotency/correlation
        key until the webhook arrives with the final `interaction_id`.
        """
        if not self.is_configured():
            raise VoiceCallError(
                "Sarvam Voice Agents is not fully configured - missing one of "
                "SARVAM_VOICE_API_KEY / SARVAM_ORG_ID / SARVAM_WORKSPACE_ID / "
                "SARVAM_APP_ID / SARVAM_CONNECTION_ID / SARVAM_AGENT_PHONE_NUMBER / "
                "PUBLIC_BACKEND_URL."
            )

        url = (
            f"{VOICE_API_BASE_URL}/outbounds/v1/orgs/{settings.sarvam_org_id}"
            f"/workspaces/{settings.sarvam_workspace_id}/outbounds"
        )
        payload = {
            "app_config": {
                "app_id": settings.sarvam_app_id,
                "app_version": settings.sarvam_app_version,
                "connection_config": {
                    "connection_id": settings.sarvam_connection_id,
                    "agent_phone_number": settings.sarvam_agent_phone_number,
                },
                "agent_variables": agent_variables,
            },
            "user_config": {"user_phone_number": phone},
            "webhook_config": {
                "url": f"{settings.public_backend_url}/api/webhooks/sarvam?token={settings.sarvam_webhook_secret}",
                "metadata": metadata,
            },
        }

        try:
            with httpx.Client(timeout=15.0) as client:
                resp = client.post(url, json=payload, headers=self._headers())
            resp.raise_for_status()
            data = resp.json()
        except httpx.HTTPStatusError as exc:
            raise VoiceCallError(f"Samvaad rejected the call request: {exc.response.text}") from exc
        except httpx.HTTPError as exc:
            raise VoiceCallError(f"Could not reach Samvaad: {exc}") from exc

        attempt_id = data.get("attempt_id")
        if not attempt_id:
            raise VoiceCallError("Samvaad did not return an attempt_id.")
        return attempt_id

    def verify_webhook(self, provided_token: str | None) -> bool:
        """Sarvam's webhook has no documented signature scheme, so we embed
        our own shared-secret token in the webhook URL's query string
        (see trigger_call) and check it here."""
        if not settings.sarvam_webhook_secret:
            logger.warning("SARVAM_WEBHOOK_SECRET not set; accepting webhook unverified.")
            return True
        return provided_token == settings.sarvam_webhook_secret


sarvam_voice_service = SarvamVoiceService()
