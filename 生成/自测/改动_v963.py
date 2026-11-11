"""v9.63（10-28）交互重做第二批（清单第二节 7、9、10、11）：
⑦ 打开书的回顾（用户 10-28 定）：轻度——不弹卡，回顾放进"上次读到这里"那条线下面（一行"距上次 N 天。上次读到……"+"展开前情"，点开才看完整回顾）；重度——照旧弹卡。
⑨ 导览：最上面一行"正在读　第三回　41%"（点了回到当前位置）；搜索框收进标题行右边的放大镜，点了才展开；每一回右边一根细进度条代替"已读 41%"。
⑩ 书的详情：和"待揭晓"合成一张——封面、书名、作者、进度条和读到哪 → 主线进度和"N 处伏笔待揭晓 ›"（点了原地展开列表）→ 版本来源信息 → 底部"继续阅读"；列表、简表排列每本书右边加"…"打开详情（不再只靠长按）。
⑪ 我的：账号卡上直接点昵称改名（原地变输入框）；"账号与安全"一页取消，账号信息在卡上，"退出登录"挪到最下面一行灰字。
备份 Demo/模板_v78备份.html。"""
import os,re
B=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))+'/'
P=B+'Demo/模板.html'
s=open(P,encoding='utf-8').read()
FR={}; cur=None
for line in open(os.path.dirname(os.path.abspath(__file__))+'/改动_v963_片段.js',encoding='utf-8').read().split('\n'):
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
# ⑦ 回顾
rep("""  if(RD.size && fromShelf && !S.finished && (heavy()||gap==null||gap>DAY)) later(()=>recap(gap),250);""",
    """  if(RD.size && fromShelf && !S.finished && heavy()) later(()=>recap(gap),250);   /* 用户 10-28：重度照旧弹卡 */
  else if(RD.size && fromShelf && !S.finished && (gap==null||gap>DAY)) lastLineRecap(gap);   /* 轻度：回顾放进"上次读到这里"那条线，点开才看 */""")
rep("function lastLineTick(){",FR['lastLineRecap']+"function lastLineTick(){")
rep("""function lastLineTick(){ const l=$('#lastLine'); if(!l||jumping()) return; if(S.current>=+l.dataset.i+3){ l.classList.add('gone'); setTimeout(()=>l.remove(),400); } }""",
    """function lastLineTick(){ const l=$('#lastLine'); if(!l||jumping()||l.classList.contains('open')) return; if(S.current>=+l.dataset.i+3){ l.classList.add('gone'); setTimeout(()=>l.remove(),400); } }""")
# ⑨ 导览
for name in ['novelOutline','propOutline','bookInfo','mePage']: fn(name)
# ⑩ 书架"…"、待揭晓并进详情
rep("""<span class="lp" id="${id}p">${pct}</span>${grip}</button>""","""<span class="lp" id="${id}p">${pct}</span>${shEdit?'':`<span class="bkm" data-bi="${k}" role="button" tabindex="0" aria-label="《${esc(t)}》详情">…</span>`}${grip}</button>""")
rep("""${pbar(x)}${fb(x.ur)}</div>${sel}${grip}</button>""","""${pbar(x)}${fb(x.ur)}</div>${shEdit?'':`<span class="bkm" data-bi="${k}" role="button" tabindex="0" aria-label="《${esc(t)}》详情">…</span>`}${sel}${grip}</button>""")
rep("""longPress(el,e=>e&&e.target.closest('.fb')?unresolvedSheet(k):openBook(k),""","""longPress(el,e=>e&&e.target.closest('.bkm')?bookInfo(k,st[k].prog):e&&e.target.closest('.fb')?bookInfo(k,st[k].prog,true):openBook(k),""")
fn('unresolvedSheet')
rep("  memo:'","  search:'<circle cx=\"11\" cy=\"11\" r=\"6.5\"/><path d=\"M16 16l4 4\"/>',\n  memo:'")
rep('</style>',FR['css']+'</style>')
open(P,'w',encoding='utf-8').write(s); print('ok')
