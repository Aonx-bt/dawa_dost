-- Dawa Dost core schema
-- Safety note: `diagnoses` and `symptoms` on prescriptions must only ever contain
-- text explicitly present in the source prescription. Never populate them by
-- inferring a diagnosis from a medication name.

create extension if not exists "pgcrypto";

create table if not exists users (
    id uuid primary key default gen_random_uuid(),
    name text not null,
    phone text not null unique,
    preferred_language text not null default 'hi-IN',
    created_at timestamptz not null default now()
);

create table if not exists prescriptions (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references users(id) on delete cascade,
    image_url text,
    doctor_name text,
    diagnoses jsonb not null default '[]'::jsonb,
    symptoms jsonb not null default '[]'::jsonb,
    raw_extraction jsonb,
    status text not null default 'UPLOADED'
        check (status in ('UPLOADED', 'PROCESSING', 'EXTRACTED', 'FAILED', 'CONFIRMED')),
    created_at timestamptz not null default now()
);

create table if not exists medications (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references users(id) on delete cascade,
    prescription_id uuid references prescriptions(id) on delete set null,
    name text not null,
    strength text,
    dose text,
    frequency text,
    frequency_code text,
    times jsonb not null default '[]'::jsonb,
    duration text,
    start_date date,
    end_date date,
    food_instruction text,
    special_instruction text,
    is_sos boolean not null default false,
    needs_review boolean not null default false,
    confirmed boolean not null default false,
    created_at timestamptz not null default now()
);

create table if not exists reminders (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references users(id) on delete cascade,
    medication_id uuid not null references medications(id) on delete cascade,
    scheduled_at timestamptz not null,
    status text not null default 'PENDING'
        check (status in ('PENDING', 'TRIGGERED', 'COMPLETED', 'MISSED', 'SNOOZED', 'CANCELLED')),
    call_id uuid,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists calls (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references users(id) on delete cascade,
    reminder_id uuid references reminders(id) on delete set null,
    sarvam_interaction_id text unique,
    started_at timestamptz,
    ended_at timestamptz,
    duration integer,
    transcript text,
    outcome jsonb,
    created_at timestamptz not null default now()
);

alter table reminders
    add constraint reminders_call_id_fkey
    foreign key (call_id) references calls(id) on delete set null;

create table if not exists adherence_events (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references users(id) on delete cascade,
    medication_id uuid not null references medications(id) on delete cascade,
    call_id uuid references calls(id) on delete set null,
    scheduled_at timestamptz not null,
    reported_at timestamptz not null default now(),
    status text not null check (status in ('TAKEN', 'MISSED', 'SNOOZED', 'REFUSED', 'UNKNOWN')),
    reason text,
    created_at timestamptz not null default now()
);

create table if not exists symptom_events (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references users(id) on delete cascade,
    call_id uuid references calls(id) on delete set null,
    symptom text not null,
    severity integer check (severity between 0 and 10),
    trend text check (trend in ('improving', 'worsening', 'same', 'unknown')),
    source text not null default 'PATIENT_REPORTED',
    reported_at timestamptz not null default now()
);

create table if not exists side_effect_events (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references users(id) on delete cascade,
    call_id uuid references calls(id) on delete set null,
    symptom text not null,
    severity integer check (severity between 0 and 10),
    reported_at timestamptz not null default now(),
    created_at timestamptz not null default now()
);

create index if not exists idx_medications_user on medications(user_id);
create index if not exists idx_reminders_user on reminders(user_id);
create index if not exists idx_reminders_medication on reminders(medication_id);
create index if not exists idx_reminders_status_time on reminders(status, scheduled_at);
create index if not exists idx_calls_user on calls(user_id);
create index if not exists idx_adherence_user on adherence_events(user_id);
create index if not exists idx_symptom_user on symptom_events(user_id);
create index if not exists idx_side_effect_user on side_effect_events(user_id);
