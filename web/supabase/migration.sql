-- Vortexia — schema leads (executar no SQL Editor do Supabase)

create table if not exists leads (
  id                uuid primary key default gen_random_uuid(),
  created_at        timestamptz not null default now(),

  nome_ou_razao     text not null,
  email             text not null,
  telefone          text,
  mensagem          text not null,
  source            text default 'landing',

  niche             text check (niche in ('lexrocha','zairyx','outro')),
  buying_intent     int  check (buying_intent between 0 and 100),
  urgency_score     int  check (urgency_score between 0 and 100),
  problem_severity  int  check (problem_severity between 0 and 100),
  intent_summary    text,
  red_flags         text[] default '{}',

  final_score       int  not null check (final_score between 0 and 100),
  score_weights     jsonb default '{"buying_intent":0.4,"urgency":0.35,"problem_severity":0.25}',

  status            text not null default 'novo'
                    check (status in ('novo','contatado','convertido','descartado')),
  telegram_sent     boolean default false,
  notas             text
);

create index if not exists leads_created_at_idx  on leads (created_at desc);
create index if not exists leads_final_score_idx on leads (final_score desc);
create index if not exists leads_status_idx      on leads (status);
create index if not exists leads_niche_idx       on leads (niche);

alter table leads enable row level security;

grant usage on schema public to anon, authenticated, service_role;
grant all on leads to service_role;
