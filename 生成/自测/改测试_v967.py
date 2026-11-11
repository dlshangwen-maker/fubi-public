"""v9.67 自测：访客书架、札记并进笔记、去大按钮、轻度带读、调整章节入口、导入引导、处理中。"""
import os,shutil,re
B=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))+'/'
P=B+'生成/自测_两本书.js'
if not os.path.exists(B+'生成/自测_两本书_v967前备份.js'): shutil.copy(P,B+'生成/自测_两本书_v967前备份.js')
s=open(P,encoding='utf-8').read()
def rep(a,b):
    global s
    assert s.count(a)==1,(s.count(a),a[:70]); s=s.replace(a,b)
# ---- 札记块整体换掉 ----
i=s.index("  // 文字规范\n  { T.minePanel('all'); const sh=document.querySelector('#sheet');")
j=s.index("    const sh2=document.querySelector('#sheet');",i)
NEW="""  // ===== 札记并进笔记（v9.67，用户 10-30）=====
  { T.minePanel('all'); const sh=document.querySelector('#sheet');
    ok('笔记底部没有"读书札记"大按钮，标签行最后是"札记"',!sh.querySelector('#expOpen')&&[...sh.querySelectorAll('.ntabs [data-tab]')].pop().dataset.tab==='arc'&&[...sh.querySelectorAll('.ntabs [data-tab]')].pop().textContent.includes('札记'));
    delete T.getS().expDraft; sh.querySelector('[data-tab="arc"]').click(); await wait(20);
    let tx=document.querySelector('#sheet').textContent;
    ok('点"札记"：还在同一个笔记面板里切换（同一排标签），不是另一整页',document.querySelector('#sheet .ntabs [data-tab="arc"][aria-pressed="true"]')&&!document.querySelector('#sheet').classList.contains('full')&&document.querySelector('#sheet .ttl').textContent==='笔记');
    ok('札记：排好的内容，含划线和想法',!!document.querySelector('#sheet .mdv')&&tx.includes('满纸荒唐言')&&tx.includes('作者也觉得自己痴'),'');
    ok('复制、导出是标题行右边的文字入口，不是大按钮',!!document.querySelector('#sheet .shead #exCopy')&&!!document.querySelector('#sheet .shead #exSave')&&!document.querySelector('#sheet .sfoot'));
    document.querySelector('#exEdit').click(); await wait(20);
    const ta=document.querySelector('#exText'); ok('点"编辑这篇札记"：原地变成输入框',!!ta&&!document.querySelector('#arcEdit').hidden&&document.querySelector('#arcView').hidden);
    ta.value=ta.value+'\\n\\n我自己补的一句。';
    document.querySelector('#exEdit').click(); await wait(20);
    ok('点"完成"：回到札记，显示编辑后的内容',!!document.querySelector('#sheet .mdv')&&document.querySelector('#sheet .mdv').textContent.includes('我自己补的一句'));
    ok('标明这是编辑过的版本',document.querySelector('#sheet').textContent.includes('这是你编辑过的版本'));
    let copied=null; try{Object.defineProperty(navigator,'clipboard',{value:{writeText:x=>{copied=x;return Promise.resolve();}},configurable:true});}catch(e){}
    document.querySelector('#exCopy').click(); await wait(30);
    ok('复制的是编辑后的内容',copied&&copied.includes('我自己补的一句'),String(copied).slice(-20));
    T.getS().notes.push({id:T.getS().nid++,type:'note',at:IDX['1.30'],quote:'元宵佳节',text:'新加的想法',t:Date.now()});
    T.minePanel('arc'); await wait(20); tx=document.querySelector('#sheet').textContent;
    ok('笔记有更新时提示重新整理',tx.includes('笔记又有更新')&&tx.includes('按最新笔记重新整理'),'');
    window.confirm=()=>true; document.querySelector('#exReset').click(); await wait(20);
    tx=document.querySelector('#sheet').textContent;
    ok('重新整理：含新想法、编辑被替换',tx.includes('新加的想法')&&!tx.includes('我自己补的一句')&&!T.getS().expDraft,'');
    T.getS().notes=T.getS().notes.filter(n=>n.text!=='新加的想法');
    // ===== 读后感（v9.24，2026-10-21）=====
    { T.minePanel('arc'); const sh=document.querySelector('#sheet'), r=T.reflectStat();
      ok('札记最上面有"读后感"一行',!!sh.querySelector('.rf')&&sh.querySelector('.rf').textContent.includes('读后感'),'');
      ok('读后感说明按记录数显示',sh.querySelector('.rfs').textContent.includes(r.ok?'记录已足够':'记录满 5 条'),r.n+'/'+r.th);
      ok('示例默认收起',sh.querySelector('#rfX').hidden);
      sh.querySelector('#rfEx').click(); ok('点"看示例"展开、按钮变"收起"',!sh.querySelector('#rfX').hidden&&sh.querySelector('#rfEx').textContent==='收起');
      ok('没有读后感时导出文本不含"读后感"',!T.archiveMD().includes('## 读后感'));
      T.getS().reflect={text:'测试读后感一段。'}; ok('有读后感时放在札记最前面',T.archiveMD().indexOf('## 读后感')>0&&T.archiveMD().indexOf('## 读后感')<(T.archiveMD().indexOf('## ',T.archiveMD().indexOf('## 读后感')+3)>>>0));
      T.getS().reflect={text:'测试读后感一段。'}; T.minePanel('arc'); let copied2=null; try{Object.defineProperty(navigator,'clipboard',{value:{writeText:x=>{copied2=x;return Promise.resolve();}},configurable:true});}catch(e){}
      const cb=document.querySelector('#sheet [data-rfc="mine"]'); ok('有读后感时：显示全文和复制图标',!!cb&&document.querySelector('#sheet .rf').textContent.includes('测试读后感一段'));
      cb.click(); await wait(30); ok('复制图标复制读后感全文',copied2==='测试读后感一段。',copied2);
      delete T.getS().reflect; T.minePanel('arc'); ok('没有读后感时：示例里有复制图标',!!document.querySelector('#sheet [data-rfc="ex"]'));
      T.closeSheet(); }

"""
s=s[:i]+NEW+s[j:]
# 旧测试里残留的札记入口
rep("""    T.closeSheet(); T.minePanel('all'); await wait(10); document.querySelector('#expOpen').click(); await wait(20);
    ok('从笔记打开札记：仍可返回笔记',!!document.querySelector('#exBack')); document.querySelector('#exBack').click(); await wait(20);
    ok('返回到笔记页',document.querySelector('#sheet .ttl').textContent==='笔记'); T.closeSheet();""",
    """    T.closeSheet(); T.minePanel('all'); await wait(10); document.querySelector('[data-tab="arc"]').click(); await wait(20);
    ok('从笔记点"札记"：还在笔记面板里',document.querySelector('#sheet .ttl').textContent==='笔记'&&!!document.querySelector('#sheet .mdv')); T.closeSheet();""")
rep("""    ok('书末"查看读书札记"直接打开札记页',document.querySelector('#sheet .ttl').textContent==='读书札记'&&!document.querySelector('#exBack'),document.querySelector('#sheet .ttl').textContent);""",
    """    ok('书末"查看读书札记"直接打开笔记里的"札记"',document.querySelector('#sheet .ttl').textContent==='笔记'&&!!document.querySelector('#sheet .ntabs [data-tab="arc"][aria-pressed="true"]'),document.querySelector('#sheet .ttl').textContent);""")
# ---- 去大按钮：导览阅读回顾改成文字入口 ----
rep("""    ok('导览：阅读回顾固定在底部（不在目录里）',!!document.querySelector('#sheet .sfoot.olfoot #olRecap')&&!document.querySelector('#olBody #olRecap'));""",
    """    ok('导览：没有底部大按钮，"回顾"是"正在读"那一行右边的文字入口',!document.querySelector('#sheet .sfoot')&&!!document.querySelector('#sheet .olnow #olRecap')&&document.querySelector('#olRecap').textContent==='回顾');""")
rep("""!!document.querySelector('#sheet .olfoot #olRecap')""","""!!document.querySelector('#sheet .olnow #olRecap')""")
# ---- 轻度带读 ----
rep("""'阅读偏好：带读开关 + 问卷答案'""","""'阅读偏好：带读开关 + 问卷答案'""")
# ---- 访客书架 ----
rep("ok('回到首页：就是一个书架——右上角\"登录\"、五本精读版封面',!!document.querySelector('.home')&&!!document.querySelector('#hmLogin')&&document.querySelectorAll('.hmbooks .book').length===5);",
    "ok('回到首页：就是书架——右上角\"登录\"，排序、排列、找书、导入都在，五本精读版封面',!!document.querySelector('.shelf')&&!!document.querySelector('#shLogin')&&!!document.querySelector('#sortB')&&!!document.querySelector('#shLib')&&!!document.querySelector('#impBtn')&&document.querySelectorAll('#bookList .book').length===5);")
rep("ok('不登录的首页不做营销页：没有大标题、介绍、大按钮',!document.querySelector('.hmtag,.hmsub,.hmfeat,.hmcta,#hmReg')&&document.querySelector('.home h1').textContent==='书架');",
    "ok('不登录的书架和登录后几乎一样：没有营销内容、没有头像',!document.querySelector('.hmtag,.hmsub,.hmfeat,.hmcta,#hmReg')&&document.querySelector('.shelf h1').textContent==='书架'&&!document.querySelector('#shMe'));")
rep("ok('首页不放\"继续阅读\"和书架操作',!document.querySelector('#shCont')&&!document.querySelector('#sortB'));",
    "ok('没登录点\"找书\"：先去登录（写明登录后找书）',(()=>{ document.querySelector('#shLib').click(); return !!document.querySelector('#auAcc')&&document.querySelector('.auhint').textContent.includes('找书'); })()); T.homePage(); await w(20);\n    ok('没登录点\"导入\"：先去登录（写明登录后导入）',(()=>{ document.querySelector('#impBtn').click(); return !!document.querySelector('#auAcc')&&document.querySelector('.auhint').textContent.includes('导入'); })()); T.homePage(); await w(20);")
rep("document.querySelector('.hmbooks .book').click(); await w(30);","document.querySelector('#bookList .book').click(); await w(30);")
open(P,'w',encoding='utf-8').write(s)
# 服务端模式
P2=B+'生成/自测/自测_服务端模式.js'
if not os.path.exists(B+'生成/自测/自测_服务端模式_v967前备份.js'): shutil.copy(P2,B+'生成/自测/自测_服务端模式_v967前备份.js')
t=open(P2,encoding='utf-8').read()
a="ok('导入页：会发生什么三步、版权提醒、去找书',document.querySelectorAll('.impsteps li').length===3&&document.querySelector('.impnote').textContent.includes('有权阅读')&&!!document.querySelector('#impFind'));"
assert t.count(a)==1
t=t.replace(a,a+"\n    ok('导入引导：外文书自动译成中文、按书面语高水准翻译、译完才能读、显示加载中',document.querySelectorAll('.impsteps li')[1].textContent.includes('自动译成中文')&&document.querySelectorAll('.impsteps li')[1].textContent.includes('高水准')&&document.querySelectorAll('.impsteps li')[1].textContent.includes('译完才能读')&&document.querySelectorAll('.impsteps li')[1].textContent.includes('加载中'));\n    ok('导入引导：调整章节写真实路径（导览里点\"调整章节\"），不再说\"阅读设置 › 更多设置\"',document.querySelectorAll('.impsteps li')[0].textContent.includes('导览')&&!document.querySelector('.impsteps').textContent.includes('更多设置'));")
open(P2,'w',encoding='utf-8').write(t)
print('ok')
