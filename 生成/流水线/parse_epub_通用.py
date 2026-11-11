"""第 1 步（通用）：EPUB → 全文.json，并按统一规则给段落分类型。

每本书只写一份很短的配置（哪些文件是正文、EPUB 的样式名各代表什么、修字表），
段落类型和"哪些折叠"由下面的通用规则决定，不按书单独设计。

段落类型（"类"字段，不写 = 正文）：
  提要    章首列出的本章小节标题（如"●天津教案 ●法越之役"），合成一段
  小标题  正文中间的小节标题
  引文    引用的原文（条约、诏书、书信、诗、对联、表格行……），EPUB 里通常是缩进或另一种字体
  文件    连续的引文合计 ≥ FOLD_CHARS 字且 ≥ FOLD_PARAS 段 → 阅读器里默认折叠（条约全文、长诏书）
  图注等出版社加的东西：直接丢掉
  表格图：配置"表格"指向一份转录（{图文件名:{rows:[[…]]}}），接在前一段末尾，写成 ⟦表:a|b;c|d⟧（第一行是表头；没有表头的写 ⟦表:!…⟧）
  排版折断的引文行：自动接回

解释单元：正文按 MIN～MAX 字分组；提要、小标题各自一个单元；一整份文件 = 一个单元；短引文并进前后正文。

用法：python3 -I parse_epub_通用.py <配置.json> <解压后的 EPUB 目录> <输出目录>
配置：{"书":"李鸿章传","语言":"zh"（西文书写 "en"/"de"…，影响换行和空格）,"章":[{"文件":"text00003.html","章":0,"标题":"序例"},…],
      "样式":{"suojin":"引文","CN_Kindle_Hei":"提要","kindle-cn-picture-txt-right":"丢弃"},
      "行内图":{"Image00003.jpg":"驩"},"修字":[["之—举","之一举"]],"删":["(今译为俾斯麦)"]}
"""
import json,sys,re,html,os
cfg=json.load(open(sys.argv[1],encoding='utf-8')); src=sys.argv[2]; out=sys.argv[3]
MIN,MAX=220,520; FOLD_CHARS,FOLD_PARAS=200,3
TBH={k:v.get('表头',True) for k,v in (json.load(open(cfg['表格'],encoding='utf-8')) if cfg.get('表格') else {}).items() if isinstance(v,dict)}
TBL={k:v['rows'] if isinstance(v,dict) else v for k,v in (json.load(open(cfg['表格'],encoding='utf-8')) if cfg.get('表格') else {}).items()}
EN=cfg.get('语言','zh')!='zh'
STY=cfg.get('样式',{}); IMG=cfg.get('行内图',{}); FIX=cfg.get('修字',[]); DEL=cfg.get('删',[])
def find(fn):
    for r,_,fs in os.walk(src):
        if fn in fs: return os.path.join(r,fn)
    raise SystemExit('找不到 '+fn)
def clean(inner):
    inner=re.sub(r'<img[^>]*src="([^"]+)"[^>]*/?>',lambda m:IMG.get(os.path.basename(m.group(1)),''),inner)
    t=html.unescape(re.sub(r'<[^>]+>','',inner)).replace('\xa0',' ')
    t=re.sub(r'\s*\n\s*',' ' if EN else '',t).strip()   # 西文：换行 = 空格；中文：换行直接去掉
    for a in DEL: t=t.replace(a,'')
    for a,b in FIX: t=t.replace(a,b)
    t=re.sub(r' {2,}',' ' if EN else '　',t)   # 中文：条款号后的多个空格 → 一个全角空格
    return t.strip()
res={"书":cfg['书'],"章":[]}
for c in cfg['章']:
    body=re.split(r'<body[^>]*>',open(find(c['文件']),encoding='utf-8').read(),maxsplit=1)[1]
    raw=[]
    for tag,attr,inner,img in re.findall(r'<(p|h\d)([^>]*)>(.*?)</\1>|<img[^>]*src="([^"]+)"',body,re.S):
        if img:                                           # 独立的图：表格图 → 接在前一段后面（不新增段，编号不变）
            rows=TBL.get(os.path.basename(img))
            if rows and raw: raw[-1][1]+='\n⟦表:'+('' if TBH.get(os.path.basename(img),True) else '!')+';'.join('|'.join(r) for r in rows)+'⟧'
            continue
        if tag[0]=='h': continue                          # 章名另给
        cl=(re.search(r'class="([^"]*)"',attr) or [None,''])[1].split()
        ty=next((STY[x] for x in cl if x in STY),None)
        if ty=='丢弃': continue
        t=clean(inner)
        if not t: continue
        raw.append([ty,t])
    # 排版折断的引文行（表格一行被拆成两段）：上一段不以标点结尾、这一段是很短的引文 → 接回去
    k=1
    while k<len(raw):
        if raw[k][0]=='引文' and raw[k-1][0]=='引文' and len(raw[k][1])<=12 and not re.search(r'[。！？；：，、”）)」』]$',raw[k-1][1]) and not re.match(r'(第|[一二三四五六七八九十]+、)',raw[k][1]):
            raw[k-1][1]+=raw[k][1]; del raw[k]
        else: k+=1
    # 章首连续的"提要"合成一段
    segs=[]; head=[t for ty,t in raw[:next((i for i,(ty,_) in enumerate(raw) if ty!='提要'),len(raw))]]
    rest=raw[len(head):]
    if head: segs.append({"文":'　'.join(head),"类":"提要"})
    for ty,t in rest:
        if ty=='提要': ty='小标题'
        segs.append({"文":t,**({"类":ty} if ty else {})})
    # 连续引文够长 → 文件（折叠）
    i=0
    while i<len(segs):
        if segs[i].get('类')!='引文': i+=1; continue
        j=i
        while j<len(segs) and segs[j].get('类')=='引文': j+=1
        if j-i>=FOLD_PARAS and sum(len(s['文']) for s in segs[i:j])>=FOLD_CHARS:
            for s in segs[i:j]: s['类']='文件'
        i=j
    n=c['章']
    for k,s in enumerate(segs): s['id']=f"{n}.{k+1}"
    segs=[{"id":s['id'],"文":s['文'],**({"类":s['类']} if s.get('类') else {})} for s in segs]
    # 解释单元
    units=[]; cur=[]; L=0
    def flush():
        global cur,L
        if cur: units.append(cur); cur=[]; L=0
    k=0
    while k<len(segs):
        s=segs[k]; ty=s.get('类')
        if ty in ('提要','小标题'): flush(); units.append([s['id']]); k+=1; continue
        if ty=='文件':
            flush(); j=k
            while j<len(segs) and segs[j].get('类')=='文件': j+=1
            units.append([x['id'] for x in segs[k:j]]); k=j; continue
        if cur and L+len(s['文'])>MAX and ty!='引文': flush()
        cur.append(s['id']); L+=len(s['文'])
        if L>=MIN: flush()
        k+=1
    if cur:
        last=units[-1] if units else None
        lt=next((x.get('类') for x in segs if last and x['id']==last[-1]),None)
        if last and L<MIN//2 and lt not in ('提要','小标题','文件'): last+=cur
        else: units.append(cur)
    res['章'].append({"章":n,"标题":c['标题'],"段":segs,"单元":[[u[0],u[-1]] for u in units]})
os.makedirs(out,exist_ok=True)
json.dump(res,open(f'{out}/全文.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
from collections import Counter
for c in res['章']:
    ct=Counter(s.get('类','正文') for s in c['段'])
    print(c['章'],c['标题'],len(c['段']),'段',len(c['单元']),'单元',sum(len(s['文']) for s in c['段']),'字',dict(ct))
print('合计',sum(len(s['文']) for c in res['章'] for s in c['段']),'字')
