"""Deterministic parsing of prescription frequency notation into clock times.

Safety rule: only patterns with an unambiguous, well-defined mapping are
auto-parsed. Anything else (SOS, PRN, BD, TDS, or unrecognised text) is
flagged for the patient to confirm/edit rather than guessed.
"""
import re
from dataclasses import dataclass

# 1-0-1 style slots map to fixed clock times used across the app.
MORNING = "08:00"
AFTERNOON = "14:00"
EVENING = "20:00"

_DASH_PATTERN = re.compile(r"^\s*(\d)\s*-\s*(\d)\s*-\s*(\d)\s*$")

_TEXTUAL_MAP = {
    "once daily": [MORNING],
    "once a day": [MORNING],
    "od": [MORNING],
    "twice daily": [MORNING, EVENING],
    "twice a day": [MORNING, EVENING],
    "three times daily": [MORNING, AFTERNOON, EVENING],
    "thrice daily": [MORNING, AFTERNOON, EVENING],
    "morning": [MORNING],
    "afternoon": [AFTERNOON],
    "evening": [EVENING],
    "night": [EVENING],
    "at night": [EVENING],
    "bedtime": [EVENING],
}

# Explicitly ambiguous shorthand. These must NEVER be auto-interpreted.
AMBIGUOUS_TERMS = {"sos", "prn", "bd", "tds", "qds", "stat"}


@dataclass
class ParsedFrequency:
    times: list[str]
    is_sos: bool
    needs_review: bool
    frequency_code: str | None


def parse_frequency(raw_frequency: str | None) -> ParsedFrequency:
    """Parse a frequency string into concrete reminder times.

    Returns needs_review=True whenever the instruction is ambiguous or
    unrecognised — callers must surface this to the patient instead of
    silently creating a schedule.
    """
    if not raw_frequency or not raw_frequency.strip():
        return ParsedFrequency(times=[], is_sos=False, needs_review=True, frequency_code=None)

    text = raw_frequency.strip().lower()

    # SOS / PRN: no fixed recurring schedule, patient-triggered only.
    if any(term in text.split() or term == text for term in AMBIGUOUS_TERMS):
        if text in ("sos", "prn"):
            return ParsedFrequency(times=[], is_sos=True, needs_review=False, frequency_code=text)
        # BD/TDS/QDS/STAT are genuinely ambiguous (could mean different clock
        # times in different clinics) — require explicit confirmation.
        return ParsedFrequency(times=[], is_sos=False, needs_review=True, frequency_code=text)

    dash_match = _DASH_PATTERN.match(text)
    if dash_match:
        slots = [MORNING, AFTERNOON, EVENING]
        times = [slot for slot, taken in zip(slots, dash_match.groups()) if taken != "0"]
        if not times:
            return ParsedFrequency(times=[], is_sos=False, needs_review=True, frequency_code=text)
        return ParsedFrequency(times=times, is_sos=False, needs_review=False, frequency_code=text)

    if text in _TEXTUAL_MAP:
        return ParsedFrequency(
            times=list(_TEXTUAL_MAP[text]), is_sos=False, needs_review=False, frequency_code=text
        )

    # Unknown / free-text instruction — never guess.
    return ParsedFrequency(times=[], is_sos=False, needs_review=True, frequency_code=text)
