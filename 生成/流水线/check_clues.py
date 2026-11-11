"""伏笔自动检查（伏笔标准 v1.1 第六节的"脚本能做的"部分）。
用法：python3 -I check_clues.py <最终.json> <全文.json> <索引_合并.json> [后文名单.json]
检查：禁用字眼；问题长度 15～30；锚句在段内且唯一；问题/猜法/揭晓说明里的人名不早于各自位置；
      后文名词；同段不超过一条；每章 1～3 条；第一章有同章回收；书里不直接回答占 20%～30%。
输出：每条的问题清单；总体统计。有"错"就返回非 0。
"""
import json,sys,re
F,TXTP,IDXP=sys.argv[1:4]; LATERP=sys.argv[4] if len(sys.argv)>4 else None
k=lambda p:tuple(int(x) for x in p.split('.'))
T=json.load(open(TXTP,encoding='utf-8')); chs=T.get('章') or T.get('回')
SEG={s['id']:s['文'] for c in chs for s in c['段']}
clues=json.load(open(F,encoding='utf-8'))
idx=json.load(open(IDXP,encoding='utf-8'))
later=json.load(open(LATERP,encoding='utf-8'))['词'] if LATERP else []
BAN=['关键','重要','注意','伏笔','将来','后来','命运','结局','注定','真相','预示']
GEN=set('他 她 我 你 那人 丈夫 爸爸 妈妈 奶奶 年轻人 司机 大臣 首长 将军 警官 教授 老师 孩子 女儿 母亲 父亲 主任 那位便衣'.split())
names={}
for e in idx['人物']:
    for a in e['别称']:
        if len(a['称'])>=2 and a['称'] not in GEN: names.setdefault(a['称'],a['从'])
    if e.get('名可显示从') and len(e['名'])>=2: names.setdefault(e['名'],e['名可显示从'])
def first_in_text(w):
    for sid in sorted(SEG,key=k):
        if w in SEG[sid]: return sid
def names_too_early(t,pos):
    out=[]
    for w,frm in names.items():
        if w in t and k(frm)>k(pos):
            ft=first_in_text(w)
            if not(ft and k(ft)<=k(pos)): out.append(f'{w}（{frm} 才出现）')
    for x in later:
        if x['词'] in t and k(x['首次'])>k(pos) and x.get('类')!='真实人物': out.append(f"后文词 {x['词']}")
    return out
errs=0; seen_para={}; per_ch={}
for c in clues:
    pr=[]; P=c['提出']; R=c.get('回收')
    q=c['问题']
    if not 15<=len(q)<=30: pr.append(f'问题长度 {len(q)}')
    for w in BAN:
        for fld in ('问题','为什么读者会问'):
            if w in c.get(fld,''): pr.append(f'{fld}含禁用词“{w}”')
    if P not in SEG: pr.append('提出段不存在')
    else:
        a=c.get('提出锚句','')
        if not a: pr.append('缺提出锚句')
        elif SEG[P].count(a)!=1: pr.append(f'提出锚句在 {P} 出现 {SEG[P].count(a)} 次')
        pr+=['问题：'+x for x in names_too_early(q,P)]
        pr+=['猜法：'+x for x in names_too_early(' '.join(c.get('能怎么猜',[])),P)]
    if R and R in SEG:
        a=c.get('回收锚句','')
        if not a: pr.append('缺回收锚句')
        elif SEG[R].count(a)!=1: pr.append(f'回收锚句在 {R} 出现 {SEG[R].count(a)} 次')
        if k(R)<=k(P): pr.append('回收不在提出之后')
        pr+=['揭晓说明：'+x for x in names_too_early(c.get('回收说明',''),R)]
    if P in seen_para: pr.append(f'和 {seen_para[P]} 同段')
    seen_para[P]=c['id']; per_ch[P.split('.')[0]]=per_ch.get(P.split('.')[0],0)+1
    if pr: errs+=1
    print(c['id'],P,'→',R,'：','通过' if not pr else '；'.join(pr))
n=len(clues); no=sum(1 for c in clues if c.get('距离')=='书里不直接回答')
print('\n每章条数',per_ch, '；不在 1～3 的：',[x for x,v in per_ch.items() if not 1<=v<=3])
first=min(per_ch,key=int)
print('第一章同章回收：',any(c['提出'].split('.')[0]==first and c.get('距离') in ('同章','同回') for c in clues))
print(f'书里不直接回答 {no}/{n} = {no/n:.0%}（目标 20%～30%）')
print('有问题的条数',errs)
sys.exit(1 if errs else 0)
