"""任务登记表：每一种要用模型的活，在这里登记一次。
每项写清：用哪份提示词（就是 生成/流水线/ 里第一阶段用过的那些文件）、怎么把变量填进去、输出要满足什么格式、没有真模型时假模型给什么。

加一种新任务 = 在 TASKS 里加一项；模型调用层（model.py）、生成服务（pipeline.py）都不用改。
"""
import os,re,json,glob
import config
def _read(p):
    with open(p,encoding='utf-8') as f: return f.read()
def _load(p):
    with open(p,encoding='utf-8') as f: return json.load(f)

def _prompt(fn):
    p=os.path.join(config.PROMPTS,fn)
    t=_read(p)
    return t.split('\n---\n',1)[1] if '\n---\n' in t else t   # 文件开头的"说明"部分（---之前）是写给人看的，不发给模型
def _rule(kind):
    fn={'小说':'规则_现代小说.txt','古典小说':'规则_小说.txt','短篇集':'规则_短篇集.txt','非虚构':'规则_非虚构.txt'}.get(kind,'规则_现代小说.txt')
    return _read(os.path.join(config.PROMPTS,fn))
def _fill(t,v):
    return re.sub(r'\{(\w+)\}',lambda m:str(v.get(m.group(1),m.group(0))),t)

SYSTEM='你是"伏笔"阅读器的内容编辑。严格遵守给你的不剧透规则；只输出要求的 JSON，不要任何解释文字。'

class Task:
    json_mode=True
    prompt=None
    def render(self,v):
        user=_fill(_prompt(self.prompt),v)
        parts=[user]
        if v.get('rule_text'): parts.append('【不剧透规则】\n'+_fill(v['rule_text'],v))
        for k,label in (('context','【截至这里的人物、概念、前几章事件】'),('text','【原文】')):
            if v.get(k): parts.append(label+'\n'+(v[k] if isinstance(v[k],str) else json.dumps(v[k],ensure_ascii=False)))
        return SYSTEM,'\n\n'.join(parts)
    def validate(self,out,v): return []
    def mock(self,v): return {}

def _need(d,keys,where=''):
    return [f'{where}缺少"{k}"' for k in keys if k not in d]

# ---------- 第 2 步：索引（每章一次） ----------
class Index(Task):
    prompt='提示词_02_索引_通用.md'
    def validate(self,out,v):
        p=_need(out,['人物','概念','事件']) if isinstance(out,dict) else ['要输出一个对象']
        if p: return p
        ids=set(v.get('ids',[]))
        for e in out['人物']:
            p+=_need(e,['名','首次','身份'],'人物 ')
            for x in e.get('身份',[]):
                if ids and x.get('从') not in ids: p.append(f'人物"{e.get("名")}"身份的"从"={x.get("从")} 不是这一章的段号')
        for c in out['概念']:
            if ids and c.get('首次') not in ids: p.append(f'概念"{c.get("词")}"的首次={c.get("首次")} 不是这一章的段号')
        return p[:20]
    def mock(self,v):
        f=os.path.join(v.get('done_dir',''),'索引',f"第{int(v['chapter']):03d}章.json")
        if os.path.exists(f): return _load(f)
        return {"人物":[],"概念":[],"事件":[{"段":v['ids'][0],"事":"（假模型：这一章的事件）"}] if v.get('ids') else []}

# ---------- 第 4 步：解释卡片（每章一次，按解释单元） ----------
class Cards(Task):
    def __init__(self,prompt): self.prompt=prompt
    def validate(self,out,v):
        if not isinstance(out,dict): return ['要输出一个对象，键是单元第一段的编号']
        p=[]
        for u in v.get('units',[]):
            if u not in out: p.append(f'少了单元 {u}'); continue
            for lv in ('入门','标准','深入'):
                c=out[u].get(lv) if isinstance(out[u],dict) else None
                if not isinstance(c,dict): p.append(f'单元 {u} 缺"{lv}"'); continue
                p+=_need(c,['白话','展开','前置'],f'单元 {u} {lv} ')
                if len(c.get('白话',''))>80: p.append(f'单元 {u} {lv} 白话太长（{len(c["白话"])} 字，要 ≤50）')
        return p[:20]
    def mock(self,v):
        f=os.path.join(v.get('done_dir',''),'卡片',f"第{int(v['chapter']):03d}章.json")
        if os.path.exists(f): return _load(f)
        z=lambda s:{"白话":s,"展开":"（假模型生成的占位解释。配置真模型后，这里是按不剧透规则写的解释。）","前置":""}
        return {u:{"入门":z('（假模型）这几段讲了什么。'),"标准":z('（假模型）这几段的写法。'),"深入":z('（假模型）背景和手法。')} for u in v.get('units',[])}

# ---------- 第 5 步第二道：剧透复查（每章一次） ----------
class Review(Task):
    prompt='提示词_05b_剧透复查.md'
    def validate(self,out,v):
        p=_need(out,['改']) if isinstance(out,dict) else ['要输出一个对象']
        for x in (out.get('改',[]) if isinstance(out,dict) else []):
            p+=_need(x,['单元','档','字段','改为'],'改 ')
        return p[:20]
    def mock(self,v): return {"改":[],"灰区":[]}

# ---------- 第 7 步：回顾（每章一次） ----------
class Recap(Task):
    prompt='提示词_07_回顾.md'
    def validate(self,out,v):
        p=_need(out,['一句话','详细','小节']) if isinstance(out,dict) else ['要输出一个对象']
        if p: return p
        ids=v.get('ids',[])
        for x in out['小节']:
            if ids and x.get('到') not in ids: p.append(f'小节的"到"={x.get("到")} 不是这一章的段号')
        if ids and out['小节'] and out['小节'][-1].get('到')!=ids[-1]: p.append(f'最后一个小节的"到"应该是这一章最后一段 {ids[-1]}')
        return p
    def mock(self,v):
        f=os.path.join(v.get('done_dir',''),'回顾','分',f"第{int(v['chapter']):03d}章.json")
        if os.path.exists(f): return _load(f)
        ids=v.get('ids',['1.1'])
        return {"回":v['chapter'],"一句话":"（假模型）这一章的一句话回顾。","详细":["（假模型）这一章的详细回顾。"],"小节":[{"到":ids[-1],"写":"（假模型）这一节讲了什么。"}]}

# ---------- 第 8.5 步：词语表（每章一次） ----------
class Gloss(Task):
    prompt='提示词_09_词语表.md'
    def validate(self,out,v):
        if not isinstance(out,list): return ['要输出一个列表']
        p=[]; seg=v.get('seg',{})
        for w in out:
            p+=_need(w,['词','义','首次'],'词条 ')
            if seg and w.get('首次') in seg and w.get('词') and w['词'] not in seg[w['首次']]: p.append(f'"{w["词"]}"不在 {w["首次"]} 那一段里')
        return p[:20]
    def mock(self,v):
        f=os.path.join(v.get('done_dir',''),'词语表.json')
        if os.path.exists(f):
            ids=set(v.get('ids',[])); return [w for w in _load(f) if w.get('首次') in ids]
        return []

# ---------- 实时：自由提问 ----------
class Ask(Task):
    prompt='提示词_11_自由提问.md'
    def validate(self,out,v):
        p=_need(out,['类型','回答']) if isinstance(out,dict) else ['要输出一个对象']
        if not p and out['类型'] not in ('读过的','后面有','书外','书里没有'): p.append('类型只能是 读过的/后面有/书外/书里没有')
        return p
    def mock(self,v): return {"类型":"书外","回答":"（假模型）配置了真模型后，这里是按阅读进度、不剧透的回答。","引用":[],"回收":"","回收说明":"","回收锚句":""}

# ---------- 实时：读后感 ----------
class Reflect(Task):
    prompt='提示词_06_读书小结.md'
    json_mode=True
    def render(self,v):
        s,u=Task.render(self,v)
        return s,u+'\n\n【读者的记录】\n'+json.dumps(v.get('record',{}),ensure_ascii=False)+'\n\n输出 JSON：{"感悟":"……","线索":["……"],"接着想":"……"}'
    def validate(self,out,v): return _need(out,['感悟']) if isinstance(out,dict) else ['要输出一个对象']
    def mock(self,v): return {"感悟":"（假模型）配置了真模型后，这里是以你的口吻写的读后感。","线索":[],"接着想":""}

# ---------- 第 1.5 步：译名表（全书一次）、翻译（每章一次）——外文书 ----------
class Terms(Task):
    prompt='提示词_01a_译名表.md'
    def validate(self,out,v):
        if not isinstance(out,dict) or not isinstance(out.get('译名'),list): return ['要输出 {"译名": [...]}']
        return [f'第 {i+1} 条缺"原文"或"中文"' for i,x in enumerate(out['译名']) if not (isinstance(x,dict) and x.get('原文') and x.get('中文'))][:10]
    def mock(self,v): return {'译名':[]}
class Translate(Task):
    prompt='提示词_01b_翻译_可读版.md'
    def render(self,v):
        s,u=Task.render(self,v)
        return s,u+'\n\n输出 JSON 对象：键是段号，值是这一段的中文。'
    def validate(self,out,v):
        if not isinstance(out,dict): return ['要输出一个对象，键是段号']
        src=v.get('src',{}); p=[]
        miss=[k for k in src if not str(out.get(k,'')).strip()]
        if miss: p.append('少了这些段：'+'、'.join(miss[:15]))
        extra=[k for k in out if k not in src]
        if extra: p.append('多出不存在的段号：'+'、'.join(extra[:8]))
        short=[k for k in src if k in out and len(src[k])>=80 and len(str(out[k]))<len(src[k])*0.2]
        if short: p.append('这些段译文太短，可能漏译：'+'、'.join(short[:8]))
        return p
    def mock(self,v):
        d=v.get('done',{})
        return {k:(d.get(k) or '（假模型译文）'+t) for k,t in v.get('src',{}).items()}

TASKS={
    'terms':Terms(),
    'translate':Translate(),
    'index':Index(),
    'cards_novel':Cards('提示词_03_解释_现代小说.md'),
    'cards_nonfiction':Cards('提示词_03_解释_非虚构.md'),
    'review':Review(),
    'recap':Recap(),
    'gloss':Gloss(),
    'ask':Ask(),
    'reflect':Reflect(),
}
RULE=_rule
