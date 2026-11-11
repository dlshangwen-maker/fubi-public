"""书：两种，读者在书架上看到的是同一种东西。
  builtin  精编书（项目里已经做好的五本：伏笔、主线、解释、回顾都有）。数据由 生成/build_demo.py 产出——和 demo 完全同一份
  import   读者自己的书：从手机里导入的文件，或在"找书"里搜到、下载到书架的公版书（search.py）。只给这个人（设备号）看
我们不存书库（2026-10-27 用户定）：找书只是搜索，读者自己下载，下载下来的书和导入的书一样处理。

阅读器拿书：GET /api/books/<id> → 和 demo 里 ALL[id] 一样的数据（props/hui/cards/suspense/…）。
"""
import os,json,time,hashlib,re,threading
import config,db,importer,pipeline

# ---------------- 精编书 ----------------
_builtin=None; _lock=threading.Lock()
BUILTIN_SHELF=[  # 书架顺序、作者国籍（和 demo 的 SHELF 一致）
    ('hlm','红楼梦','曹雪芹',''),('tractatus','逻辑哲学论','维特根斯坦','奥地利'),('nahan','呐喊','鲁迅',''),
    ('lhz','李鸿章传','梁启超',''),('hound','巴斯克维尔的猎犬','柯南·道尔','英国')]
def builtin_data():
    """调 build_demo.py 的打包逻辑（不写 html），结果缓存在内存里；源文件改了重启服务即可"""
    global _builtin
    with _lock:
        if _builtin is None:
            cache=config.path('builtin.json')
            src=os.path.join(config.ROOT,'生成','build_demo.py')
            if os.path.exists(cache) and os.path.exists(src) and os.path.getmtime(cache)>=_newest_source():
                _builtin=json.load(open(cache,encoding='utf-8'))
            else:
                g={'__name__':'fubi_server','__file__':src}
                os.environ['FUBI_NO_HTML']='1'
                try: exec(compile(open(src,encoding='utf-8').read(),src,'exec'),g)
                finally: os.environ.pop('FUBI_NO_HTML',None)
                _builtin=g['data']['books']
                tmp=cache+'.tmp'; json.dump(_builtin,open(tmp,'w',encoding='utf-8'),ensure_ascii=False); os.replace(tmp,cache)
    return _builtin
def _newest_source():
    t=0
    for d in ('生成','文本数据','server'):
        for root,_,fs in os.walk(os.path.join(config.ROOT,d)):
            if '备份' in root or '__pycache__' in root: continue
            for f in fs:
                if f.endswith(('.json','.py')): t=max(t,os.path.getmtime(os.path.join(root,f)))
    return t

def sync_builtin():
    """启动时把精编书登记进 books 表"""
    for i,(k,t,a,nat) in enumerate(BUILTIN_SHELF):
        db.run("insert into books(id,title,author,nat,kind,status,t,meta) values(?,?,?,?,'builtin','ready',?,?) on conflict(id) do update set title=excluded.title,author=excluded.author,nat=excluded.nat",
               (k,t,a,nat,i,json.dumps({'order':i})))

BUILTIN_INFO={'hlm':'贾府由盛而衰，宝玉、黛玉、宝钗的故事（收录前五回）。','tractatus':'维特根斯坦用 526 条编号命题，划出语言能说清的界限。',
    'nahan':'鲁迅第一部小说集：《狂人日记》《孔乙己》《阿Q正传》《故乡》等。','lhz':'梁启超为刚去世的李鸿章作传，夹叙夹议。','hound':'巴斯克维尔家族的魔犬传说，福尔摩斯和华生去荒原查案。'}
BUILTIN_ALIAS={'hlm':['石头记','红楼梦','紅樓夢'],'tractatus':['Tractatus Logico-Philosophicus','Logisch-philosophische Abhandlung'],'nahan':['吶喊'],'lhz':['李鸿章','中国四十年来大事记'],'hound':['The Hound of the Baskervilles','福尔摩斯','Sherlock Holmes']}
def builtin_hits(q):
    """找书时，精编书也在结果里（排最前，已经在书架上）"""
    import search
    nq=search._n(q)
    if not nq: return []
    return [{'来源':'builtin','编号':k,'书名':t,'作者':a,'国籍':nat,'简介':BUILTIN_INFO[k]} for k,t,a,nat in BUILTIN_SHELF
            if any(nq in search._n(x) or search._n(x) in nq and len(search._n(x))>=2 for x in [t,a]+BUILTIN_ALIAS.get(k,[]))]

# ---------------- 找书下载 ----------------
def download(device,source,ref,title='',author='',sources=None):
    """找书结果"下载到书架"：服务器去来源网站下载（同一本书有几个来源就按顺序试）→ 和导入的文件一样处理。
    title/author 是搜索结果里的（外文书有中文名时用中文名）"""
    import search
    srcs=[{'来源':str(x.get('来源','')),'编号':str(x.get('编号',''))[:120]} for x in (sources or []) if isinstance(x,dict)][:4] or [{'来源':source,'编号':str(ref)}]
    for x in srcs: search.candidates(x['来源'],x['编号'])          # 先检查每个来源和编号都合法
    data,fname,used=search.fetch_any(srcs)
    s_,r_=used['来源'],used['编号']
    meta={'来源':s_,'编号':r_,'链接':(f'https://www.gutenberg.org/ebooks/{r_}' if s_=='gutenberg' else 'https://zh.wikisource.org/wiki/'+r_)}
    if title: meta['书名']=str(title)[:80]
    if author: meta['作者']=str(author)[:60]
    return import_file(data,fname,device,meta=meta,background=not os.environ.get('FUBI_SYNC_IMPORT'))

# ---------------- 导入 ----------------
def _bid(data,device): return 'u'+hashlib.sha1(device.encode()+b'|'+data).hexdigest()[:12]
def import_file(data,filename,device,kind='import',background=True,meta=None):
    """读者上传 → 书 id。同一个人重复导入同一个文件，返回原来那本，不重复建"""
    if len(data)>config.MAX_UPLOAD: raise importer.ImportError_(f'文件太大（上限 {config.MAX_UPLOAD//1024//1024}MB）')
    bid=_bid(data,device)
    if db.one('select 1 from books where id=?',(bid,)): return bid
    ext=os.path.basename(filename).rsplit('.',1)[-1].lower() if '.' in filename else 'bin'
    if not re.fullmatch(r'[a-z0-9]{1,8}',ext): ext='bin'
    p=pipeline.bdir(bid,'原文.'+ext); open(p,'wb').write(data)
    db.run("insert into books(id,title,author,kind,owner,fmt,src,status,t,meta) values(?,?,?,?,?,?,?,'parsing',?,?)",
           (bid,os.path.basename(filename)[:80],'',kind,device if kind=='import' else '',ext,os.path.basename(filename)[:200],time.time(),json.dumps(meta or {},ensure_ascii=False)))
    if background: threading.Thread(target=_parse,args=(bid,data,filename),daemon=True).start()
    else: _parse(bid,data,filename)
    return bid

def _parse(bid,data,filename):
    try:
        book=importer.import_book(data,filename)
        pipeline._save(pipeline.bdir(bid,'全文.json'),book)
        m=json.loads(db.one('select meta from books where id=?',(bid,))[0] or '{}')
        lang=guess_lang(book)
        m.update({'类型':m.get('类型') or guess_kind(book),'导入':book.get('导入',{}),'语言':lang,'需翻译':lang!='zh'})
        cv=importer.cover(data,filename)            # 书自带的封面（epub 标的封面图、扫描版 PDF 第一页）；没有就书架按书名生成
        if cv: open(pipeline.bdir(bid,'cover.jpg'),'wb').write(cv); m['cover']=1
        db.run("update books set title=?,author=?,status='ready',chars=?,chapters=?,meta=? where id=?",
               (m.get('书名') or book['书'],m.get('作者') or book.get('导入',{}).get('作者',''),book['导入']['字数'],book['导入']['章数'],json.dumps(m,ensure_ascii=False),bid))
        if pipeline.generation_on(): pipeline.enqueue(bid)
    except importer.ImportError_ as e:
        db.run("update books set status='failed',meta=json_set(meta,'$.err',?) where id=?",(str(e),bid))
    except Exception as e:
        db.run("update books set status='failed',meta=json_set(meta,'$.err',?) where id=?",('导入时程序出错：'+repr(e)[:200],bid))

def guess_lang(book):
    """正文是什么语言：zh / en / de / fr（外文书要先翻译成中文）"""
    txt=' '.join(s['文'] for c in book['章'][:4] for s in c['段'][:40])[:30000]
    if not txt: return 'zh'
    cjk=len(re.findall(r'[\u4e00-\u9fff]',txt))
    if cjk>len(txt)*0.15: return 'zh'
    w=re.findall(r'[a-zäöüßéèàçê]+',txt.lower()); n=max(1,len(w))
    score={l:sum(1 for x in w if x in ws)/n for l,ws in (('en',{'the','and','of','to','was','he','that','his'}),('de',{'der','die','und','das','ist','nicht','ich','zu'}),('fr',{'le','la','et','les','des','est','une','que'}))}
    return max(score,key=score.get)
def guess_kind(book):
    """粗分类型，决定用哪套不剧透规则：小说 / 非虚构。拿不准按小说（规则更严）"""
    txt=''.join(s['文'] for c in book['章'][:3] for s in c['段'])[:20000]
    talk=txt.count('“')+txt.count('"')+txt.count('「')
    return '小说' if talk>len(txt)/400 else '非虚构'

# ---------------- 查询 ----------------
def get(bid):
    r=db.rows('select * from books where id=?',(bid,))
    if not r: return None
    r=r[0]; r['meta']=json.loads(r['meta'] or '{}'); return r
def visible(bid,device):
    """精编书谁都能打开；自己的书（导入的、下载的）只有自己能打开"""
    r=get(bid)
    return r if r and (r['kind']!='import' or r['owner']==device) else None
def shelf(device):
    rows=db.rows("select * from books where kind='builtin' or (kind='import' and owner=?) order by kind='builtin' desc, t",(device,))
    out=[]
    for r in rows:
        m=json.loads(r['meta'] or '{}')
        x={'id':r['id'],'title':r['title'],'author':r['author'],'nat':r['nat'],'kind':r['kind'],'status':r['status'],'chars':r['chars'],'chapters':r['chapters']}
        if r['kind']!='builtin': x['gen']=pipeline.progress(r['id']); x['err']=m.get('err','')
        out.append(x)
    return out
def data(bid):
    """阅读器要的整本书数据"""
    r=get(bid)
    if not r: return None
    if r['kind']=='builtin': return builtin_data().get(bid)
    if r['status'] in ('parsing','failed') : return None
    return pipeline.packed(bid)
def delete(bid,device):
    r=get(bid)
    if not r or r['kind']!='import' or r['owner']!=device: return False
    import shutil
    db.run('delete from jobs where book=?',(bid,)); db.run('delete from books where id=?',(bid,)); db.run('delete from progress where book=?',(bid,))
    shutil.rmtree(os.path.join(config.DATA,'books',bid),ignore_errors=True); return True
