"""v9.59（10-28）第三阶段 F："我的"、找书、二级页按规范 v2 换样式（和书架同一套标题、间距、圆角；卡片不加阴影，用底色或分隔线）；
横屏阅读页：底部导航移到左侧竖排，正文限宽 28em 居中，顶栏让出左侧导航。备份 Demo/模板_v74备份.html。"""
import os
B=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))+'/'
P=B+'Demo/模板.html'
s=open(P,encoding='utf-8').read()
def rep(a,b,n=1):
    global s
    c=s.count(a); assert c==n,(c,a[:80]); s=s.replace(a,b)
CSS=r'''
/* ===== v9.59 我的、找书、二级页（规范 v2 第六节 5、6） ===== */
.pgbar{height:calc(52px + var(--safe-t));padding:var(--safe-t) 12px 0}
.pgbar b{font-size:var(--t-panel);letter-spacing:.06em}
.pgbar .back{color:var(--ink2)}
.pgbody{padding:8px 24px calc(48px + var(--safe-b))}
.mecard,.mebox,.melist,.medl{border-radius:6px;box-shadow:none;background:var(--paper2)}
.mecard{padding:16px;margin:8px 0 16px}
.mestat{gap:8px;margin:0 0 16px}
.mestat div{border-radius:6px;box-shadow:none;background:var(--paper2);padding:12px 4px}
.mestat b{font-size:20px}
.mebox{padding:16px;margin:0 0 16px}
.melist button{padding:16px;border-top-color:var(--line)}
.week .d{border-radius:6px;background:var(--sheet)}
.cal .d{border-radius:4px}
.d.on{background:var(--ink)!important}
.d.on.today{box-shadow:0 0 0 2px var(--line)}
.calsel select{border-radius:6px;background:var(--sheet)}
.av{background:var(--ink)}
.libsearch{padding:8px 0 12px}
.libsearch input{height:44px;padding:0 14px;border-radius:6px;background:var(--sheet)}
.hotw{gap:8px}
.hotw button{height:32px;padding:0 12px;border-radius:6px;background:transparent}
.librow{padding:16px 0}
.libh{margin:16px 0 12px}
.fsrc .btn{height:32px;padding:0 14px;display:inline-flex;align-items:center}
.qzc,.qzres{border-radius:6px}
.qzc.open{box-shadow:0 0 0 1px var(--ink)}
.qzchips button{height:40px;padding:0 14px;border-radius:6px;background:var(--sheet)}
.qzrh b,.qzr b,.qzt b{color:var(--ink)}
.about .welic{border-radius:6px}
.gemic i{background:var(--hl)}
/* ===== 横屏阅读页：左侧竖排导航，正文限宽居中（规范 v2 第六节 3） ===== */
@media (orientation:landscape) and (max-height:520px){
  .app:has(.text){max-width:none}
  .text{max-width:calc(28em + 2 * var(--pad) + 32px);margin:0 auto;padding-left:calc(var(--pad) + 56px + var(--safe-l));padding-right:calc(var(--pad) + 32px + var(--safe-r))}
  .bar{padding-left:calc(56px + var(--safe-l) + 12px);padding-right:calc(var(--safe-r) + 12px);height:44px;padding-top:0}
  .nav{left:0;top:0;bottom:0;transform:none;width:calc(56px + var(--safe-l));max-width:none;height:auto;flex-direction:column;justify-content:center;gap:16px;padding:0 0 var(--safe-b) var(--safe-l);border-top:0;border-right:1px solid var(--line)}
  .calmread .nav{transform:translateX(-100%)}
  .toast{left:auto;right:calc(var(--safe-r) + 24px);transform:translate(0,12px);width:340px;bottom:calc(16px + var(--safe-b))}
  .toast.show{transform:none}
  #mlfx{left:auto;right:calc(var(--safe-r) + 24px);width:360px;transform:translate(0,24px);bottom:calc(16px + var(--safe-b))}
  #mlfx.show{transform:none}
}
'''
rep('</style>',CSS+'</style>')
# 10-28 自测修：shv() 每次新建对象；topLine 不受顶栏收起影响
s=s.replace("const shv=()=>PROF.shelf=Object.assign({lay:'grid',sort:'recent',order:[]},PROF.shelf||{});","const shv=()=>{ const v=PROF.shelf=PROF.shelf||{}; if(!v.lay) v.lay='grid'; if(!v.sort) v.sort='recent'; if(!v.order) v.order=[]; return v; };")
s=s.replace("const topLine=()=>{ const b=document.getElementById('bar'); return (b?b.getBoundingClientRect().bottom:0)+6; };","const topLine=()=>{ const b=document.getElementById('bar'); return (b?b.offsetHeight:0)+6; };")
for a,b in [('页边的黄色菱形是书里埋着的问题，读到答案时自动揭晓；每本书还有一条主线，揭晓一处就拼上一块。', '页边朱色的“伏笔”批注是书里埋着的问题，读到答案处自动揭晓；每本书还有一条主线，揭晓一处就拼上一块。'), ('页边的黄色菱形是书里埋着的问题，读到答案时自动揭晓。', '页边朱色的“伏笔”批注是书里埋着的问题，读到答案处自动揭晓。'), ('阅读时，页边的黄色菱形标记书中的伏笔', '阅读时，页边朱色的“伏笔”批注标出书中的伏笔')]:
    s=s.replace(a,b)
open(P,'w',encoding='utf-8').write(s); print('ok')
