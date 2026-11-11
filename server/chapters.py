"""调整章节（读者自己导入的书）：改章名、和上一章合并、在某一段前分出新的一章。

原则：
- 段落的先后顺序永远不变，只是"哪几段算一章"变了 → 阅读器里按"第几段"记的阅读记录（读过哪些段、读到哪、划线、想法）全都不受影响。
- 段号（"章.段"）会变：返回 旧段号→新段号 的对照表，阅读器用它改写少数按段号记的东西（模型回答里引用的段）。
- 已经生成的东西尽量搬过去，不重花钱：
    改章名  什么都不用重做
    合并    译文、索引、解释卡片、回顾、词语表全部接上（两章的拼在一起）
    分章    译文、词语表、没跨过分章点的解释卡片照搬；被切开的那一章的索引、回顾，以及正好跨过分章点的那张卡片要重新生成
- 书库的书是大家共用的，读者不能改（由我们整理）。
"""
import os,json,shutil,time
import db,pipeline
from pipeline import _load,_save,gen,bdir,chfile

class EditError(Exception): pass
_k=lambda p:tuple(int(x) for x in str(p).split('.'))

def apply(book,ops):
    T=pipeline.text_of(book)
    foreign=pipeline.needs_translation(book)
    O=pipeline.original(book) if foreign else None
    # 每一章：标题、段（旧段号）、单元（旧段号）、来源（旧章号列表）、怎么来的
    seg_of={s['id']:s for c in T['章'] for s in c['段']}
    cur=[{'t':c['标题'],'ids':[s['id'] for s in c['段']],'units':[list(u) for u in c['单元']],'src':[c['章']],'how':'same'} for c in T['章']]
    renamed=False
    for op in ops:
        kind=op.get('op')
        if kind=='rename':
            ch=next((x for x in cur if x['src'][0]==int(op['ch'])),None)
            if not ch: raise EditError('该章不存在')
            t=str(op.get('title','')).strip()[:60]
            if t: ch['t']=t; renamed=True
    for op in sorted([o for o in ops if o.get('op')=='merge'],key=lambda o:-int(o['ch'])):   # 从后往前并，章号不乱
        i=next((k for k,x in enumerate(cur) if x['src'][0]==int(op['ch'])),None)
        if i is None: raise EditError('该章不存在')
        if i==0: raise EditError('第一章之前没有可合并的章')
        a,b=cur[i-1],cur.pop(i)
        a['ids']+=b['ids']; a['units']+=b['units']; a['src']+=b['src']
        a['how']='split' if 'split' in (a['how'],b['how']) else 'merged'
    for op in [o for o in ops if o.get('op')=='split']:
        at=str(op.get('at',''))
        i=next((k for k,x in enumerate(cur) if at in x['ids']),None)
        if i is None: raise EditError('该段不存在')
        ch=cur[i]; j=ch['ids'].index(at)
        if j==0: raise EditError('这一段已经是一章的开头')
        left,right=ch['ids'][:j],ch['ids'][j:]
        lu=[];ru=[]; cut=set()
        for u in ch['units']:
            ia,ib=ch['ids'].index(u[0]),ch['ids'].index(u[1])
            if ib<j: lu.append(u)
            elif ia>=j: ru.append(u)
            else: lu.append([u[0],left[-1]]); ru.append([at,u[1]]); cut.add(u[0])   # 跨过分章点的单元：切成两个，原来那张卡片作废
        t=str(op.get('title','')).strip()[:60] or seg_of[at]['文'][:12]
        cur[i:i+1]=[dict(ch,ids=left,units=lu,how='split',cut=ch.get('cut',set())|cut),{'t':t,'ids':right,'units':ru,'src':list(ch['src']),'how':'split','cut':cut}]
    if not any(o.get('op') in ('merge','split') for o in ops):
        if not renamed: return {}
        for c,x in zip(T['章'],cur): c['标题']=x['t']
        _save(bdir(book,'全文.json'),T)
        if O:
            for c,x in zip(O['章'],cur): c['标题']=x['t']
            _save(bdir(book,'原文.json'),O)
        pipeline.mark_dirty(book); return {}

    # ---- 新编号 ----
    idmap={}
    for n,x in enumerate(cur,1):
        for j,i in enumerate(x['ids'],1): idmap[i]=f'{n}.{j}'
    R=lambda v:_remap(v,idmap)
    old_jobs={(r[0],r[1]) for r in db.all("select step,unit from jobs where book=? and status='done'",(book,))}
    had_jobs=bool(db.one("select count(*) from jobs where book=?",(book,))[0])

    def rebuild(src_text):
        segs={s['id']:s for c in src_text['章'] for s in c['段']}
        chs=[]
        for n,x in enumerate(cur,1):
            chs.append({**{k:v for k,v in next(c for c in src_text['章'] if c['章']==x['src'][0]).items() if k not in ('章','标题','段','单元')},
                        '章':n,'标题':x['t'],'段':[dict(segs[i],id=idmap[i]) for i in x['ids']],'单元':[[idmap[a],idmap[b]] for a,b in x['units']]})
        return dict(src_text,章=chs)
    newT=rebuild(T); newO=rebuild(O) if O else None

    # ---- 已生成的东西 ----
    old_chs=[c['章'] for c in T['章']]
    L=lambda folder,n:_load(chfile(book,folder,n))
    old={f:{n:L(f,n) for n in old_chs} for f in ('索引','卡片','回顾/分','词语表_分','译文')}
    cards_all={}; [cards_all.update(v or {}) for v in old['卡片'].values()]
    tr_all={}; [tr_all.update(v or {}) for v in old['译文'].values()]
    words=[w for n in old_chs for w in (old['词语表_分'][n] or [])]
    for f in ('索引','卡片','回顾/分','词语表_分','译文','剧透复查'): shutil.rmtree(gen(book,f),ignore_errors=True)
    regen=set()
    for n,x in enumerate(cur,1):
        ids=set(x['ids']); cut=x.get('cut',set())
        if tr_all and any(i in tr_all for i in ids): _save(chfile(book,'译文',n),{idmap[i]:tr_all[i] for i in x['ids'] if i in tr_all})
        cards={idmap[a]:cards_all[a] for a,b in x['units'] if a in cards_all and a not in cut}
        if cards: _save(chfile(book,'卡片',n),cards)   # 键已经是新段号；卡片内容里没有段号
        if x['how']!='split':
            parts=[old['索引'][s] for s in x['src']]
            if all(parts): _save(chfile(book,'索引',n),R({'人物':sum((p.get('人物',[]) for p in parts),[]),'概念':sum((p.get('概念',[]) for p in parts),[]),'事件':sum((p.get('事件',[]) for p in parts),[])}))
            rs=[old['回顾/分'][s] for s in x['src']]
            if all(rs): _save(chfile(book,'回顾/分',n),R({'回':n,'一句话':'；'.join(r['一句话'] for r in rs),'详细':sum((r['详细'] for r in rs),[]),'小节':sum((r['小节'] for r in rs),[])}))
        else: regen.add(n)
        ws=[R(w) for w in words if w.get('首次') in ids]
        if ws or any(old['词语表_分'][s] is not None for s in x['src']): _save(chfile(book,'词语表_分',n),ws)
    _save(bdir(book,'全文.json'),newT)
    if newO: _save(bdir(book,'原文.json'),newO)
    pipeline.merge_index(book); pipeline.merge_small(book)
    db.run('update books set chapters=? where id=?',(len(cur),book))

    # ---- 生成任务重新排：有成品的标做完，缺的排上 ----
    if had_jobs:
        db.run('delete from jobs where book=?',(book,)); pipeline.enqueue(book); now=time.time()
        done=lambda s,u='':db.run("update jobs set status='done',t_done=? where book=? and step=? and unit=?",(now,book,s,str(u)))
        if ('terms','') in old_jobs: done('terms')
        for n,x in enumerate(cur,1):
            if os.path.exists(chfile(book,'译文',n)) and len(_load(chfile(book,'译文',n)))==len(x['ids']): done('translate',n)
            if os.path.exists(chfile(book,'索引',n)): done('index',n)
            if os.path.exists(chfile(book,'词语表_分',n)): done('gloss',n)
            if os.path.exists(chfile(book,'回顾/分',n)): done('recap',n)
            c=_load(chfile(book,'卡片',n)) or {}
            if all(idmap[a] in c for a,b in x['units']):
                done('cards',n)
                if all(('review',str(s)) in old_jobs for s in x['src']) and n not in regen: done('review',n)
        if not db.one("select count(*) from jobs where book=? and step='translate' and status!='done'",(book,))[0]: done('zh')
        if not db.one("select count(*) from jobs where book=? and step='index' and status!='done'",(book,))[0]: done('merge')
        left=db.one("select count(*) from jobs where book=? and status!='done'",(book,))[0]
        db.run("update books set status=? where id=?",('generating' if left else 'ready',book))
    pipeline.mark_dirty(book)
    return idmap

def _remap(v,m):
    """把 JSON 里所有"正好是旧段号"的字符串（值和键）换成新段号"""
    if isinstance(v,str): return m.get(v,v)
    if isinstance(v,list): return [_remap(x,m) for x in v]
    if isinstance(v,dict): return {m.get(k,k):_remap(x,m) for k,x in v.items()}
    return v
