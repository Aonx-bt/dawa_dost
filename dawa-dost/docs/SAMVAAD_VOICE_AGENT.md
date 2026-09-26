# The Samvaad Voice Agent

Dawa Dost's medication reminders aren't push notifications — they're phone
calls. At the scheduled dose time, a Sarvam Samvaad voice agent calls the
patient directly, speaks to them in their own language, and has a real
conversation: did they take the medicine, do they need more time, and how
are they actually feeling.

This is the part of the app that makes it a *companion* rather than an
alarm clock — someone (something) actually checks in.

## What the agent does on every call

1. **Reminds** the patient which medicine, what dose, and any food
   instruction ("after food," "on an empty stomach"), for the exact dose
   that's due right now.
2. **Asks** whether they've taken it.
3. **Responds to what the patient says**, not a fixed script:
   - *"Yes, I took it"* → marks the dose as taken.
   - *"Not yet, give me a bit"* → offers to call back later and snoozes the
     reminder for however long the patient asks for.
   - *"I stopped taking it"* / refusal → recorded, never argued with or
     overridden.
4. **Checks up on the patient**, not just the pill — asks how a
   previously-reported symptom is doing ("that fever from yesterday, is it
   better today?") and listens for any new side effects.
5. **Ends the call** and reports back what happened.

## Example conversation

```
Agent:   Namaste Rina ji, main Dawa Dost bol raha hoon. Aapki Crocin ki
         evening dose ka time ho gaya hai. Kya aapne medicine le li?
Patient: Nahi, main abhi dinner kar rahi hoon.
Agent:   Theek hai. Kya main aapko 30 minute baad yaad dila doon?
Patient: Haan.
Agent:   Aapko jo fever tha, woh kal ke comparison mein kaisa hai?
Patient: Thoda kam hai.
Agent:   Accha laga sunkar. Main aapko 30 minute baad call karta hoon.
```

From this one call, Dawa Dost records: a snooze request (with a new
reminder time), and a symptom update — fever, improving, patient-reported
— without a single tap from the patient.

## Why a phone call, not an app notification

The people this is built for are often mid-illness, may not be fluent
readers, and are far more likely to *answer a phone* than to open an app
and tap through a checklist. A conversation also catches things a
notification can't: *why* someone hasn't taken their dose, whether a
symptom is getting better or worse, whether something new and worrying has
shown up. A "mark as taken" button can't ask a follow-up question.

## What Dawa Dost never asks the agent to do

The agent's job is to gather information and carry out the patient's own
stated wishes (snooze, mark taken) — never to make a medical judgment call.
It does not, and Dawa Dost's backend would ignore it if it tried to:

- diagnose a symptom or condition,
- decide a dose is wrong or should change,
- tell the patient to stop, start, or substitute a medication,
- talk the patient out of what they've reported.

If a patient mentions something serious (a severe side effect, worsening
symptoms), the agent flags it for the patient to bring to a real doctor —
it doesn't try to handle it itself. See the main [README](../README.md#20-safety)
for the full list of safety rules this enforces end-to-end.

## How a call becomes structured data

The agent doesn't just produce a transcript for someone to read later. At
the end of the call it sets a handful of named variables (e.g.
`medication_taken`, `snooze_requested`, `symptom_name`,
`symptom_severity`, `symptom_trend`), and those are what Dawa Dost's
backend actually acts on — creating an adherence record, rescheduling a
reminder, logging a symptom trend. The full transcript is kept too, but
purely as an audit trail; the app's state never depends on parsing free
text. See [`README.md`](../README.md#8-sarvam-setup) for exactly which
variable names the agent needs to set and how the backend wires up to it.

## Where this stands right now

Placing an actual outbound phone call requires a phone number connected
through Sarvam (via their own rental or a provider like Twilio), which is
a paid step. For this build, the same agent and the same conversation are
instead reachable through Sarvam's no-code browser widget on the
dashboard's **"Talk to Dawa Dost"** button — a live voice call over the
browser, no telephony required. The moment a phone connection is added,
the exact same agent starts placing real scheduled calls with zero code
changes on the app side; the integration point (webhook → adherence/
symptom updates) is identical either way.
