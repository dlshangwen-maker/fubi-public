"""v9.62（10-28）交互重做第一批（`第三阶段_交互重做清单_v0.1.md` 第二节 1～6、8；用户 10-28 定：猜想用滑条、选字流程 A、一口气做完）。
① 解释卡片：标题写位置（第一回 + 这一段开头几个字）；深浅三档挪到内容顶部一行小字；底部"‹ 上一段 / 下一段 ›"（正文跟着滚过去）；去掉"连切三次问要不要设默认"，直接记住最后选的深浅。
② 伏笔卡：可带"‹"返回来处；写猜想原地换成填写页（‹ 返回伏笔卡），保存后回到伏笔卡、提示"已保存 · 撤销"（把握仍是滑条）；已揭晓的可"看揭晓"。
③ 揭晓卡：上下对照"你当时猜 / 书里的答案"，主线碎片加一行"拼上第 k 块"；底部"回到原文"。
④ 伏笔面板：每条两行（位置 + 印章 / 楷体问题，右边"已猜"），没打开的也排在里面写"点开查看问题"；点一条原地进伏笔卡或揭晓卡，‹ 回列表。
⑤ 笔记：分类一行纯文字（全部、划线、想法、疑问、书签）；每条 = 位置和种类 → 原文（黛色竖线）→ 自己写的（楷体）；点一条回到原文，右边"…"进这条记录；底部"查看读书札记"。
⑥ 选字：菜单"划线 · 解释 · 复制"；输入条上方"想法 | 疑问"切换（按内容自动选好，读者可改）；存为想法的提示改成"已保存为想法 · 撤销"。
⑧ 阅读设置：第一层只放排版，面板矮、遮罩透明；"更多设置 ›"进第二层；"带读"只留在"我的 › 阅读偏好"。
备份 Demo/模板_v77备份.html。新函数体在同目录 改动_v962_片段.js（按 ### 名字 分段）。"""
import os,re
B=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))+'/'
P=B+'Demo/模板.html'
s=open(P,encoding='utf-8').read()
FR={}
cur=None
for line in open(os.path.dirname(os.path.abspath(__file__))+'/改动_v962_片段.js',encoding='utf-8').read().split('\n'):
    m=re.match(r'^### (\S+)',line)
    if m: cur=m.group(1); FR[cur]=[]; continue
    if cur: FR[cur].append(line)
FR={k:'\n'.join(v).strip('\n')+'\n' for k,v in FR.items()}
def rep(a,b,n=1):
    global s
    c=s.count(a); assert c==n,(c,a[:80]); s=s.replace(a,b)
def fn(name):
    global s
    i=s.index('\nfunction '+name+'(')+1; j=s.index('\n}\n',i)+2
    s=s[:i]+FR[name]+s[j:]
for name in ['renderCard','switchLv','openClue','guessEditor','reveal','revealMine','cluePanel','noteSheet','minePanel']: fn(name)
rep("""  s.querySelectorAll('[data-go]:not(a)').forEach(b=>b.onclick=()=>{closeSheet();jump(b.dataset.go);});""",
    """  s.querySelectorAll('[data-go]:not(a):not(.nr)').forEach(b=>b.onclick=()=>{closeSheet();jump(b.dataset.go);});""")
# ⑥ 选字
rep("""  m.innerHTML=`<button data-a="hl">${ic('hl')}划线</button><button data-a="ex">${ic('qm')}解释</button>`;""",
    """  m.innerHTML=`<button data-a="hl">${ic('hl')}划线</button><button data-a="ex">${ic('qm')}解释</button><button data-a="cp">${ic('copy')}复制</button>`;""")
rep("""  if(b.dataset.a==='ex'){""","""  if(b.dataset.a==='cp'){ const t=getSelection().toString(); getSelection().removeAllRanges(); hideMenu(); selParts=null; copyText(t,'已复制'); return; }
  if(b.dataset.a==='ex'){""")
rep("""<span class="qttl">写点什么</span><span class="qhint"></span><button class="qx" id="qx" aria-label="关闭">×</button></div>""",
    """<span class="qttl">写点什么</span><div class="qkind" role="group" aria-label="记成"><button data-qk="note" aria-pressed="true">想法</button><button data-qk="q" aria-pressed="false">疑问</button></div><button class="qx" id="qx" aria-label="关闭">×</button></div>""")
rep("""  ta.oninput=fit;""",FR['qkind'].rstrip('\n'))
rep("""    if(judgeKind(t,hl)==='q') askQuestion(hl,t);""","""    if(kindNow()==='q') askQuestion(hl,t);""")
rep("""  toast(`<div class="tq">已保存为想法</div><button>改为疑问</button>`,()=>{S.notes=S.notes.filter(x=>x.id!==n.id);save();askQuestion(hl,t);},4000);""",
    """  toast(`<div class="tq">已保存为想法</div><button>撤销</button>`,()=>{S.notes=S.notes.filter(x=>x.id!==n.id);save();paintUL();paintMarks();},4000);""")
# ⑧ 设置
i=s.index('\nfunction settings(')+1; j=s.index('\n}\n',i)+2
new=s[i:j]
def nrep(a,b):
    global new
    assert new.count(a)==1,a[:60]; new=new.replace(a,b)
nrep("function settings(){\n  const v=S.view;","function settings(layer){\n  /* v9.62：第一层只放排版（面板矮、遮罩透明，边调边看）；\"更多设置\"进第二层；\"带读\"只在\"我的 › 阅读偏好\" */\n  const v=S.view, more=layer==='more';")
nrep("""  openSheet(`<div class="shead"><span class="ttl">阅读设置</span><button class="x" data-close aria-label="关闭">×</button></div>
  <div class="sbody">""","""  openSheet(`<div class="shead">${more?'<button class="x back" id="setBack" aria-label="返回阅读设置">‹</button>':''}<span class="ttl">${more?'更多设置':'阅读设置'}</span><button class="x" data-close aria-label="关闭">×</button></div>
  <div class="sbody">${more?'':`""")
a="""也可以切换成只看原文。</p></div>`:''}"""
nrep(a,a+"""
    <button class="setmore" id="setMore"><span>更多设置</span><small>阅读引导、解释深浅、清空记录</small><span class="chev">›</span></button>`}${more?`""")
i2=new.index("""    <div class="setrow"><div class="lbl"><span>带读</span></div>"""); j2=new.index("""    <div class="setrow"><div class="lbl"><span>解释的默认深浅</span></div>""")
new=new[:i2]+new[j2:]
nrep("""    <div class="setrow inline"><div class="lbl"><span>清空本书记录</span></div><button class="btn ghost" id="rs">清空</button></div>
  </div>`,{tall:true});""","""    <div class="setrow inline"><div class="lbl"><span>清空本书记录</span></div><button class="btn ghost danger" id="rs">清空</button></div>
    <p class="mini" style="margin-top:16px">带读的轻重在书架右上角“我的 › 阅读偏好”里设置，所有书通用。</p>`:''}
  </div>`);
  if(!more){ $('#sheet').classList.add('setp'); $('#scrim').classList.add('clear'); }
  $('#setMore')?.addEventListener('click',()=>settings('more')); $('#setBack')?.addEventListener('click',()=>settings());""")
nrep("  $('#fs').oninput=e=>{v.fs=+e.target.value;$('#fsv').textContent=v.fs;applyView();save();};","  if($('#fs')) $('#fs').oninput=e=>{v.fs=+e.target.value;$('#fsv').textContent=v.fs;applyView();save();};")
nrep("  $('#mdseg').querySelectorAll('button')","  $('#mdseg')?.querySelectorAll('button')")
nrep("  $('#lvseg').querySelectorAll('button')","  $('#lvseg')?.querySelectorAll('button')")
nrep("  $('#rs').onclick=","  if($('#rs')) $('#rs').onclick=")
s=s[:i]+new+s[j:]
rep("""  const s=$('#sheet'); s.innerHTML='<div class="grab"></div>'+html; s.classList.toggle('tall',tall);""",
    """  const s=$('#sheet'); s.innerHTML='<div class="grab"></div>'+html; s.classList.toggle('tall',tall); s.classList.remove('setp'); $('#scrim').classList.remove('clear');""")
rep('</style>',FR['css']+'</style>')
open(P,'w',encoding='utf-8').write(s); print('ok')
