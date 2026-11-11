"""生成服务：一本书 → 拆成很多小任务 → 排队调模型 → 每步落盘 → 自动检查 → 打包给阅读器。

一本书的文件（DATA/books/<书id>/）：
  原文.<扩展名>     读者上传的原文件
  全文.json         导入后的正文（和第一阶段流水线同一格式）
  gen/              生成的东西，目录结构和第一阶段 生成/<书>/ 完全一样，所以打包直接用 packer.py：
    索引/第001章.json  卡片/第001章.json  回顾/分/第001章.json  词语表_分/第001章.json
    索引_合并.json  回顾/回顾.json  词语表.json
  pack.json         打包好、阅读器直接用的数据（gen 有变化时自动重打）

任务（jobs 表，一行一步；unique(book,step,unit) 保证不会重复排）：
  index:N   第 N 章的索引（人物/概念/事件）         ← 不依赖别的
  gloss:N   第 N 章的词语表                         ← 不依赖别的
  merge     合并全书索引                            ← 所有 index 做完
  cards:N   第 N 章的解释卡片（带截至本章的上下文）    ← merge
  review:N  第 N 章卡片的剧透复查，直接改卡片         ← cards:N
  recap:N   第 N 章的回顾                           ← merge
做完一步就存一个文件；中断了（额度用完、网络断、服务器重启）从没做完的那一步接着做，做完的不重做。
伏笔、主线、示范问答还要人工审（第一阶段的经验），导入的书暂时不自动生成——阅读器里没有就不显示。

失败怎么办：
  额度用完（QuotaExceeded）→ 这一步标 waiting，第二天自动接着跑，不算失败
  模型暂时不可用 / 连不上 → 过一会儿重试，最多 4 次
  输出格式不对（模型层已经带着错误重试过一次）→ 再排一次；还不行标 failed，后台能看到原因、能点"重试"
"""
import os,json,time,re,threading,traceback,shutil
import config,db,model,packer,tasks

STEPS_PER_CH=('index','gloss','cards','review','recap')
MAX_TRIES={'transient':4,'bad':2}
RETRY_WAIT=60                      # 模型暂时不可用时，多久后重试（秒）

# ---------------- 文件 ----------------
def bdir(book,*a): return config.path('books',book,*a)
def _save(p,obj):
    os.makedirs(os.path.dirname(p),exist_ok=True); tmp=p+'.tmp'
    with open(tmp,'w',encoding='utf-8') as f: json.dump(obj,f,ensure_ascii=False,indent=1)
    os.replace(tmp,p)                                   # 先写临时文件再改名：写到一半断电也不会留下坏文件
def _load(p,default=None):
    if not os.path.exists(p): return default
    with open(p,encoding='utf-8') as f: return json.load(f)
def text_of(book): return _load(bdir(book,'全文.json'))
def gen(book,*a): return bdir(book,'gen',*a)
def chfile(book,folder,n): return gen(book,folder,f'第{int(n):03d}章.json')

def mark_dirty(book):
    db.run("update books set meta=json_set(meta,'$.dirty',1) where id=?",(book,))

# ---------------- 给模型的输入（和第一阶段 make_inputs_通用.py / make_context_通用.py 一样） ----------------
TAG={'提要':'【提要】','小标题':'【小标题】','引文':'【引文】','文件':'【文件·默认折叠】'}
def numbered(T,c,U='章'):
    line=lambda s:f"{s['id']}　{TAG.get(s.get('类'),'')}{s['文']}"
    return f"《{T['书']}》第 {c['章']} {U}　{c['标题']}\n\n"+'\n\n'.join(line(s) for s in c['段'])
def by_units(T,c,U='章'):
    S={s['id']:s for s in c['段']}; ids=[s['id'] for s in c['段']]
    line=lambda s:f"{s['id']}　{TAG.get(s.get('类'),'')}{s['文']}"
    parts=[f"《{T['书']}》第 {c['章']} {U}　{c['标题']}　（共 {len(c['单元'])} 个解释单元）",'']
    for a,b in c['单元']:
        parts.append(f'【单元 {a}～{b}】（读者读到 {b} 为止）')
        parts+=[line(S[x]) for x in ids[ids.index(a):ids.index(b)+1]]; parts.append('')
    return '\n'.join(parts)
_k=lambda p:tuple(int(x) for x in str(p).split('.'))
def context(merged,N):
    lim=(N,10**6); ppl=[]
    for e in merged['人物']:
        if _k(e['首次'])>lim: continue
        ppl.append({'名(内部)':e['名'],'名可显示从':e.get('名可显示从'),'首次':e['首次'],
          '别称':[a for a in e['别称'] if _k(a['从'])<=lim],'身份':[x for x in e['身份'] if _k(x['从'])<=lim],
          '关系':[r for r in e['关系'] if _k(r[2])<=lim],'事迹':[x for x in e['事迹'] if _k(x['从'])<=lim],'备注':e['备注']})
    return {'说明':f'截至第{N}章的索引。每条信息都有"从"（从哪一段起读者才知道）；写某一段的卡片时，只能用"从"不晚于该段的信息。"名(内部)"只是数据里的标识：在"名可显示从"之前，读者还不知道这个名字，只能用当时已出现的别称。',
            '人物':ppl,'概念':[c for c in merged['概念'] if _k(c['首次'])<=lim],'前几章事件':[e for e in merged['事件'] if _k(e['段'])<(N,0)]}

def merge_index(book):
    """合并各章索引（同 merge_index_通用.py；导入的书没有人工归并表）"""
    T=text_of(book); SEGS=[(s['id'],s['文']) for c in T['章'] for s in c['段']]
    def first_pos(w,after):
        for sid,t in SEGS:
            if _k(sid)>=_k(after) and w in t: return sid
    people={}; concepts={}; events=[]
    for c in T['章']:
        d=_load(chfile(book,'索引',c['章']))
        if not d: continue
        for p in d.get('人物',[]):
            e=people.setdefault(p['名'],{'名':p['名'],'篇':None,'别称':[],'首次':p['首次'],'出场':'','身份':[],'关系':[],'事迹':[],'备注':[]})
            for a in p.get('这章的叫法',[]):
                if a not in [x['称'] for x in e['别称']]:
                    fp=first_pos(a,p['首次'].split('.')[0]+'.1')
                    e['别称'].append({'称':a,'从':fp if fp and fp.split('.')[0]==p['首次'].split('.')[0] else p['首次']})
            if _k(p['首次'])<_k(e['首次']): e['首次']=p['首次']
            if p.get('出场') and (not e['出场'] or _k(p['出场'])<_k(e['出场'])): e['出场']=p['出场']
            e['身份']+=[x for x in p.get('身份',[]) if x.get('从')]
            for r in p.get('关系',[]):
                rr=[r[0],r[1],r[2] if len(r)>2 else p['首次']]
                if rr[:2] not in [x[:2] for x in e['关系']]: e['关系'].append(rr)
            if p.get('这章做了什么'): e['事迹'].append({'从':p['首次'],'写':p['这章做了什么']})
            if p.get('备注'): e['备注'].append(p['备注'])
        for c2 in d.get('概念',[]): concepts.setdefault(c2['词'],c2)
        events+=d.get('事件',[])
    for e in people.values():
        hit=[a['从'] for a in e['别称'] if a['称']==e['名']]
        e['名可显示从']=min(hit,key=_k) if hit else None
        for key in ('别称','身份','事迹'): e[key].sort(key=lambda x:_k(x['从']))
    out={'人物':sorted(people.values(),key=lambda e:_k(e['首次'])),'概念':sorted(concepts.values(),key=lambda c:_k(c['首次'])),'事件':events}
    _save(gen(book,'索引_合并.json'),out); return out

def merge_small(book):
    """回顾、词语表：各章的合成一份（每次有一章做完就重合一次，读者马上能看到）"""
    T=text_of(book); rec=[]; words=[]; seen=set()
    for c in T['章']:
        r=_load(chfile(book,'回顾/分',c['章']))
        if r: r['回']=c['章']; rec.append(r)
        for w in _load(chfile(book,'词语表_分',c['章']),[]) or []:
            if w.get('词') and w['词'] not in seen: seen.add(w['词']); words.append(w)
    _save(gen(book,'回顾','回顾.json'),rec); _save(gen(book,'词语表.json'),words)

# ---------------- 每一步做什么 ----------------
def _meta(book):
    r=db.one('select title,meta from books where id=?',(book,)); m=json.loads(r[1] or '{}'); m['title']=r[0]; return m
def _common(book,c,T):
    m=_meta(book); kind=m.get('类型','小说')
    rule=tasks.RULE(kind)
    return {'书名':m['title'],'N':c['章'],'chapter':c['章'],'ids':[s['id'] for s in c['段']],'done_dir':gen(book),
            'rule_text':rule,'规则':'见下面的【不剧透规则】','POS':'（每个单元各自的最后一段）'},kind

LANG_NAME={'en':'英文','de':'德文','fr':'法文'}
def needs_translation(book): return bool(_meta(book).get('需翻译'))
def original(book):
    """外文书的原文（导入时的全文.json 第一次翻译前存一份成 原文.json）"""
    p=bdir(book,'原文.json')
    if not os.path.exists(p): _save(p,text_of(book))
    return _load(p)
def assemble_zh(book):
    """原文 + 各章译文 → 全文.json：文=中文，每段另存原文（阅读器可切换"原文"，解释卡片里能看这一段的原文）。
    还没译完的段落先放原文，阅读器照样能读"""
    O=original(book); lang=_meta(book).get('语言','en'); T=json.loads(json.dumps(O))
    for c in T['章']:
        tr=_load(chfile(book,'译文',c['章']),{}) or {}
        for x in c['段']: x[lang]=x['文']; x['文']=tr.get(x['id']) or x['文']
    T['原文语言']=lang; _save(bdir(book,'全文.json'),T)

def do_step(book,step,unit):
    if step=='terms':
        O=original(book); v={'书名':_meta(book)['title'],'rule_text':'',
            'text':'\n\n'.join(f"第 {c['章']} 章　{c['标题']}\n"+'\n'.join(x['文'][:400] for x in c['段'][:8]) for c in O['章'])[:60000]}
        _save(gen(book,'译名表.json'),model.call('terms',v,book=book)); return
    if step=='translate':
        O=original(book); c=next(x for x in O['章'] if x['章']==int(unit))
        terms=_load(gen(book,'译名表.json'),{'译名':[]})
        prev=_load(chfile(book,'译文',int(unit)-1),{}) or {}
        src={x['id']:x['文'] for x in c['段']}
        v={'书名':_meta(book)['title'],'rule_text':'','src':src,'done':{},
           'text':'【译名表】\n'+json.dumps(terms.get('译名',[]),ensure_ascii=False)+('\n\n【上一章最后几段的译文（保持文气连贯）】\n'+'\n'.join(list(prev.values())[-3:]) if prev else '')
                 +'\n\n【这一章的原文】\n'+'\n'.join(f'{k}　{t}' for k,t in src.items())}
        _save(chfile(book,'译文',unit),model.call('translate',v,book=book)); assemble_zh(book); return
    if step=='zh': assemble_zh(book); return
    T=text_of(book)
    if step=='merge': merge_index(book); return
    c=next(x for x in T['章'] if x['章']==int(unit)); v,kind=_common(book,c,T)
    if step=='index':
        v.update(text=numbered(T,c),rule_text='')
        _save(chfile(book,'索引',unit),model.call('index',v,book=book))
    elif step=='gloss':
        v.update(text=numbered(T,c),rule_text='',seg={s['id']:s['文'] for s in c['段']})
        _save(chfile(book,'词语表_分',unit),model.call('gloss',v,book=book)); merge_small(book)
    elif step=='cards':
        merged=_load(gen(book,'索引_合并.json'),{'人物':[],'概念':[],'事件':[]})
        v.update(text=by_units(T,c),context=context(merged,c['章']),units=[a for a,b in c['单元']],POS='（每个单元的最后一段）')
        task='cards_nonfiction' if kind=='非虚构' else 'cards_novel'
        _save(chfile(book,'卡片',unit),model.call(task,v,book=book))
    elif step=='review':
        cards=_load(chfile(book,'卡片',unit))
        v.update(text=by_units(T,c)+'\n\n【要检查的解释卡片】\n'+json.dumps(cards,ensure_ascii=False))
        out=model.call('review',v,book=book); n=0
        for x in out.get('改',[]):
            u=cards.get(x['单元'],{}).get(x['档'])
            if isinstance(u,dict) and x['字段'] in u and x.get('改为'): u[x['字段']]=x['改为']; n+=1
        _save(chfile(book,'卡片',unit),cards)
        _save(gen(book,'剧透复查',f'第{int(unit):03d}章.json'),{'改了':n,**out})
    elif step=='recap':
        merged=_load(gen(book,'索引_合并.json'),{'人物':[],'概念':[],'事件':[]})
        v.update(text=numbered(T,c),context=context(merged,c['章']),POS=c['段'][-1]['id'])
        _save(chfile(book,'回顾/分',unit),model.call('recap',v,book=book)); merge_small(book)
    else: raise ValueError('不认识的步骤：'+step)

# ---------------- 排队 ----------------
def enqueue(book):
    """给一本书排上全部任务（已经排过的不重复排，已经做完的不重做）"""
    T=text_of(book); now=time.time()
    pre=[(book,'terms','')]+[(book,'translate',str(c['章'])) for c in T['章']]+[(book,'zh','')] if needs_translation(book) else []
    rows=pre+[(book,s,str(c['章'])) for c in T['章'] for s in ('index','gloss')]+[(book,'merge','')]+[(book,s,str(c['章'])) for c in T['章'] for s in ('cards','review','recap')]
    for b,s,u in rows: db.run("insert or ignore into jobs(book,step,unit,status,t_new) values(?,?,?,'todo',?)",(b,s,u,now))
    db.run("update books set status='generating' where id=? and status in ('ready','failed')",(book,))

def _deps_ok(book,step,unit):
    q=lambda sql,a=(): db.one(sql,(book,)+a)[0]
    if step=='terms': return True
    if step=='translate': return q("select count(*) from jobs where book=? and step='terms' and status='done'")>0
    if step=='zh': return q("select count(*) from jobs where book=? and step='translate' and status!='done'")==0
    if step in ('index','gloss'): return q("select count(*) from jobs where book=? and step='zh' and status!='done'")==0   # 外文书：译完才做；中文书没有 zh 这一步
    if step=='merge': return q("select count(*) from jobs where book=? and step='index' and status!='done'")==0
    if step in ('cards','recap'): return q("select count(*) from jobs where book=? and step='merge' and status='done'")>0
    if step=='review': return q("select count(*) from jobs where book=? and step='cards' and unit=? and status='done'",(unit,))>0
    return True

def next_job():
    """挑一个可以做的任务：按书的先后、步骤的先后；依赖没做完的跳过；waiting 的到时间才做"""
    now=time.time()
    for j in db.rows("select * from jobs where status in ('todo','waiting') and t_new<=? order by book, case step when 'terms' then -3 when 'translate' then -2 when 'zh' then -1 when 'index' then 0 when 'merge' then 1 when 'cards' then 2 when 'review' then 3 when 'recap' then 4 else 5 end, cast(unit as integer) limit 200",(now,)):
        if _deps_ok(j['book'],j['step'],j['unit']):
            cur=db.run("update jobs set status='running' where id=? and status in ('todo','waiting')",(j['id'],))
            if cur.rowcount: return j
    return None

def run_job(j):
    book,step,unit=j['book'],j['step'],j['unit']
    try:
        do_step(book,step,unit)
        db.run("update jobs set status='done',t_done=?,err='' where id=?",(time.time(),j['id'])); mark_dirty(book)
    except model.QuotaExceeded as e:
        tomorrow=time.mktime(time.strptime(time.strftime('%Y-%m-%d'),'%Y-%m-%d'))+86400+60
        db.run("update jobs set status='waiting',err=?,t_new=? where id=?",(str(e),tomorrow,j['id']))
    except model.TruncatedOutput as e:
        # 回答被输出上限截断：同样的请求再发一遍还是会被截断，白烧额度。直接标失败，后台能看到原因，调大 FUBI_MODEL_MAX_TOKENS 后点"全部重试"
        db.run("update jobs set status='failed',tries=tries+1,err=? where id=?",('回答被截断：'+str(e)[:300]+'。可调大 FUBI_MODEL_MAX_TOKENS 后重试',j['id']))
    except model.BadOutput as e:
        tries=j['tries']+1
        db.run("update jobs set status=?,tries=?,err=?,t_new=? where id=?",('failed' if tries>=MAX_TRIES['bad'] else 'todo',tries,'输出格式不对：'+str(e)[:400],time.time(),j['id']))
    except model.ModelError as e:
        tries=j['tries']+1
        db.run("update jobs set status=?,tries=?,err=?,t_new=? where id=?",('failed' if tries>=MAX_TRIES['transient'] else 'todo',tries,str(e)[:400],time.time()+RETRY_WAIT*tries,j['id']))
    except Exception as e:
        db.run("update jobs set status='failed',tries=tries+1,err=? where id=?",(('程序出错：'+repr(e))[:300]+'\n'+traceback.format_exc()[-600:],j['id']))
    finish_if_done(book)

def finish_if_done(book):
    left=db.one("select count(*) from jobs where book=? and status in ('todo','running','waiting')",(book,))[0]
    if left: return
    bad=db.one("select count(*) from jobs where book=? and status='failed'",(book,))[0]
    db.run("update books set status=? where id=? and status='generating'",('ready',book))
    db.run("update books set meta=json_set(meta,'$.gen_done',?,'$.gen_failed',?) where id=?",(time.time(),bad,book))

def progress(book):
    r={s:0 for s in ('todo','running','waiting','done','failed')}
    for s,n in db.all("select status,count(*) from jobs where book=? group by status",(book,)): r[s]=n
    r['total']=sum(r.values()); return r

READABLE_RATIO=0.2   # 用户 11-03 定：前 20% 的章（向上取整）生成好就能读

def readable_chapters(n_chapters):
    """至少要生成好前几章才能读：章数的 20%，向上取整，至少 1 章"""
    import math
    return max(1,math.ceil(n_chapters*READABLE_RATIO)) if n_chapters>0 else 0

def _eta_seconds(book,p):
    """粗略估计还要多久（秒）。只用这本书自己已完成任务的平均耗时 × 剩余任务数 ÷ 并发数；样本少于 3 个返回 None（不给假数字）。
    不含：额度用完要等到明天的任务、失败的任务。并发数取 FUBI_WORKERS（默认 2），实际受模型限速影响，所以只是量级。"""
    done=db.rows("select t_new,t_done from jobs where book=? and status='done' and t_done is not null and t_new is not null and t_done>=t_new",(book,))
    if len(done)<3: return None
    per=sum(r['t_done']-r['t_new'] for r in done)/len(done)
    left=p['todo']+p['running']
    workers=max(1,int(os.environ.get('FUBI_WORKERS','2')))
    return int(per*left/workers)

def status(book):
    """给书架、导入页、详情页用的一份汇总：要不要锁、读到什么程度、预估多久。
    state: parsing 整理中 / generating 生成中（未到门槛，不能读）/ readable 可读但还在生成 / done 全部完成 / waiting 额度用完明天继续 / failed 有失败
    注意：外文书另有"译完才能读"的规则（前端按 untranslated 判断），这里只管生成阶段"""
    p=progress(book); b=db.one('select status,chapters from books where id=?',(book,))
    if not b: return None
    st,n=b[0],b[1] or 0; need=readable_chapters(n)
    if st=='parsing': return {'state':'parsing','need':need,'chapters':n,'ready_chapters':0,'done':0,'total':0}
    # 每章"解释+复查+回顾"三步都 done 才算这一章生成好；前 need 章都好了才可读
    rows=db.all("select unit,step,status from jobs where book=? and step in ('cards','review','recap')",(book,))
    ok={}
    for u,sp,sta in rows: ok.setdefault(u,[]).append(sta=='done')
    ready=0
    for u in sorted(ok,key=lambda x:int(x) if str(x).isdigit() else 10**9):
        if len(ok[u])==3 and all(ok[u]): ready+=1
        else: break   # 必须是从第 1 章起连续的
    total=p['total']; done=p['done']
    if total==0: state='done' if st=='ready' else st   # 没排过任务：假模型/没开自动生成/老书，不锁
    elif done>=total: state='done'
    elif p['failed'] and not (p['todo'] or p['running'] or p['waiting']): state='failed'
    elif ready>=need: state='readable'
    elif p['waiting'] and not (p['todo'] or p['running']): state='waiting'
    else: state='generating'
    return {'state':state,'need':need,'chapters':n,'ready_chapters':ready,'done':done,'total':total,'failed':p['failed'],'waiting':p['waiting'],'eta':_eta_seconds(book,p) if state in ('generating','readable') else None}

def retry_failed(book=None):
    if book: db.run("update jobs set status='todo',tries=0,t_new=? where status='failed' and book=?",(time.time(),book))
    else: db.run("update jobs set status='todo',tries=0,t_new=? where status='failed'",(time.time(),))
    db.run("update books set status='generating' where id in (select distinct book from jobs where status='todo')")

def recover():
    """服务器重启：上次跑到一半的任务放回队列"""
    db.run("update jobs set status='todo' where status='running'")

# ---------------- 打包 ----------------
def pack(book):
    """全文 + gen/ → pack.json（阅读器要的格式）。gen 里缺什么都行：没生成的就是没有"""
    r=db.one('select title,author,meta from books where id=?',(book,)); m=json.loads(r[2] or '{}')
    unit='篇' if m.get('类型')=='短篇集' else '章'
    d=packer.pack_book(bdir(book,'全文.json'),gen(book),book,unit,'rb_imp_'+book)
    d.update({'whole':True,'imported':True,'titled':bool(m.get('有章名',True))})
    if m.get('需翻译'):
        lang=m.get('语言','en'); done=db.one("select count(*) from jobs where book=? and step='translate' and status='done'",(book,))[0]
        if done: d['orig']=[[lang,LANG_NAME.get(lang,'原文')]]       # 有译文了：阅读器显示"中文/原文"切换
        d['untranslated']=not done
    _save(bdir(book,'pack.json'),d)
    db.run("update books set meta=json_remove(meta,'$.dirty') where id=?",(book,))
    return d

def packed(book):
    r=db.one('select meta from books where id=?',(book,))
    if not r: return None
    if json.loads(r[0] or '{}').get('dirty') or not os.path.exists(bdir(book,'pack.json')): return pack(book)
    return _load(bdir(book,'pack.json'))

# ---------------- 后台工人 ----------------
class Worker(threading.Thread):
    """一个后台线程不停地取任务做。模型请求慢（几十秒），所以可以开几个并行（FUBI_WORKERS）"""
    def __init__(self,stop): super().__init__(daemon=True); self.stop=stop
    def run(self):
        while not self.stop.is_set():
            try: j=next_job()
            except Exception: j=None
            if not j: self.stop.wait(2); continue
            run_job(j)

def generation_on():
    """真模型配好了就自动生成；假模型时默认不生成（不然读者会看到"假模型"占位文字），测试时用 FUBI_MOCK_GENERATE=1 打开"""
    return config.MODEL['provider']!='mock' or os.environ.get('FUBI_MOCK_GENERATE')=='1'

def drain(limit=10**6):
    """不开线程，把能做的任务一个个做完（测试和命令行用）"""
    n=0
    while n<limit:
        j=next_job()
        if not j: break
        run_job(j); n+=1
    return n
