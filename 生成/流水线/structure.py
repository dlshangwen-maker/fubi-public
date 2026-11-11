import json,re,os
d=json.load(open('simp.json'))
B='/sessions/blissful-gallant-einstein/mnt/ Read Book/文本数据/红楼梦/'
def segs_of(p): return [s for s in re.split(r'[，。？！；、]',p) if s]
def is_poem(p):
    if '下回分解' in p or '且听下回' in p: return False
    if re.search(r'[“”「」：]',p): return False
    S=segs_of(p)
    if len(S)<2 or len(p)>200: return False
    L=[len(s) for s in S]
    return all(l in (3,4,5,6,7) for l in L) and max(L)-min(L)<=3 and len(set(L))<=3
def split_poem_prose(p):
    # 底本常把判词和后面的叙述放在同一段："……一梦遥。后面又画着……"
    m=re.search(r'(?<=[。！？])(?=(后面|诗后|画后|又有|其词|其判))',p)
    if m and is_poem(p[:m.start()]): return [p[:m.start()],p[m.start():]]
    return [p]
out={'书':'红楼梦','底本':'程乙本（维基文库「红楼梦（程乙本）」，2026-10-16 下载；原文公有领域，标点为后人所加）',
     '处理':'ICU Hant-Hans 繁转简 + 人工修正表；判词与叙述同段的已拆开；“类型:诗”为规则判断，前五回人工核对','回':[]}
# 前五回人工核对：规则漏判的诗词、曲名标题
MANUAL_POEM={'3.31','3.33','4.7','4.8','5.51','5.53','5.55','5.58','5.60','5.62','5.64','5.66','5.68','5.70','5.72','5.74','5.76','5.78'}
MANUAL_TITLE={'5.50','5.52','5.54','5.57','5.59','5.61','5.63','5.65','5.67','5.69','5.71','5.73','5.75','5.77'}
npoem=0
for h in d:
    ps=[]
    for p in h['段']: ps+=split_poem_prose(p)
    segs=[]
    for k,p in enumerate(ps,1):
        s={'id':f"{h['回']}.{k}",'文':p}
        if s['id'] in MANUAL_TITLE: s['类型']='曲名'
        elif s['id'] in MANUAL_POEM or is_poem(p): s['类型']='诗'; npoem+=1
        segs.append(s)
    out['回'].append({'回':h['回'],'回目':h['回目'],'段':segs})
os.makedirs(B,exist_ok=True)
json.dump(out,open(B+'全文.json','w'),ensure_ascii=False,indent=1)
for h in out['回']:
    with open(B+f"第{h['回']:03d}回.txt",'w') as f:
        f.write(f"第{h['回']}回　{h['回目']}\n\n"+'\n\n'.join(('　　' if s.get('类型')=='诗' else '')+s['文'] for s in h['段'])+'\n')
print('poems',npoem,'segs',sum(len(h['段']) for h in out['回']))
for h in out['回'][:5]:
    print('---',h['回'],len(h['段']))
    for s in h['段']:
        if s.get('类型')=='诗': print(' ',s['id'],s['文'][:46])
