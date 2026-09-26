"use client";

import Script from "next/script";
import { useEffect, useRef } from "react";

/**
 * Embeds Sarvam's no-code voice-agent widget (sarvam-convai-embed) directly
 * in the browser - a WebSocket-based voice/chat call to the deployed Samvaad
 * agent, with no phone number or telephony connection required.
 *
 * The widget's api-key is intentionally public/client-side (Sarvam's
 * documented embed pattern) - keep it a separate, narrowly-scoped key from
 * the backend's SARVAM_VOICE_API_KEY used for outbound phone calls.
 */
export function VoiceWidget({
  userId,
  buttonText = "Talk to Dawa Dost",
}: {
  userId: string;
  buttonText?: string;
}) {
  const containerRef = useRef<HTMLDivElement>(null);

  const apiKey = process.env.NEXT_PUBLIC_SARVAM_WIDGET_API_KEY;
  const appId = process.env.NEXT_PUBLIC_SARVAM_APP_ID;
  const orgId = process.env.NEXT_PUBLIC_SARVAM_ORG_ID;
  const workspaceId = process.env.NEXT_PUBLIC_SARVAM_WORKSPACE_ID;

  const configured = Boolean(apiKey && appId && orgId && workspaceId);

  useEffect(() => {
    if (!configured || !containerRef.current) return;
    const container = containerRef.current;
    container.innerHTML = "";

    // Built imperatively (rather than as JSX) since <sarvam-widget> is a
    // third-party custom element with no TypeScript/JSX typings.
    const widget = document.createElement("sarvam-widget");
    widget.setAttribute("api-key", apiKey!);
    widget.setAttribute("app-id", appId!);
    widget.setAttribute("org-id", orgId!);
    widget.setAttribute("workspace-id", workspaceId!);
    widget.setAttribute("user-id", userId);
    widget.setAttribute("button-text", buttonText);
    widget.setAttribute("interaction-type", "call");
    widget.setAttribute("background-color", "#ffffff");
    widget.setAttribute("foreground-color", "#0f766e1a");
    widget.setAttribute("accent-color", "#0d9488");
    container.appendChild(widget);
  }, [configured, apiKey, appId, orgId, workspaceId, userId, buttonText]);

  if (!configured) return null;

  return (
    <>
      <Script src="https://unpkg.com/sarvam-convai-embed" strategy="afterInteractive" />
      <div ref={containerRef} />
    </>
  );
}
