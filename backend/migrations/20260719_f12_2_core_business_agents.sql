-- F12.2: Core business agents

create unique index if not exists idx_agents_owner_name_unique
  on public.agents(owner_user_id, name);

insert into public.agents (owner_user_id, name, mission, is_active)
values
  (
    'system',
    'General Assistant',
    'General operational assistant for Jarvis.',
    true
  ),
  (
    'system',
    'Strategy Agent',
    'Identify the highest-value opportunities.',
    true
  ),
  (
    'system',
    'Research Agent',
    'Collect reliable information and build context.',
    true
  ),
  (
    'system',
    'Creation Agent',
    'Create production-ready content.',
    true
  ),
  (
    'system',
    'Review Agent',
    'Guarantee quality before publication.',
    true
  ),
  (
    'system',
    'Media Agent',
    'Produce media assets.',
    true
  ),
  (
    'system',
    'Publishing Agent',
    'Deliver completed work to its destination.',
    true
  ),
  (
    'system',
    'Analytics Agent',
    'Measure results and generate feedback.',
    true
  )
on conflict (owner_user_id, name) do update
set
  mission = excluded.mission,
  is_active = true;
