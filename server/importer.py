"""导入：读者上传的书 → 全文.json（和第一阶段流水线同一个格式：{"书","章":[{"章","标题","段":[{"id","文"}],"单元"}]}）。

支持的格式（按常见程度）：
  epub   书自带的目录分章；不需要每本书写配置
  txt    自动识别编码（UTF-8 / GBK / GB18030 / Big5 / UTF-16）；按"第X章/回/篇/节/卷、Chapter X、序、后记……"分章，识别不出就按字数切
  pdf    文字版：逐页取字，去掉页眉页脚和页码、把断行接回去、按标题分章；扫描版（取不出字）：OCR（需要服务器装 tesseract 和中文语言包）
  docx   Word：按"标题"样式分章，没有就按文字规则
  doc / rtf / odt / wps   先用 LibreOffice 转成 docx 再导入（服务器装了 LibreOffice 才有；Docker 镜像里会装）
  html / htm / md   网页、Markdown：按 h1/h2 或 # 分章
  mobi / azw3 / fb2   先用 calibre 的 ebook-convert 转成 epub 再导入（服务器装了 calibre 才有；Docker 镜像里会装）
繁体书自动转简体（可关）；段落太长的按句号切开（阅读器一段不宜超过约 1500 字）。

安全：文件大小有上限；epub/docx 是压缩包，解压后的总大小也有上限（防"压缩炸弹"）；不用上传的文件名拼路径；不执行文件里的任何脚本。
"""
import os,re,io,json,zipfile,html,subprocess,tempfile,shutil
from html.parser import HTMLParser

MAX_UNZIP=300*1024*1024       # 解压后最多 300MB
PARA_MAX=1500                 # 一段最长多少字，超过按句号切
UNIT_MIN,UNIT_MAX=220,520     # 解释单元的字数（和流水线一致）
CHUNK=6000                    # 没有章节标题时，每"章"大约多少字

class ImportError_(Exception): pass

# ================= 通用：分章、分段、编号 =================
CH_PAT=re.compile(r'^\s*(?:'
    r'第\s*[零〇○一二三四五六七八九十百千两\d]+\s*[章回篇节卷部集折幕]'          # 第三章、第十二回
    r'|[序跋]\s*$|序[言章幕]|楔子|引子|前言|后记|尾声|附录|自序|代序|跋'         # 序、楔子、后记
    r'|卷\s*[零〇○一二三四五六七八九十百千\d]+'
    r'|(?:chapter|book|part)\s+(?:[ivxlcdm]+|\d+)\b'                        # Chapter 12 / Book II
    r'|(?:prologue|epilogue|preface|introduction)\b'
    r')',re.I)
def is_heading(line):
    s=line.strip()
    return bool(s) and len(s)<=40 and bool(CH_PAT.match(s)) and not re.search(r'[。！？；，][^」』”]*\S',s[:-1] if len(s)>1 else s)

def split_long(t):
    if len(t)<=PARA_MAX: return [t]
    out=[]; cur=''
    for sent in re.split(r'(?<=[。！？!?」』”])|(?<=[.;:"’”])\s+(?=[A-Z“"‘(])',t):
        if len(cur)+len(sent)>PARA_MAX and cur: out.append(cur); cur=''
        cur+=sent
    if cur: out.append(cur)
    res=[]
    for x in out:   # 一句就超长（没有句号的长段）：在逗号、空格处硬切
        while len(x)>PARA_MAX+300:
            k=max(x.rfind(c,0,PARA_MAX) for c in '，,；; ')
            k=k+1 if k>PARA_MAX//2 else PARA_MAX
            res.append(x[:k].strip()); x=x[k:].strip()
        if x: res.append(x)
    return res

def units_of(segs):
    units=[]; cur=[]; L=0
    for s in segs:
        if cur and L+len(s['文'])>UNIT_MAX: units.append(cur); cur=[]; L=0
        cur.append(s['id']); L+=len(s['文'])
        if L>=UNIT_MIN: units.append(cur); cur=[]; L=0
    if cur:
        if units and L<UNIT_MIN//2: units[-1]+=cur
        else: units.append(cur)
    return [[u[0],u[-1]] for u in units]

SOFT,BIG=15000,40000          # 一章超过 SOFT 字就试着找漏掉的短标题；超过 BIG 还找不到就按字数切
TINY=80                       # 一章不到这么多字（"第一部"、"PART ONE" 这种只有标题的）并到下一章开头
def _short_title(p,prev):
    """独占一行的短标题（"社戏""Chapter Two"）：≤12 字、没有标点、上一段以句末标点结尾、不是纯数字序号"""
    s=p.strip()
    return 0<len(s)<=12 and not re.search(r'[，,。．！？!?；;：:︰、“”"‘’（）()…—]',s) and not re.fullmatch(r'[\d零〇一二三四五六七八九十百ivxlcdmIVXLCDM\s.、]+',s) and bool(re.search(r'[。！？!?」』”…）)]$',prev or '。'))
def _resplit(t,paras):
    L=sum(len(x) for x in paras)
    if L<=SOFT: return [(t,paras)]
    out=[]; cur_t=t; cur=[]
    for i,p in enumerate(paras):
        if cur and sum(len(x) for x in cur)>1500 and _short_title(p,cur[-1]) and i+1<len(paras) and len(paras[i+1])>30:
            out.append((cur_t,cur)); cur_t=p.strip(); cur=[]
        else: cur.append(p)
    out.append((cur_t,cur))
    m=[]
    for x in out:                                   # 太短的一段（多半是误认的标题）并回上一章
        if m and sum(len(z) for z in x[1])<1500: m[-1]=(m[-1][0],m[-1][1]+[x[0]]+x[1])
        else: m.append(x)
    out=m
    if len(out)>=2: return [y for x in out for y in ([x] if sum(len(z) for z in x[1])<=BIG else _resplit_size(*x))]
    if L<=BIG: return [(t,paras)]
    return _resplit_size(t,paras)
def _resplit_size(t,paras):
    out=[]; cur=[]; L=0; k=1                       # 找不到标题：按字数切成"（一）（二）"
    for p in paras:
        cur.append(p); L+=len(p)
        if L>=CHUNK*2: out.append((f'{t}（{k}）',cur)); cur=[]; L=0; k+=1
    if cur: out.append((f'{t}（{k}）' if k>1 else t,cur))
    return out

def finish(title,chapters,meta=None):
    """chapters: [(标题, [段落文字…]), …] → 全文.json 格式；空章去掉、超长章再细分、编号从 1 起"""
    chs=[]; n=0
    chapters=[x for t,ps in chapters for x in _resplit(t,ps)]
    merged=[]; carry=[]
    for i,(t,ps) in enumerate(chapters):   # 只有标题的"部/卷/PART"：并到下一章开头
        if sum(len(x) for x in ps)<TINY and i+1<len(chapters): carry+=([t] if t and t!='开篇' else [])+ps; continue
        merged.append((t,carry+ps)); carry=[]
    chapters=merged
    for t,paras in chapters:
        ps=[p for x in paras for p in split_long(re.sub(r'\s+',' ',x).strip()) if p.strip()]
        if not ps: continue
        n+=1
        segs=[{"id":f"{n}.{k+1}","文":p} for k,p in enumerate(ps)]
        chs.append({"章":n,"标题":(t or f'第{n}章').strip()[:60],"段":segs,"单元":units_of(segs)})
    if not chs: raise ImportError_('未能读取到正文。若为扫描版 PDF，需要服务器开启文字识别。')
    return {"书":title,"章":chs,**({"导入":meta} if meta else {})}

def by_headings(lines,title):
    """一串行 → 按标题分章；开头没有标题的部分叫"开篇"；整本都没有标题就按字数切"""
    chapters=[]; cur_t=None; cur=[]
    for ln in lines:
        if is_heading(ln):
            if cur or cur_t is not None: chapters.append((cur_t or '开篇',cur))
            cur_t=ln.strip(); cur=[]
        elif ln.strip(): cur.append(ln.strip())
    chapters.append((cur_t or '开篇',cur))
    chapters=[c for c in chapters if c[1]]
    if len(chapters)<=1:   # 没有章节标题：按字数切
        paras=chapters[0][1] if chapters else []
        chapters=[]; cur=[]; L=0
        for p in paras:
            cur.append(p); L+=len(p)
            if L>=CHUNK: chapters.append((f'第{len(chapters)+1}部分',cur)); cur=[]; L=0
        if cur: chapters.append((f'第{len(chapters)+1}部分',cur))
    return chapters

# ================= txt =================
def decode(b):
    for bom,enc in ((b'\xef\xbb\xbf','utf-8-sig'),(b'\xff\xfe','utf-16'),(b'\xfe\xff','utf-16')):
        if b.startswith(bom): return b.decode(enc)
    for enc in ('utf-8','gb18030','big5'):
        try: return b.decode(enc)
        except UnicodeDecodeError: pass
    try:
        import charset_normalizer; r=charset_normalizer.from_bytes(b).best()
        if r: return str(r)
    except Exception: pass
    return b.decode('utf-8','replace')

def from_txt(b,title):
    t=decode(b).replace('\r\n','\n').replace('\r','\n').replace('\u3000\u3000','\n\u3000\u3000')
    lines=t.split('\n')
    # 有的 txt 一段里硬换行（每行 30～40 字）：行尾不是标点、下一行不缩进 → 接起来
    # 段首缩进的 txt（每段以两个全角空格或空格开头）：没缩进的行都是上一段的续行
    ne=[l for l in lines if l.strip()]
    ind=sum(1 for l in ne if re.match(r'[\u3000 ]{2}|\t',l))
    if ne and 0.08<ind/len(ne)<0.7:
        joined=[]
        for ln in lines:
            s=ln.rstrip()
            if joined and joined[-1].strip() and s.strip() and not re.match(r'[\u3000 ]{2}|\t',ln) and not is_heading(s) and not is_heading(joined[-1]): joined[-1]+=s.strip()
            else: joined.append(s)
        return finish(title,by_headings(joined,title),{"格式":"txt"})
    joined=[]
    for ln in lines:
        s=ln.rstrip()
        if joined and joined[-1] and s and not is_heading(s) and not is_heading(joined[-1]) and not re.search(r'[。！？!?」』”：:…）)]$',joined[-1]) and not re.match(r'[\u3000 ]{2}',ln) and 20<=len(joined[-1])<=80:
            joined[-1]+=s.strip()
        else: joined.append(s)
    return finish(title,by_headings(joined,title),{"格式":"txt"})

# ================= html / md =================
BLOCK={'p','div','li','blockquote','h1','h2','h3','h4','h5','h6','br','tr','section','article','pre','dd','dt'}
def _join_wrapped(blocks):
    """一行一个 <p> 的硬换行文本：大多数段落不以句读结尾、长度相近 → 把没缩进的续行接到上一段"""
    ps=[t for k,t,*_ in blocks if k=='p']
    if len(ps)<20: return [(k,t) for k,t,*_ in blocks]
    noend=sum(1 for t in ps if not re.search(r'[。！？!?」』”：:…）)\]]$',t.strip()))
    if noend/len(ps)<0.4: return [(k,t) for k,t,*_ in blocks]
    out=[]
    for k,t,ind in blocks:
        if k=='p' and out and out[-1][0]=='p' and not ind and not re.search(r'[。！？!?」』”：:…）)]$',out[-1][1]): out[-1]=('p',out[-1][1]+t)
        else: out.append((k,t))
    return out
class _HTML(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True); self.out=[]; self.buf=''; self.skip=0; self.tag=None
    def handle_starttag(self,tag,a):
        if tag in ('script','style','head','nav','title'): self.skip+=1
        if tag in BLOCK: self._flush()
        if tag in ('h1','h2','h3','h4'): self.tag='h'
        elif tag=='p':
            d=dict(a); hint=(d.get('class','')+' '+d.get('style','')).lower()
            if re.search(r'(title|head|chapter|margin-top:\s*[1-9])',hint): self.tag='hint'
    def handle_endtag(self,tag):
        if tag in ('script','style','head','nav','title'): self.skip=max(0,self.skip-1)
        if tag in BLOCK: self._flush()
    def handle_data(self,d):
        if not self.skip: self.buf+=d
    def _flush(self):
        ind=bool(re.match(r'[ \u3000\xa0]{2}',self.buf.lstrip('\n')))   # 段首缩进：用来判断硬换行的续行
        t=re.sub(r'\s+',' ',self.buf).strip()
        if t: self.out.append(('h' if self.tag=='h' else 'hint' if self.tag=='hint' else 'p',t,ind))
        self.buf=''; self.tag=None
def html_blocks(s):
    p=_HTML(); p.feed(s); p._flush()
    p.out=_join_wrapped(p.out)
    # "提示是标题"的短段（带上边距、class 像标题）：没有句读、≤20 字 → 标题；否则还是正文
    return [('h' if k=='hint' and len(t)<=20 and not re.search(r'[。！？!?，,；;：:]',t) else 'p' if k=='hint' else k,t) for k,t in p.out]

def from_html(b,title):
    blocks=html_blocks(decode(b))
    return finish(title,_blocks_to_chapters(blocks),{"格式":"html"})
def _blocks_to_chapters(blocks,min_heads=2,only_chapter_heads=False):
    from collections import Counter
    # ① 太长、带句读的"标题"是正文（有的书用 h4 写一整句）② 同一个标题出现 ≥3 次是页眉（PDF、网页）
    blocks=[('p' if k=='h' and (len(t)>40 or re.search(r'[。！？!?；;][^」』”]',t) or (len(t)>16 and re.search(r'[，,、]',t)) or re.search(r'[：:︰]$',t)) else k,t) for k,t in blocks]
    rep={t for t,n in Counter(t for k,t in blocks if k=='h').items() if n>=3}
    blocks=[(k,t) for k,t in blocks if not (k=='h' and t in rep)]
    if only_chapter_heads: blocks=[('h' if k=='h' and is_heading(t) else 'p' if k=='h' else k,t) for k,t in blocks]
    elif sum(1 for k,_ in blocks if k=='h')>=min_heads: blocks=[('h' if k=='p' and len(t)<=30 and is_heading(t) else k,t) for k,t in blocks]
    merged=[]
    for k,t in blocks:   # 连着的两个标题（"Chapter 1." + "Mr. Sherlock Holmes"、"第一回" + 回目）合成一个
        if k=='h' and merged and merged[-1][0]=='h' and len(merged[-1][1])+len(t)<=60: merged[-1]=('h',merged[-1][1].rstrip('.。 ')+'　'+t); continue
        if k=='p' and merged and merged[-1][0]=='h' and len(t)<=30 and not re.search(r'[。！？!?，,；;]',t) and '　' not in merged[-1][1] and re.fullmatch(r'(第.{1,6}[章回篇节卷]|chapter\s+\w+\.?|[ivxlcdm]+\.?|\d+\.?)',merged[-1][1].strip(),re.I): merged[-1]=('h',merged[-1][1].rstrip('.。 ')+'　'+t); continue
        merged.append((k,t))
    blocks=merged
    if sum(1 for k,_ in blocks if k=='h')>=min_heads:
        chapters=[]; cur_t=None; cur=[]
        for k,t in blocks:
            if k=='h':
                if cur: chapters.append((cur_t or '开篇',cur))
                cur_t=t; cur=[]
            else: cur.append(t)
        if cur: chapters.append((cur_t or '开篇',cur))
        return chapters
    if only_chapter_heads: return [(None,[t for _,t in blocks])]
    return by_headings([t for _,t in blocks],'')

def from_md(b,title):
    lines=decode(b).split('\n'); blocks=[]; buf=[]
    for ln in lines+['']:
        m=re.match(r'^(#{1,3})\s+(.*)',ln)
        if m or not ln.strip():
            if buf: blocks.append(('p',' '.join(buf))); buf=[]
            if m: blocks.append(('h',m.group(2).strip()))
        else: buf.append(re.sub(r'[*_`>]+','',ln.strip()))
    return finish(title,_blocks_to_chapters(blocks),{"格式":"md"})

# ================= 去掉"不是书的内容"（通用：古登堡、维基文库、出版社） =================
BOILER=[
    (re.compile(r'(\*\*\*\s*START OF (THE|THIS) PROJECT GUTENBERG|^\s*START OF THE PROJECT GUTENBERG)',re.I),'start'),   # 这一行之前都不要
    (re.compile(r'(\*\*\*\s*END OF (THE|THIS) PROJECT GUTENBERG|END OF THE PROJECT GUTENBERG EBOOK|THE FULL PROJECT GUTENBERG.{0,3}LICENSE)',re.I),'end'),   # 这一行之后都不要
]
JUNK=re.compile(r'^(←.*→?|.*→$|姊妹计划.*|姊妹計劃.*|本作品.*公有领域.*|本作品.*公有領域.*|Public domain.*|This work is in the public domain.*|关于本作品的其它版本.*|關於本作品的其它版本.*|Produced by .*|Transcriber.?s? [Nn]ote.*|图书在版编目.*|圖書在版編目.*|ISBN.*|版权所有.*|版權所有.*|Copyright ©.*|All rights reserved.*)$')
def strip_boiler(paras):
    """paras: [(kind,text)…]；去掉古登堡头尾、维基文库导航、版权页这类"不是书"的行"""
    st=next((i for i,(k,t) in enumerate(paras) if BOILER[0][0].search(t)),None)
    if st is not None: paras=paras[st+1:]
    en=next((i for i,(k,t) in enumerate(paras) if BOILER[1][0].search(t)),None)
    if en is not None: paras=paras[:en]
    return [(k,t) for k,t in paras if not JUNK.match(t.strip())]

def looks_heading(t):
    """一段很短、像章节标题的文字（epub 里常用 <p> 写标题）"""
    s=t.strip()
    if not s or len(s)>40: return False
    if is_heading(s): return True
    return False

# ================= epub（通用） =================
# 分章的依据按可靠程度：① 书自带的目录（toc.ncx / nav，可以指到文件里的某个位置）② 正文里的标题（h1～h4、像"第X章"的短段）③ 按字数切。
# 目录里的封面、版权、目录、献词、索引、注释这类条目跳过；一个目录条目里如果又有好几个"第X回"标题（一个文件放十回），再按标题细分。
def _safe_zip(b):
    try: z=zipfile.ZipFile(io.BytesIO(b))
    except zipfile.BadZipFile: raise ImportError_('文件已损坏，无法打开（不是有效的压缩包）')
    if sum(i.file_size for i in z.infolist())>MAX_UNZIP: raise ImportError_('文件解压后太大')
    return z
SKIPTITLE=re.compile(r'^[\s□■◆◇●○·•*#\-—]*(封面|版权(页|信息)?|版權|目录|目錄|扉页|书名页|献词|题献|Cover( Page)?|Title Page|Half Title|Copyright( Page)?|Contents|Table of Contents|Dedication|Epigraph|Colophon|Index|Footnotes?|Endnotes|Notes|注释|注釋|Books by .*|Also by .*|About (the|this) .*|关于本书|Illustrations|List of .*|[a-z]*\d*_?(fn|note|ref)\d+[a-z]?)\s*[:：︰]?\s*$',re.I)
def _toc(z,opf,manifest,j):
    items=[]
    ncx=next((h for h,mt in manifest.values() if 'ncx' in mt),None)
    if ncx:
        try:
            x=z.read(j(ncx)).decode('utf-8','replace')
            for lab,src in re.findall(r'<navPoint\b.*?<text>(.*?)</text>.*?<content[^>]*src="([^"]+)"',x,re.S):
                items.append((html.unescape(re.sub('<[^>]+>','',lab)).strip(),j(src),(html.unescape(src).split('#')+[''])[1]))
        except KeyError: pass
    if not items:
        nav=next((h for i,(h,mt) in manifest.items() if 'nav' in i.lower() and 'html' in mt),None)
        m=re.search(r'<item\b[^>]*properties="[^"]*\bnav\b[^"]*"[^>]*>',opf)
        if m: nav=re.search(r'href="([^"]+)"',m.group(0)).group(1)
        if nav:
            try:
                x=z.read(j(nav)).decode('utf-8','replace'); x=re.split(r'<nav\b[^>]*epub:type="toc"',x)[-1].split('</nav>')[0]
                for src,lab in re.findall(r'<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>',x,re.S):
                    items.append((html.unescape(re.sub('<[^>]+>','',lab)).strip(),j(src),(html.unescape(src).split('#')+[''])[1]))
            except KeyError: pass
    return items
def _cut(raw,anchors):
    """一个文件的 html 按目录里的锚点切开：返回 [(锚点或'',html片段)]，第一个片段是第一个锚点之前的部分"""
    pos=[]
    for a in anchors:
        m=re.search(r'<[^>]+\bid=["\']'+re.escape(a)+r'["\']',raw) if a else None
        pos.append((m.start() if m else (0 if not a else None),a))
    pos=sorted([(p,a) for p,a in pos if p is not None])
    out=[]; last=0; cur=''
    for p,a in pos:
        out.append((cur,raw[last:p])); last=p; cur=a
    out.append((cur,raw[last:]))
    return out
def from_epub(b,title):
    z=_safe_zip(b)
    try:
        cont=z.read('META-INF/container.xml').decode('utf-8','replace')
        opf_path=re.search(r'full-path="([^"]+)"',cont).group(1)
    except (KeyError,AttributeError): raise ImportError_('不是有效的 epub（缺 container.xml）')
    opf=z.read(opf_path).decode('utf-8','replace'); base=os.path.dirname(opf_path)
    j=lambda h: os.path.normpath(os.path.join(base,html.unescape(h).split('#')[0])).replace('\\','/')
    manifest={}
    for m in re.finditer(r'<item\b([^>]*)/?>',opf):
        a=m.group(1); i=re.search(r'\bid="([^"]+)"',a); h=re.search(r'\bhref="([^"]+)"',a); t=re.search(r'media-type="([^"]+)"',a)
        if i and h: manifest[i.group(1)]=(h.group(1),t.group(1) if t else '')
    spine=[]
    for m in re.finditer(r'<itemref\b([^>]*)/?>',opf):
        a=m.group(1); i=re.search(r'idref="([^"]+)"',a)
        if i and i.group(1) in manifest and 'linear="no"' not in a: spine.append(j(manifest[i.group(1)][0]))
    meta_t=re.search(r'<dc:title[^>]*>(.*?)</dc:title>',opf,re.S); meta_a=re.search(r'<dc:creator[^>]*>(.*?)</dc:creator>',opf,re.S)
    toc=[t for t in _toc(z,opf,manifest,j) if t[1] in spine]
    use_toc=sum(1 for lab,f,a in toc if lab and not SKIPTITLE.match(lab))>=3
    # 按阅读顺序把全书接成一串：('ch',目录标题) 是目录条目的开始，('skip',…) 是要跳过的条目
    stream=[]
    for f in spine:
        try: raw=z.read(f).decode('utf-8','replace')
        except KeyError: continue
        anchors=[(a,lab) for lab,ff,a in toc if ff==f] if use_toc else []
        for a,part in _cut(raw,[x for x,_ in anchors]) if anchors else [('',raw)]:
            lab=next((l for x,l in anchors if x==a),None) if anchors else None
            if lab is not None: stream.append(('skip' if SKIPTITLE.match(lab) or not lab else 'ch',lab))
            stream+=html_blocks(part)
    stream=strip_boiler(stream)
    # 分章
    chapters=[]
    if use_toc:
        cur_t=None; cur=[]; skipping=False
        def push():
            if cur_t is not None and not skipping and cur:
                sub=_blocks_to_chapters(cur,min_heads=2,only_chapter_heads=True)
                if len(sub)>1: chapters.extend((t if t!='开篇' else cur_t,ps) for t,ps in sub)
                else: chapters.append((cur_t,[t for k,t in cur if k!='h' or t!=cur_t]))
        for k,t in stream:
            if k in ('ch','skip'):
                push(); cur_t=t; cur=[]; skipping=(k=='skip')
            elif cur_t is None and not chapters:
                cur_t='开篇'; cur=[(k,t)]
            else: cur.append((k,t))
        push()
        chapters=[(t,[x for x in ps if x.strip() and x.strip()!=t.strip()]) for t,ps in chapters]
    else:
        chapters=_blocks_to_chapters([x for x in stream if x[0] not in ('ch','skip')])
    chapters=[(t,ps) for t,ps in chapters if ps and not SKIPTITLE.match(t or '')]
    title=html.unescape(meta_t.group(1)).strip() if meta_t and meta_t.group(1).strip() else title
    title=re.sub(r'\s*[/:：].*$','',title) if len(title)>30 else title
    return finish(title,chapters,{"格式":"epub","作者":html.unescape(meta_a.group(1)).strip() if meta_a else '',"分章":"目录" if use_toc else "标题"})

# ================= docx =================
def from_docx(b,title):
    z=_safe_zip(b)
    try: x=z.read('word/document.xml').decode('utf-8','replace')
    except KeyError: raise ImportError_('不是有效的 Word 文档')
    blocks=[]
    for p in re.findall(r'<w:p[ >].*?</w:p>',x,re.S):
        t=html.unescape(''.join(re.findall(r'<w:t[^>]*>(.*?)</w:t>',p,re.S))).strip()
        if not t: continue
        st=re.search(r'<w:pStyle w:val="([^"]+)"',p)
        blocks.append(('h' if st and re.match(r'(Heading|heading|标题|Title)\s*[12]?$',st.group(1)) else 'p',t))
    return finish(title,_blocks_to_chapters(blocks),{"格式":"docx"})

# ================= pdf =================
def from_pdf(b,title,ocr=True):
    pages=_pdf_text(b)
    if sum(len(p.strip()) for p in pages)<max(200,len(pages)*20):   # 几乎取不出字：扫描版
        if not ocr: raise ImportError_('这是扫描版 PDF，需要文字识别')
        pages=_ocr(b)
        if not pages: raise ImportError_('这是扫描版 PDF。服务器尚未安装文字识别组件（tesseract 和中文语言包），暂时无法导入。')
    lines=_pdf_clean(pages)
    return finish(title,by_headings(lines,title),{"格式":"pdf","页数":len(pages)})

def _pdf_text(b):
    try:
        import pypdf
        r=pypdf.PdfReader(io.BytesIO(b))
        if r.is_encrypted:
            try: r.decrypt('')
            except Exception: raise ImportError_('PDF 已加密，无法导入')
        return [(pg.extract_text() or '') for pg in r.pages]
    except ImportError_: raise
    except Exception:
        if shutil.which('pdftotext'):
            with tempfile.TemporaryDirectory() as d:
                f=os.path.join(d,'a.pdf'); open(f,'wb').write(b)
                out=subprocess.run(['pdftotext','-layout',f,'-'],capture_output=True,timeout=300).stdout.decode('utf-8','replace')
                return out.split('\f')
        raise ImportError_('无法读取该 PDF')

def _pdf_clean(pages):
    """去页眉页脚、页码；把一句话被换行切开的地方接回去"""
    from collections import Counter
    heads=Counter(); feet=Counter()
    plines=[[l.strip() for l in p.split('\n') if l.strip()] for p in pages]
    for ls in plines:
        if ls: heads[re.sub(r'\d+','#',ls[0])]+=1; feet[re.sub(r'\d+','#',ls[-1])]+=1
    n=len(plines); rep=lambda c:{k for k,v in c.items() if n>=4 and v>=n*0.4}
    H,F=rep(heads),rep(feet)
    out=[]
    for ls in plines:
        if ls and re.sub(r'\d+','#',ls[0]) in H: ls=ls[1:]
        if ls and re.sub(r'\d+','#',ls[-1]) in F: ls=ls[:-1]
        ls=[l for l in ls if not re.fullmatch(r'[-—\s]*(第\s*)?\d+\s*(页)?[-—\s]*|[ivxlcdm]+',l,re.I)]
        for l in ls:
            if out and out[-1] and not is_heading(l) and not is_heading(out[-1]) and not re.search(r'[。！？!?」』”：:…）)]$',out[-1]):
                sep=' ' if re.search(r'[A-Za-z,]$',out[-1]) and re.match(r'[A-Za-z]',l) else ''
                out[-1]=out[-1].rstrip('-') if out[-1].endswith('-') and re.match(r'[a-z]',l) else out[-1]
                out[-1]+=sep+l
            else: out.append(l)
    return out

def _ocr(b):
    if not (shutil.which('tesseract') and shutil.which('pdftoppm')): return []
    langs=subprocess.run(['tesseract','--list-langs'],capture_output=True).stdout.decode()
    lang='+'.join(x for x in ('chi_sim','eng') if x in langs) or 'eng'
    with tempfile.TemporaryDirectory() as d:
        f=os.path.join(d,'a.pdf'); open(f,'wb').write(b)
        subprocess.run(['pdftoppm','-r','200','-png',f,os.path.join(d,'p')],timeout=1800,check=True)
        out=[]
        imgs=sorted(x for x in os.listdir(d) if x.endswith('.png'))
        for img in imgs:
            out.append(subprocess.run(['tesseract',os.path.join(d,img),'-','-l',lang],capture_output=True,timeout=300).stdout.decode('utf-8','replace'))
            if len(out)==min(3,len(imgs)) and 'chi_sim' not in lang:   # 只有英文语言包：先认三页看看，认出来的多半不是英文单词（中文书）就放弃
                words=re.findall(r'[A-Za-z]+','\n'.join(out)); real=[w for w in words if len(w)>=3 and re.fullmatch(r'[a-z]+|[A-Z][a-z]+',w)]
                if len(real)<max(30,len(words)*0.5): return []
        return out

# ================= doc / rtf / odt / wps：用 LibreOffice 先转 docx =================
def via_office(b,ext,title):
    exe=shutil.which('soffice') or shutil.which('libreoffice')
    if not exe: raise ImportError_(f'.{ext} 需要服务器装 LibreOffice 才能导入；可以先另存为 .docx 再导入')
    with tempfile.TemporaryDirectory() as d:
        src=os.path.join(d,'in.'+ext); open(src,'wb').write(b)
        subprocess.run([exe,'--headless','-env:UserInstallation=file://'+d+'/lo','--convert-to','docx','--outdir',d,src],capture_output=True,timeout=300)
        dst=os.path.join(d,'in.docx')
        if not os.path.exists(dst): raise ImportError_(f'.{ext} 转换失败')
        book=from_docx(open(dst,'rb').read(),title); book['导入']['格式']=ext; return book

# ================= mobi / azw3 / fb2：先转 epub =================
def via_calibre(b,ext,title):
    exe=shutil.which('ebook-convert')
    if not exe: raise ImportError_(f'{ext} 格式需要服务器装 calibre 才能导入；可以先转成 epub 再导入')
    with tempfile.TemporaryDirectory() as d:
        src=os.path.join(d,'in.'+ext); dst=os.path.join(d,'out.epub'); open(src,'wb').write(b)
        r=subprocess.run([exe,src,dst],capture_output=True,timeout=600)
        if r.returncode or not os.path.exists(dst): raise ImportError_(f'{ext} 转换失败')
        return from_epub(open(dst,'rb').read(),title)

# ================= 入口 =================
FORMATS={'epub':from_epub,'txt':from_txt,'pdf':from_pdf,'docx':from_docx,'html':from_html,'htm':from_html,'xhtml':from_html,'md':from_md,'markdown':from_md}
CALIBRE={'mobi','azw','azw3','fb2','kfx','lit','pdb'}
OFFICE={'doc','rtf','odt','wps'}
def supported(): return sorted(FORMATS)+sorted(OFFICE)+sorted(CALIBRE)

def import_book(data,filename,to_simplified=True):
    """data: 文件内容（bytes）；filename 只用来看扩展名和默认书名，不用来拼路径"""
    name=os.path.basename(filename or 'book')
    ext=name.rsplit('.',1)[-1].lower() if '.' in name else ''
    title=re.sub(r'[_\-]+',' ',name.rsplit('.',1)[0]).strip() or '未命名'
    if ext in OFFICE: book=via_office(data,ext,title)
    elif ext in FORMATS: book=FORMATS[ext](data,title)
    elif ext in CALIBRE: book=via_calibre(data,ext,title)
    else:
        # 没有扩展名：看文件头
        if data[:4]==b'%PDF': book=from_pdf(data,title)
        elif data[:2]==b'PK':
            try: book=from_epub(data,title)
            except ImportError_: book=from_docx(data,title)
        else: book=from_txt(data,title)
    if to_simplified: _to_simplified(book)
    book['导入'].update({"文件":name,"字数":sum(len(s['文']) for c in book['章'] for s in c['段']),"章数":len(book['章'])})
    return book

# ================= 封面 =================
COVER_W,COVER_H=240,340          # 书架上的封面缩略图（2 倍屏够用）
def cover(data,filename):
    """从原文件里取封面，返回缩小后的 JPEG（bytes）；取不到返回 None（书架按书名生成封面）。
    epub：opf 里标的封面图（cover-image / <meta name="cover">），没标就找文件名带 cover 的图；
    pdf：第一页渲染成图（扫描版、出版社 PDF 第一页通常就是封面）；文字版第一页只有字的，也照样用（看起来像书的扉页）。
    其它格式：经转换的（mobi/azw3）取转换后 epub 的封面；txt/docx 没有封面。"""
    ext=(os.path.basename(filename or '').rsplit('.',1)+[''])[1].lower()
    try:
        raw=None
        if ext=='epub' or (not ext and data[:2]==b'PK'): raw=_epub_cover(data)
        elif ext=='pdf' or data[:4]==b'%PDF':
            raw=_pdf_cover(data)
            if raw and (_mostly_white(raw) or _page1_chars(data)>300): raw=None      # 第一页是满页文字（文字版正文/版权页），不当封面
        elif ext in CALIBRE: raw=_calibre_cover(data,ext)
        return _thumb(raw) if raw else None
    except Exception: return None
def _epub_cover(b):
    z=_safe_zip(b)
    opf_path=re.search(r'full-path="([^"]+)"',z.read('META-INF/container.xml').decode('utf-8','replace')).group(1)
    opf=z.read(opf_path).decode('utf-8','replace'); base=os.path.dirname(opf_path)
    items=[]
    for m in re.finditer(r'<item\b([^>]*)/?>',opf):
        a=m.group(1); g=lambda k:(re.search(k+r'="([^"]+)"',a) or [None,''])[1]
        items.append({'id':g('id'),'href':g('href'),'type':g('media-type'),'props':g('properties')})
    pick=next((i for i in items if 'cover-image' in i['props'] and i['type'].startswith('image/')),None)
    if not pick:
        m=re.search(r'<meta\b[^>]*name="cover"[^>]*>',opf) or re.search(r'<meta\b[^>]*content="[^"]*"[^>]*name="cover"[^>]*>',opf)
        if m:
            cid=re.search(r'content="([^"]+)"',m.group(0)).group(1)
            it=next((i for i in items if i['id']==cid),None)
            if it and it['type'].startswith('image/'): pick=it
            elif it and 'html' in it['type']:      # 封面是一页 html：取里面第一张图
                try:
                    x=z.read(os.path.normpath(os.path.join(base,html.unescape(it['href']))).replace('\\','/')).decode('utf-8','replace')
                    src=re.search(r'<(?:img|image)\b[^>]*(?:src|xlink:href|href)="([^"]+)"',x)
                    if src:
                        p=os.path.normpath(os.path.join(base,os.path.dirname(html.unescape(it['href'])),html.unescape(src.group(1)))).replace('\\','/')
                        return z.read(p)
                except KeyError: pass
    if not pick: pick=next((i for i in items if i['type'].startswith('image/') and re.search(r'cover|封面',i['href'],re.I)),None)
    if not pick: return None
    if re.search(r'\d+-cover\.png$',pick['href']) and 'gutenberg' in opf.lower(): return None   # 古登堡自动生成的花纹封面，不如按书名生成的好看
    return z.read(os.path.normpath(os.path.join(base,html.unescape(pick['href']))).replace('\\','/'))
def _pdf_cover(b):
    if not shutil.which('pdftoppm'): return None
    with tempfile.TemporaryDirectory() as d:
        f=os.path.join(d,'a.pdf'); open(f,'wb').write(b)
        subprocess.run(['pdftoppm','-f','1','-l','1','-r','60','-jpeg',f,os.path.join(d,'c')],capture_output=True,timeout=60)
        out=[x for x in os.listdir(d) if x.startswith('c')]
        return open(os.path.join(d,out[0]),'rb').read() if out else None
def _calibre_cover(b,ext):
    exe=shutil.which('ebook-convert')
    if not exe: return None
    with tempfile.TemporaryDirectory() as d:
        src=os.path.join(d,'in.'+ext); dst=os.path.join(d,'out.epub'); open(src,'wb').write(b)
        subprocess.run([exe,src,dst],capture_output=True,timeout=600)
        return _epub_cover(open(dst,'rb').read()) if os.path.exists(dst) else None
def _page1_chars(b):
    try:
        import pypdf; return len((pypdf.PdfReader(io.BytesIO(b)).pages[0].extract_text() or '').strip())
    except Exception: return 0
def _mostly_white(raw):
    try:
        from PIL import Image
        im=Image.open(io.BytesIO(raw)).convert('L').resize((60,85))
        px=list(im.getdata()); return sum(1 for v in px if v>225)/len(px)>0.82
    except Exception: return False
def _thumb(raw):
    """缩成书架封面大小的 JPEG；太小（logo、图标）或比例太怪（横幅）的不算封面。没有 PIL 时原图照用（只收 jpg/png）"""
    try:
        from PIL import Image
        im=Image.open(io.BytesIO(raw)); im.load()
        w,h=im.size
        if w<120 or h<160 or not (1.1<=h/w<=1.9): return None
        im=im.convert('RGB'); im.thumbnail((COVER_W,COVER_H))
        out=io.BytesIO(); im.save(out,'JPEG',quality=82,optimize=True); return out.getvalue()
    except ImportError:
        return raw if raw[:3]==b'\xff\xd8\xff' or raw[:8]==b'\x89PNG\r\n\x1a\n' else None
    except Exception: return None

def _t2s():
    """繁转简：服务器装了 opencc（pip install opencc-python-reimplemented）就用；本机开发环境有 ICU 时用第一阶段的 t2s.py；都没有就不转（不报错）"""
    try:
        import opencc; c=opencc.OpenCC('t2s'); return c.convert
    except Exception: pass
    try:
        import sys; sys.path.insert(0,os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),'生成','流水线'))
        import t2s; return t2s.conv
    except Exception: return None
def _to_simplified(book):
    """繁体字占比高的书 → 简体"""
    conv=_t2s()
    if not conv: return
    sample=''.join(s['文'] for c in book['章'][:3] for s in c['段'][:30])[:4000]
    try: diff=sum(1 for a,b in zip(sample,conv(sample)) if a!=b)
    except Exception: return
    if sample and diff/len(sample)>0.03:
        for c in book['章']:
            c['标题']=conv(c['标题'])
            for s in c['段']: s['文']=conv(s['文'])
        book['导入']['繁转简']=True
