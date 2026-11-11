"""使用情况记录（D1）：只记行为，不记任何书的正文、提问内容、划线或笔记的文字。

事件（白名单，别的一律丢掉）：
  open   打开应用（每次页面加载一条）
  book   打开一本书                book=书 id
  read   读到哪、读了多久          book=书 id，n=读到的百分比 0～100，extra=本次在书里的秒数
  clue   点开了一处伏笔            book=书 id
  quiz   问卷答案                  extra=题号:答案，例如 q3:less

上报：前端攒一批，页面隐藏或每 60 秒 POST /api/event 一次；服务端只认已登录账号，按账号限流，单批最多 20 条。
看：后台"使用情况"一栏（近 14 天每天的活跃人数、读书分钟、点开伏笔次数；次日回访；每本书的读者数和平均最远进度；问卷分布）。
删：账号注销时按账号 id 全部删除（accounts.delete_account）；其余记录保留 180 天后自动清掉。
"""
import time,re
import db

KINDS={'open','book','read','clue','quiz'}
MAX_BATCH=20; KEEP_DAYS=180
_BOOK=re.compile(r'[A-Za-z0-9_-]{1,40}$'); _QUIZ=re.compile(r'q[1-9]:[A-Za-z0-9_,-]{1,40}$')
_last_prune=[0]

def _day(t=None): return time.strftime('%Y-%m-%d',time.localtime(t or time.time()))

def record(uid,events):
    """写入一批事件，返回实际写入的条数。不合规的条目静默丢弃，不报错（前端不需要重试）"""
    now=time.time(); n=0
    for e in list(events or [])[:MAX_BATCH]:
        if not isinstance(e,dict): continue
        k=str(e.get('k',''))
        if k not in KINDS: continue
        book=str(e.get('b','') or '')
        if k in ('book','read','clue') and not _BOOK.match(book): continue
        if k not in ('book','read','clue'): book=''
        try: pct=max(0,min(100,int(e.get('n',0) or 0)))
        except (TypeError,ValueError): pct=0
        extra=''
        if k=='read':
            try: extra=str(max(0,min(3600,int(e.get('s',0) or 0))))   # 一次上报最多算 1 小时，防止挂机刷时长
            except (TypeError,ValueError): extra='0'
        elif k=='quiz':
            extra=str(e.get('v','') or '')
            if not _QUIZ.match(extra): continue
        db.run('insert into events(uid,t,day,kind,book,n,extra) values(?,?,?,?,?,?,?)',(uid,now,_day(now),k,book,pct if k=='read' else 0,extra)); n+=1
    _prune(now)
    return n

def _prune(now):
    if now-_last_prune[0]<86400: return
    _last_prune[0]=now; db.run('delete from events where t<?',(now-KEEP_DAYS*86400,))

def delete_user(uid): db.run('delete from events where uid=?',(uid,))

def daily(days=14):
    """近 N 天每天：活跃人数、读书分钟、点开伏笔次数。没有记录的日子补 0"""
    start=_day(time.time()-(days-1)*86400)
    act={d:n for d,n in db.all("select day,count(distinct uid) from events where day>=? group by day",(start,))}
    mins={d:int(s or 0)//60 for d,s in db.all("select day,sum(cast(extra as integer)) from events where kind='read' and day>=? group by day",(start,))}
    clue={d:n for d,n in db.all("select day,count(*) from events where kind='clue' and day>=? group by day",(start,))}
    out=[]
    for i in range(days):
        d=_day(time.time()-(days-1-i)*86400); out.append({'day':d,'active':act.get(d,0),'minutes':mins.get(d,0),'clues':clue.get(d,0)})
    return out

def retention():
    """次日回访：某天首次出现的账号，第二天又出现的占比。只统计已满一天的；返回 (首次出现的人数, 次日回来的人数)"""
    today=_day()
    rows=db.all("select uid,min(day) from events group by uid")
    first={};
    for uid,d in rows: first[uid]=d
    seen={}
    for uid,d in db.all("select distinct uid,day from events"): seen.setdefault(uid,set()).add(d)
    total=back=0
    for uid,d in first.items():
        if d>=today: continue   # 今天才来的，还没到第二天
        nxt=_day(time.mktime(time.strptime(d,'%Y-%m-%d'))+86400+3600)
        total+=1; back+= nxt in seen.get(uid,())
    return total,back

def per_book():
    """每本书：打开过的人数、读到的最远进度的平均值、读书总分钟"""
    out=[]
    for b,readers in db.all("select book,count(distinct uid) from events where kind in ('book','read') and book!='' group by book order by 2 desc"):
        far=[m for (m,) in db.all("select max(n) from events where kind='read' and book=? group by uid",(b,))]
        mins=db.one("select coalesce(sum(cast(extra as integer)),0) from events where kind='read' and book=?",(b,))[0]//60
        out.append({'book':b,'readers':readers,'avg_far':round(sum(far)/len(far)) if far else 0,'minutes':mins})
    return out

def quiz_dist():
    """问卷：每道题每个答案各多少人（同一人多次答只算最后一次）"""
    last={}
    for uid,v in db.all("select uid,extra from events where kind='quiz' order by t"):
        q,_,a=v.partition(':')
        for part in a.split(','):   # 多选题：q2:words,people
            pass
        last[(uid,q)]=a
    dist={}
    for (uid,q),a in last.items():
        for part in a.split(','):
            if part: dist.setdefault(q,{}); dist[q][part]=dist[q].get(part,0)+1
    return dist

def totals():
    r=db.one("select count(distinct uid),count(*) from events")
    return {'users':r[0],'events':r[1]}
