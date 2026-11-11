"""v9.58（10-28）第三阶段 D 面板 + E 提示和文案（规范 v2 第四、五、八、九节）。
D：所有面板同一结构（拖动条 → 标题行 → 内容 → 底部操作），标题行整行可下拉关闭（原来只有拖动条），横屏在屏幕中间弹出；内边距 20；
   底部操作次按钮在左、主按钮在右，高 40；分段切换、标签、圆角统一。
E：提示条按规范第八节处理——删："页边的黄色菱形是一处伏笔，点击查看"（页边已有批注和动效）、加/移除书签的提示（图标本身变化）、切换中文/原文的提示；
   合并："猜想已保存 / 伏笔已记下 / 疑问已记下"→"已保存"；改写："正在想……"→"正在生成回答"；
   不对读者说开发期的话："测试版""模型"→ 改写成读者能懂的说法。
备份 Demo/模板_v73备份.html。"""
import os
B=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))+'/'
P=B+'Demo/模板.html'
s=open(P,encoding='utf-8').read()
def rep(a,b,n=1):
    global s
    c=s.count(a); assert c==n,(c,a[:80]); s=s.replace(a,b)

# ---------- D：下拉关闭——拖动条和标题行都能抓 ----------
rep("""function dragToClose(s){
  const g=s.querySelector('.grab'); let y0=null;
  g.ontouchstart=e=>{y0=e.touches[0].clientY};
  g.ontouchmove=e=>{if(y0===null)return;const dy=e.touches[0].clientY-y0;if(dy>0)s.style.transform=`translate(-50%,${dy}px)`};
  g.ontouchend=e=>{const dy=(e.changedTouches[0].clientY-(y0||0));s.style.transform='';if(dy>70)closeSheet();y0=null};
}""","""function dragToClose(s){
  /* 竖屏：抓住拖动条或标题行往下拉 80px 关闭（规范 v2）；横屏面板在屏幕中间，不下拉 */
  [s.querySelector('.grab'),s.querySelector('.shead')].filter(Boolean).forEach(g=>{ let y0=null;
    g.ontouchstart=e=>{ if(e.target.closest('button,input,select,textarea')||matchMedia('(orientation:landscape) and (max-height:520px)').matches) return; y0=e.touches[0].clientY; s.style.transition='none'; };
    g.ontouchmove=e=>{if(y0===null)return;const dy=e.touches[0].clientY-y0;if(dy>0)s.style.transform=`translate(-50%,${dy}px)`};
    g.ontouchend=e=>{ if(y0===null) return; const dy=(e.changedTouches[0].clientY-y0); s.style.transition=''; s.style.transform=''; if(dy>80)closeSheet(); y0=null; }; });
}""")

# ---------- E：提示条 ----------
rep("""if(S.bm[i]){delete S.bm[i];toast(`<div class="tq">已移除${label(i)}的书签。</div>`,null,2000);} else {S.bm[i]=Date.now();toast(`<div class="tq">已为${label(i)}添加书签。</div><button>查看</button>`,()=>minePanel('bm'),2500);} save();""",
    """if(S.bm[i]) delete S.bm[i]; else S.bm[i]=Date.now(); save();   /* 规范 v2：书签图标本身变化即可，不出提示 */""")
rep("""keepPlace(()=>{setLang(); $('#tlg').textContent=LANGS.find(x=>x[0]===S.lang)[1];});
    toast(`<div class="tq">${S.lang==='zh'?'中文。点任一段，可在解释里看原文':'只看原文（'+D.orig.find(x=>x[0]===ogl())[1]+'）'}。</div>`,null,2200); });""",
    """keepPlace(()=>{setLang(); $('#tlg').textContent=LANGS.find(x=>x[0]===S.lang)[1];}); });""")
rep("""  if(!(ML()&&list.some(s=>isPiece(s.id)))&&tipOnce('tipFound')){
    const tip=()=>{ if($('#toast').classList.contains('show')) return later(tip,3000); toast(`<div class="tq">页边的黄色菱形是一处伏笔，点击查看。</div><button>查看</button>`,()=>openClue(list[0].id),7000); }; later(tip,2600);}   /* 正在显示别的提示（如主线）时，等它过去再说 */""",
    """  /* 规范 v2：不再出"页边的黄色菱形是一处伏笔"——页边已有"伏笔"批注和底部动效 */""")
rep("""toast(`<div class="tq">${g?'猜想已保存。':fb?'伏笔已记下。':'疑问已记下。'}</div><button>查看</button>`""","""toast(`<div class="tq">已保存</div><button>查看</button>`""")
rep("""toast(`<div class="tq">正在想……</div>`,null,30000);""","""toast(`<div class="tq">正在生成回答</div>`,null,30000);""")
rep("""toast(`<div class="tq">已记为想法。</div><button>改为疑问</button>`""","""toast(`<div class="tq">已保存为想法</div><button>改为疑问</button>`""")
# ---------- E：不对读者说开发期的话 ----------
rep("<title>伏笔 · Demo</title>","<title>伏笔</title>")
rep("<dt>数据</dt><dd>测试版只保存在这台设备上</dd>","<dt>数据</dt><dd>${SRV?'保存在服务器上':'保存在这台设备上'}</dd>")
rep("""    <p class="mini" style="margin-top:20px">测试版。书架上的书都是公有领域版本，来源见书的详情（在书架上长按）。</p></div>`),()=>mePage());""",
    """    <p class="mini" style="margin-top:20px">书架上的精读版均为公有领域版本，来源见书籍详情（在书架上长按）。目前是试用阶段，界面和内容仍在调整。</p></div>`),()=>mePage());""")
rep("['篇幅','一百二十回。本测试版收录前五回']","['篇幅','一百二十回。精读版目前收录前五回']")
rep("<small>本测试版收录至第${cnum(D.scope)}${UNIT}</small>","<small>精读版目前收录至第${cnum(D.scope)}${UNIT}</small>",2)
rep("'<p class=\"auto\">答案在本测试版之后的章节</p>'","'<p class=\"auto\">答案在尚未收录的章节</p>'")
rep("<p class=\"mini\">答案在本测试版之后的章节。</p>","<p class=\"mini\">答案在尚未收录的章节。</p>")
rep("${q.ai?'由模型按你的阅读进度回答，可能有错。':'测试版的回答为预先撰写。'}","${q.ai?'按你的阅读进度自动生成，可能有误。':'由编辑预先撰写。'}")
rep("'还没有翻译（需要服务器配置模型）'","'尚未翻译'")
s=s.replace("'还没有生成（需要服务器配置模型）'","'尚未生成'")

CSS=r'''
/* ===== v9.58 面板（规范 v2 第五节"半屏面板"） ===== */
.sheet{border-radius:14px 14px 0 0;box-shadow:0 -8px 30px rgba(0,0,0,.12);transition:transform .28s var(--ease)}
.grab{margin:8px auto 0}
.shead{min-height:52px;padding:8px 20px 8px;gap:12px;touch-action:none}
.shead .ttl,.shead .n{font-family:var(--serif);font-size:var(--t-panel);font-weight:600;letter-spacing:.06em;line-height:1.4}
.shead .x{width:32px;height:32px;display:flex;align-items:center;justify-content:center;padding:0;font-size:20px;margin-left:auto}
.shead .back{font-size:20px;color:var(--mute);width:32px;height:32px;display:flex;align-items:center;justify-content:center;padding:0}
.sbody{padding:4px 20px 16px}
.sfoot{gap:12px;padding:12px 20px calc(12px + var(--safe-b));border-top:1px solid var(--line)}
.sheet{padding-bottom:0}
.sfoot .btn{height:40px;padding:0 18px;display:inline-flex;align-items:center;justify-content:center;font-size:14px;letter-spacing:.04em}
.seg{border-radius:6px;padding:2px}.seg button{border-radius:4px;height:28px;padding:0}
.seg button[aria-pressed=true]{color:var(--ink);background:var(--sheet)}
.tabs button{height:28px;padding:0 12px}
.plain{font-size:var(--t-key);line-height:1.7}
.more{font-size:var(--t-body);line-height:1.8}
.q .qt{border-left-width:2px;padding-left:12px}
.scrim{background:rgba(30,38,34,.22)}
/* 横屏：面板在屏幕中间弹出 */
@media (orientation:landscape) and (max-height:520px){
  .sheet{left:50%;bottom:50%;width:min(520px,calc(100vw - 96px));max-height:88vh;border-radius:14px;transform:translate(-50%,60%);opacity:0;pointer-events:none;transition:transform .28s var(--ease),opacity .2s}
  .sheet.show{transform:translate(-50%,50%);opacity:1;pointer-events:auto}
  .sheet.tall{height:88vh}
  .sheet .grab{display:none}
  .sfoot{padding-bottom:12px}
}
/* 提示条（规范 v2 第五节）：底部导航上方 12px，墨底纸字 13 号，右侧最多一个文字按钮 + × */
.toast{bottom:calc(56px + 12px + var(--safe-b));min-height:44px;padding:8px 8px 8px 16px;gap:12px;width:calc(100% - 32px)}
.toast .tx{color:var(--paper);opacity:.6;font-size:16px;width:32px;height:32px;padding:0}
.calmread ~ .toast,.calmread .toast{bottom:calc(12px + var(--safe-b))}
'''
rep('</style>',CSS+'</style>')
rep("""'服务器配好模型后，会自动生成这本书的解释和回顾；现在可以照常阅读、划线、写想法和提问。'""","""'解释和回顾正在准备，完成后会自动出现；现在可以照常阅读、划线、写想法和提问。'""")
open(P,'w',encoding='utf-8').write(s); print('ok')
