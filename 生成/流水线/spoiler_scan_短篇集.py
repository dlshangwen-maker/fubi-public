"""短篇集剧透扫描。两类"后文"：
1. 篇内：卡片里出现的人名/别称/概念，早于它在本篇原文第一次出现的位置（读者位置 = 单元最后一段）；
2. 篇外：卡片里出现了别的篇的人名、篇名（各篇独立，不该提）。
另扫暗示字眼。用法：python3 -I spoiler_scan_短篇集.py <生成/书 目录> <全文.json>"""
import json,sys,glob,re
B,TXTP=sys.argv[1],sys.argv[2]
k=lambda p:tuple(int(x) for x in p.split('.'))
T=json.load(open(TXTP,encoding='utf-8'))
SEG={s['id']:s['文'] for c in T['章'] for s in c['段']}
END={a:b for c in T['章'] for a,b in c['单元']}
TITLES={str(c['章']):c['标题'] for c in T['章']}
cards={}
for f in sorted(glob.glob(f'{B}/卡片/第*.json')): cards.update(json.load(open(f,encoding='utf-8')))
idx=json.load(open(f'{B}/索引_合并.json',encoding='utf-8'))
GEN=set('他 她 我 你 我们 他们 那人 老头子 孩子 女人 男人 母亲 父亲 儿子 女儿 老爷 太太 先生 少爷 掌柜 伙计 地保 酒客 车夫 巡警 朋友 客人 和尚 尼姑'.split())
def first_in(w,story):
    for sid in sorted((s for s in SEG if s.split('.')[0]==story),key=k):
        if w in SEG[sid]: return sid
# 只扫"名字式"的人物称呼（≥2 字、不是泛称、不是普通词）：篇内太早 + 别篇的人。概念词太泛，不扫跨篇（革命、新青年这类是书外背景，不算剧透）
COMMON=set('一个人 一个女人 孩子们 他儿子 哥哥 大伯 结果 看客 老头子 花白胡子 店伙 监督 鲁迅'.split())
words={}   # 词 -> {篇: 首次}
for e in idx['人物']:
    st=e['篇']
    for a in e['别称']:
        w=a['称']
        if len(w)>=2 and w not in GEN and w not in COMMON and not re.fullmatch(r'(一个|那个|这个|几个).*|.*们',w): words.setdefault(w,{}).setdefault(st,a['从'])
CONC={}   # 篇内概念：只扫篇内太早
for f in glob.glob(f'{B}/索引/第*章.json'):
    st=str(int(re.search(r'第(\d+)章',f).group(1)))
    for c in json.load(open(f,encoding='utf-8'))['概念']:
        w=c['词']
        if 2<=len(w)<=6 and '、' not in w and c.get('虚构'): CONC.setdefault(w,{}).setdefault(st,c['首次'])
HINT=['注定','终将','伏笔','预示','暗示了','值得注意','关键线索','真相','其实是','后文','后面会','日后','下一单元','为后面','铺垫','象征着','象征了','隐喻','讽刺了','批判了','国民性','精神胜利法']
hits=[]
for key,card in cards.items():
    st=key.split('.')[0]; pos=END.get(key,key)
    for lv,fs in card.items():
        for fld,t in fs.items():
            for w,m in words.items():
                if w not in t: continue
                if st in m:
                    fi=first_in(w,st) or m[st]
                    if k(fi)>k(pos): hits.append([key,lv,fld,'篇内太早',w,f'本篇 {fi} 才出现',t[max(0,t.index(w)-20):t.index(w)+20]])
                elif not any(w in SEG[s] for s in SEG if s.split('.')[0]==st):
                    hits.append([key,lv,fld,'别篇的词',w,'出自第'+','.join(m)+'篇',t[max(0,t.index(w)-20):t.index(w)+20]])
            for w,m in CONC.items():
                if w in t and st in m:
                    fi=first_in(w,st) or m[st]
                    if k(fi)>k(pos): hits.append([key,lv,fld,'篇内太早',w,f'本篇 {fi} 才出现',t[max(0,t.index(w)-20):t.index(w)+20]])
            for s2,tt in TITLES.items():
                if s2!=st and len(tt)>=2 and '《'+tt+'》' in t: hits.append([key,lv,fld,'提到别篇',tt,'',t[max(0,t.index(tt)-20):t.index(tt)+20]])
            for w in HINT:
                if w in t: hits.append([key,lv,fld,'暗示/解读字眼',w,'',t[max(0,t.index(w)-25):t.index(w)+20]])
json.dump(hits,open(f'{B}/剧透扫描.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
from collections import Counter
print('卡片',len(cards),'命中',len(hits),dict(Counter(h[3] for h in hits)))
for h in hits: print(h)
