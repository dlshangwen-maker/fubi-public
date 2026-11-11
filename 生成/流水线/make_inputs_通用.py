"""给子任务用的输入：每章一份"编号"原文（建索引、伏笔用）和一份"按解释单元分组"的原文（写卡片用）。
段落类型照实标出来（【提要】【小标题】【引文】【文件·默认折叠】），写卡片时按类型处理。
用法：python3 -I make_inputs_通用.py <全文.json> <生成/书/输入 目录> <单位：章/篇>
"""
import json,sys,os
d=json.load(open(sys.argv[1],encoding='utf-8')); out=sys.argv[2]; U=sys.argv[3] if len(sys.argv)>3 else '章'
os.makedirs(out,exist_ok=True)
TAG={'提要':'【提要】','小标题':'【小标题】','引文':'【引文】','文件':'【文件·默认折叠】'}
for c in d['章']:
    n=c['章']; S={s['id']:s for s in c['段']}; ids=[s['id'] for s in c['段']]
    line=lambda s:f"{s['id']}　{TAG.get(s.get('类'),'')}{s['文']}"
    head=f"《{d['书']}》第 {n} {U}　{c['标题']}"
    open(f'{out}/第{n:03d}{U}_编号.txt','w',encoding='utf-8').write(head+'\n\n'+'\n\n'.join(line(s) for s in c['段'])+'\n')
    parts=[head+f'　（共 {len(c["单元"])} 个解释单元）','']
    for a,b in c['单元']:
        seg=ids[ids.index(a):ids.index(b)+1]
        parts.append(f'【单元 {a}～{b}】（读者读到 {b} 为止）')
        parts+= [line(S[x]) for x in seg]; parts.append('')
    open(f'{out}/第{n:03d}{U}_单元.txt','w',encoding='utf-8').write('\n'.join(parts))
    print(n,len(ids),'段',len(c['单元']),'单元')
