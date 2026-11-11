"""合并每回的索引成全书累积索引。
同一人物不同回的条目合并：别称并集，身份按"从哪一段起"分版本。
ALIAS：不同回里对同一人物用了不同的"名"，手工归并到同一个标准名。
注意：归并只影响数据组织；读者看到哪个名字、哪个身份，由"从"字段控制（读到之前不显示）。"""
import json,glob,os,re,sys
B=sys.argv[1] if len(sys.argv)>1 else '红楼梦'
ALIAS={'迎春':'贾迎春','探春':'贾探春','惜春':'贾惜春','警幻仙姑':'警幻仙子','贾琏之妻':'王熙凤',
       '黛玉之母':'贾敏','贾源':'荣国公','荣公':'荣国公','皇上':'皇帝','薛家姨母':'薛姨妈','那僧':'僧（茫茫大士）','那道人':'道人（渺渺真人）',
       '甄老爷':'甄士隐','绛珠':'绛珠仙草'}
def k(pos): a,b=pos.split('.'); return (int(a),int(b))
people={}; concepts={}; events=[]
for f in sorted(glob.glob(f'{B}/索引/第*回.json')):
    d=json.load(open(f))
    for p in d['人物']:
        name=ALIAS.get(p['名'],p['名'])
        e=people.setdefault(name,{'名':name,'别称':[],'首次':p['首次'],'出场':'','身份':[],'关系':[],'事迹':[],'备注':[]})
        for a in p['这回的叫法']:
            if a not in [x['称'] for x in e['别称']]: e['别称'].append({'称':a,'从':p['首次']})
        if k(p['首次'])<k(e['首次']): e['首次']=p['首次']
        if p.get('出场') and (not e['出场'] or k(p['出场'])<k(e['出场'])): e['出场']=p['出场']
        if p.get('这回交代的身份'): e['身份'].append({'从':p['首次'],'写':p['这回交代的身份']})
        for r in p.get('关系',[]):
            rr=[ALIAS.get(r[0],r[0]),r[1],p['首次']]
            if rr[:2] not in [x[:2] for x in e['关系']]: e['关系'].append(rr)
        if p.get('这回做了什么'): e['事迹'].append({'从':p['首次'],'写':p['这回做了什么']})
        if p.get('备注'): e['备注'].append(p['备注'])
    for c in d['概念']:
        if c['词'] not in concepts: concepts[c['词']]=c
    events+=d['事件']
# 别称的“从”：在原文里实际第一次出现的段（找不到就用该人物在那一回的首次）
TXT=json.load(open(f'../文本数据/{B}/全文.json'))
SEGS=[(s['id'],s['文']) for h in TXT['回'] for s in h['段']]
def first_pos(word,after):
    for sid,tx in SEGS:
        if k(sid)>=k(after) and word in tx: return sid
    return None
for n,e in people.items():
    for a in e['别称']:
        fp=first_pos(a['称'],'1.1')
        # 原文里能找到、且和索引记录在同一回：用原文的精确位置；否则保留索引记录（如“姓贾名化”里找不到“贾化”）
        if fp and fp.split('.')[0]==a['从'].split('.')[0]: a['从']=fp
for n,e in people.items():
    # 标准名本身也是到它在书里出现时才能显示；之前人物卡用当时最早的叫法做标题
    hit=[a['从'] for a in e['别称'] if a['称']==n]
    e['名可显示从']=min(hit,key=k) if hit else None
    for key in ('别称','身份','事迹'): e[key].sort(key=lambda x:k(x['从']))
out={'人物':sorted(people.values(),key=lambda e:k(e['首次'])),'概念':sorted(concepts.values(),key=lambda c:k(c['首次'])),'事件':events}
json.dump(out,open(f'{B}/索引_合并.json','w'),ensure_ascii=False,indent=1)
print('人物',len(out['人物']),'概念',len(out['概念']),'事件',len(out['事件']))
