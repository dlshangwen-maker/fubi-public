"""翻译自动检查（翻译_说明.md 第 3 步）。
用法：python3 -I check_translation.py <原文.json> <译文.json> <术语表.json> [公式图片.json] [旧译.json]
检查：编号对齐、非空；术语一致（原文出现术语 → 译文出现对应中文）；图片标记一致；残留 LaTeX/英文双引号；中文引号成对；
      长度比例异常（可能漏译）；（可选）和旧译的相似度——防雷同，太像的列出来人工看。
"""
import json,sys,re,difflib
S=json.load(open(sys.argv[1],encoding='utf-8')); T=json.load(open(sys.argv[2],encoding='utf-8'))
G=json.load(open(sys.argv[3],encoding='utf-8'))['术语']
IMG=json.load(open(sys.argv[4],encoding='utf-8')) if len(sys.argv)>4 else {}
OLD=json.load(open(sys.argv[5],encoding='utf-8')) if len(sys.argv)>5 else {}
src={p['n']:p for p in S['命题']}; zh=T['命题']
probs=[]
def P(n,m): probs.append((n,m))
if set(src)!=set(zh): P('-',f'编号不一致：缺 {sorted(set(src)-set(zh))[:10]} 多 {sorted(set(zh)-set(src))[:10]}')
for n,p in src.items():
    t=zh.get(n,'')
    if not t.strip(): P(n,'空'); continue
    if re.search(r'\\[a-zA-Z]',t): P(n,'残留 LaTeX')
    if '"' in t: P(n,'英文双引号')
    if t.count('“')!=t.count('”'): P(n,'中文引号不成对')
    if re.findall(r'⟦img:[^⟧]+⟧',t)!=IMG.get(n,[]): P(n,f"图片标记不一致：{re.findall(r'⟦img:[^⟧]+⟧',t)} vs {IMG.get(n,[])}")
    de=re.sub(r'\\[a-zA-Z]+|[{}]','',p.get('de',''))
    r=len(re.sub(r'\s','',t))/max(1,len(re.sub(r'\s','',de)))
    if len(de)>40 and r<0.18: P(n,f'译文偏短（{r:.2f}），可能漏译')
    for g in G:
        des=[x.strip() for x in g['de'].split('/')]; zhs=[x.strip() for x in g['zh'].split('/')]
        for i,d in enumerate(des):
            if len(d)>=5 and re.search(r'\b'+re.escape(d),de):
                want=zhs[min(i,len(zhs)-1)]
                if want not in t and not any(z in t for z in zhs+g.get('也可',[])): P(n,f'术语：{d} → 应含“{want}”')
sim=[]
for n,o in OLD.items():
    if n in zh and len(o)>=20:
        r=difflib.SequenceMatcher(None,re.sub(r'⟦[^⟧]+⟧','',o),re.sub(r'⟦[^⟧]+⟧','',zh[n])).ratio()
        if r>=0.8: sim.append((n,round(r,2)))
for n,m in probs: print(n,m)
print(f'\n问题 {len(probs)} 处')
if OLD: print(f'和旧译相似度 ≥0.8 的（≥20 字）：{len(sim)} 条',sorted(sim,key=lambda x:-x[1])[:20])
