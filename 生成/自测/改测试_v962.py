"""v9.62 交互重做第一批：自测跟着改（伏笔面板、笔记的新结构）+ 新增第一批的测试。备份 生成/自测_两本书_v962前备份.js"""
import os,shutil
B=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))+'/'
P=B+'生成/自测_两本书.js'
if not os.path.exists(B+'生成/自测_两本书_v962前备份.js'): shutil.copy(P,B+'生成/自测_两本书_v962前备份.js')
s=open(P,encoding='utf-8').read()
def rep(a,b):
    global s
    assert s.count(a)==1,(s.count(a),a[:70]); s=s.replace(a,b)
rep("""  T.cluePanel('done'); t=document.querySelector('#sheet').textContent;
  ok('伏笔页“已回收”里直接带解释',t.includes('烟消火灭'),'');""",
"""  T.cluePanel('done'); document.querySelector('#sheet [data-cl="H02"]').click(); await wait(20); t=document.querySelector('#sheet').textContent;
  ok('伏笔页"已揭晓"里点一条，原地打开揭晓卡（有解释、能返回列表）',t.includes('烟消火灭')&&!!document.querySelector('#sheet [data-bk]'),'');
  document.querySelector('#sheet [data-bk]').click(); await wait(20); ok('揭晓卡 ‹ 回到伏笔列表',!!document.querySelector('#sheet [data-ct="done"][aria-pressed="true"]'));""")
rep("""    const row=id=>[...document.querySelectorAll('#sheet .q')].find(r=>r.querySelector(`[data-ms="${id}"]`));
    ok('伏笔页只有“我发现的伏笔”，没有普通提问',!!row(n14.id)&&!row(n13.id));
    ok('后文有答案：能写猜想，不能手动标记',!!row(n14.id)?.querySelector('[data-ed]')&&!row(n14.id)?.querySelector('[data-dn]'));
    ok('伏笔页标签“我发现的”',row(n14.id)?.textContent.includes('我发现的'));""",
"""    const row=id=>document.querySelector(`#sheet [data-cm="${id}"]`);
    ok('伏笔页只有“我发现的伏笔”，没有普通提问',!!row(n14.id)&&!row(n13.id));
    ok('伏笔页标签“我发现的”',row(n14.id)?.textContent.includes('我发现的'));
    row(n14.id).click(); await wait(20); ok('后文有答案：点开能编辑（写猜想），不能手动标记',!!document.querySelector('#sheet [data-ed]')&&!document.querySelector('#sheet [data-dn]'));""")
rep("""    T.minePanel('q'); await wait(20); const fb=[...document.querySelectorAll('#sheet [data-dn]')].find(b=>+b.dataset.dn===n11.id);
    fb&&fb.click(); await wait(20);""","""    T.minePanel('q'); await wait(20); document.querySelector(`#sheet [data-nm="${n11.id}"]`)?.click(); await wait(20); const fb=document.querySelector(`#sheet [data-dn="${n11.id}"]`);
    fb&&fb.click(); await wait(20);""")
rep("""    ok('确定后标为已揭晓、记下答案，回到笔记',!!n11.done&&n11.ans==='在后面'&&document.querySelector('#sheet .ttl')?.textContent==='笔记');""",
"""    ok('确定后标为已解答、记下答案，回到这条记录',!!n11.done&&n11.ans==='在后面'&&!!document.querySelector('#sheet .ttl'));""")
rep("""    ok('笔记里普通提问能点“我找到答案了”',!!document.querySelector(`#sheet [data-dn="${n13.id}"]`)&&!document.querySelector(`#sheet [data-dn="${n14.id}"]`));
    ok('笔记“疑问”栏不含伏笔',!document.querySelector(`#sheet [data-ed="${n14.id}"]`)&&document.querySelector('#sheet [data-tab="q"]').textContent.includes('疑问'));""",
"""    ok('笔记"疑问"栏不含伏笔',!document.querySelector(`#sheet [data-nm="${n14.id}"]`)&&!!document.querySelector(`#sheet [data-nm="${n13.id}"]`)&&document.querySelector('#sheet [data-tab="q"]').textContent.includes('疑问'));""")
rep("""    T.minePanel('q'); await wait(20);
    ok('笔记"疑问"栏不含伏笔'""","""    T.minePanel('q'); await wait(20);
    { const t0=document.querySelector('#sheet').textContent; document.querySelector(`#sheet [data-nm="${n13.id}"]`).click(); await wait(20); ok('笔记里普通提问点"…"进记录，能点"我找到答案了"',!!document.querySelector(`#sheet [data-dn="${n13.id}"]`)); T.minePanel('q'); await wait(20); }
    ok('笔记"疑问"栏不含伏笔'""")
rep("""  { T.cluePanel('open'); await wait(40); const c=document.querySelector('#sheet .src.clamp');""","""  { T.cluePanel('open'); await wait(40); document.querySelector('#sheet .cr[data-cl]')?.click(); await wait(30); const c=document.querySelector('#sheet .src.clamp');""")
rep("""    ok('笔记底部是“读书札记 · 查看”',!!sh.querySelector('#expOpen')&&sh.querySelector('#expOpen').textContent==='查看');""",
"""    ok('笔记底部是"查看读书札记"',!!sh.querySelector('#expOpen')&&sh.querySelector('#expOpen').textContent.includes('查看读书札记'));""")
rep("""  ok('点“看解释”打开回收卡片',t.includes('揭晓说明')&&t.includes('烟消火灭'),t.slice(0,60));""",
"""  ok('点“看解释”打开回收卡片：你当时猜 / 书里的答案',t.includes('你当时猜')&&t.includes('书里的答案')&&t.includes('烟消火灭'),t.slice(0,60));""")
# 新增：第一批
NEW="""
  // ===== v9.62 交互重做第一批 =====
  { const w=ms=>new Promise(r=>setTimeout(r,ms)); T.closeSheet(); const IX=T.getIDX(), S_=T.getS();
    T.openCard(IX['1.11']); await w(20); let sh=document.querySelector('#sheet');
    ok('解释卡片：深浅三档在内容顶部（不在标题行）',!!sh.querySelector('.sbody .lvrow [data-lv]')&&!sh.querySelector('.shead [data-lv]'));
    ok('解释卡片：底部有"上一段""下一段"',!!sh.querySelector('#cPrev')&&!!sh.querySelector('#cNext'));
    const lv0=S_.level; sh.querySelector('[data-lv="2"]').click(); await w(20); ok('切深浅：直接记住，不再问要不要设为默认',S_.level===2&&!document.querySelector('#sheet .nudge'));
    sh=document.querySelector('#sheet'); sh.querySelector('[data-lv="'+lv0+'"]').click(); await w(20);
    const n0=document.querySelector('#sheet .n').textContent+document.querySelector('#sheet .nsub').textContent; document.querySelector('#cNext').click(); await w(60);
    ok('点"下一段"：换成下一段的解释',document.querySelector('#sheet').classList.contains('show')&&(document.querySelector('#sheet .n').textContent+document.querySelector('#sheet .nsub').textContent)!==n0);
    T.closeSheet();
    S_.seen.H02=S_.seen.H02||Date.now(); delete S_.doneS.H02; delete S_.guesses.H02; T.save();
    T.cluePanel('open'); await w(20); const cr=document.querySelector('#sheet [data-cl="H02"]');
    ok('伏笔面板：每条两行（位置 / 问题），没有按钮堆',!!cr&&!!cr.querySelector('.crh')&&!!cr.querySelector('.crq')&&!document.querySelector('#sheet .qacts'));
    cr.click(); await w(20); ok('点一条：原地打开伏笔卡，左上角能回列表',!!document.querySelector('#sheet #cg')&&!!document.querySelector('#sheet [data-bk]'));
    document.querySelector('#cg').click(); await w(20); ok('写下猜想：原地换成填写页，有 ‹ 返回，把握仍是滑条',!!document.querySelector('#gt')&&!!document.querySelector('#sheet [data-bk]')&&document.querySelector('#cf')?.type==='range');
    document.querySelector('#gt').value='测试猜想'; document.querySelector('#gs').click(); await w(30);
    ok('保存后回到伏笔卡、卡上显示我的猜想',!!document.querySelector('#sheet .gv')&&document.querySelector('#sheet .gv').textContent.includes('测试猜想')&&!!document.querySelector('#sheet #cg'));
    ok('保存后提示"已保存 · 撤销"',document.querySelector('#toast').textContent.includes('已保存')&&document.querySelector('#toast').textContent.includes('撤销'));
    document.querySelector('#toast button:not(.tx)').click(); await w(20); ok('撤销后猜想没了',!S_.guesses.H02);
    T.closeSheet(); T.minePanel('all'); await w(20); sh=document.querySelector('#sheet');
    ok('笔记分类是一行纯文字（全部、划线、想法、疑问、书签）',sh.querySelectorAll('.ntabs [data-tab]').length===5&&!sh.querySelector('.ntabs svg'));
    ok('笔记每条没有一排按钮，只有"…"',!sh.querySelector('.qacts')&&(sh.querySelectorAll('.nr').length===0||!!sh.querySelector('.nr .nrm')));
    T.closeSheet(); const uid=T.addUL([{c:'p'+IX['1.9'],s:0,e:8}]); T.quickNote(uid); await w(40);
    const qb=document.querySelector('#qbar'); ok('输入条上有"想法 | 疑问"切换',!!qb&&qb.querySelectorAll('[data-qk]').length===2);
    const ta=qb.querySelector('#qt'); ta.value='为什么这样写'; ta.dispatchEvent(new Event('input')); ok('写了问句：自动选"疑问"',qb.querySelector('[data-qk="q"]').getAttribute('aria-pressed')==='true');
    qb.querySelector('[data-qk="note"]').click(); ok('读者可以改成"想法"',qb.querySelector('[data-qk="note"]').getAttribute('aria-pressed')==='true');
    qb.querySelector('#qs').click(); await w(260); const nn=S_.notes.find(n=>n.text==='为什么这样写'); ok('按读者选的存成想法',!!nn&&nn.type==='note');
    S_.notes=S_.notes.filter(n=>n!==nn); T.removeUL(uid); T.save(); document.querySelector('#toast').classList.remove('show');
    T.settings(); await w(20); sh=document.querySelector('#sheet');
    ok('阅读设置第一层只有排版，没有"清空本书记录""带读"',!!sh.querySelector('#fs')&&!sh.querySelector('#rs')&&!sh.querySelector('#mdseg')&&!!sh.querySelector('#setMore'));
    ok('阅读设置：遮罩透明、面板矮，边调边看',sh.classList.contains('setp')&&document.querySelector('#scrim').classList.contains('clear'));
    document.querySelector('#setMore').click(); await w(20); ok('"更多设置"里有阅读引导、解释深浅、清空记录，能返回',!!document.querySelector('#rs')&&!!document.querySelector('#lvseg')&&!!document.querySelector('[data-tg="guide"]')&&!!document.querySelector('#setBack'));
    document.querySelector('#setBack').click(); await w(20); ok('返回第一层',!!document.querySelector('#fs')); T.closeSheet();
    ok('关掉设置后遮罩恢复',!document.querySelector('#scrim').classList.contains('clear'));
  }"""
anchor="  // ===== v9.60：双击开解释、横屏批注栏 ====="
rep(anchor,NEW.strip('\n')+"\n"+anchor)
open(P,'w',encoding='utf-8').write(s); print('ok')
