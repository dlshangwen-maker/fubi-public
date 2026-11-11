"""v9.67（10-30 用户七点）：
① 没登录的页面 = 登录后的书架（排序、排列、找书、导入都在），右上角是"登录"；用到才要求登录（读、找书、导入、下载、我的），登录后回到原处。
② "带读轻度"→"轻度带读"（重度同）。
③ 读书札记并进笔记：笔记标签行最后多一个"札记"，在原处切换；不再是另一整页；标题行右边是"复制 / 导出"文字入口，札记底部"编辑这篇札记"。
④ 去掉"读书札记""阅读回顾"两个大按钮：笔记底部不再有；导览的阅读回顾改成"正在读"那一行右边的"回顾"文字入口。
⑤ "调整章节"入口放到找得到的地方：导览（导入的书）顶部"调整章节"文字入口、书籍详情里也有；导入页引导语写真实路径。
⑥ 导入引导语第二条改成"外文书自动译成中文——按书面语、高水准翻译，译完才能读，译的时候书架上显示加载中"；还没处理完的书（外文没译完、还在整理）点开不进阅读器，书籍详情写"处理中，完成后自动可读"，封面上有转圈；服务器处理完（轮询）自动变成可读。
备份 Demo/模板_v82备份.html。函数体在 改动_v967_片段.js、改动_v967_片段2.js。"""
import os,re
B=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))+'/'
P=B+'Demo/模板.html'
s=open(P,encoding='utf-8').read()
def frag(name):
    FR={}; cur=None
    for line in open(os.path.dirname(os.path.abspath(__file__))+'/'+name,encoding='utf-8').read().split('\n'):
        m=re.match(r'^### (\S+)',line)
        if m: cur=m.group(1); FR[cur]=[]; continue
        if cur: FR[cur].append(line)
    return {k:'\n'.join(v).strip('\n')+'\n' for k,v in FR.items()}
F1=frag('改动_v967_片段.js'); F2=frag('改动_v967_片段2.js')
def rep(a,b,n=1):
    global s
    c=s.count(a); assert c==n,(c,a[:90]); s=s.replace(a,b)
def fn(name,txt):
    global s
    i=s.index('\nfunction '+name+'(')+1; j=s.index('\n}\n',i)+2
    s=s[:i]+txt+s[j:]
# ---- ① 访客书架 ----
rep("function homePage(){",F1['needLogin']+"function homePage(){")
fn('shelf',F1['shelfRender']); fn('homePage',F1['homePage'])
# 书架上"我的"没有登录时没有 #shMe：mePage 入口保持；authPage 里 ‹ 回书架（原来回 homePage，现在 homePage=shelf）
# bookInfo：访客的底部按钮、处理中的书
rep("""<button class="btn" id="bOpen" style="margin-left:auto">${guest?'登录后阅读':st.fin?'再读一遍':st.started?'继续阅读':'开始阅读'}</button></div>`,{tall:true});
  $('#bOpen')?.addEventListener('click',()=>{ closeSheet(); if(guest&&!curUser()){ AFTER_LOGIN=()=>openBook(k); AFTER_T=`登录后阅读《${b.t}》`; authPage('login'); } else openBook(k); });""",
"""<button class="btn" id="bOpen" style="margin-left:auto" ${b.busy?'disabled':''}>${b.busy?'处理中，完成后可读':guest?'登录后阅读':st.fin?'再读一遍':st.started?'继续阅读':'开始阅读'}</button></div>`,{tall:true});
  $('#bOpen')?.addEventListener('click',()=>{ closeSheet(); if(b.busy) return; if(guest&&!curUser()){ AFTER_LOGIN=()=>openBook(k); AFTER_T=`登录后阅读《${b.t}》`; authPage('login'); } else openBook(k); });""")
rep("function openBook(k){ if((!window.__TEST||window.__GUESTCHK)&&!curUser()){",
    "function openBook(k){ if(BOOKS[k]&&BOOKS[k].busy){ toast(`<div class=\"tq\">《${esc(BOOKS[k].t)}》${esc(BOOKS[k].busy)}，完成后才能读</div>`,null,3000); return bookInfo(k,bookStat(k).prog); } if((!window.__TEST||window.__GUESTCHK)&&!curUser()){")
# 找书、导入、"我的"：没登录点了先登录
rep("""  document.querySelectorAll('.hmbooks [data-k]')""","""  document.querySelectorAll('.hmbooks [data-k]')""",0) if False else None
# ---- ② 轻度带读 ----
rep("MODE_T={light:'轻度',heavy:'重度'}","MODE_T={light:'轻度带读',heavy:'重度带读'}")
rep("<small>带读${MODE_T[PROF.mode]}</small>","<small>${MODE_T[PROF.mode]}</small>")
rep("伏笔会以 <b>${MODE_T[m]}</b> 的方式陪你读","伏笔会以 <b>${MODE_T[m]}</b> 的方式陪你读")
# ---- ③④ 札记并入笔记 ----
fn('minePanel',F2['minePanel'])
rep("\nfunction exportSheet(mode,from){",F2['arcBody']+"\nfunction exportSheet_old(mode,from){")
# 旧 exportSheet 保留为 exportSheet_old（不再被调用），新的入口：
rep("\nfunction exportSheet_old(mode,from){","\n"+F2['exportSheet']+"function exportSheet_old(mode,from){")
rep("""$('#endArc')?.addEventListener('click',()=>exportSheet(null,'end'));""","""$('#endArc')?.addEventListener('click',()=>minePanel('arc'));""")
# 导览：阅读回顾 = "正在读"右边的文字入口（小说 / 哲学书各一处）
rep("""<button class="olnow" data-go="${P[curI].n}"><span>正在读</span><b>命题 ${P[curI].n}</b><em>${pctOf()}%</em><span class="chev">›</span></button>""",
    """<div class="olnow"><button data-go="${P[curI].n}" class="olnb"><span>正在读</span><b>命题 ${P[curI].n}</b><em>${pctOf()}%</em></button><button class="olrc" id="olRecap">回顾</button></div>""")
rep("""<button class="olnow" data-go="${P[curI].n}"><span>正在读</span><b>${esc(unitName(curH.n))}</b><em>${pctOf()}%</em><span class="chev">›</span></button>""",
    """<div class="olnow"><button data-go="${P[curI].n}" class="olnb"><span>正在读</span><b>${esc(unitName(curH.n))}</b><em>${pctOf()}%</em></button><button class="olrc" id="olRecap">回顾</button></div>""")
rep("""  ${RD.size?`<div class="sfoot olfoot"><button class="btn ghost wide" id="olRecap">${ic('toc','')}阅读回顾</button></div>`:''}`,{tall:true});""","""`,{tall:true});""")
rep("""  ${tab==='hui'&&RD.size?`<div class="sfoot olfoot"><button class="btn ghost wide" id="olRecap">${ic('toc','')}阅读回顾</button></div>`:''}`,{tall:true});""","""`,{tall:true});""")
# ---- ⑤ 调整章节入口：导览顶部 + 书籍详情 ----
rep("""<div class="olnow"><button data-go="${P[curI].n}" class="olnb"><span>正在读</span><b>${esc(unitName(curH.n))}</b><em>${pctOf()}%</em></button><button class="olrc" id="olRecap">回顾</button></div>`:'')+HUI.map""",
    """<div class="olnow"><button data-go="${P[curI].n}" class="olnb"><span>正在读</span><b>${esc(unitName(curH.n))}</b><em>${pctOf()}%</em></button><button class="olrc" id="olRecap">回顾</button></div>`:'')+(CANEDIT()?`<div class="olchap"><span>章节分得不准？</span><button class="linkbtn" id="olChap">调整章节</button></div>`:'')+HUI.map""")
rep("""  $('#olRecap')?.addEventListener('click',()=>novelRecap(Infinity,true,true));""","""  $('#olRecap')?.addEventListener('click',()=>novelRecap(Infinity,true,true));
  $('#olChap')?.addEventListener('click',()=>chapterEditor());""")
rep("""    <dl class="meta bimeta">""","""    ${b.imported&&k===BK&&CANEDIT()?'<p class="bichap"><button class="linkbtn" id="biChap">调整章节</button></p>':''}
    <dl class="meta bimeta">""")
rep("""  $('#bOpen')?.addEventListener('click',()=>{ closeSheet(); if(b.busy)""","""  $('#biChap')?.addEventListener('click',()=>{ closeSheet(); chapterEditor(); });
  $('#bOpen')?.addEventListener('click',()=>{ closeSheet(); if(b.busy)""")
# ---- ⑥ 导入页引导语 + 处理中 ----
rep("""      <li><b>识别章节和封面</b>自动分章；分得不准，可以在书里的“阅读设置 › 更多设置”里调整。</li>
      <li><b>外文书先译成中文</b>译完之前，可以先读原文。</li>
      <li><b>逐步生成解释和回顾</b>需要一些时间；生成期间可以照常阅读、划线、写想法，还没生成的段落会有说明。</li>""",
"""      <li><b>识别章节和封面</b>自动分章；分得不准，打开书后在“导览”里点“调整章节”。</li>
      <li><b>外文书自动译成中文</b>按书面语、高水准的标准翻译；译完才能读，处理期间书架上这本书显示加载中。</li>
      <li><b>逐步生成解释和回顾</b>需要一些时间；生成期间可以照常阅读、划线、写想法。</li>""")
rep("""<span>${m.chapters} 章，约 ${ch} 字。解释和回顾会在后台逐步生成。</span>""","""<span>${m.chapters} 章，约 ${ch} 字。${m.foreign&&d.untranslated?'外文书正在译成中文，译完才能读。':'解释和回顾会逐步生成。'}</span>""")
# addShelfBook：外文没译完 → busy
rep("""  BOOKS[k]={t:m.title,imported:true,cover:m.cover||'',rows:""","""  const busy=m.foreign&&d.untranslated?(g.total?`翻译中 ${g.done}/${g.total}`:'等待翻译'):(m.status==='parsing'?'正在整理':'');
  BOOKS[k]={t:m.title,imported:true,busy,cover:m.cover||'',rows:""")
rep("""'正在翻译（${g.done} / ${g.total}）':'尚未翻译')""","""'正在翻译（${g.done} / ${g.total}）':'等待翻译')""",0) if False else None
# ---- CSS ----
rep('</style>',F1['css']+F2['css']+"\n.olnow{padding:0}.olnow .olnb{display:flex;align-items:center;gap:10px;flex:1;min-width:0;padding:12px 0 12px 14px;text-align:left;font-family:var(--ui)}\n.olchap{display:flex;align-items:center;gap:8px;margin:0 0 8px;font-size:var(--t-tag);color:var(--faint)}.olchap .linkbtn{padding:0}\n.bichap{margin:12px 0 0}.bichap .linkbtn{padding:0}\n</style>")
rep('if(SRV) Object.entries(ALL).forEach(([k,d])=>{ if(d.meta) addShelfBook(k,d); });',"if(SRV) Object.entries(ALL).forEach(([k,d])=>{ if(d.meta) addShelfBook(k,d); });\n/* v9.67：外文书译完之前不能读——书架上显示加载中；每 6 秒问一次服务器，处理完自动变成可读 */\nif(SRV&&!window.__TEST) setInterval(async()=>{ const ks=Object.keys(BOOKS).filter(k=>BOOKS[k].busy); if(!ks.length||!curUser()) return;\n  for(const k of ks){ try{ const d=await (await fetch('/api/books/'+k)).json(); if(d&&d.meta){ ALL[k]=d; const was=BOOKS[k].busy; const row=SHELF.find(x=>x[0]===k), keepId=row&&row[1]; if(row) SHELF.splice(SHELF.indexOf(row),0); SHELF=SHELF.filter(x=>x[0]!==k); addShelfBook(k,d); const nr=SHELF.find(x=>x[0]===k); if(nr&&keepId) nr[1]=keepId; if(was!==BOOKS[k].busy&&$('.shelf')) shelf(); } }catch(e){} } },6000);")
rep('if(window.__TEST) setTimeout(()=>window.__TEST({avatarSheet,',"if(window.__TEST) setTimeout(()=>window.__TEST({addBusyBook:(k,d,replace)=>{ if(replace){ SHELF=SHELF.filter(x=>x[0]!==k); } ALL[k]=Object.assign({key:'rb_test_'+k},d); d.meta.title=d.meta.title||'测试外文书'; addShelfBook(k,d); },avatarSheet,")
rep('<p class="mini avnote">图片只存在这台设备上，会自动裁成正方形。</p>','<p class="mini avnote">图片会自动裁成正方形。</p>')
rep('<div class="secbtns"><button class="btn ghost wide" id="secOut">退出登录</button><button class="meout" id="secDel">注销账号</button></div>','<div class="secbtns"><button class="secrow" id="secOut">退出登录</button><button class="secrow danger" id="secDel">注销账号</button></div>')
rep('</style>','\n/* v9.67 UI 审查：账户页底部的"退出登录/注销账号"不用大按钮，做成和"我的"菜单一致的分隔行 */\n.secbtns{gap:0;margin-top:8px;border-top:1px solid var(--line)}\n.secrow{display:flex;align-items:center;width:100%;min-height:48px;border-bottom:1px solid var(--line);text-align:left;font-size:var(--t-body);color:var(--ink)}\n.secrow.danger{color:#A33A2A}\n'+'</style>')
open(P,'w',encoding='utf-8').write(s); print('ok')
