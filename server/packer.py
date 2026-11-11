"""打包库（2026-10-26 从 build_demo.py 抽出）：把一本书的流水线产物打成阅读器要的数据。
只有这一份：demo 打包（生成/build_demo.py）和服务端都 import 它，保证两边一模一样。

pack_book(全文路径, 产物文件夹, key=, unit=, **选项) → dict
  - 产物文件夹里没有的东西（卡片、伏笔、回顾、示范问答、索引、词语表、主线）都可以缺：
    缺了就是空的，阅读器照样能读、能记（导入的书在接模型之前就是这样）。
  - 路径都是绝对路径或相对 ROOT（Read Book 文件夹）。
"""
import json,os,re,glob
from collections import Counter
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))+"/"
def _p(p): return p if os.path.isabs(p) else ROOT+p
def _j(p,default=None):
    p=_p(p)
    if not os.path.exists(p):
        if default is not None: return default
        raise FileNotFoundError(p)
    with open(p,encoding='utf-8') as f: return json.load(f)

# ---------- 主线（产物文件夹/主线.json） ----------
def mainline(folder,IX,sus):
    p=_p(folder.rstrip('/')+'/主线.json')
    if not os.path.exists(p): return None
    m=json.load(open(p,encoding='utf-8')); ids={x['id'] for x in sus}
    if m['出现']!='前言' and m['出现'] not in IX: raise ValueError('主线出现位置不存在：'+m['出现'])
    bad=[x for x in m['碎片'] if x not in ids]
    if bad: raise ValueError('主线碎片不在伏笔里：'+','.join(bad))
    note=m.get('碎片说明',{}); miss=[x for x in m['碎片'] if x not in note]
    if miss: raise ValueError('主线碎片缺"这一块说明了什么"：'+','.join(miss))
    return {"q":m['问题'],"from":m['出现'],"pieces":m['碎片'],"end":m['收尾'],"notes":note}

GENW=set(('他们 她们 我们 你们 一个人 一个女人 朋友 车夫 巡警 秀才 老爷 太太 先生 少爷 掌柜 伙计 地保 酒客 女人 男人 老头子 小孩 孩子们 父亲 母亲 哥哥 大哥 我大哥 妹子 教师 总长 同乡 小厮 举人老爷 她 他 那人 丈夫 爸爸 妈妈 奶奶 年轻人 同事 首长 将军 主任 医生 教授 孩子 儿子 妻子 小家伙 追随者 大王 巫师 司机 少校 那位便衣 穿警服的年轻人 杨冬的母亲 她父亲 我的一个学生 叶文洁的学生 黑衣人').split())

def pack_book(txtp,folder,key,unit='章',store=None,**opt):
    """txtp：全文.json；folder：产物文件夹（生成/<书>/）；key：书的标识；store：浏览器里存记录用的键"""
    G=folder.rstrip('/')+'/'
    t=_j(txtp); hui=[]; props=[]
    for c in t['章']:
        hui.append({"n":c['章'],"t":c['标题'],"first":len(props)})
        for s_ in c['段']: props.append({"n":s_['id'],"zh":s_['文'],"poem":False,"h":c['章'],**({"k":s_['类']} if s_.get('类') else {}),**({L:s_[L] for L in ('en','de','fr') if s_.get(L)})})
    SID=[p['n'] for p in props]; IX={n:i for i,n in enumerate(SID)}; SEG=[p['zh'] for p in props]
    # 解释卡片：按解释单元写，展开到单元里的每一段；没有卡片的单元就不放（阅读器显示"暂无解释"）
    raw={}
    for f in sorted(glob.glob(_p(G+'卡片/第*章.json'))): raw.update(_j(f))
    cards={}; units={}
    for c in t['章']:
        for a_,b_ in c.get('单元',[[s['id'],s['id']] for s in c['段']]):
            for i in range(IX[a_],IX[b_]+1):
                units[SID[i]]=[IX[a_],IX[b_]]
                if a_ in raw: cards[SID[i]]=raw[a_]
    fin=_j(G+'伏笔/最终.json',[])
    sus=[{"id":f['id'],"提出":f['提出'],"揭晓":f['回收'] if f['回收'] in IX else None,"问题":f['问题'],"兑现说明":f['回收说明'],"提出锚句":f.get('提出锚句'),"揭晓锚句":f.get('回收锚句')} for f in fin]
    qa=_j(G+'示范问答/示范问答.json',[])
    rec=_j(G+'回顾/回顾.json',[])
    for r in rec:
        for x in r['小节']: x.setdefault('写',x.get('标题',''))
    idx=_j(G+'索引_合并.json',{"人物":[],"概念":[],"事件":[]})
    out,names=_people(idx,IX,SID,SEG)
    d={"key":store or ('rb_'+key),"novel":True,"unit":unit,"props":props,"hui":hui,"cards":cards,"units":units,"suspense":sus,
       "qa":qa,"recap":rec,"people":out,"names":names,"scope":len(t['章']),"main":mainline(G,IX,sus)}
    d.update(opt); return d

def _people(idx,IX,SID,SEG):
    # 人物：只链名字式的称呼（≥2 字、不是泛称、只属于一个人）；身份、关系直接用索引里带"从"的
    cnt=Counter((e.get('篇'),a['称']) for e in idx['人物'] for a in e['别称'])   # 短篇集：同一篇里只属于一个人就行
    persons=[]
    for e in idx['人物']:
        al=[]
        for a in e['别称']:
            w=a['称']
            f=next((i for i in range(IX.get(a['从'],0),len(SEG)) if w in SEG[i] and (not e.get('篇') or SID[i].split('.')[0]==e['篇'])),None)
            if f is None: continue
            al.append([w,f,len(w)>=2 and w not in GENW and cnt[(e.get('篇'),w)]==1 and '备注' not in w and not re.fullmatch(r'(一个|那个|这个).*',w) and not w.endswith('的') and not (len(e['别称'])>1 and w!=e['名'] and (re.search(r'(大臣|总督|巡抚|提督|皇帝|陛下|太后|公使|领事|中堂|亲王|大学士)$',w) or re.fullmatch(r'.{0,2}(使|皇|帝|上|工|者|官|帅)',w)))])
        if any(x[2] for x in al): persons.append((e,al))
    # ① 称呼只从它在书里指这个人的那一段起才链 ② 别人全名的一部分不单独链 ③ 落在一个更长的概念词里的不链
    allnames=[e['名'] for e,al in persons]
    LONG=sorted({c['词'] for c in idx['概念'] if len(c['词'])>=3},key=len,reverse=True)
    pats=sorted([(w,i,f) for i,(e,al) in enumerate(persons) for w,f,l in al if l and not (w!=e['名'] and any(n!=e['名'] and re.search(r'[·・]'+re.escape(w)+'$',n) for n in allnames))],key=lambda x:-len(x[0]))
    names={}; appear=[[] for _ in persons]; ac=[Counter() for _ in persons]
    for si,tx in enumerate(SEG):
        taken=[]; got={}
        st=SID[si].split('.')[0]
        inlong=[m.span() for L_ in LONG if L_ in tx for m in re.finditer(re.escape(L_),tx)]
        for w,i,f in pats:
            if persons[i][0].get('篇') and persons[i][0]['篇']!=st: continue
            if si<f: continue
            tcut=tx.find('⟦表:')
            for m in re.finditer(re.escape(w),tx):
                s0,e0=m.span()
                if tcut>=0 and s0>=tcut: continue
                if any(a<=s0 and e0<=b and (b-a)>len(w) and w not in tx[a:b][:len(w)+0] or (a<=s0 and e0<=b and (b-a)>len(w) and not tx[a:b].startswith(w)) for a,b in inlong): continue
                if any(s0<b and a<e0 for a,b,_ in taken): continue
                taken.append((s0,e0,i)); ac[i][w]+=1
                if si not in appear[i]: appear[i].append(si)
        for s0,e0,i in sorted(taken):
            if i in got: continue
            got[i]=1; names.setdefault(SID[si],[]).append([s0,e0,i])
    drop={i for i,(e,al) in enumerate(persons) if len(appear[i])==1 and not e.get('出场')}
    for k_ in list(names):
        names[k_]=[x for x in names[k_] if x[2] not in drop]
        if not names[k_]: del names[k_]
    out=[]
    for i,(e,al) in enumerate(persons):
        if not appear[i] or i in drop: continue
        ap=sorted(appear[i])
        ids=[[IX[x['从']],x['写']] for x in e['身份'] if x['从'] in IX]
        vis=e.get('名可显示从'); nf=IX.get(vis) if vis else None
        early=None
        if nf is None or nf>ap[0]:
            pre=[a for a in al if a[1]<=ap[0]]
            early=(pre[0][0] if pre else al[0][0])
        out.append({"id":i,"name":e['名'],"nameFrom":nf,"al":[[w,f] for w,f,l in al],"cnt":dict(ac[i]),"ids":ids,"ap":ap,"first":ap[0],"early":early,"rels":[]})
    O={x['name']:x for x in out}
    for x in out:
        for r in next(e for e,al in persons if e['名']==x['name']).get('关系',[]):
            if r[0] in O and r[2] in IX: x['rels'].append([O[r[0]]['id'],r[1],max(IX[r[2]],O[r[0]]['first'],x['first'])])
    return out,names
