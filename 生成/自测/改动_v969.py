"""v9.69（11-02 逐页审查第一批，用户确认 6–11 + 前面 5 条）。备份 Demo/模板_v84备份.html"""
import os
B=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))+'/'
P=B+'Demo/模板.html'
s=open(P,encoding='utf-8').read()
def rep(a,b,n=1):
    global s
    c=s.count(a); assert c==n,(c,a[:90]); s=s.replace(a,b)
# A1 问卷收起行标签
rep("const SHORT={q1:'平时',q2:'常卡在',q3:'希望'};","const SHORT={q1:'厚书',q2:'读不下去',q3:'伏笔'};")
rep("q.k==='q1'?'平时':q.k==='q2'?'常卡在':'希望'","q.k==='q1'?'厚书':q.k==='q2'?'读不下去':'伏笔'")
# A2 详情去进度条
rep("""${st.started&&!st.fin?`<span class="pbar"><i style="width:${st.pct}%"></i></span>`:''}</div></div>""","""</div></div>""")
# A3 页内确认：加"取消后回到哪"
rep("function confirmSheet(title,desc,okText,onOk,danger){","function confirmSheet(title,desc,okText,onOk,danger,onCancel){")
rep("""<button class="btn ghost" data-close>取消</button><button class="btn ${danger?'dgr':''}" id="cfOk\"""","""<button class="btn ghost" id="cfNo">取消</button><button class="btn ${danger?'dgr':''}" id="cfOk\"""")
rep("  $('#cfOk').onclick=()=>{ closeSheet(); onOk(); };","  $('#cfOk').onclick=()=>{ closeSheet(); onOk(); };\n  $('#cfNo').onclick=()=>{ closeSheet(); if(onCancel) onCancel(); };")
rep("const cancel=()=>{const t=ta.value.trim(); if(t&&!confirm('内容尚未保存，确定放弃？划线将保留。')) return; close();};","const cancel=()=>{const t=ta.value.trim(); if(t) return confirmSheet('放弃这条内容？','还没保存。放弃后，划线会保留。','放弃',close); close();};")
rep("""  $('#exReset')?.addEventListener('click',()=>{ if(!confirm(stale?'将按最新笔记重新整理，你的编辑会被替换。确定？':'将恢复原始内容，你的编辑会被替换。确定？')) return; delete S.expDraft; save(); minePanel('arc'); });""","""  $('#exReset')?.addEventListener('click',()=>confirmSheet(stale?'重新整理札记？':'恢复原始内容？',stale?'将按最新笔记重新整理，你编辑过的内容会被替换。':'你编辑过的内容会被替换。',stale?'重新整理':'恢复',()=>{ delete S.expDraft; save(); minePanel('arc'); },false,()=>minePanel('arc')));""")
rep("""if($('#rs')) $('#rs').onclick=()=>{if(confirm('将删除本书的进度、书签、划线、想法、疑问与猜想。确定清空？')){const keep=S.view;Object.assign(S,structuredClone(DEF));S.view=keep;save();closeSheet();reader(false);}};""","""if($('#rs')) $('#rs').onclick=()=>confirmSheet('清空本书记录？','这本书的进度、书签、划线、想法、疑问和猜想都会删除，无法恢复。','确认清空',()=>{const keep=S.view;Object.assign(S,structuredClone(DEF));S.view=keep;save();reader(false);},true,()=>settings('more'));""")
# B4 / B5
rep("来源见书籍详情（在书架上长按）。目前是试用阶段，界面和内容仍在调整。","来源见书籍详情（点书旁的“…”）。")
rep("""    <p class="foot">${guest?'登录后可以阅读、记录和找书。':'长按书籍可查看详情。'}</p>\n""","")
# 6 7
rep('<div class="meh"><b>带读</b></div>','<div class="meh"><b>伏笔怎么陪你读</b></div>')
rep('<button id="meAbout"><span>关于伏笔</span><small></small>','<button id="meAbout"><span>关于伏笔</span>')
# 8 功能入口墨色，蓝只留给读者写的
rep(".linkbtn{display:inline-flex;align-items:center;gap:5px;color:var(--blue);",".linkbtn{display:inline-flex;align-items:center;gap:5px;color:var(--ink);")
rep(".olnow .olrc{margin-left:8px;color:var(--blue);",".olnow .olrc{margin-left:8px;color:var(--ink);")
# 10 找书文案
rep("这里能搜到的是古登堡计划和维基文库里的公版书。手里有这本书的文件","这里能搜到的是已过版权期的公版书。手里有这本书的文件")
rep("书来自古登堡计划和维基文库，都是公版书；下载的书只在你自己的书架上。","这些都是已过版权期的公版书；下载的书只在你自己的书架上。")
rep("内容提要（英文，来自古登堡计划）","内容提要（英文）")
# 11 导入页缩短
rep("自动分章；分得不准，打开书后在“导览”里点“调整章节”。","自动分章；分得不准，在书里的“导览”点“调整章节”。")
rep("按书面语、高水准的标准翻译；译完才能读，处理期间书架上这本书显示加载中。","按书面语、高水准翻译；译完才能读，期间书架上显示加载中。")
rep("需要一些时间；生成期间可以照常阅读、划线、写想法。","需要一些时间，期间可以照常阅读。")
open(P,'w',encoding='utf-8').write(s); print('ok')
