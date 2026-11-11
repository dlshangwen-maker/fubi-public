"""构建 demo（2026-10-27 起只有一个给用户的 demo）：
  生成/自测/单文件版.html  纯单文件版（没有服务端功能），只给 374 项自测、启动检查用
  Demo/伏笔_demo.html      给用户的 demo = 服务端页面 + 网络桩：精编书、找书、下载、导入入口、调整章节都在（由 生成/自测/体验页.py 生成）
原注释：一个文件里放两本书（《逻辑哲学论》《红楼梦》前五回）。
用法：python3 生成/build_demo.py   （会自动找文件夹位置）"""
import json,base64,os,re
B=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))+"/"
J=lambda p:json.load(open(B+p))
k=lambda p:tuple(int(x) for x in p.split('.'))

# ---------- 通用：重度带读的"更多伏笔"（生成/<书>/伏笔/重度加亮.json，make_extra.py 生成）、主线（生成/<书>/主线.json） ----------
def extras(G,IX):
    p=B+G+'伏笔/重度加亮.json'
    if not os.path.exists(p): return []
    return [{"id":f['id'],"提出":f['提出'],"揭晓":f['回收'] if f['回收'] in IX else None,"问题":f['问题'],"兑现说明":f['回收说明'],"提出锚句":f.get('提出锚句'),"揭晓锚句":f.get('回收锚句'),"x":1,**({"qa":f['qa']} if f.get('qa') else {})} for f in json.load(open(p,encoding='utf-8')) if f['提出'] in IX]
def mainline(G,IX,sus):
    p=B+G+'主线.json'
    if not os.path.exists(p): return None
    m=json.load(open(p,encoding='utf-8')); ids={x['id'] for x in sus}
    if m['出现']!='前言' and m['出现'] not in IX: raise SystemExit('主线出现位置不存在：'+m['出现'])
    bad=[x for x in m['碎片'] if x not in ids]
    if bad: raise SystemExit('主线碎片不在伏笔里：'+','.join(bad))
    note=m.get('碎片说明',{}); miss=[x for x in m['碎片'] if x not in note]
    if miss: raise SystemExit('主线碎片缺"这一块说明了什么"：'+','.join(miss))
    return {"q":m['问题'],"from":m['出现'],"pieces":m['碎片'],"end":m['收尾'],"notes":note}

# ---------- 逻辑哲学论 ----------
# 2026-10-21：只用公版来源。命题顺序取自古登堡 #5740 德英对照本（原文.json）；公式图片从古登堡 PDF 重新裁切
d=[{'n':x['n']} for x in J('生成/翻译/逻辑哲学论/原文.json')['命题']]
IMGD='文本数据/逻辑哲学论_图片_公版/'
imgs={f:'data:image/jpeg;base64,'+base64.b64encode(open(B+IMGD+f,'rb').read()).decode() for f in os.listdir(B+IMGD)}
# 2026-10-20 换成自译本（德文为准、参照 1922 年英译）；每条同时带德文、英文原文，阅读器可选 中文 / 原文 / 对照
import sys as _s; _s.path.insert(0,B+'生成/流水线'); from latex_clean import clean as _clean
tr=J('生成/翻译/逻辑哲学论/译文.json'); og=J('生成/翻译/逻辑哲学论/原文.json'); OG={x['n']:x for x in og['命题']}
paras=tr['前言'][:]
tractatus={"key":"rb_demo_tractatus_v1","props":[{"n":x['n'],"zh":tr['命题'][x['n']],"de":_clean(OG[x['n']]['de']),"en":_clean(OG[x['n']]['en'])} for x in d],"cards":J('生成/卡片_合并.json'),
  "suspense":J('生成/悬念线.json'),"qa":J('生成/示范问答.json'),"preface":{"paras":paras,"foot":tr['脚注_命题1'],"de":og['前言']['de'],"en":og['前言']['en'],"foot_de":og['脚注_命题1']['de'],"foot_en":og['脚注_命题1']['en']},"images":imgs,
  "orig":[["de","德文"],["en","英文"]]}
tractatus["main"]=mainline('生成/翻译/逻辑哲学论/',{x['n']:i for i,x in enumerate(d)},tractatus['suspense'])

# ---------- 红楼梦 前五回 ----------
H='生成/红楼梦/'
txt=J('文本数据/红楼梦/全文.json'); N=5
hui=[]; props=[]
for h in txt['回'][:N]:
    hui.append({"n":h['回'],"t":h['回目'],"first":len(props)})
    for s in h['段']: props.append({"n":s['id'],"zh":s['文'],"poem":s.get('类型')=='诗',"h":h['回']})
SEG=[p['zh'] for p in props]; SID=[p['n'] for p in props]; IX={n:i for i,n in enumerate(SID)}
fin=J(H+'伏笔/最终.json')
sus=[{"id":f['id'],"提出":f['提出'],"揭晓":f['回收'] if f['回收'] in IX else None,"问题":f['问题'],"兑现说明":f['回收说明'],"提出锚句":f.get('提出锚句'),"揭晓锚句":f.get('回收锚句')} for f in fin]

# 人物：只链“像名字”的称呼；泛称、几个人共用的称呼不链
idx=J(H+'索引_合并.json'); fix=J(H+'人物卡/身份修订.json')
NOLINK=set(fix.get('_不链接的称呼',[]))
GEN=set('''我 弟 弟子 施主 老先生 老爷 兄 晚生 尊兄 吾兄 太老爷 太爷 新任太爷 女儿 小女 一婢 丫头 这丫头 被卖的丫头 仙子 丽人 姐姐 仙姑 神仙姐姐 奶母 小童 女子 丫鬟 此女子 和尚 那和尚
岳丈 父亲 官府 官儿 妹妹 姑娘 远客 外孙女儿 外甥女儿 母亲 你母亲 姑妈 其母 贱荆 老兄 他父亲 祖母 太君 外祖母 老太太 老母 好祖宗 舅舅 二舅舅 姨父 太太 舅母 二舅母 你娘 姨娘 姨母 你贾家的姨娘 哥哥 表兄
内侄 孽障 痴儿 嫂 嫂子 少奶奶 他的夫人 有人 奶娘 小丫头 寡母 他母亲 凶身 外甥 哥儿 令甥 小人 小的 故人 内人 祖父 妹 妹子 姐儿 吾妹 仙姬 一僧 那僧 僧 一道 道人 那道人 仙师 二仙 石兄 此物 蠢物
女学生 一位公子 一位小姐 长女 大小姐 二小姐 三小姐 四小姐 卖主 原告 小主人 小人的主人 死鬼买主 王氏 赦 政 珠 李 父 盐政 新盐政 林公 大舅 大舅母 家岳母 衔玉之子 玉儿 青年公子 你家哥儿 宝二叔 嫡孙宝玉 李凤二人 姑嫂 宝玉乳母
当今 皇上 今上 龙颜 作者 小婿 女婿 甄爷 老祖宗 太夫人 妹丈 大内兄 二内兄 乃叔政老爷 政公 政老前辈 赦老 我师 拐卖的人 这个学生 他的夫人 贾兄 贾爷 雨村兄 甄老爷 薛公子 冯公子 死者冯渊 贵东家林公 林公的夫人 黛玉之母 宁府珍爷 敬老爷 赦老爷 政老爷 珍爷 琏爷 琏二 恩侯 存周 时飞 文起 情僧 林海 贾化 甄费 贾氏 嫡妻贾氏 贾氏夫人 寡嫂李氏 贾珠之妻李氏 珠大哥 贾赦之妻邢氏 贾珍之妻 贾蓉之妻 尔祖宁荣二公 宁荣二公 荣国公贾源 宁公 荣公 代善 娲皇'''.split())
SKIP=set('作者 皇帝 报喜之人 原告 门子之妻 薛蟠之父 薛蟠祖父 秦氏的兄弟 封肃的外孙女儿 甄府学生 甄家大丫鬟 葫芦庙和尚 奶母 小童 新太爷 智通寺老僧 卓文君 曹植 孔梅溪 王老爷 甄家丫鬟 严老爷'.split())
# 别称只在“名字式”的情况下显示在人物卡里（这些虽然不在正文里加下划线，但作为“也叫”可以列出）
SHOWALIAS=set('林海 贾化 甄费 时飞 文起 恩侯 存周 宫裁 情僧 蕊珠 颦颦 凤辣子 泼辣货 呆霸王 混世魔王 娲皇 茫茫大士 渺渺真人'.split())
def first_from(w,frm):
    for i in range(IX.get(frm,0),len(SEG)):
        if w in SEG[i]: return i
    return None
def bad(w,t,s,e):   # 不该链的出现位置
    if w=='宝玉' and t[max(0,s-2):s]=='通灵': return True
    if w=='石头' and t[e:e+1] in '记城': return True
    return False
persons=[]; pid={}
for e in idx['人物']:
    if e['名'] in SKIP: continue
    al=[]
    for a in e['别称']:
        w=a['称']
        if w in NOLINK: continue
        f=first_from(w,a['从']) if a['从'] in IX else None
        if f is None: continue
        al.append([w,f, len(w)>=2 and w not in GEN])
    if not any(x[2] for x in al): continue
    pid[e['名']]=len(persons)
    persons.append({"name":e['名'],"al":al,"src":e})
# 共用的称呼不链
from collections import Counter
cnt=Counter(w for p in persons for w,f,l in p['al'] if l)
for p in persons:
    for x in p['al']:
        if cnt[x[0]]>1: x[2]=False
# 正文里人名的位置：每段每人只链第一次出现；长的称呼优先，不重叠
pats=sorted([(w,i) for i,p in enumerate(persons) for w,f,l in p['al'] if l],key=lambda x:-len(x[0]))
names={}; appear=[[] for _ in persons]; acount=[Counter() for _ in persons]
for si,t in enumerate(SEG):
    taken=[]; got={}
    for w,i in pats:
        for m in re.finditer(re.escape(w),t):
            s,e2=m.span()
            if bad(w,t,s,e2) or any(s<b and a<e2 for a,b,_ in taken): continue
            taken.append((s,e2,i)); acount[i][w]+=1
            if si not in appear[i]: appear[i].append(si)
    for s,e2,i in sorted(taken):
        if i in got: continue
        got[i]=1; names.setdefault(SID[si],[]).append([s,e2,i])
for a in appear: a.sort()
DROPREL=set()
EARLY={'王熙凤':'琏爷的夫人','贾母':'荣府太夫人','贾宝玉':'宝玉','林黛玉':'黛玉','薛宝钗':'宝钗','王夫人':'贾政的夫人','薛姨妈':'薛家姨母','李纨':'珠大嫂子','僧（茫茫大士）':'茫茫大士','道人（渺渺真人）':'渺渺真人','贾元春':'元春','贾迎春':'迎春','贾探春':'探春','贾惜春':'惜春','穆莳':'东安郡王穆莳'}
out=[]
for i,p in enumerate(persons):
    e=p['src']; first=appear[i][0] if appear[i] else None
    if first is None: continue
    ids=fix.get(e['名']) or e['身份']
    ids=[[IX[x['从']],x['写']] for x in ids if x['从'] in IX]
    # 人名在“有身份可说”之前出现（如 1.1 作者解释取名）不链接
    start=max(first,ids[0][0]) if ids else first
    ids=[[max(a,start),b] for a,b in ids]
    ap=[x for x in appear[i] if x>=start]
    if not ap: continue
    if start>first:
        for sid in [SID[x] for x in appear[i] if x<start]:
            names[sid]=[n for n in names.get(sid,[]) if n[2]!=i]
    first=ap[0]
    nameFrom=first_from(e['名'],SID[first])
    shown=[[w,f] for w,f,l in p['al'] if l or w in SHOWALIAS]
    out.append({"id":i,"name":e['名'],"nameFrom":nameFrom,"al":shown,"cnt":dict(acount[i]),"ids":ids,"ap":ap,"first":first,"early":EARLY.get(e['名'])})
# 关系：人工整理的双向关系表
alias2={'茫茫大士':'僧（茫茫大士）','渺渺真人':'道人（渺渺真人）'}
O={x['name']:x for x in out}
for x in out: x['rels']=[]
for line in open(B+H+'人物卡/关系.txt'):
    line=line.strip()
    if not line or line.startswith('#'): continue
    a,b2,ab,ba,frm=[c.strip() for c in line.split('|')]
    a=alias2.get(a,a); b2=alias2.get(b2,b2)
    if a not in O or b2 not in O: print('关系里的人不在人物表：',a,b2); continue
    f=max(IX[frm],O[a]['first'],O[b2]['first'])
    O[a]['rels'].append([O[b2]['id'],ba,f]); O[b2]['rels'].append([O[a]['id'],ab,f])
hlm={"key":"rb_demo_hlm_v1","novel":True,"unit":"回","scope":5,"props":props,"hui":hui,"cards":J(H+'卡片_合并.json'),"suspense":sus,
     "qa":J(H+'示范问答/示范问答.json'),"recap":J(H+'回顾/回顾.json'),"people":out,"names":names,"main":mainline(H,IX,sus)}

# ---------- 通用打包（2026-10-26 抽到 server/packer.py，demo 和服务端共用） ----------
import sys as _s2; _s2.path.insert(0,B+'server'); import packer as _pk
def build_modern(key,folder,txtp,unitword,store): return _pk.pack_book(txtp,'生成/'+folder+'/',key,unitword,store)
# ---------- 呐喊（短篇集，全本；篇名代替"第几章"） ----------
nahan=build_modern('nahan','呐喊','文本数据/呐喊/全文.json','篇','rb_demo_nahan_v1')
nahan.update({"titled":True,"whole":True})
# ---------- 巴斯克维尔的猎犬（英文推理小说，自译；中文 / 原文 / 对照） ----------
hound=build_modern('hound','猎犬','文本数据/猎犬/全文.json','章','rb_demo_hound_v1')
hound.update({"whole":True,"orig":[["en","英文"]]})

# ---------- 李鸿章传（传记/非虚构，全本；序例为第 0 章；条约等"文件"默认折叠） ----------
lhz=build_modern('lhz','李鸿章传','文本数据/李鸿章传/全文.json','章','rb_demo_lhz_v1')
lhz.update({"whole":True})
data={"books":{"tractatus":tractatus,"hlm":hlm,"nahan":nahan,"lhz":lhz,"hound":hound}}
if os.environ.get('FUBI_NO_HTML')!='1':   # 服务端（server/books.py）只要 data，不写 html
  js=json.dumps(data,ensure_ascii=False).replace('</','<\\/')
  t=open(B+'Demo/模板.html').read().replace('%%DATA%%',js)
  open(B+'生成/自测/单文件版.html','w').write(t);
  if os.environ.get('FUBI_NO_BUNDLE')!='1':   # 自动测试（GitHub Actions）只要单文件版：合并版要读带版权的原始电子书，不入库
    import subprocess; subprocess.run([_s2.executable,'-I',B+'生成/自测/体验页.py'],check=True,env=dict(os.environ,PYTHONWARNINGS='ignore'))   # 合并版 → Demo/伏笔_demo.html
  print(len(t)//1024,'KB','人物',len(out),'人名链接',sum(len(v) for v in names.values()))
