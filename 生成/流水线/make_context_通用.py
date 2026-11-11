"""为第 N 章生成"截至本章"的上下文（通用版）。只含首次 ≤ 本章末的人物；别称、身份、关系、事迹都截到本章；概念截到本章；前几章事件。
用法：python3 -I make_context_通用.py <生成/书 目录> <N>
"""
import json,sys
B=sys.argv[1]; N=int(sys.argv[2])
d=json.load(open(f'{B}/索引_合并.json',encoding='utf-8'))
k=lambda p:tuple(int(x) for x in p.split('.'))
lim=(N,10**6)
ppl=[]
for e in d['人物']:
    if k(e['首次'])>lim: continue
    ppl.append({'名(内部)':e['名'],'名可显示从':e.get('名可显示从'),'首次':e['首次'],
      '别称':[a for a in e['别称'] if k(a['从'])<=lim],
      '身份':[x for x in e['身份'] if k(x['从'])<=lim],
      '关系':[r for r in e['关系'] if k(r[2])<=lim],
      '事迹':[x for x in e['事迹'] if k(x['从'])<=lim],'备注':e['备注']})
ctx={'说明':f'截至第{N}章的索引。每条信息都有"从"（从哪一段起读者才知道）；写某一段的卡片时，只能用"从"不晚于该段的信息。"名(内部)"只是数据里的标识：在"名可显示从"之前，读者还不知道这个名字，只能用当时已出现的别称。',
     '人物':ppl,'概念':[c for c in d['概念'] if k(c['首次'])<=lim],
     '前几章事件':[e for e in d['事件'] if k(e['段'])<(N,0)]}
json.dump(ctx,open(f'{B}/输入/上下文_第{N:03d}章.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
print(N,len(ppl),'人')
