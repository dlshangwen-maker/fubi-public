"""通用版索引合并（配合 提示词_02_索引_通用.md 的输出格式：身份/关系自带"从"）。
用法：python3 -I merge_index_通用.py <生成/书 目录> <全文.json> [归并表.json]
归并表：{"不同章里的名字":"标准名"}，人工填（例：{"大史":"史强"}）。
输出：<书>/索引_合并.json —— 人物（别称带"从"、身份按"从"排序、关系、事迹）、概念、事件。
"""
import json,glob,sys,os
B,TXTP=sys.argv[1],sys.argv[2]
ALIAS=json.load(open(sys.argv[3],encoding='utf-8')) if len(sys.argv)>3 and os.path.exists(sys.argv[3]) else {}
PERSTORY=bool(ALIAS.pop('_各篇独立',False))   # 短篇集：同名人物只在同一篇内合并（故乡的"我"不是社戏的"我"）
ALIAS={k:v for k,v in ALIAS.items() if not k.startswith('_')}
k=lambda p:tuple(int(x) for x in p.split('.'))
TXT=json.load(open(TXTP,encoding='utf-8'))
SEGS=[(s['id'],s['文']) for c in TXT['章'] for s in c['段']]
def first_pos(w,after='1.1'):
    for sid,t in SEGS:
        if k(sid)>=k(after) and w in t: return sid
    return None
people={}; concepts={}; events=[]
for f in sorted(glob.glob(f'{B}/索引/第*章.json')):
    d=json.load(open(f,encoding='utf-8'))
    for p in d['人物']:
        name=ALIAS.get(p['名'],p['名'])
        key=(p['首次'].split('.')[0]+'|'+name) if PERSTORY else name
        e=people.setdefault(key,{'名':name,'篇':p['首次'].split('.')[0] if PERSTORY else None,'别称':[],'首次':p['首次'],'出场':'','身份':[],'关系':[],'事迹':[],'备注':[]})
        for a in p.get('这章的叫法',[]):
            if a not in [x['称'] for x in e['别称']]:
                fp=first_pos(a,p['首次'].split('.')[0]+'.1')
                e['别称'].append({'称':a,'从':fp if fp and fp.split('.')[0]==p['首次'].split('.')[0] else p['首次']})
        if k(p['首次'])<k(e['首次']): e['首次']=p['首次']
        if p.get('出场') and (not e['出场'] or k(p['出场'])<k(e['出场'])): e['出场']=p['出场']
        e['身份']+=[x for x in p.get('身份',[]) if x.get('从')]
        for r in p.get('关系',[]):
            rr=[ALIAS.get(r[0],r[0]),r[1],r[2] if len(r)>2 else p['首次']]
            if rr[:2] not in [x[:2] for x in e['关系']]: e['关系'].append(rr)
        if p.get('这章做了什么'): e['事迹'].append({'从':p['首次'],'写':p['这章做了什么']})
        if p.get('备注'): e['备注'].append(p['备注'])
    for c in d['概念']:
        if c['词'] not in concepts: concepts[c['词']]=c
    events+=d['事件']
for n,e in people.items():
    hit=[a['从'] for a in e['别称'] if a['称']==e['名']]
    e['名可显示从']=min(hit,key=k) if hit else None
    for key in ('别称','身份','事迹'): e[key].sort(key=lambda x:k(x['从']))
out={'人物':sorted(people.values(),key=lambda e:k(e['首次'])),'概念':sorted(concepts.values(),key=lambda c:k(c['首次'])),'事件':events}
json.dump(out,open(f'{B}/索引_合并.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
print('人物',len(out['人物']),'概念',len(out['概念']),'事件',len(out['事件']))
