-- enable extensions
create extension if not exists vector;
create extension if not exists pg_trgm;

-- ai_skills
create table if not exists ai_skills (
  id uuid primary key default gen_random_uuid(),
  slug text not null unique,
  name text not null,
  description text not null,
  system_prompt text not null,
  rag_categories text[] not null default '{}',
  created_at timestamptz not null default now()
);

-- private_knowledge
create table if not exists private_knowledge (
  id uuid primary key default gen_random_uuid(),
  content text not null,
  content_hash text not null unique,
  embedding vector(1536),
  category text not null default 'general',
  source text,
  created_at timestamptz not null default now()
);

-- line_messages
create table if not exists line_messages (
  id uuid primary key default gen_random_uuid(),
  user_id text not null,
  message text not null,
  direction text not null check (direction in ('inbound', 'outbound')),
  skill_slug text,
  created_at timestamptz not null default now()
);

-- retrieval_logs
create table if not exists retrieval_logs (
  id uuid primary key default gen_random_uuid(),
  user_id text not null,
  query text not null,
  results jsonb not null default '[]',
  created_at timestamptz not null default now()
);

-- index
create index if not exists private_knowledge_category_idx
  on private_knowledge (category);

create index if not exists private_knowledge_trgm_idx
  on private_knowledge using gin (content gin_trgm_ops);