"""现代白话书的第 1 步：章 → 段 → 编号“章.段”，并把段落分组成“解释单元”。

为什么要分组：现代小说对话多，一句“打吧。”就是一段。每段写三档解释既浪费也没意义。
解释单元 = 同一章里连续的几段，凑到约 MIN 字（不超过 MAX 字）为一组；读者点组里任何一段，看到的是这一组的解释。
古典小说（红楼梦）段落本来就长，不需要分组（每段一个单元）。

用法：python3 -I structure_modern.py <输入json> <输出目录> <书名> [只取前N章]
输入：[{"章":1,"标题":"第一章 科学边界","段落":["…","…"]}, …]
输出：<输出目录>/全文.json  {"书","章":[{"章","标题","段":[{"id","文"}],"单元":[["1.1","1.4"],…]}]}
"""
import json,sys,re
src,out,name=sys.argv[1],sys.argv[2],sys.argv[3]
N=int(sys.argv[4]) if len(sys.argv)>4 else None
MIN,MAX=220,520
d=json.load(open(src,encoding='utf-8'))
if N: d=d[:N]
res={"书":name,"章":[]}
for c in d:
    n=c['章']; paras=[p.strip() for p in c['段落'] if p.strip()]
    segs=[{"id":f"{n}.{i+1}","文":p} for i,p in enumerate(paras)]
    units=[]; cur=[]; L=0
    for s in segs:
        brk=bool(re.fullmatch(r'[……\-—*＊·\s]+',s['文']))   # 场景分隔（如单独一行“……”）
        if cur and (L+len(s['文'])>MAX or brk):
            units.append(cur); cur=[]; L=0
        cur.append(s['id']); L+=len(s['文'])
        if L>=MIN: units.append(cur); cur=[]; L=0
    if cur:
        if units and L<MIN//2: units[-1]+=cur      # 章末太短的尾巴并进上一组
        else: units.append(cur)
    title=re.sub(r'\s+','',c['标题'].split(' ',1)[1]) if ' ' in c['标题'] else c['标题']
    res['章'].append({"章":n,"标题":title,"段":segs,"单元":[[u[0],u[-1]] for u in units]})
json.dump(res,open(f'{out}/全文.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
for c in res['章']: print(c['章'],c['标题'],len(c['段']),'段',len(c['单元']),'个解释单元')
