"""《呐喊》繁→简（逐字转换 + 修正表）并编号：篇.段。自序算第 0 篇。
用法：python3 -I convert_nahan.py <trad.json> <输出目录>
输出：全文.json {"书","章":[{"章","标题","段":[{"id","文","类"?}],"单元":[[a,b],…]}]}"""
import json,sys,re,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from t2s import conv
d=json.load(open(sys.argv[1],encoding='utf-8')); out=sys.argv[2]
FIX=[('甚么','什么'),('着作','著作'),('显着','显著'),('着名','著名'),('干隆','乾隆'),('干坤','乾坤'),
     ('眼楮','眼睛'),('拚命','拼命'),('书名和着者','书名和著者'),('部份','部分'),('︰','：'),('，，','，')]
def fix(s):
    for a,b in FIX: s=s.replace(a,b)
    return s
pc=lambda s:fix(''.join(conv(c) for c in s))
MIN,MAX=160,520
res={"书":"呐喊","章":[]}
for k,c in enumerate(d):
    title=pc(c['篇']).replace('《呐喊》','')
    segs=[]
    for i,p in enumerate(c['段']):
        x={"id":f"{k}.{i+1}","文":pc(p['文'])}
        if p.get('类'): x['类']=p['类']
        segs.append(x)
    # 解释单元：短段（对话）凑成一组；小标题、日期单独
    units=[]; cur=[]; L=0
    for s in segs:
        if s.get('类'):
            if cur: units.append(cur); cur=[]; L=0
            units.append([s['id']]); continue
        if cur and L+len(s['文'])>MAX: units.append(cur); cur=[]; L=0
        cur.append(s['id']); L+=len(s['文'])
        if L>=MIN: units.append(cur); cur=[]; L=0
    if cur:
        if units and L<MIN//2 and not any(x.get('类') for x in segs if x['id']==units[-1][-1]): units[-1]+=cur
        else: units.append(cur)
    res['章'].append({"章":k,"标题":title,"段":segs,"单元":[[u[0],u[-1]] for u in units]})
json.dump(res,open(f'{out}/全文.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
alltxt=''.join(s['文'] for c in res['章'] for s in c['段'])
left=sorted({ch for ch in alltxt if conv(ch)!=ch}); print('残留繁体字:',''.join(left)[:100])
for c in res['章']: print(c['章'],c['标题'],len(c['段']),'段',len(c['单元']),'单元',sum(len(s['文']) for s in c['段']),'字')
print('合计',len(alltxt),'字')
