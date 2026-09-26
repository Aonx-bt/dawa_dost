"use client";

import { useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";
import { useLanguage } from "@/lib/LanguageContext";

// Simple in-memory cache so navigating back to a page (or re-rendering)
// doesn't re-call Sarvam Translate for text we've already translated.
const cache = new Map<string, string>();

function cacheKey(text: string, lang: string) {
  return `${lang}::${text}`;
}

/**
 * Translates a list of short strings (medicine names, instructions,
 * diagnoses, etc.) into the patient's selected language via Sarvam
 * Translate. Falls back to the original text while loading or on the
 * server's default language (en-IN), and on any translation failure.
 */
export function useTranslatedTexts(texts: string[]): { translated: string[]; loading: boolean } {
  const { language } = useLanguage();
  const [translated, setTranslated] = useState<string[]>(texts);
  const [loading, setLoading] = useState(false);
  const requestId = useRef(0);

  useEffect(() => {
    // English is the extraction/API's baseline language for most content;
    // still translate when needed, but skip the round trip if there's
    // nothing to translate.
    const meaningful = texts.filter((t) => t && t.trim());
    if (meaningful.length === 0) {
      setTranslated(texts);
      return;
    }

    const uncached = texts.filter((t) => t && t.trim() && !cache.has(cacheKey(t, language)));

    if (uncached.length === 0) {
      setTranslated(texts.map((t) => (t && cache.has(cacheKey(t, language)) ? cache.get(cacheKey(t, language))! : t)));
      return;
    }

    const currentRequest = ++requestId.current;
    setLoading(true);

    api
      .translate(uncached, language)
      .then((res) => {
        if (requestId.current !== currentRequest) return;
        uncached.forEach((original, i) => {
          cache.set(cacheKey(original, language), res.translated_texts[i] ?? original);
        });
        setTranslated(
          texts.map((t) => (t && cache.has(cacheKey(t, language)) ? cache.get(cacheKey(t, language))! : t)),
        );
      })
      .catch(() => {
        if (requestId.current !== currentRequest) return;
        setTranslated(texts); // fall back to originals on failure
      })
      .finally(() => {
        if (requestId.current === currentRequest) setLoading(false);
      });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [JSON.stringify(texts), language]);

  return { translated, loading };
}
