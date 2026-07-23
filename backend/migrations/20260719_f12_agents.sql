-- F12: Agents persistent entity (Supabase/PostgreSQL)

create table if not exists public.agents (
  id uuid primary key default gen_random_uuid(),
  owner_user_id text not null,
  name text not null,
  mission text not null,
  is_active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists idx_agents_owner_user_id on public.agents(owner_user_id);
create index if not exists idx_agents_is_active on public.agents(is_active);

create or replace function public.set_agents_updated_at()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

drop trigger if exists trg_agents_updated_at on public.agents;
create trigger trg_agents_updated_at
before update on public.agents
for each row execute function public.set_agents_updated_at();
