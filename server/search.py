"""找书：读者搜，从公版书网站下载到自己的书架，我们再处理（2026-10-27 用户定：书库只做搜索 + 热门搜索，我们不存书）。

流程：读者在"找书"里搜书名或作者 → 这里同时去两个来源搜 → 列出结果（书名、作者、语言、来源）→
      读者点"下载到书架" → 服务器按来源和编号自己拼下载地址去下载（不接受读者传来的任意网址）→ 走导入 → 生成解释。

来源（都只有公版或自由授权的书）：
  gutenberg   古登堡计划：用 Gutendex（古登堡书目的公开查询接口，https://gutendex.com）搜，
              下载 https://www.gutenberg.org/ebooks/<编号>.epub3.images
  wikisource  维基文库（中文）：用 MediaWiki 搜索接口搜书名，下载用维基文库官方的导出工具 ws-export（epub）
地址都能用环境变量改（FUBI_GUTENDEX / FUBI_WIKISOURCE_API / FUBI_WSEXPORT / FUBI_GUT_MIRRORS），比如自己架 Gutendex 镜像。

多个下载源（2026-10-27 用户：以免某个下载不了）：
  ① 同一本书在两个来源都有（古登堡也收了不少中文古籍），搜索结果合成一条，下载时按顺序试；
  ② 每个来源自己也有几条路：古登堡试 epub3 → epub → 纯文本，主站不行再试镜像；维基文库试 epub3 → epub2 → 纯文本。
  哪一条成功就用哪一条，都不行才告诉读者"暂时下载不了"。
书的信息（2026-10-27 用户）：点搜索结果看这本书的信息和介绍（不显示原文），下面列出几个下载来源，读者可以选一个下载。
  介绍：hot.json 里有这本书就用那里的中文一句话简介；古登堡另有英文内容提要（Gutendex 的 summaries），作为"内容提要"附上。
（preview() 能取书的开头几段，接口还在，阅读器现在不用。）

公版判断：中国大陆著作权保护期 = 作者终生 + 50 年。古登堡结果带作者去世年份：
  去世满 50 年 → 可以下载；没满（古登堡按美国法收的，比如 1980 年去世的作者）→ 列出来但不能下载，写明原因；
  不知道去世年份 → 可以下载，标"作者年份不详"。维基文库只收公版和自由授权作品，都能下载。
热门搜索：没有搜索记录时用 hot.json；有了以后按最近 30 天的真实搜索次数排（searches 表）。
"""
import os,json,time,re,urllib.request,urllib.parse,threading,hashlib
import config,db

GUTENDEX=os.environ.get('FUBI_GUTENDEX','https://gutendex.com/books')
WS_API=os.environ.get('FUBI_WIKISOURCE_API','https://zh.wikisource.org/w/api.php')
WS_EXPORT=os.environ.get('FUBI_WSEXPORT','https://ws-export.wmcloud.org/')
GUT_MIRRORS=[x.strip() for x in os.environ.get('FUBI_GUT_MIRRORS','https://www.gutenberg.org,https://gutenberg.pglaf.org,https://aleph.gutenberg.org').split(',') if x.strip()]
GUT_PATHS=['/ebooks/{id}.epub3.images','/ebooks/{id}.epub.images','/cache/epub/{id}/pg{id}-images-3.epub','/cache/epub/{id}/pg{id}.txt']   # 镜像站多半只有 /cache/ 路径
WS_FORMATS=['epub-3','epub-2','txt']
UA='fubi-reader/0.2 (public-domain book search)'
LANG_NAME={'en':'英文','zh':'中文','de':'德文','fr':'法文','es':'西班牙文','it':'意大利文','ru':'俄文','ja':'日文','la':'拉丁文','pt':'葡萄牙文','nl':'荷兰文'}
CACHE_S=24*3600
opener=None                       # 测试时换成假的网络

class SearchError(Exception): pass

def _year(): return int(time.strftime('%Y'))
def pd_ok(death):
    """中国大陆：作者去世满 50 年（到第 50 年年底）"""
    return death is None or death<=_year()-51

def _get(url,timeout=20):
    req=urllib.request.Request(url,headers={'User-Agent':UA,'Accept':'application/json'})
    with (opener or urllib.request.urlopen)(req,timeout=timeout) as r: return r.read()

# ---------------- 热门搜索 ----------------
def _hot_file():
    p=os.path.join(os.path.dirname(os.path.abspath(__file__)),'hot.json')
    with open(p,encoding='utf-8') as f: return json.load(f)['词']
def hot(n=12):
    """最近 30 天搜得多的在前（至少被不同设备搜过 2 次才算），不够的用预设补"""
    real=[r[0] for r in db.all("select q from searches where t>? group by q having count(distinct device)>=2 order by count(*) desc limit ?",(time.time()-30*86400,n))]
    out=list(real)
    for h in _hot_file():
        if len(out)>=n: break
        if h['词'] not in out: out.append(h['词'])
    return out[:n]
def _alias(q):
    """读者搜中文名时，古登堡要用原名搜（傲慢与偏见 → Pride and Prejudice）"""
    nq=_n(q)
    return [h['原名'] for h in _hot_file() if h.get('原名') and (_n(h['词'])==nq or _n(h.get('作者',''))==nq)]
def _zh_title(orig):
    no=_n(orig)
    return next((h['词'] for h in _hot_file() if h.get('原名') and _n(h['原名'])==no),'')
def _n(s): return re.sub(r'[\s·・.\-—_，,、：:（）()《》“”"\'!！?？]+','',str(s or '')).lower()

# ---------------- 搜索 ----------------
_cache={}; _clock=threading.Lock()
def search(q,device=''):
    q=re.sub(r'\s+',' ',str(q or '')).strip()[:60]
    if not q: return {'q':'','results':[],'errors':[]}
    if device: db.run('insert into searches(q,device,t) values(?,?,?)',(q,device,time.time()))
    with _clock:
        c=_cache.get(q)
        if c and time.time()-c[0]<CACHE_S: return c[1]
    res=[]; errs=[]
    terms=list(dict.fromkeys([q,_s2t(q)]+[a for a in _alias(q) if _n(a)!=_n(q)]))   # 古登堡的中文书是繁体书名
    for t in terms:
        try: res+=gutenberg(t)
        except Exception as e: errs.append('古登堡暂时连不上')
    try: res+=wikisource(q)
    except Exception as e: errs.append('维基文库暂时连不上')
    seen=set(); uniq=[]
    for r in res:
        k=(r['来源'],r['编号'])
        if k in seen: continue
        seen.add(k); uniq.append(r)
    out=[_enrich(r) for r in merge_sources(uniq)]
    nq=_n(q)
    out.sort(key=lambda r:(not r['可下载'],-(_n(r['书名'])==nq or _n(r.get('中文名',''))==nq),-(nq in _n(r['书名'])+_n(r.get('中文名',''))),r['来源']!='wikisource' if re.search(r'[一-鿿]',q) else r['来源']=='wikisource',-r.get('热度',0)))
    data={'q':q,'results':out[:30],'errors':sorted(set(errs))}
    if not errs:
        with _clock: _cache[q]=(time.time(),data)
    return data

def gutenberg(q):
    d=json.loads(_get(GUTENDEX+'?'+urllib.parse.urlencode({'search':q})))
    out=[]
    for b in d.get('results',[])[:20]:
        if b.get('media_type','Text')!='Text': continue
        au=(b.get('authors') or [{}])[0]; death=au.get('death_year')
        name=au.get('name','')
        if ', ' in name: last,first=name.split(', ',1); name=f'{first} {last}'
        langs=b.get('languages') or ['en']; lang=langs[0]
        ok=pd_ok(death)
        out.append({'来源':'gutenberg','编号':str(b['id']),'书名':b.get('title','').split(';')[0].split('\n')[0][:120],'中文名':_zh_title(b.get('title','')),
                    '生卒':(f"{au.get('birth_year') or '?'}—{death}" if death else ''),'主题':[re.sub(r'\s*--.*','',x) for x in (b.get('subjects') or [])][:4],'简介':((b.get('summaries') or [''])[0] or '')[:400],
                    '作者':re.sub(r'\s*\(.*?\)','',name),'去世':death,'语言':lang,'语言名':LANG_NAME.get(lang,lang),'热度':b.get('download_count',0),
                    '可下载':ok,'说明':'' if ok else f'作者 {death} 年去世，在中国大陆还没进入公版（要到 {death+51} 年）','需翻译':lang!='zh',
                    '链接':f'https://www.gutenberg.org/ebooks/{b["id"]}'})
    return out

def _s2t(q):
    try:
        import opencc; return opencc.OpenCC('s2t').convert(q)
    except Exception: return q
def wikisource(q):
    """维基文库：搜书名（作品的主页面，不要"书名/第一回"这样的子页面），简体也能搜到繁体页面"""
    out=[]; seen=set()
    for t in dict.fromkeys([q,_s2t(q)]):
        d=json.loads(_get(WS_API+'?'+urllib.parse.urlencode({'action':'query','list':'search','srsearch':t,'srnamespace':0,'srlimit':20,'format':'json','srprop':'snippet|wordcount'})))
        for r in d.get('query',{}).get('search',[]):
            title=r['title']
            if '/' in title or title in seen: continue
            if re.search(r'(消歧义|消歧義|列表|目录|目錄)',title): continue
            seen.add(title)
            snip=re.sub(r'<[^>]+>','',r.get('snippet',''))[:60]
            out.append({'来源':'wikisource','编号':title,'书名':title,'中文名':'','作者':'','去世':None,'语言':'zh','语言名':'中文','热度':r.get('wordcount',0),
                        '可下载':True,'说明':'','需翻译':False,'摘要':snip,'链接':'https://zh.wikisource.org/wiki/'+urllib.parse.quote(title)})
    return out[:12]

def _simp(t):
    try:
        import importer; c=importer._t2s(); return c(t) if c else t
    except Exception: return t
def merge_sources(rows):
    """同一本书（简体书名相同、语言相同、作者不冲突）在几个来源都有 → 合成一条，"源"里按优先顺序列出：
    中文书维基文库在前（排版、校对通常更好），外文书古登堡在前"""
    out=[]; idx={}
    for r in rows:
        r=dict(r); r['源']=[{'来源':r['来源'],'编号':r['编号']}]
        k=(_n(_simp(r['书名'])),r['语言'])
        j=idx.get(k)
        if j is not None and r['可下载']==out[j]['可下载'] and (not r['作者'] or not out[j]['作者'] or _n(r['作者'])==_n(out[j]['作者']) or r['语言']=='zh'):
            o=out[j]; o['源'].append(r['源'][0])
            for f in ('作者','生卒','简介','摘要'):
                if not o.get(f) and r.get(f): o[f]=r[f]
            o['主题']=o.get('主题') or r.get('主题') or []
            continue
        idx[k]=len(out); out.append(r)
    for o in out:
        pri=(lambda x:0 if x['来源']=='wikisource' else 1) if o['语言']=='zh' else (lambda x:0 if x['来源']=='gutenberg' else 1)
        o['源'].sort(key=pri); o['来源'],o['编号']=o['源'][0]['来源'],o['源'][0]['编号']
        o['来源名']='、'.join(dict.fromkeys('古登堡计划' if x['来源']=='gutenberg' else '维基文库' for x in o['源']))
    return out

SRC_NAME={'gutenberg':'古登堡计划','wikisource':'维基文库'}
def _link(src,ref): return f'https://www.gutenberg.org/ebooks/{ref}' if src=='gutenberg' else 'https://zh.wikisource.org/wiki/'+urllib.parse.quote(str(ref))
def _enrich(r):
    """补上书的信息：中文简介、作者国籍（来自 hot.json）；每个来源的名字、格式说明、网页地址"""
    keys={_n(r.get('中文名')),_n(_simp(r['书名'])),_n(r['书名'])}-{''}
    h=next((x for x in _hot_file() if _n(x['词']) in keys or (x.get('原名') and _n(x['原名']) in keys)),None)
    if r.get('简介') and r['语言']!='zh': r['内容提要']=r['简介']     # 古登堡的英文内容提要
    r['简介']=(h or {}).get('简介') or (r.get('简介') if r['语言']=='zh' else '') or ''
    if h:
        r['中文名']=r.get('中文名') or (h['词'] if r['语言']!='zh' else '')
        r['国籍']=h.get('国籍',''); r['作者中文']=h.get('作者','')
        if h.get('去世') is not None and not r.get('去世'): r['去世']=h['去世']
    for x in r['源']:
        x['名']=SRC_NAME[x['来源']]; x['链接']=_link(x['来源'],x['编号'])
        x['说明']='epub，主站不行时自动换镜像站或纯文本' if x['来源']=='gutenberg' else 'epub，导出失败时自动换纯文本'
    return r

# ---------------- 下载 ----------------
def candidates(source,ref):
    """一本书的所有下载地址（按顺序试）。只按来源和编号拼地址——不接受读者传来的任意网址（防止被当成跳板去访问别的地方）。
    返回 [(地址, 文件名)]，文件名的扩展名决定导入时按什么格式解析"""
    if source=='gutenberg':
        if not re.fullmatch(r'\d{1,6}',str(ref)): raise SearchError('编号不对')
        i=int(ref); out=[]
        for m in GUT_MIRRORS:
            for pth in GUT_PATHS:
                if 'www.gutenberg.org' not in m and pth.startswith('/ebooks/'): continue
                out.append((m.rstrip('/')+pth.format(id=i),f'gutenberg_{i}'+('.txt' if pth.endswith('.txt') else '.epub')))
        return out
    if source=='wikisource':
        ref=str(ref).strip()
        if not ref or len(ref)>120 or re.search(r'[<>\[\]{}|#]',ref): raise SearchError('书名不对')
        base=re.sub(r'[\\/:*?"<>|]','_',ref)
        return [(WS_EXPORT+'?'+urllib.parse.urlencode({'lang':'zh','page':ref,'format':f,'fonts':''}),base+('.txt' if f=='txt' else '.epub')) for f in WS_FORMATS]
    raise SearchError('不认识的来源')
def download_url(source,ref): return candidates(source,ref)[0]

def _looks_ok(data,fname):
    if fname.endswith('.epub'): return data[:2]==b'PK'
    head=data[:2000].lower()
    return len(data)>2000 and b'<html' not in head and b'<!doctype' not in head   # 纯文本：不是一张网页（错误页、验证页）
def fetch(source,ref):
    """下载一本书：这个来源的几条路按顺序试，成功一条就停。同一本书 30 天内只真的下载一次，多个读者共用缓存"""
    key=hashlib.sha1(f'{source}|{ref}'.encode()).hexdigest()[:16]
    for ext in ('.epub','.txt'):
        p=config.path('cache',key+ext)
        if os.path.exists(p) and time.time()-os.path.getmtime(p)<30*86400:
            with open(p,'rb') as f: return f.read(),candidates(source,ref)[0][1].rsplit('.',1)[0]+ext
    last=None; notbook=False
    for url,fname in candidates(source,ref):
        try:
            req=urllib.request.Request(url,headers={'User-Agent':UA})
            with (opener or urllib.request.urlopen)(req,timeout=120) as r: data=r.read(config.MAX_UPLOAD+1)
        except urllib.error.HTTPError as e: last='没有这本'; continue
        except Exception as e: last='连不上'; continue
        if len(data)>config.MAX_UPLOAD: raise SearchError('该书籍文件过大，无法下载')
        if not _looks_ok(data,fname): notbook=True; continue
        p=config.path('cache',key+'.'+fname.rsplit('.',1)[1]); tmp=p+'.tmp'; open(tmp,'wb').write(data); os.replace(tmp,p)
        return data,fname
    if notbook: raise SearchError('来源网站未返回电子书文件，请稍后重试')
    if last=='没有这本': raise SearchError('来源网站上找不到这本书的文件')
    raise OSError('来源网站暂时无法连接')
def fetch_any(sources):
    """同一本书的几个来源按顺序试：[{"来源":…,"编号":…}]。返回 (数据, 文件名, 用上的那个来源)"""
    err=None
    for x in sources[:4]:
        try: data,fname=fetch(x['来源'],x['编号']); return data,fname,x
        except (SearchError,OSError) as e: err=e
    raise err or SearchError('无可用来源')

# ---------------- 预览 ----------------
def preview(sources):
    """下载（或用缓存）→ 解析 → 书名、作者、章数、字数、目录前几章、开头几段（跳过献词、目录这类）"""
    import importer
    data,fname,src=fetch_any(sources)
    pk=hashlib.sha1(f"{src['来源']}|{src['编号']}".encode()).hexdigest()[:16]
    cp=config.path('cache',pk+'.preview.json')
    if os.path.exists(cp) and os.path.getmtime(cp)>=time.time()-30*86400:
        with open(cp,encoding='utf-8') as f: return json.load(f)
    book=importer.import_book(data,fname)
    chs=book['章']; first=next((c for c in chs if sum(len(x['文']) for x in c['段'])>1500),chs[0])
    paras=[]; n=0
    for x in first['段']:
        if n>=900: break
        paras.append(x['文'][:600]); n+=len(x['文'])
    out={'书名':book['书'],'作者':book.get('导入',{}).get('作者',''),'章数':len(chs),'字数':book['导入']['字数'],
         '目录':[c['标题'] for c in chs[:12]],'开头章':first['标题'],'开头':paras,'来源':src['来源'],'编号':src['编号']}
    with open(cp,'w',encoding='utf-8') as f: json.dump(out,f,ensure_ascii=False)
    return out
