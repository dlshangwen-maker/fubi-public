"""v9.68（11-02 用户八点）：登录描边、默认列表并记住、问卷改写（中间题可自己填、常用答案记下作选项）、退出/注销拦截页、
伏笔"点开"引导（页边红点 + 首次发现时一句话）、札记挪出标签行（笔记标题行右边的二级入口）、列表去进度条。备份 Demo/模板_v83备份.html"""
import os
B=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))+'/'
P=B+'Demo/模板.html'
s=open(P,encoding='utf-8').read()
def rep(a,b,n=1):
    global s
    c=s.count(a); assert c==n,(c,a[:90]); s=s.replace(a,b)
# 1 登录描边
rep('.shlogin{margin-left:auto;align-self:center}','.shlogin{margin-left:auto;align-self:center;height:32px;padding:0 18px;border-radius:16px;box-shadow:inset 0 0 0 1px var(--ink);color:var(--ink);font-size:var(--t-aux);letter-spacing:.06em}\n.shlogin:active{background:var(--paper2)}')
# 2 默认列表，改过就记住
rep("if(!v.lay) v.lay='grid';","if(!v.layUser) v.lay='list'; if(!v.lay) v.lay='list';")
rep("document.querySelectorAll('[data-lay]').forEach(b=>b.onclick=()=>{ v.lay=b.dataset.lay;","document.querySelectorAll('[data-lay]').forEach(b=>b.onclick=()=>{ v.lay=b.dataset.lay; v.layUser=1;")
# 7 去进度条
rep("const pbar=x=>x.started&&!x.fin?`<span class=\"pbar\"><i style=\"width:${x.pct}%\"></i></span>`:'';","const pbar=()=>'';   /* v9.68：书架上不画进度条，只写文字 */")
# 4 拦截页
rep("function secPage(){","""function confirmSheet(title,desc,okText,onOk,danger){
  openSheet(`<div class="shead"><span class="ttl">${title}</span><button class="x" data-close aria-label="关闭">×</button></div><div class="sbody"><p class="cfd">${desc}</p></div><div class="sfoot"><button class="btn ghost" data-close>取消</button><button class="btn ${danger?'dgr':''}" id="cfOk" style="margin-left:auto">${okText}</button></div>`);
  $('#cfOk').onclick=()=>{ closeSheet(); onOk(); };
}
function secPage(){""")
rep("$('#secOut').onclick=()=>{ if(!confirm('确定退出登录？')) return; ACC.cur=null; saveAcc(); homePage(); };","$('#secOut').onclick=()=>confirmSheet('退出登录？','退出后回到书架。阅读记录和笔记都还在，重新登录就能接着读。','退出登录',()=>{ ACC.cur=null; saveAcc(); homePage(); });")
rep("$('#secDel').onclick=()=>{ if(!confirm('注销后，这个账号和它的设置会被删除，无法恢复。确定注销？')) return; delete ACC.users[u.id]; ACC.cur=null; saveAcc(); homePage(); };","$('#secDel').onclick=()=>confirmSheet('注销这个账号？','账号和阅读偏好会被删除，无法恢复。想只是换个账号读，请用“退出登录”。','确认注销',()=>{ delete ACC.users[u.id]; ACC.cur=null; saveAcc(); homePage(); },true);")
# 6 札记挪出标签行
rep(".concat([['arc','札记',0]]);",";")
rep("""  openSheet(`<div class="shead"><span class="ttl">笔记</span>${tab==='arc'?'<span class="nacts"><button class="linkbtn" id="exCopy">复制</button><button class="linkbtn" id="exSave">导出</button></span>':''}<button class="x" data-close aria-label="关闭">×</button></div>
    ${tabs}<div class="sbody ${tab==='arc'?'arcb':''}">${body}</div>`,{tall:true});""","""  openSheet(`<div class="shead">${tab==='arc'?'<button class="x back" id="arcBack" aria-label="返回笔记">‹</button><span class="ttl">札记</span><span class="nacts"><button class="linkbtn" id="exCopy">复制</button><button class="linkbtn" id="exSave">导出</button></span>':'<span class="ttl">笔记</span><span class="nacts"><button class="linkbtn" id="nArc">札记</button></span>'}<button class="x" data-close aria-label="关闭">×</button></div>
    ${tab==='arc'?'':tabs}<div class="sbody ${tab==='arc'?'arcb':''}">${body}</div>`,{tall:true});
  $('#arcBack')?.addEventListener('click',()=>minePanel('all')); $('#nArc')?.addEventListener('click',()=>minePanel('arc'));""")
# 5 伏笔：页边红点 + 首次发现一句话
rep("@media (prefers-reduced-motion:reduce){.mk.clue:not(.seen):not(.solved){animation:none}}","@media (prefers-reduced-motion:reduce){.mk.clue:not(.seen):not(.solved){animation:none}}\n/* v9.68：没点开过的伏笔右上角一个红点（和\"未读\"同一个习惯）；点开后红点消失 */\n.mk.clue:not(.seen):not(.solved)::after{content:\"\";position:absolute;top:-3px;right:-3px;width:7px;height:7px;border-radius:50%;background:var(--hl);box-shadow:0 0 0 2px var(--paper)}")
rep("const msg=list.length>1?`发现了 ${list.length} 处伏笔`:'发现了一处伏笔';","let msg=list.length>1?`发现了 ${list.length} 处伏笔`:'发现了一处伏笔'; if(tipOnce('clueTap')) msg+='，点页边的“伏笔”打开';")
# 3 问卷
rep("{k:'q1',t:'你平时读书，更像哪一种？',o:[['often','常读，能读完大部头'],['half','偶尔读，常读到一半放下'],['long','很久没读完一本书了']]}","{k:'q1',t:'拿到一本厚书，你通常……',o:[['often','多半能读完'],['half','读到一半就放下了'],['long','很久没读完过一本了']]}")
rep("{k:'q2',t:'读这类书，最常卡在哪里？',m:1,o:[['words','字词看不懂'],['people','人物和事记不住'],['bored','读着读着没劲了'],['how','不知道怎么读']]}","{k:'q2',t:'读的时候，什么最容易让你读不下去？',m:1,own:1,o:[['words','生僻字词、文言太多'],['people','人物太多，记不住'],['bored','情节慢，读着没劲'],['how','不知道该抓什么重点']]}")
rep("{k:'q3',t:'你希望伏笔怎样陪你读？',o:[['less','少打扰，我自己读'],['more','多带一带我'],['auto','说不好，你来定']]}","{k:'q3',t:'读的时候，你希望伏笔……',o:[['less','少打扰，我自己读'],['more','多带一带，该提醒就提醒'],['auto','说不好，你来定']]}")
rep("function quizMode(A){","""const qlab=(q,v)=>String(v).startsWith('x:')?String(v).slice(2):(q.o.find(o=>o[0]===v)||[])[1];
const qzSaved=()=>(PROF.qzc||[]).slice().sort((a,b)=>b.n-a.n).slice(0,4).map(x=>x.t);   /* 别人（这里是本机）常写的答案，排前面当选项 */
function quizMode(A){""")
rep("const ans=q=>q.m?(A[q.k]||[]).map(v=>q.o.find(o=>o[0]===v)[1]).join('、'):(q.o.find(o=>o[0]===A[q.k])||[])[1];","const ans=q=>q.m?(A[q.k]||[]).map(v=>qlab(q,v)).join('、'):qlab(q,A[q.k]);")
rep("""<div class="qzchips">${q.o.map(([v,l])=>`<button data-v="${v}" aria-pressed="${q.m?(A[q.k]||[]).includes(v):A[q.k]===v}">${l}</button>`).join('')}</div>""","""<div class="qzchips">${q.o.concat(q.own?[...new Set([...qzSaved(),...(A[q.k]||[]).filter(v=>v.startsWith('x:')).map(v=>v.slice(2))])].filter(t=>!q.o.some(o=>o[1]===t)).map(t=>['x:'+t,t]):[]).map(([v,l])=>`<button data-v="${v}" aria-pressed="${q.m?(A[q.k]||[]).includes(v):A[q.k]===v}">${esc(l)}</button>`).join('')}</div>
      ${q.own?`<div class="qzown"><input id="qzOwn" maxlength="12" placeholder="都不是？自己写一个" aria-label="自己写一个答案"><button class="linkbtn" id="qzOwnOk">添加</button></div>`:''}""")
rep("  $('#qzNext')?.addEventListener('click',nextOpen);","""  $('#qzNext')?.addEventListener('click',nextOpen);
  const own=()=>{ const t=($('#qzOwn').value||'').trim(); if(!t){ $('#qzOwn').focus(); return; } const a=A[q.k]=A[q.k]||[]; const base=q.o.find(o=>o[1]===t); const v=base?base[0]:'x:'+t; if(!a.includes(v)) a.push(v); go(cur); };
  $('#qzOwnOk')?.addEventListener('click',own); $('#qzOwn')?.addEventListener('keydown',e=>{ if(e.key==='Enter'){ e.preventDefault(); own(); } });""")
rep("$('#qrOk')?.addEventListener('click',()=>{ A.t=Date.now(); PROF.qz=A;","$('#qrOk')?.addEventListener('click',()=>{ A.t=Date.now(); (A.q2||[]).filter(v=>v.startsWith('x:')).forEach(v=>{ const t=v.slice(2), L=PROF.qzc=PROF.qzc||[], e=L.find(x=>x.t===t); e?e.n++:L.push({t,n:1}); }); PROF.qz=A;")
rep("lab_=(q,v)=>(QZ.find(x=>x.k===q).o.find(x=>x[0]===v)||[])[1];","lab_=(q,v)=>qlab(QZ.find(x=>x.k===q),v);")
rep("聊三句，伏笔就知道怎么陪你读了。","三个小问题，让伏笔知道怎么陪你读。")
rep('</style>','\n.cfd{margin:4px 0 12px;font-size:var(--t-body);line-height:1.7;color:var(--ink2)}\n.btn.dgr{background:#A33A2A;color:#fff}\n.qzown{display:flex;align-items:center;gap:8px;margin-top:12px}\n.qzown input{flex:1;min-width:0;height:40px;padding:0 12px;border-radius:6px;background:var(--field);box-shadow:inset 0 0 0 1px var(--line);font-size:var(--t-body);color:var(--ink)}\n</style>')
open(P,'w',encoding='utf-8').write(s); print('ok')
