"""事后剧透扫描（通用版）。三类：
1. 卡片里出现的人名/别称/概念，早于它在原文中第一次出现的位置（按单元最后一段算读者位置）；
2. 后文名单里的词（第一次出现在收录范围之后、或晚于该单元）；
3. 暗示字眼。
用法：python3 -I spoiler_scan_通用.py <生成/书 目录> <全文.json>
卡片键是单元第一段；读者位置取该单元最后一段（全文.json 里的"单元"）。没有单元的书，每段一个单元。
"""
import json,sys,glob,re
B,TXTP=sys.argv[1],sys.argv[2]
k=lambda p:tuple(int(x) for x in p.split('.'))
TXT=json.load(open(TXTP,encoding='utf-8'))
chs=TXT.get('章') or TXT.get('回')
SEG={s['id']:s['文'] for c in chs for s in c['段']}
END={}
for c in chs:
    for a,b in c.get('单元') or [[s['id'],s['id']] for s in c['段']]: END[a]=b
cards={}
for f in sorted(glob.glob(f'{B}/卡片/第*.json')): cards.update(json.load(open(f,encoding='utf-8')))
idx=json.load(open(f'{B}/索引_合并.json',encoding='utf-8'))
later=json.load(open(f'{B}/后文名单.json',encoding='utf-8'))['词']
GENERIC=set('他 她 我 你 那人 丈夫 爸爸 妈妈 奶奶 年轻人 司机 大臣 首长 将军 警官 教授 老师 孩子 女儿 母亲 父亲 主任'.split())
def first_in_text(w):
    for sid in sorted(SEG,key=k):
        if w in SEG[sid]: return sid
    return None
names={}
for e in idx['人物']:
    for a in e['别称']:
        w=a['称']
        if len(w)>=2 and w not in GENERIC:
            names.setdefault(w,(a['从'],e['名']))
    nm,vis=e['名'],e.get('名可显示从')
    if vis and len(nm)>=2 and nm not in GENERIC: names.setdefault(nm,(vis,nm))
    elif not vis and len(nm)>=2: names.setdefault(nm,('99.1',nm))   # 名字原文从未出现（内部称呼）
HINT=['注定','终将','伏笔','预示','暗示了','值得注意','关键线索','真相','其实是','后文','后面会','日后','下一单元','下一章','为后面','铺垫']   # 现代白话里“后来”“最终”“结局”太常见，不扫（2026-10-19 三体）
hits=[]
for key,card in cards.items():
    pos=END.get(key,key)
    for lv,f in card.items():
        for fld,t in f.items():
            if not isinstance(t,str): continue
            for w,(frm,who) in names.items():
                if w in t and k(frm)>k(pos):
                    ft=first_in_text(w)
                    if ft and k(ft)<=k(pos): continue          # 作为普通词在原文更早出现过
                    hits.append([key,lv,fld,'名字太早',w,f'{who}：读者 {frm} 才知道',t[:70]])
            for x in later:
                if x['词'] in t and k(x['首次'])>k(pos):
                    kind='后文名词' if x.get('类')!='真实人物' else '提醒·真实人物'
                    hits.append([key,lv,fld,kind,x['词'],f"原文 {x['首次']} 首次出现",t[max(0,t.index(x['词'])-20):t.index(x['词'])+20]])
            for w in HINT:
                if w in t: hits.append([key,lv,fld,'暗示字眼',w,'',t[max(0,t.index(w)-25):t.index(w)+20]])
json.dump(hits,open(f'{B}/剧透扫描.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
from collections import Counter
print('卡片',len(cards),'命中',len(hits),dict(Counter(h[3] for h in hits)))
for h in hits: print(h)
