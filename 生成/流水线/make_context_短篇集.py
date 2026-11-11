"""短篇集：为第 N 篇生成上下文——只含这一篇的人物、概念、事件（各篇独立，不带入其他篇）。
用法：python3 -I make_context_短篇集.py <生成/书 目录> <N>
概念直接从 索引/第00N章.json 读（合并版按全书去重了，会丢掉别篇的同名词）。"""
import json,sys
B=sys.argv[1]; N=int(sys.argv[2])
d=json.load(open(f'{B}/索引_合并.json',encoding='utf-8'))
raw=json.load(open(f'{B}/索引/第{N:03d}章.json',encoding='utf-8'))
ppl=[{'名(内部)':e['名'],'名可显示从':e.get('名可显示从'),'首次':e['首次'],'别称':e['别称'],'身份':e['身份'],'关系':e['关系'],'事迹':e['事迹'],'备注':e['备注']}
     for e in d['人物'] if e.get('篇')==str(N)]
ctx={'说明':f'第{N}篇的索引（只有这一篇；各篇独立，不要提别篇）。每条信息都有"从"：写某一段的卡片时，只能用"从"不晚于该段的信息。"名(内部)"在"名可显示从"之前读者还不知道，只能用当时已出现的别称。',
     '人物':ppl,'概念':raw['概念'],'本篇事件（只用于判断位置，不能提前说）':raw['事件']}
json.dump(ctx,open(f'{B}/输入/上下文_第{N:03d}篇.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
print(N,len(ppl),'人',len(raw['概念']),'概念')
