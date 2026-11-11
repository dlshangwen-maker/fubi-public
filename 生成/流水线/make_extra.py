"""重度带读用的"更多伏笔"（通用，2026-10-23）。
用法：python3 -I make_extra.py <书文件夹，如 生成/猎犬> <全文.json> <前缀字母>
来源两处，按同一套规则筛：
  ① 伏笔定位里落选的候选（定位.json，没进 最终.json 的）
  ② 示范问答里类型为"后面有"的问题
保留条件：答案在书里（回收段存在、在提出之后）；落选理由不是"离核心太近/不放"（剧透风险）、"重复"、"太泛/太宽"；
  提出段上没有正式伏笔，同一段只留一条；答案和正式伏笔（或已选的）答案相距 5 段以内 = 重复，不要；问题和揭晓说明里的人名不早于各自位置（借用 check_clues.py 的检查）。
没有揭晓锚句的，用答案那段最后一句（阅读器按"那一句读过"判定揭晓）。
输出：<书文件夹>/伏笔/重度加亮.json
"""
import json,sys,os,re,subprocess,tempfile
G,TXTP,PFX=sys.argv[1:4]
B=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))+'/'
J=lambda p:json.load(open(p if os.path.isabs(p) else B+p,encoding='utf-8'))
k=lambda p:tuple(int(x) for x in p.split('.'))
T=J(TXTP); chs=T.get('章') or T.get('回')
SEG={s['id']:s['文'] for c in chs for s in c['段']}
fin=J(G+'/伏笔/最终.json'); finQ={x['问题'] for x in fin}; finP={x['提出'] for x in fin}
cand={x.get('id'):x for x in (J(G+'/伏笔/候选.json') if os.path.exists(B+G+'/伏笔/候选.json') else [])}
loc=J(G+'/伏笔/定位.json') if os.path.exists(B+G+'/伏笔/定位.json') else []
qa=J(G+'/示范问答/示范问答.json') if os.path.exists(B+G+'/示范问答/示范问答.json') else []
BADNOTE=re.compile(r'不放|太近.*核心|核心太近|重复|太泛|太宽|剧透')
def last_sent(t):
    t=re.sub(r'⟦[^⟧]*⟧','',t).strip()
    parts=[p for p in re.split(r'(?<=[。！？!?])',t) if p.strip()]
    s=(parts[-1] if parts else t).strip()
    s=re.sub(r'^[”’」』"\']+','',s)
    return s[-14:] if len(s)>14 else s
out=[]; used=set(finP)
def add(src,pid,q,ans,expl,a1,a2,qa=None):
    if pid not in SEG or ans not in SEG or k(ans)<=k(pid) or pid in used: return
    if q in finQ: return
    # 和正式伏笔重复：答案落在某条正式伏笔的答案前后 5 段之内（同一章）
    for f in fin:
        R=f.get('回收')
        if R in SEG and R.split('.')[0]==ans.split('.')[0] and abs(k(R)[1]-k(ans)[1])<=5: return
    for o in out:
        if o['回收'].split('.')[0]==ans.split('.')[0] and abs(k(o['回收'])[1]-k(ans)[1])<=5: return
    a2=a2 if a2 and SEG[ans].count(a2)==1 else last_sent(SEG[ans])
    if a1 and SEG[pid].count(a1)!=1: a1=None
    used.add(pid)
    out.append({"id":f"{PFX}{len(out)+1:02d}","来源":src,"提出":pid,"问题":q,"回收":ans,"回收说明":expl,"提出锚句":a1,"回收锚句":a2,"距离":"重度",**({"qa":qa} if qa else {})})
for x in loc:
    if x.get('入选') or x['问题'] in finQ: continue
    if BADNOTE.search(x.get('备注','')): continue
    R=x.get('回收')
    if not R or R=='无' or not x.get('回收说明'): continue
    c=cand.get(x.get('id'),{})
    add('落选候选',x['提出'],x['问题'],R,x['回收说明'],x.get('提出锚句') or c.get('提出锚句'),x.get('回收锚句'))
for x in qa:
    if x.get('类型')!='后面有' or not x.get('回收') or not x.get('回收说明'): continue
    add('示范问答',x['锚点'],x['问题'],x['回收'],x['回收说明'],None,x.get('回收锚句'),x['id'])
# 人名 / 后文词检查：借用 check_clues.py，只看"早于位置"的那几类
with tempfile.NamedTemporaryFile('w',suffix='.json',delete=False,encoding='utf-8') as f: json.dump(out,f,ensure_ascii=False); tmp=f.name
args=['python3','-I',B+'生成/流水线/check_clues.py',tmp,B+TXTP if not os.path.isabs(TXTP) else TXTP,B+G+'/索引_合并.json']
if os.path.exists(B+G+'/后文名单.json'): args.append(B+G+'/后文名单.json')
r=subprocess.run(args,capture_output=True,text=True).stdout
bad=set()
for line in r.splitlines():
    m=re.match(r'^(\S+) \S+ →',line)
    if m and re.search(r'才出现|后文词|禁用词',line): bad.add(m.group(1)); print('去掉',line)
out=[x for x in out if x['id'] not in bad]
for i,x in enumerate(out): x['id']=f"{PFX}{i+1:02d}"
json.dump(out,open(B+G+'/伏笔/重度加亮.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
print(G,'更多伏笔',len(out),'条（落选候选',sum(1 for x in out if x['来源']=='落选候选'),'· 示范问答',sum(1 for x in out if x['来源']=='示范问答'),'）')
