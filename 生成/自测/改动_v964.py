"""v9.64（10-28）交互重做第三批（清单第二节 12、13）：
⑫ 读书札记：改成整页（铺满屏幕、纸色底、像书里的一页：宋体正文、楷体批注、朱色标题小印）；从书末、从笔记打开都进这一页，左上角返回各自来源。
⑬ 找书：每条结果只露第一个下载来源，其余收进"其他来源"；搜索中显示三条占位灰条。
   人物卡："首次出场""最近出场"改成两行可点的列表（位置 + 那一段开头几个字）；关系一行一个人。
备份 Demo/模板_v79备份.html。"""
import os
B=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))+'/'
P=B+'Demo/模板.html'
s=open(P,encoding='utf-8').read()
def rep(a,b,n=1):
    global s
    c=s.count(a); assert c==n,(c,a[:80]); s=s.replace(a,b)
# ⑫ 札记整页：openSheet 加 full 选项
rep("""function openSheet(html,{tall=false,onClose=null}={}){
  const s=$('#sheet'); s.innerHTML='<div class="grab"></div>'+html; s.classList.toggle('tall',tall);""",
"""function openSheet(html,{tall=false,onClose=null,full=false}={}){
  const s=$('#sheet'); s.innerHTML='<div class="grab"></div>'+html; s.classList.toggle('tall',tall); s.classList.toggle('full',full);""")
rep("""    :`<button class="btn ghost" id="exEdit">编辑</button><button class="btn ghost" id="exCopy" style="margin-left:auto">复制</button><button class="btn" id="exSave">导出文件</button>`}</div>`,{tall:true});""",
    """    :`<button class="btn ghost" id="exEdit">编辑</button><button class="btn ghost" id="exCopy" style="margin-left:auto">复制</button><button class="btn" id="exSave">导出文件</button>`}</div>`,{tall:true,full:true});""")
rep("""  $('#sheet').classList.remove('show'); $('#scrim').classList.remove('show');""",
    """  $('#sheet').classList.remove('show','full','setp'); $('#scrim').classList.remove('show','clear');""")
# ⑬ 找书：其他来源收起
rep(""":r['可下载']?L.map((x,k)=>`<div class="fsrc"><span>${esc(x['名']||x['来源'])}<small>${esc(x['说明']||'')}</small></span><button class="btn ${k?'ghost':''}" data-dl="${ri}" data-k="${k}">下载</button></div>`).join('')""",
    """:r['可下载']?(sr=>sr[0]+(sr.length>1?`<details class="fmore"><summary>其他来源（${sr.length-1}）</summary>${sr.slice(1).join('')}</details>`:''))(L.map((x,k)=>`<div class="fsrc"><span>${esc(x['名']||x['来源'])}<small>${esc(x['说明']||'')}</small></span><button class="btn ${k?'ghost':''}" data-dl="${ri}" data-k="${k}">下载</button></div>`))""")
rep("""  $('#libList').innerHTML='<p class="mini libwait">正在搜索…</p>';""",
    """  $('#libList').innerHTML='<div class="libwait" aria-label="正在搜索"><i></i><i></i><i></i></div>';""")
# ⑬ 人物卡
rep("""    <div class="refrow">${ap.length?`<button class="refchip nv" data-go="${P[ap[0]].n}">首次出场 · ${label(ap[0])}</button>`:''}${last!=null&&last!==ap[0]?`<button class="refchip nv" data-go="${P[last].n}">最近出场 · ${label(last)}</button>`:''}</div>""",
    """    <div class="aprow">${ap.length?`<button data-go="${P[ap[0]].n}"><small>首次出场　${label(ap[0])}</small><span>${esc(firstLine(txt(P[ap[0]]),22))}</span></button>`:''}${last!=null&&last!==ap[0]?`<button data-go="${P[last].n}"><small>最近出场　${label(last)}</small><span>${esc(firstLine(txt(P[last]),22))}</span></button>`:''}</div>""")
CSS=r'''
/* ===== v9.64 交互重做第三批 ===== */
.sheet.full{top:0;bottom:0;max-height:none;height:100%;border-radius:0;background:var(--paper);box-shadow:none;padding-top:var(--safe-t)}
.sheet.full .grab{display:none}
.sheet.full .sbody{padding:8px 28px 32px}
.sheet.full .mdv{max-width:30em;margin:0 auto;font-family:var(--serif);font-size:16px;line-height:1.9;color:var(--ink)}
.sheet.full .mdv h3.mt{font-size:20px;letter-spacing:.06em;margin:8px 0 4px;text-align:center}
.sheet.full .mdv p.meta{text-align:center;margin-bottom:24px}
.sheet.full .mdv h4{display:flex;align-items:center;gap:8px;font-family:var(--ui);color:var(--hl);margin:28px 0 8px}
.sheet.full .mdv h4::before{content:"";width:6px;height:6px;background:var(--hl);transform:rotate(45deg)}
.sheet.full .mdv blockquote{font-family:var(--serif);border-left:2px solid var(--line);padding-left:12px;color:var(--ink2)}
.sheet.full .mdv li{font-family:var(--kai);font-size:16px}
.sheet.full .mdv .sub{font-family:var(--ui)}
.sheet.full .rf{max-width:30em;margin:0 auto 16px}
@media (orientation:landscape) and (max-height:520px){.sheet.full{transform:translate(-50%,0)!important;bottom:0;left:50%;width:100%;max-height:none;border-radius:0}.sheet.full:not(.show){opacity:0}}
.fmore{margin-top:2px}
.fmore summary{list-style:none;font-size:var(--t-tag);color:var(--blue);padding:6px 0;cursor:pointer}
.fmore summary::-webkit-details-marker{display:none}
.libwait{display:flex;flex-direction:column;gap:16px;margin-top:20px}
.libwait i{display:block;height:64px;border-radius:6px;background:linear-gradient(90deg,var(--paper2) 0,var(--sheet) 50%,var(--paper2) 100%);background-size:200% 100%;animation:shim 1.2s linear infinite}
@keyframes shim{to{background-position:-200% 0}}
.aprow{display:flex;flex-direction:column}
.aprow button{display:flex;flex-direction:column;gap:2px;width:100%;text-align:left;padding:10px 0;border-bottom:1px solid var(--line)}
.aprow small{font-size:var(--t-tag);color:var(--mute)}
.aprow span{font-family:var(--serif);font-size:var(--t-aux);color:var(--ink2)}
.rels b{color:var(--ink)}
'''
rep('</style>',CSS+'</style>')
# 10-30 截图后补：回顾句末重复句号；伏笔卡里的问题用楷体
s=s.replace("""${sec?`：${esc(sec['写'])}`:'开头'}。`;""","""${sec?`：${esc(sec['写'].replace(/[。．.]$/,''))}`:'开头'}。`;""")
s=s.replace("""/* ===== v9.64 交互重做第三批 ===== */""","""/* ===== v9.64 交互重做第三批 ===== */\n#sheet .q .qt,#sheet .rvq .qt{font-family:var(--kai)}   /* 伏笔的问题一律楷体（规范 v2） */""")
open(P,'w',encoding='utf-8').write(s); print('ok')
