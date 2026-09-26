# Dawa Dost

Dawa Dost ("medicine friend") is a medication-adherence companion that stays
with a patient after they receive a prescription: it reads the prescription,
builds a reminder schedule, calls the patient at dose time through an
existing Sarvam Samvaad voice agent, and tracks adherence, symptoms and side
effects on a patient-facing dashboard.

Dawa Dost is **not** a diagnostic or prescribing system. It never infers a
diagnosis, changes a dose, or recommends a medication change - see
[Safety rules](#safety-rules).

## 1. What it does

```
Prescription → AI extraction → Patient confirmation → Medication schedule
  → Voice reminder call → Patient response → Adherence + symptom tracking
  → Patient dashboard
```

1. Patient uploads a photo/PDF of a prescription.
2. Sarvam Document AI (`doc_ai.extract`) extracts medicines, strength, dose,
   frequency, duration, food instructions and any diagnoses/symptoms that
   are **explicitly written** on the prescription.
3. Patient reviews the extraction and confirms it (ambiguous frequencies like
   `BD`/`TDS`/`SOS` are flagged, never guessed).
4. The backend turns confirmed medications into a reminder schedule.
5. At the scheduled time, APScheduler triggers the existing Sarvam Samvaad
   voice agent, which calls the patient.
6. The patient tells the agent whether they took the dose, wants a snooze,
   or wants to report a symptom/side effect.
7. Samvaad posts a structured outcome back to `/api/webhooks/sarvam`.
8. The dashboard updates: adherence %, today's doses, symptom trend, call
   history.

## 2. Architecture

```
Patient
  ├─ Next.js web app  ──────────────┐
  └─ Phone (Sarvam Samvaad call)    │
                                     ▼
                          FastAPI backend
                  (business logic, scheduling,
                    voice orchestration)
                    │        │         │
                    ▼        ▼         ▼
             Supabase   Sarvam    APScheduler
             Postgres   Document       │
                │        AI            ▼
                │                Sarvam Samvaad ──▶ Phone call
                │                      │
                │                      ▼
                │              Structured outcome
                │                      │
                └──────────────────────┴──▶ /api/webhooks/sarvam
```

## 3. Tech stack

- **Frontend**: Next.js (App Router) + TypeScript + Tailwind CSS, mobile-first
- **Backend**: Python + FastAPI + Pydantic + SQLAlchemy
- **Database**: Supabase Postgres in production; local SQLite by default for
  the hackathon (same SQLAlchemy models, just point `DATABASE_URL` at
  Postgres to switch)
- **Scheduling**: APScheduler, running in-process inside FastAPI
- **AI**: Sarvam Document AI for prescription extraction, existing Sarvam
  Samvaad agent for calls (not rebuilt here - treated as an external service)

## 4. Project structure

```
dawa-dost/
├── frontend/           Next.js app (pages under app/, shared UI in components/)
├── backend/
│   └── app/
│       ├── main.py         FastAPI app, startup/shutdown, router registration
│       ├── config.py       Settings from environment variables
│       ├── database.py     SQLAlchemy engine/session
│       ├── models/         SQLAlchemy models (mirrors supabase/migrations)
│       ├── schemas/        Pydantic request/response schemas
│       ├── routers/        prescriptions, medications, voice, webhooks, dashboard, calls, demo
│       ├── services/
│       │   ├── sarvam_vision.py       Prescription extraction (Sarvam Document AI)
│       │   ├── sarvam_voice.py        Samvaad call trigger/context/webhook verification
│       │   ├── scheduler.py           ReminderScheduler (APScheduler wrapper)
│       │   ├── prescription_parser.py Deterministic frequency → clock-time parsing
│       │   └── medication_service.py  Confirmed medication → medication + reminders
│       └── seed.py         Demo patient + seed data
├── supabase/migrations/    SQL schema for Supabase Postgres
├── .env.example
└── docker-compose.yml
```

## 5. Install & run locally

### Backend

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate   # optional but recommended
pip install -r requirements.txt
cp ../.env.example .env   # fill in SARVAM_API_KEY at minimum
python3 -m uvicorn app.main:app --reload --port 8000
```

The API is now at `http://localhost:8000`, with interactive docs at
`http://localhost:8000/docs`. On first startup it creates the SQLite schema
and (when `DEMO_MODE=true`) seeds a demo patient (Rina Sharma) with sample
medications, calls and symptom history so the dashboard isn't empty.

### Frontend

```bash
cd frontend
npm install
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
npm run dev
```

Open `http://localhost:3000`.

## 6. Environment variables

See `.env.example` at the repo root.

```env
# Database
DATABASE_URL=sqlite:///./dawa_dost.db     # or postgresql://... for Supabase
SUPABASE_URL=
SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=

# Sarvam - Document AI (prescription extraction) & Text Translate
SARVAM_API_KEY=

# Sarvam Voice Agents (Samvaad) - separate API key, created at
# https://indus.sarvam.ai/samvaad/settings/api-key
SARVAM_VOICE_API_KEY=
SARVAM_ORG_ID=
SARVAM_WORKSPACE_ID=
SARVAM_APP_ID=              # the deployed voice agent's app id
SARVAM_APP_VERSION=1
SARVAM_CONNECTION_ID=       # telephony connection ("deployment id")
SARVAM_AGENT_PHONE_NUMBER=  # number the agent calls FROM
SARVAM_WEBHOOK_SECRET=      # our own shared secret, appended to the webhook URL
PUBLIC_BACKEND_URL=         # publicly reachable URL for THIS backend

# Application
NEXT_PUBLIC_API_URL=http://localhost:8000
DEMO_MODE=true
CORS_ORIGINS=http://localhost:3000
```

Sarvam credentials are read server-side only (`app/config.py`) and are never
sent to the frontend. `SARVAM_API_KEY` alone is enough to test prescription
extraction and translation. Placing real Voice Agent calls additionally
needs every `SARVAM_*`/`PUBLIC_BACKEND_URL` variable above filled in (see
Demo Mode below for a fallback when they aren't).

`PUBLIC_BACKEND_URL` matters because Sarvam calls your webhook from its own
servers - `http://localhost:8000` is not reachable from there. For local
development, expose your backend with a tunnel (e.g. `ngrok http 8000`) and
set `PUBLIC_BACKEND_URL` to the `https://...ngrok...` URL it gives you; in
production, use your Railway/Render URL.

## 7. Supabase setup (for real deployment)

1. Create a Supabase project.
2. Run `supabase/migrations/0001_init.sql` against it (via the SQL editor or
   `supabase db push`).
3. Create a storage bucket for prescription images if you want to move
   uploads off local disk (the hackathon build stores uploads under
   `backend/uploads/` and serves them at `/uploads/...`).
4. Set `DATABASE_URL` to the Postgres connection string, and
   `SUPABASE_URL`/`SUPABASE_ANON_KEY`/`SUPABASE_SERVICE_ROLE_KEY` if you wire
   up Supabase Auth for real login (the MVP uses a single seeded demo
   patient - see `app/utils/current_user.py`).

## 8. Sarvam setup

For what the voice agent actually does on a call - the conversation itself,
not just the API wiring - see [`docs/SAMVAAD_VOICE_AGENT.md`](docs/SAMVAAD_VOICE_AGENT.md).

- **Document AI / Translate**: only needs `SARVAM_API_KEY`. See
  `app/services/sarvam_vision.py` (calls `doc_ai.extract()`, polls
  `get_status()`, reads `get_results()`) and `app/services/sarvam_translate.py`
  (`text.translate()`).

- **Voice Agents (Samvaad)**: uses Sarvam's documented Instant Outbound Call
  API (https://docs.sarvam.ai/conversations/api/instant-outbound/create):
  - Backend → Samvaad: `SarvamVoiceService.trigger_call()` posts to
    `POST https://apps.sarvam.ai/api/outbounds/v1/orgs/{org_id}/workspaces/{workspace_id}/outbounds`
    with `X-API-Key: SARVAM_VOICE_API_KEY`, the agent's `app_id`/`app_version`/
    `connection_id`/`agent_phone_number`, a minimal `agent_variables` object
    (`patient_name`, `medication_name`, `dose`, `food_instruction`,
    `scheduled_time`), and a `webhook_config.metadata` carrying our
    `reminder_id` so we can correlate the later webhook back to this
    reminder. Returns an `attempt_id`.
  - Samvaad → Backend (tool calls during the call, if your agent is
    configured to use them):
    `POST /api/voice/context`, `POST /api/voice/medication/taken`,
    `POST /api/voice/medication/snooze`, `POST /api/voice/symptom`,
    `POST /api/voice/side-effect`.
  - Samvaad → Backend (after the call ends):
    `POST /api/webhooks/sarvam?token=SARVAM_WEBHOOK_SECRET` with Sarvam's
    documented webhook payload (`attempt_id`, `status`, `duration`,
    `interaction_id`, `final_agent_variables`, `interaction_transcript`,
    `webhook_config`). See `SarvamWebhookPayload` in
    `app/schemas/schemas.py` - it also derives our internal
    `StructuredCallOutcome` from `final_agent_variables`, so **your Samvaad
    agent must be configured to set these variable names** during the
    conversation: `medication_taken`, `snooze_requested`, `snooze_minutes`,
    `symptom_reported`, `symptom_name`, `symptom_severity`, `symptom_trend`,
    `side_effect_reported`, `side_effect_name`, `side_effect_severity`.
  - Sarvam has no documented webhook signature scheme, so we verify
    inbound webhooks via our own `?token=SARVAM_WEBHOOK_SECRET` query
    parameter, which we append ourselves when building the
    `webhook_config.url` at call-trigger time.

## 9. How the scheduler works

`app/services/scheduler.py` wraps an APScheduler `BackgroundScheduler`
running inside the FastAPI process:

- `schedule_reminder(reminder_id, when)` adds/replaces a `DateTrigger` job.
- `cancel_reminder(reminder_id)` removes the job and marks the reminder
  `CANCELLED`.
- `snooze_reminder(reminder_id, minutes)` reschedules the job and marks the
  reminder `SNOOZED`.
- `process_due_reminders()` is a fallback sweep (run once at startup) that
  fires any reminder whose time has already passed - covers the case where
  the process restarted and missed its APScheduler job.

When a reminder fires, the scheduler calls `SarvamVoiceService.trigger_call()`
with a minimal context payload and marks the reminder `TRIGGERED`.

This is intentionally a thin, swappable abstraction - a production
deployment can replace the in-process APScheduler with a durable
cron/queue without touching any caller.

## 10. How the Samvaad webhook works

`POST /api/webhooks/sarvam` (`app/routers/webhooks.py`):

1. Verifies the webhook (shared-secret header, when `SARVAM_WEBHOOK_SECRET`
   is set).
2. Looks up the call by `interaction_id`. If it already exists, returns
   `{"status": "ok", "duplicate": true}` **without** creating any new rows -
   this makes retried webhook deliveries idempotent.
3. Otherwise creates a `calls` row, links it to the reminder, and applies the
   structured outcome: creates an `adherence_events` row (`TAKEN` /
   `SNOOZED` / `REFUSED` / `UNKNOWN`), updates the reminder status, and
   optionally creates `symptom_events` / `side_effect_events` rows.

Demo Mode's `/api/demo/simulate-outcome` calls the exact same processing
function, so a simulated call and a real Samvaad webhook are handled
identically.

## 11. Demo Mode

For judging without a live phone call:

1. Upload a prescription → extract → confirm (creates real reminders).
2. On the dashboard, **"Talk to Dawa Dost"** tries a real Samvaad call first
   (if the `SARVAM_VOICE_API_KEY`/`SARVAM_APP_ID`/etc. variables are configured); if that
   fails or isn't configured, it falls back to
   `POST /api/demo/simulate-outcome`, which fabricates a completed-call
   webhook and runs it through the real processing path.
3. Individual reminders can also be marked taken from the medication detail
   page ("Mark taken (demo)").

The seeded demo patient (Rina Sharma, Hindi) ships with a populated
dashboard out of the box (`app/seed.py`).

## 12. Running tests

```bash
cd backend
python3 -m pytest -q
```

Covers: frequency parsing (`1-0-1`, `1-1-1`, textual forms, SOS/PRN/BD/TDS
ambiguity), the reminder scheduler (schedule/cancel/snooze/process-due),
adherence event creation, webhook idempotency/malformed-payload handling,
and the safety rules (no diagnosis inference, no guessed ambiguous
frequencies).

## 13. Deployment

- **Frontend → Vercel**: `vercel deploy` from `frontend/`, with
  `NEXT_PUBLIC_API_URL` set to your deployed backend URL.
- **Backend → Railway/Render**: deploy `backend/` with start command
  `uvicorn app.main:app --host 0.0.0.0 --port $PORT`, and set `DATABASE_URL`
  to your Supabase Postgres connection string plus the Sarvam env vars.
- Run `supabase/migrations/0001_init.sql` against your Supabase project
  before first deploy.

## Safety rules

Enforced throughout the codebase, not just documented:

1. Diagnoses/symptoms on a prescription are only ever the text explicitly
   extracted from the document (`app/services/sarvam_vision.py`,
   `app/schemas/schemas.py`) - never inferred from a medicine name.
2. Extraction alone never activates a medication schedule - only
   `POST /api/prescriptions/{id}/confirm`, an explicit patient action, does
   (`app/routers/prescriptions.py`).
3. Ambiguous frequency notation (`SOS`, `PRN`, `BD`, `TDS`, `QDS`, `STAT`, or
   anything unrecognised) is flagged `needs_review` and never auto-scheduled
   (`app/services/prescription_parser.py`).
4. `SOS`/`PRN` medications never get a fixed recurring reminder.
5. The backend never modifies dosage, substitutes medications, or stops a
   medication automatically.
6. Serious side effects (severity ≥ 7) are flagged for medical attention
   (`flagged_for_medical_attention` in `POST /api/voice/side-effect`)
   rather than diagnosed.
7. Symptom trends are always labelled "Patient-reported" in the UI, never
   presented as a diagnosis or medical conclusion.
