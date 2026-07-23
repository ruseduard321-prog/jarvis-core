-- F12.3: Stable slug for agents

alter table if exists public.agents
  add column if not exists slug text;

update public.agents
set slug = case
  when owner_user_id = 'system' and name = 'General Assistant' then 'general'
  when owner_user_id = 'system' and name = 'Strategy Agent' then 'strategy'
  when owner_user_id = 'system' and name = 'Research Agent' then 'research'
  when owner_user_id = 'system' and name = 'Creation Agent' then 'creation'
  when owner_user_id = 'system' and name = 'Review Agent' then 'review'
  when owner_user_id = 'system' and name = 'Media Agent' then 'media'
  when owner_user_id = 'system' and name = 'Publishing Agent' then 'publishing'
  when owner_user_id = 'system' and name = 'Analytics Agent' then 'analytics'
  else slug
end
where slug is null;

update public.agents
set slug = lower(regexp_replace(name, '[^a-z0-9]+', '-', 'g')) || '-' || substr(id::text, 1, 8)
where slug is null;

alter table if exists public.agents
  alter column slug set not null;

create unique index if not exists idx_agents_slug_unique
  on public.agents(slug);
