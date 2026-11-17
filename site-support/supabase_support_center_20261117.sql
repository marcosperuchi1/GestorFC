
-- FutBR Manager support/feedback backend, 17 Nov 2026.
-- End-user access exclusively under RLS; staff membership is server-managed.
create table if not exists public.support_staff (
  user_id uuid primary key references auth.users(id) on delete cascade,
  role text not null default 'agent' check (role in ('agent','admin')),
  created_at timestamptz not null default now()
);

create table if not exists public.support_tickets (
  id uuid primary key default gen_random_uuid(),
  ticket_no bigint generated always as identity unique,
  user_id uuid not null references auth.users(id) on delete cascade,
  contact_email text not null default '',
  category text not null check (category in ('bug','feedback','question','billing','other')),
  platform text not null default 'windows' check (platform in ('windows','android','website','other')),
  game_version text not null default '' check (char_length(game_version) <= 50),
  subject text not null check (char_length(btrim(subject)) between 6 and 120),
  description text not null check (char_length(btrim(description)) between 15 and 5000),
  status text not null default 'open' check (status in ('open','in_progress','waiting_user','resolved','closed')),
  priority text not null default 'normal' check (priority in ('normal','high')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  last_activity_at timestamptz not null default now()
);

create table if not exists public.support_messages (
  id uuid primary key default gen_random_uuid(),
  ticket_id uuid not null references public.support_tickets(id) on delete cascade,
  author_id uuid not null references auth.users(id) on delete cascade,
  body text not null check (char_length(btrim(body)) between 2 and 4000),
  is_staff boolean not null default false,
  created_at timestamptz not null default now()
);

create index if not exists support_tickets_owner_activity_idx on public.support_tickets(user_id,last_activity_at desc);
create index if not exists support_tickets_status_activity_idx on public.support_tickets(status,last_activity_at desc);
create index if not exists support_messages_ticket_created_idx on public.support_messages(ticket_id,created_at);

alter table public.support_staff enable row level security;
alter table public.support_tickets enable row level security;
alter table public.support_messages enable row level security;

revoke all on public.support_staff from anon,authenticated;
revoke all on public.support_tickets from anon,authenticated;
revoke all on public.support_messages from anon,authenticated;

grant select on public.support_staff to authenticated;
grant select,insert,update on public.support_tickets to authenticated;
grant select,insert on public.support_messages to authenticated;

create policy support_staff_self_read
 on public.support_staff for select to authenticated
 using (user_id = (select auth.uid()));

create policy support_tickets_owner_or_team_read
 on public.support_tickets for select to authenticated
 using (
   user_id = (select auth.uid())
   or exists(select 1 from public.support_staff s where s.user_id = (select auth.uid()))
 );

create policy support_tickets_create_own
 on public.support_tickets for insert to authenticated
 with check (
    user_id = (select auth.uid())
    and status = 'open'
    and priority = 'normal'
 );

create policy support_tickets_team_manage
 on public.support_tickets for update to authenticated
 using (exists(select 1 from public.support_staff s where s.user_id = (select auth.uid())))
 with check (exists(select 1 from public.support_staff s where s.user_id = (select auth.uid())));

create policy support_messages_ticket_access
 on public.support_messages for select to authenticated
 using (
   exists(
     select 1 from public.support_tickets t
      where t.id = ticket_id
        and (
          t.user_id = (select auth.uid())
          or exists(select 1 from public.support_staff s where s.user_id = (select auth.uid()))
        )
   )
 );

create policy support_messages_author_insert
 on public.support_messages for insert to authenticated
 with check (
   author_id = (select auth.uid())
   and exists(
     select 1 from public.support_tickets t
      where t.id = ticket_id
        and t.status <> 'closed'
        and (
          t.user_id = (select auth.uid())
          or exists(select 1 from public.support_staff s where s.user_id = (select auth.uid()))
        )
   )
 );

-- Derive ownership/email/status on the server, even if an attacker posts raw REST data.
create or replace function public.support_prepare_ticket()
 returns trigger language plpgsql security definer
 set search_path = '' as $$
declare actor uuid;
begin
  actor := (select auth.uid());
  if actor is null then raise exception 'Autenticacao obrigatoria'; end if;
  if exists (
     select 1 from public.support_tickets
     where user_id=actor and created_at > now() - interval '60 seconds'
  ) then
     raise exception 'Aguarde 1 minuto antes de abrir outro chamado';
  end if;
  new.user_id := actor;
  select u.email into new.contact_email from auth.users u where u.id=actor;
  if new.contact_email is null then raise exception 'Conta nao encontrada'; end if;
  new.status := 'open';
  new.priority := 'normal';
  new.created_at := now();
  new.updated_at := now();
  new.last_activity_at := now();
  return new;
end $$;

create or replace function public.support_prepare_ticket_update()
 returns trigger language plpgsql
 set search_path = '' as $$
begin
  new.id := old.id;
  new.user_id := old.user_id;
  new.ticket_no := old.ticket_no;
  new.contact_email := old.contact_email;
  new.created_at := old.created_at;
  new.updated_at := now();
  return new;
end $$;

create or replace function public.support_prepare_message()
 returns trigger language plpgsql security definer
 set search_path = '' as $$
declare actor uuid;
begin
  actor := (select auth.uid());
  if actor is null then raise exception 'Autenticacao obrigatoria'; end if;
  new.author_id := actor;
  new.is_staff := exists(select 1 from public.support_staff s where s.user_id=actor);
  new.created_at := now();
  return new;
end $$;

create or replace function public.support_touch_ticket()
 returns trigger language plpgsql security definer
 set search_path = '' as $$
begin
  update public.support_tickets
  set last_activity_at=now(),
      status=case
        when new.is_staff and status='open' then 'in_progress'
        when not new.is_staff and status in ('resolved','waiting_user') then 'open'
        else status
      end
  where id=new.ticket_id;
  return null;
end $$;

revoke all on function public.support_prepare_ticket() from public,anon,authenticated;
revoke all on function public.support_prepare_ticket_update() from public,anon,authenticated;
revoke all on function public.support_prepare_message() from public,anon,authenticated;
revoke all on function public.support_touch_ticket() from public,anon,authenticated;

create trigger support_ticket_insert_guard before insert
 on public.support_tickets for each row execute function public.support_prepare_ticket();
create trigger support_ticket_update_guard before update
 on public.support_tickets for each row execute function public.support_prepare_ticket_update();
create trigger support_message_insert_guard before insert
 on public.support_messages for each row execute function public.support_prepare_message();
create trigger support_message_update_ticket after insert
 on public.support_messages for each row execute function public.support_touch_ticket();

-- Only the two owner/operator accounts get staff access. No app-side role claims.
insert into public.support_staff (user_id,role)
select id,'admin' from auth.users
where lower(email) in ('marcosperuchi@live.com','marcosperuchi1@gmail.com')
on conflict (user_id) do nothing;
