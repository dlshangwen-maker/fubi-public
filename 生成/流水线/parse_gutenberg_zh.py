"""古登堡中文书（定宽换行的 txt 转 epub，如 #27166《吶喊》）→ 篇/段 JSON（繁体）。
用法：python3 -I parse_gutenberg_zh.py <epub解压后的OEBPS目录> <输出json>
做的事：
1. 取正文 <p>/<h*> 行，去掉古登堡页眉页脚、录入者署名（打字︰…、輸入︰…、﹝《吶喊》﹞）。
2. 每篇以篇名行开始（短、无标点、不缩进或缩进 1 格）；篇末的“注釋/□注釋”到下一篇之前全部丢掉（编者注，不是鲁迅原文）。
3. 原书每行约 38 个汉字定宽折行，每行都有 4 格缩进（不能靠缩进分段）：一行没写满 = 段落结束，写满了 = 下一行接上。
   例外：章节小标题（如“一”“第一章序”）单独成段；篇末写作日期（“一九一八年四月。”）单独成段。
4. 删掉正文里的注释序号（ぇえぉおかがきぎくぐ… 这类假名、□）。
"""
import re,html,json,sys,glob,os
D=sys.argv[1]; out=sys.argv[2]
T=''.join(open(f,encoding='utf-8').read() for f in sorted(glob.glob(os.path.join(D,'*27166-0-[0-2].txt.xhtml'))))
L=[html.unescape(re.sub(r'<[^>]+>','',m.group(2))).replace('　',' ').rstrip() for m in re.finditer(r'<(p|h\d)[^>]*>(.*?)</\1>',T,re.S)]
# 只要正文：从“《吶喊》自序”开始，到古登堡页脚之前
st=next(i for i,x in enumerate(L) if x.strip()=='《吶喊》自序')
L=L[st:]
end=next((i for i,x in enumerate(L) if 'END OF THE PROJECT GUTENBERG' in x),len(L)); L=L[:end]
NOTE=re.compile(r'[ぁ-ゟァ-ヿ]')    # 假名（含ゝゞヾ）= 编者注序号
# 古登堡 #27166 有几处生僻字编码损坏（变成空格、问号或乱码）。按 1923 年新潮社初版原文修复（公有领域）。
REPAIR=[('耳朵已經諾南熳帕耍 昧心','耳朵已經喤喤的響著了，用了心'),
 ('冬冬?  諾南歟  揮刑  僥愕幕啊！','冬冬喤喤的響，並沒有听到你的話。”'),
 ('冬冬?  胖 鄭 溝降諞晃杼ㄈХ耍','冬冬喤喤之災，竟到第一舞台去了，'),
 ('冬冬?  諾那麼潁 旌 搪痰幕蔚矗 又 允   悖 齠  刮沂 蟺皆謖里不適于生存了','冬冬喤喤的敲打，紅紅綠綠的晃蕩，加之以十二點，忽而使我省悟到在這里不適于生存了'),
 ('擠而又擠2','擠而又擠'),('，，','，'),
 ('一匹 盡力','一匹猹盡力'),('那 卻將','那猹卻將'),('所謂 的','所謂猹的'),('看見 了，你便刺','看見猹了，你便刺'),
 ('﹝弓京﹞','弶'),('﹝口皇﹞','嗡'),('正在        的響','正在窸窸窣窣的響'),
 ('黑    中蕩來','黑魆魆中蕩來'),('黑    的挺立','黑魆魆的挺立'),('怯怯的  進去','怯怯的躄進去'),('于是  出路角','于是躄出路角'),
 ('（ ）',''),('刺蝟， 。','刺蝟，猹。'),('， 在咬瓜','，猹在咬瓜'),('貝殼， ，','貝殼，猹，'),('小Don','小Don'),('太牢々','太牢'),('烏 樹','烏桕樹'),('烏 葉','烏桕葉'),('枯 樹','枯桕樹'),('○','〇')]
def repair(t):
    for a,b in REPAIR: t=t.replace(a,b)
    t=re.sub(r'(?<=[一-鿿A-Za-z”》！？])\s+(?=[一-鿿，。、；…“”])','',t)   # 注释序号删掉后留下的空格
    return re.sub(r'\s+(?=[，。；…])','',t)
W=lambda t: sum(2 if ord(c)>0x2e80 else 1 for c in t.strip())   # 显示宽度：汉字 2、字母数字 1
FULL=sorted(W(x) for x in L)[int(len(L)*0.8)]                   # 满行宽度（取第 80 百分位，约 76）
TITLES=['《吶喊》自序','一件小事','狂人日記','鴨的喜劇','端午節','故鄉','孔乙己','藥','阿Q正傳','兔和貓','社戲','風波','頭發的故事','明天','白光']
def is_title(x): return x.strip() in TITLES and not x.startswith('    '+x.strip()) or (x.strip() in TITLES and x.strip()!='《吶喊》自序' and len(x)-len(x.lstrip())<=1)
SUB=re.compile(r'^(一|二|三|四|五|六|七|八|九|十|十一|十二|十三|第[一二三四五六七八九]章.{0,8})$')
JUNK=re.compile(r'^(打字|輸入)︰|^﹝《吶喊》﹞$')
stories=[]; cur=None; skip=False; seen=set()
for x in L:
    s=x.strip()
    if not s: continue
    if s in TITLES and s not in seen and (len(x)-len(x.lstrip())<=1 or s=='《吶喊》自序'):
        seen.add(s); cur={'篇':s,'段':[]}; stories.append(cur); skip=False; continue
    if cur is None: continue
    if s in ('注釋︰','□注釋','注釋'): skip=True; continue
    if skip or JUNK.search(s): continue
    raw=s; s=NOTE.sub('',s).replace('□','')
    if SUB.match(s) or re.match(r'^一九[一二]\S*年\S*月\S*。?$',s):
        cur['段'].append({'文':s,'类':'小标题' if SUB.match(s) else '日期'}); cur['_open']=False; continue
    if not cur['段'] or not cur.get('_open'):
        cur['段'].append({'文':s})
    else:
        cur['段'][-1]['文']+=s
    # 这一行没写满（宽度 < 满行的 85%）= 段落在这里结束；写满的行 = 段落还没完，下一行接上
    cur['_open']=W(raw)>=FULL*0.85
for c in stories:
    c.pop('_open',None)
    for p_ in c['段']: p_['文']=repair(NOTE.sub('',p_['文']))
bad=[(c['篇'],i+1,re.findall(r'[?ㄈХ﹝﹞\d]|\s',p_['文'])) for c in stories for i,p_ in enumerate(c['段']) if re.search(r'[?ㄈХ﹝﹞]|\s{2,}',p_['文'])]
print('仍可疑：',bad)
# 自序重复的标题行
json.dump(stories,open(out,'w',encoding='utf-8'),ensure_ascii=False,indent=1)
for c in stories: print(c['篇'],len(c['段']),'段',sum(len(p['文']) for p in c['段']),'字')
