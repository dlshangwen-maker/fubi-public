"""数据库：SQLite（一个文件，零运维）。用户多了换 PostgreSQL 时，只改这个文件。
表：
  books        书：内置精编书 + 书库的书 + 读者导入的书
  jobs         生成任务（一本书拆成很多小步，每步一条）
  model_calls  每次模型调用的账（花费、耗时、成败）
  progress     阅读记录（按设备号存；账号以后接上时把设备号换成用户 id）
  searches     找书的搜索记录（热门搜索按最近 30 天的次数排）
"""
import sqlite3,threading,json,time,os
import config
_local=threading.local()
SCHEMA='''
create table if not exists books(
  id text primary key, title text, author text, nat text default '', kind text,   -- kind: builtin（精编书）/ import（读者自己的书：导入的、找书下载的）
  owner text default '',          -- 导入的书属于哪个设备（只给本人看）
  fmt text default '', src text default '', status text default 'ready',  -- ready / parsing / generating / failed
  chars integer default 0, chapters integer default 0, meta text default '{}', t real);
create table if not exists jobs(
  id integer primary key autoincrement, book text, step text, unit text default '',
  status text default 'todo',     -- todo / running / done / failed / waiting（额度用完，之后再跑）
  tries integer default 0, err text default '', t_new real, t_done real, after text default '',
  unique(book,step,unit));
create table if not exists model_calls(
  id integer primary key autoincrement, day text, t real, task text, book text, provider text, model text,
  ok integer, ms integer, chars_in integer, chars_out integer, err text default '');
create table if not exists progress(
  device text, book text, state text, t real, primary key(device,book));
create table if not exists searches(
  id integer primary key autoincrement, q text, device text, t real);   -- 找书的搜索记录（热门搜索按它排）
create table if not exists users(
  id integer primary key autoincrement, email text unique not null, name text default '', av text default '{}',
  pw text not null,                -- scrypt$盐$哈希
  t real, last_login real default 0);
create table if not exists events(
  id integer primary key autoincrement, uid integer not null, t real not null, day text not null,
  kind text not null,              -- open / book / read / clue / quiz（白名单见 usage.py）
  book text default '', n integer default 0, extra text default '');
create index if not exists events_day on events(day,kind);
create index if not exists events_uid on events(uid,t);
create table if not exists sessions(h text primary key, uid integer not null, t real, exp real);   -- h：令牌的哈希
create table if not exists invites(code text primary key, note text default '', t real, used_by integer, used_t real);
create table if not exists resets(email text primary key, h text, exp real, tries integer default 0);
create index if not exists sessions_uid on sessions(uid);
create index if not exists searches_t on searches(t);
create index if not exists jobs_book on jobs(book,status);
create index if not exists calls_day on model_calls(day);
'''
def conn():
    c=getattr(_local,'c',None)
    if c is None:
        p=config.path('fubi.db')
        c=sqlite3.connect(p,timeout=30,check_same_thread=False); c.execute('pragma journal_mode=wal'); c.execute('pragma foreign_keys=on')
        c.executescript(SCHEMA)
        cols={r[1] for r in c.execute('pragma table_info(users)')}
        for col,ddl in (('agreed_ver',"alter table users add column agreed_ver text default ''"),('agreed_t',"alter table users add column agreed_t real default 0")):
            if col not in cols: c.execute(ddl)   # 老库升级：补上"同意了哪一版协议、什么时候同意的"
        c.commit(); _local.c=c
    return c
def run(sql,args=()):
    c=conn(); cur=c.execute(sql,args); c.commit(); return cur
def one(sql,args=()): return conn().execute(sql,args).fetchone()
def all(sql,args=()): return conn().execute(sql,args).fetchall()
def rows(sql,args=()):
    cur=conn().execute(sql,args); cols=[d[0] for d in cur.description]
    return [dict(zip(cols,r)) for r in cur.fetchall()]
def reset_for_tests():
    c=getattr(_local,'c',None)
    if c: c.close(); _local.c=None
