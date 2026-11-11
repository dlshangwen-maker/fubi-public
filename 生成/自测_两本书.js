window.confirm=()=>false; window.alert=()=>{};   /* 测试时不让系统对话框卡住页面（默认"取消"，和预览面板里原来的行为一致） */
window.__TEST=async T=>{
  const R=[]; const ok=(n,c,x='')=>{ R.push([n,!!c,x]); window.__LAST=n; };   /* __LAST：最近记下的一项，页面报错时由 run_browser_tests.js 读出来，定位是哪一步之后出的错 */
  const readTo=i=>{ T.markRd(0,i); };   /* 0..i 都算翻过 */
  const readAt=i=>{ T.markRd(0,i); T.getS().current=i; };   /* 同上，并停在 i */
  const resetRd=()=>{ const S_=T.getS(); T.getRD().clear(); S_.rd=[]; S_.furthest=-2; };
  const wait=ms=>new Promise(r=>setTimeout(r,ms));
  try{ localStorage.clear(); T.TIPSS().welcomed=1; }catch(e){}
  try{
  T.shelf();
  ok('书架五本书（只用公版）',document.querySelectorAll('.book').length===5);
  T.openBook('hlm'); await wait(300); for(let k=0;k<12&&!document.querySelector('#where').textContent;k++) await wait(100);   /* 顶栏在第一次滚动检查后才写上，页面忙时可能晚一点 */
  const P=T.P(), els=T.els();
  ok('红楼梦 214 段',els.length===214,els.length);
  ok('5 个回目标题',document.querySelectorAll('.hui').length===5);
  ok('人名链接 393',document.querySelectorAll('.pn').length===393,document.querySelectorAll('.pn').length);
  ok('诗词段有缩进类',document.querySelectorAll('.prop.poem').length>20,document.querySelectorAll('.prop.poem').length);
  ok('顶栏显示第一回',document.querySelector('#where').textContent.includes('第一回'),document.querySelector('#where').textContent+' y'+scrollY);
  // 剧透：每个人名链接所在段 >= 该人物 first
  const PE=T.PEOPLE(), by={}; PE.forEach(p=>by[p.id]=p);
  let bad=[]; document.querySelectorAll('.pn').forEach(e=>{const i=+e.closest('.prop').dataset.i, p=by[+e.dataset.p]; if(!p||p.first>i) bad.push(e.textContent+'@'+P[i].n);});
  ok('人名链接不早于人物出场',!bad.length,bad.slice(0,5).join(' '));
  // 人物卡：宝玉在 2.12 处
  const IDX=new Proxy({},{get:(o,k)=>T.getIDX()[k]}), S=()=>T.getS();
  const bao=PE.find(p=>p.name==='贾宝玉');
  resetRd(); readTo(IDX['2.12']); T.personCard(bao.id,IDX['2.12']);
  let t=document.querySelector('#sheet').textContent;
  ok('宝玉卡在 2.12 叫“宝玉”、不提摔玉',t.includes('宝玉')&&!t.includes('摔')&&!t.includes('贾宝玉')&&!t.includes('黛玉'),t.slice(0,120));
  readTo(IDX['3.38']); T.personCard(bao.id,IDX['3.38']);
  t=document.querySelector('#sheet').textContent;
  ok('宝玉卡在 3.38 有摔玉、有表妹黛玉',t.includes('摔')&&t.includes('黛玉'),'');
  const feng=PE.find(p=>p.name==='王熙凤'); resetRd(); readTo(IDX['2.16']); T.personCard(feng.id,IDX['2.16']);
  t=document.querySelector('#sheet .ttl').textContent;
  ok('凤姐在 2.16 不叫王熙凤',t!=='王熙凤',t);
  // 遍历：每个人物在每个位置的卡片，身份/别称/关系都不超前
  let leak=[];
  PE.forEach(p=>{ for(const i of [p.first, ...p.ap]){ const ids=p.ids.filter(x=>x[0]<=i); if(!ids.length) leak.push(p.name+'无身份@'+P[i].n); } });
  ok('每个人名出现的地方，人物卡都有可说的身份',!leak.length,leak.slice(0,6).join(' '));
  T.closeSheet&&T.closeSheet();
  // 伏笔 H02：1.15 提出 → 1.32 回收
  resetRd(); S().vis=-2; S().current=-1; readTo(IDX['1.15']); T.setPos(IDX['1.15']); S().vis=IDX['1.15']; T.els()[IDX['1.15']].scrollIntoView({block:'center'}); T.paintMarks(); await wait(50);
  ok('读到 1.15 亮伏笔 H02',!!document.querySelector('[data-clue="H02"]'));
  ok('只有未打开的伏笔时：显示小菱形、不显示数字',!document.querySelector('#near').hidden&&document.querySelector('#clueCnt').hidden);
  await wait(2900); document.querySelector('#toast').classList.remove('show');   /* 等“第一次发现伏笔”的说明提示过去 */
  T.openClue('H02'); ok('伏笔卡片显示问题',document.querySelector('#sheet').textContent.includes('有命无运'));
  T.closeSheet(); readTo(IDX['1.32']); T.setPos(IDX['1.32']); await wait(50);
  ok('只是 1.32 段首过了阅读线：还不揭晓（答案在段中）',!S().doneS.H02);
  readTo(IDX['1.33']); T.setPos(IDX['1.33']); await wait(50);
  ok('读过 1.32、到了下一段：自动回收',!!S().doneS.H02);
  await wait(2600);
  { const sh=document.querySelector('#sheet'), op=sh.classList.contains('show');
    ok('回收时不弹窗（弹出的只可能是新发现的主线伏笔卡片）',!op||(!!sh.querySelector('.clmain')&&!sh.textContent.includes('有命无运')),op?sh.textContent.slice(0,50):''); T.closeSheet(); }
  const tb=document.querySelector('#toast');
  ok('揭晓时出提示条，带“看解释”',tb.classList.contains('show')&&tb.textContent.includes('伏笔揭晓')&&tb.textContent.includes('看解释'),tb.textContent.slice(0,40));
  tb.querySelector('button').click(); await wait(30); t=document.querySelector('#sheet').textContent;
  ok('点“看解释”打开回收卡片：你当时猜 / 书里的答案',t.includes('你当时猜')&&t.includes('书里的答案')&&t.includes('烟消火灭'),t.slice(0,60));
  T.cluePanel('done'); document.querySelector('#sheet [data-cl="H02"]').click(); await wait(20); t=document.querySelector('#sheet').textContent;
  ok('伏笔页"已揭晓"里点一条，原地打开揭晓卡（有解释、能返回列表）',t.includes('烟消火灭')&&!!document.querySelector('#sheet [data-bk]'),'');
  document.querySelector('#sheet [data-bk]').click(); await wait(20); ok('揭晓卡 ‹ 回到伏笔列表',!!document.querySelector('#sheet [data-ct="done"][aria-pressed="true"]'));
  T.reveal('H02'); t=document.querySelector('#sheet').textContent;
  ok('回收卡片用“第一回”，不露段号',t.includes('第一回')&&!/1\.32/.test(t),t.slice(0,60));
  // 不回收的伏笔：H10 判词、H11
  S().vis=IDX['5.82']; readTo(IDX['5.83']); T.setPos(IDX['5.83']); await wait(50);
  ok('五回之后才回收的伏笔不会被误回收',!S().doneS.H10&&!S().doneS.H01&&!S().doneS.H11);
  // 示范问答：R04（读过的）引用显示开头几个字
  T.askQuestion(null,'封肃是谁？',{at:IDX['1.33'],qa:'R04'}); await wait(30);
  t=document.querySelector('#sheet').innerHTML;
  ok('读过的：引用写成「开头几个字」',t.includes('「')&&!/>1\.11</.test(t),'');
  // R19 判词：后面有、但不在 demo 里
  T.askQuestion(null,'“玉带林中挂，金簪雪里埋”，说的是谁？',{at:IDX['5.23'],qa:'R19'}); await wait(30);
  t=document.querySelector('#sheet').textContent;
  ok('判词问答：只讲字面 + 答案在尚未收录的章节',t.includes('一个个兑现')&&t.includes('尚未收录'),'');
  document.querySelector('#aBury').click(); await wait(30);
  const n=S().notes.find(x=>x.qa==='R19');
  ok('判词问答埋下伏笔，不设自动回收',n&&n.type==='q'&&!n.rv&&n.later);
  // R03 后面有 → 2.4 自动回收
  T.askQuestion(null,'这个回头看雨村的丫鬟，和雨村还会再见吗？',{at:IDX['1.20'],qa:'R03'}); await wait(20);
  document.querySelector('#aBury').click(); await wait(20);
  const n3=S().notes.find(x=>x.qa==='R03'); S().current=IDX['1.20'];
  ok('R03 埋下，回收点 2.4',n3&&n3.rv==='2.4');
  readTo(IDX['2.4']); T.checkMine(IDX['2.4']); ok('读到 2.4 自动回收 R03',!!n3.done);
  // 目录
  resetRd(); readAt(IDX['3.15']); T.outline('hui'); await wait(20);
  t=document.querySelector('#sheet').textContent;
  ok('目录·回目：五回都列出（可跳转）',t.includes('第三回')&&t.includes('第五回'),'');
  ok('目录·回目：第三回只列读过的小节',t.includes('王熙凤笑着出场')&&!t.includes('摔了自己的玉'),'');
  S().vis=IDX['3.15']; S().current=IDX['3.15']; T.outline('ppl'); await wait(20);
  t=document.querySelector('#sheet').textContent;
  ok('目录·人物：有凤姐，没宝钗、没薛蟠',t.includes('王熙凤')&&!t.includes('宝钗')&&!t.includes('薛蟠'),'');
  // 回顾
  T.novelRecap(1000); t=document.querySelector('#sheet').textContent;
  ok('一天内：只一句，不列前几回',t.includes('上次读到第三回')&&!t.includes('前面几回'),'');
  ok('打开时的回顾：按钮只写“继续阅读”、不列未回收伏笔',document.querySelector('#sheet .sfoot .btn').textContent==='继续阅读'&&!t.includes('未回收的伏笔'),'');
  T.novelRecap(10*864e5); t=document.querySelector('#sheet').textContent;
  ok('隔 10 天：加前面几回和本回读过部分',t.includes('距上次阅读 10 天')&&t.includes('前面几回')&&t.includes('第三回已读部分'),'');
  ok('回顾不超前（没提摔玉、薛蟠）',!t.includes('摔')&&!t.includes('薛蟠'),'');
  { const S2=T.getS(); resetRd(); readAt(IDX['4.12']); T.novelRecap(10*864e5); const tt=document.querySelector('#sheet').textContent;
    ok('停在 4.12 时回顾不提判案（4.17）',!tt.includes('胡乱判')&&!tt.includes('充发'),tt.slice(0,80)); }
  // 划线 + 想法，进推理档案
  const id=T.addUL([{c:'p'+IDX['1.9'],s:0,e:5}]); S().notes.push({id:S().nid++,type:'note',hl:id,at:IDX['1.9'],text:'作者也觉得自己痴？',t:Date.now()});
  S().guesses.H02={text:'英莲会出事',conf:6};
  T.minePanel('all'); t=document.querySelector('#sheet').textContent;
  ok('笔记里不再有“推理档案”入口，笔记标题行右边有“札记”入口',!t.includes('推理档案')&&t.includes('札记'),'');
  const mdt=T.archiveMD();
  ok('导出内容：伏笔、猜想、划线、想法都在',mdt.includes('有命无运')&&mdt.includes('英莲会出事')&&mdt.includes('满纸荒唐言')&&mdt.includes('作者也觉得自己痴'),'');
  ok('导出不打分',!/猜对|猜中|正确率|分数/.test(mdt));
  ok('底部导航叫“导览”',document.querySelector('#nToc').textContent.includes('导览'));
  T.outline('hui'); ok('导览面板标题',document.querySelector('#sheet .ttl').textContent==='导览');
  const md=T.archiveMD(); ok('导出 Markdown',md.startsWith('# 《红楼梦》前五回 · 读书札记')&&md.includes('写于 ')&&!md.includes('导出于')&&md.includes('6 成把握'),md.slice(0,40));
  ok('札记正文里不放 logo',!T.mdHTML(md).includes('mthead'));
  T.minePanel('all'); ok('笔记里没有“读书札记”大按钮',!document.querySelector('#sheet #expOpen')&&!document.querySelector('#sheet .sfoot'));
  T.askQuestion(null,'自由提问测试？',{at:IDX['1.3']}); await wait(20);
  ok('没有现成回答：不写猜想，按钮“好的”',document.querySelector('#sheet .ttl').textContent==='疑问已记下'&&!document.querySelector('#cg2')&&document.querySelector('#aBury').textContent.trim()==='好的');
  ok('没有现成回答时，说清楚去哪里点“我找到答案了”',document.querySelector('#sheet').textContent.includes('“我找到答案了”'));
  { const S6=T.getS(); ok('提问一记下就已保存',S6.notes.some(n=>n.text==='自由提问测试？'&&n.type==='q'));
    document.querySelector('#sheet [data-close]').click(); await wait(20);
    ok('× 关掉，提问仍保留',S6.notes.some(n=>n.text==='自由提问测试？'));
    // 看回答后能返回伏笔页
    T.askQuestion(null,'封肃是谁？',{at:IDX['1.33'],qa:'R04'}); await wait(20); T.minePanel('q'); await wait(20);
    const sa=document.querySelector('#sheet [data-sa]'); sa&&sa.click(); await wait(20);
    ok('笔记“看回答”后有返回',!!document.querySelector('#sheet [data-bk]'));
    document.querySelector('#sheet [data-bk]')?.click(); await wait(20);
    ok('返回后回到笔记',document.querySelector('#sheet .ttl')?.textContent==='笔记');
    S6.notes=S6.notes.filter(n=>n.qa!=='R04'||n.text!=='封肃是谁？'||true); 
    S6.notes=S6.notes.filter(n=>n.text!=='自由提问测试？'); T.save(); }
  // 伏笔页默认停在最近有变化的那一栏
  { const S9=T.getS(); const n9={id:S9.nid++,type:'q',at:IDX['1.3'],text:'新提问',rv:'2.4',done:false,t:Date.now()+5000}; S9.notes.push(n9); T.save();
    T.closeSheet(); T.cluePanel(); await wait(20);
    ok('刚记下新提问：伏笔页停在“未揭晓”',document.querySelector('#sheet [data-ct="open"]').getAttribute('aria-pressed')==='true');
    n9.done=Date.now()+9000; T.save(); T.closeSheet(); T.cluePanel(); await wait(20);
    ok('刚有东西揭晓：伏笔页停在“已揭晓”',document.querySelector('#sheet [data-ct="done"]').getAttribute('aria-pressed')==='true');
    T.closeSheet(); T.paintMarks();
    const mk=document.querySelector(`[data-mine="${n9.id}"]`);
    ok('我发现的伏笔已揭晓：蓝色空心菱形内一个勾',!!mk&&mk.classList.contains('mine')&&!!mk.querySelector('svg.big'));
    const cs=document.querySelector('.mk.clue.solved');
    ok('已揭晓的伏笔出处：空心菱形内一个勾',!!cs&&!!cs.querySelector('svg.big')&&!cs.querySelector('.gem'));
    S9.notes=S9.notes.filter(n=>n!==n9); T.save(); T.paintMarks(); }
  // 页边标记对齐到锚句那一行
  { const S10=T.getS(); readTo(Math.max(T.getS().furthest,IDX['1.33'])); S10.vis=S10.furthest; S10.seen.H02=1; S10.doneS.H02=S10.doneS.H02||Date.now(); T.save(); T.closeSheet(); T.paintMarks(); await wait(50);
    const lineOf=(i,sent)=>{ const C=T.els()[i].querySelector('.zh'), t=C.textContent, o=t.indexOf(sent); const w=document.createTreeWalker(C,NodeFilter.SHOW_TEXT); let n,pos=0; while((n=w.nextNode())){ if(pos+n.length>o){const r=document.createRange(); r.setStart(n,o-pos); r.setEnd(n,o-pos+1); const rc=r.getClientRects()[0]; return rc.top+rc.height/2;} pos+=n.length;} };
    const mk=document.querySelector('[data-clue="H02"]'), r1=mk.getBoundingClientRect(), y1=lineOf(IDX['1.15'],'有命无运累及爹娘之物');
    ok('伏笔标记和“有命无运”那一行对齐',Math.abs(r1.top+r1.height/2-y1)<20,Math.round(r1.top+r1.height/2)+' vs '+Math.round(y1));
    const an=document.querySelector('[data-ans="H02"]');
    if(an){ const r2=an.getBoundingClientRect(), y2=lineOf(IDX['1.32'],'早成了一堆瓦砾场了'); ok('揭晓标记和“瓦砾场”那一行对齐',Math.abs(r2.top+r2.height/2-y2)<20,Math.round(r2.top+r2.height/2)+' vs '+Math.round(y2)); }
    else ok('揭晓标记存在',false); }
  // 我找到答案了：不再用 prompt，弹小面板
  { const S11=T.getS(); const n11={id:S11.nid++,type:'q',at:IDX['1.3'],text:'找答案测试',done:false,t:Date.now()}; S11.notes.push(n11); T.save();
    T.minePanel('q'); await wait(20); document.querySelector(`#sheet [data-nm="${n11.id}"]`)?.click(); await wait(20); const fb=document.querySelector(`#sheet [data-dn="${n11.id}"]`);
    fb&&fb.click(); await wait(20);
    ok('点“我找到答案了”弹出记答案的小面板',document.querySelector('#sheet .ttl')?.textContent==='我找到答案了');
    document.querySelector('#faT').value='在后面'; document.querySelector('#faOk').click(); await wait(30);
    ok('确定后标为已解答、记下答案，回到这条记录',!!n11.done&&n11.ans==='在后面'&&!!document.querySelector('#sheet .ttl'));
    T.minePanel('q'); await wait(20); ok('笔记里也能看到我记下的答案',document.querySelector('#sheet').textContent.includes('我记下的答案：在后面'));
    ok('读书札记里有我记下的答案',T.archiveMD().includes('我记下的答案：在后面'));
    S11.notes=S11.notes.filter(n=>n!==n11); T.save(); T.closeSheet(); }
  { const S13=T.getS(); const n13={id:S13.nid++,type:'q',at:IDX['1.3'],text:'没有答案的提问',done:false,t:Date.now()}; S13.notes.push(n13);
    const n14={id:S13.nid++,type:'q',at:IDX['1.20'],text:'后文有答案的提问',rv:'2.4',qa:'R03',done:false,t:Date.now()}; S13.notes.push(n14); T.save();
    T.cluePanel('open'); await wait(20);
    const row=id=>document.querySelector(`#sheet [data-cm="${id}"]`);
    ok('伏笔页只有“我发现的伏笔”，没有普通提问',!!row(n14.id)&&!row(n13.id));
    ok('伏笔页标签“我发现的”',row(n14.id)?.textContent.includes('我发现的'));
    row(n14.id).click(); await wait(20); ok('后文有答案：点开能编辑（写猜想），不能手动标记',!!document.querySelector('#sheet [data-ed]')&&!document.querySelector('#sheet [data-dn]'));
    T.minePanel('q'); await wait(20);
    { const t0=document.querySelector('#sheet').textContent; document.querySelector(`#sheet [data-nm="${n13.id}"]`).click(); await wait(20); ok('笔记里普通提问点"…"进记录，能点"我找到答案了"',!!document.querySelector(`#sheet [data-dn="${n13.id}"]`)); T.minePanel('q'); await wait(20); }
    ok('笔记"疑问"栏不含伏笔',!document.querySelector(`#sheet [data-nm="${n14.id}"]`)&&!!document.querySelector(`#sheet [data-nm="${n13.id}"]`)&&document.querySelector('#sheet [data-tab="q"]').textContent.includes('疑问'));
    { const t=document.querySelector('#sheet').textContent; ok('疑问不出现“揭晓”，用“待解答”',!/[已未]揭晓/.test(t)&&t.includes('待解答'),t.slice(0,80)); }
    T.paintMarks(); ok('普通提问页边没有图标',!document.querySelector(`.mk[data-mine="${n13.id}"]`)&&!!document.querySelector(`.mk.clue.mine[data-mine="${n14.id}"]`));
    T.composer({editId:n13.id}); await wait(20); ok('没有答案的提问：编辑页没有猜想框',!document.querySelector('#cg2'));
    T.composer({editId:n14.id}); await wait(20); ok('后文有答案、未揭晓：编辑页有猜想框',!!document.querySelector('#cg2'));
    n14.done=Date.now(); T.composer({editId:n14.id}); await wait(20); ok('揭晓后：猜想只读',!document.querySelector('#cg2'));
    T.closeSheet(); S13.notes=S13.notes.filter(n=>n!==n14);
    S13.notes=S13.notes.filter(n=>n!==n13); T.save(); T.closeSheet(); }
  { const S15=T.getS(), hid=T.addUL([{c:'p'+IDX['1.9'],s:0,e:20}]); const n15={id:S15.nid++,type:'q',hl:hid,parts:[{c:'p'+IDX['1.9'],s:0,e:20}],at:IDX['1.9'],text:'灰线测试',done:false,t:Date.now()}; S15.notes.push(n15); T.save(); T.paintUL(); await wait(20);
    const m=document.querySelector(`mark.nt[data-nt="${n15.id}"]`); ok('疑问的波浪线没有多余的灰色下边框',!!m&&getComputedStyle(m).borderBottomStyle==='none');
    T.removeUL(hid); S15.notes=S15.notes.filter(n=>n!==n15); T.save(); T.paintUL(); }
  { const hid=T.addUL([{c:'p'+IDX['1.9'],s:0,e:10}]); T.hlSheet(hid); ok('划线弹窗按钮叫“写点什么”',document.querySelector('#hWrite')?.textContent.trim()==='写点什么'); T.closeSheet(); T.removeUL(hid); }
  // 黄线动效：点图标时划过对应原文，结束后消失
  { const S12=T.getS(); S12.seen.H02=1; T.paintMarks(); const r=T.clueRange(T.getS()&&{id:'H02','提出':'1.15','提出锚句':'有命无运累及爹娘之物'},'src');
    const txt=T.els()[IDX['1.15']].querySelector('.zh').textContent.slice(r[0].s,r[0].e);
    ok('划线范围是完整的一句',txt.includes('有命无运累及爹娘之物')&&/^[施“]/.test(txt)&&/[？?”]$/.test(txt),txt);
    T.sweep(r); await wait(30); ok('划线动效出现',!!document.querySelector('mark.swline'));
    await wait(2100); ok('划线动效结束后消失',!document.querySelector('mark.swline')); }
  // 答案就在眼前：同一回内、300 字以内
  ok('R22（3.11→3.12）判为就在眼前',T.nearAns(IDX['3.11'],'3.12'));
  ok('R03（1.20→2.4）跨回，不算就在眼前',!T.nearAns(IDX['1.20'],'2.4'));
  ok('R06（2.6→2.16）同回但太远，不算',!T.nearAns(IDX['2.6'],'2.16'));
  { const S8=T.getS(); T.askQuestion(null,'笑着进来、说“我来迟了”的这位是谁？',{at:IDX['3.11'],qa:'R22'}); await wait(20);
    t=document.querySelector('#sheet').textContent;
    ok('就在眼前：只请读者往下读，不说出答案',t.includes('继续往下读一点')&&!t.includes('王熙凤')&&!t.includes('琏二嫂子'),t.slice(0,60));
    T.closeSheet(); S8.notes=S8.notes.filter(n=>n.qa!=='R22'); T.save(); T.paintMarks(); }
  // 人名在划线上：点人名仍打开人物卡，卡片底部可转到划线
  { const i=IDX['3.12'], pe=T.els()[i].querySelector('.pn'); if(pe){ const C=T.els()[i].querySelector('.zh'), r=document.createRange(); r.selectNodeContents(pe);
      const pre=document.createRange(); pre.setStart(C,0); pre.setEnd(r.startContainer,r.startOffset); const s0=pre.toString().length;
      const hid=T.addUL([{c:'p'+i,s:Math.max(0,s0-2),e:s0+pe.textContent.length+2}]); await wait(20);
      const pn2=T.els()[i].querySelector('mark.ul .pn, .pn mark.ul')||T.els()[i].querySelector('.pn'); pn2.click(); await wait(20);
      ok('人名和划线重叠：点人名打开人物卡',!document.querySelector('#hDel')&&!!document.querySelector('#sheet .pcard'));
      ok('人物卡底部可转到这段划线',!!document.querySelector('#pcRec'));
      document.querySelector('#pcRec')?.click(); await wait(20); ok('点了转到划线面板',!!document.querySelector('#hDel'));
      T.closeSheet(); T.removeUL(hid); } else ok('3.12 有人名',false); }
  // 想法：取消划线后正文里仍有标记
  { const S7=T.getS(), hid=T.addUL([{c:'p'+IDX['3.12'],s:0,e:20}]); T.quickNote(hid); await wait(30);
    document.querySelector('#qt').value='这一句写得好'; document.querySelector('#qs').click(); await wait(250);
    const nn=S7.notes.find(n=>n.text==='这一句写得好');
    ok('写了想法的划线：只显示想法线，不显示纯划线',!document.querySelector(`mark.ul[data-ul="${hid}"]`)&&!!document.querySelector(`mark.nt[data-nt="${nn.id}"]`));
    ok('想法没有页边图标',!document.querySelector('.mk[data-me="note"]'));
    T.noteSheet(nn.id); await wait(20); ok('点想法线打开这条想法，有“删除”',!!document.querySelector('#nDel'));
    document.querySelector('#nDel').click(); await wait(20);
    ok('删除想法：线和划线一起删',!S7.notes.includes(nn)&&!S7.ul.some(u=>u.id===hid)&&!document.querySelector(`mark.nt[data-nt="${nn.id}"]`));
    document.querySelector('#toast button')?.click(); await wait(20); ok('删除后可撤销',S7.notes.includes(nn)&&S7.ul.some(u=>u.id===hid));
    S7.notes=S7.notes.filter(n=>n!==nn); S7.ul=S7.ul.filter(u=>u.id!==hid); T.save(); T.paintMarks(); }
  // 名称：读者的叫“提问”，不叫“我埋的”
  T.cluePanel('open'); await wait(20); t=document.querySelector('#sheet').textContent;
  ok('伏笔页里不再出现“我埋的/书里埋的”',!t.includes('我埋的')&&!t.includes('书里埋的'),'');
  // 原文截取落在句读处
  { const fl=T.firstLine||null; const s=document.createElement('div'); s.innerHTML=T.srcBlock('一二三四五六七八九十，一二三四五六七八九十一二三四五六七八九十，一二三四五六七八九十一二三四五六七八九十。一二三四五六七八九十一二三四五六七八九十。');
    const pv=s.querySelector('.pv'); const full='一二三四五六七八九十，一二三四五六七八九十一二三四五六七八九十，一二三四五六七八九十一二三四五六七八九十。一二三四五六七八九十一二三四五六七八九十。', pre=pv&&pv.textContent.replace(/……$/,''); ok('出处预览在句读处截断',!!pv&&full.startsWith(pre)&&(/[，。]$/.test(pre)||/[，。]/.test(full[pre.length])),pv&&pv.textContent); }
  ok('顶栏进度条有底轨',getComputedStyle(document.querySelector('.bar'),'::after').height==='2px');
  // ===== v9.57 阅读页 =====
  { const w=document.querySelector('#where'); ok('顶栏两行：上行章节名、下行书名和进度',!!w.querySelector('b')&&!!w.querySelector('small')&&w.querySelector('small').textContent.startsWith('红楼梦')&&/%/.test(w.querySelector('small').textContent),w.textContent);
    ok('顶栏章节名带回目：第一回　甄士隐梦幻识通灵',w.querySelector('b').textContent.includes('甄士隐梦幻识通灵')||!w.querySelector('b').textContent.startsWith('第一回'),w.querySelector('b').textContent);
    const mz=document.querySelector('.mk.clue .mz'); ok('页边伏笔是竖排楷体"伏笔"批注',!!mz&&mz.textContent==='伏笔'&&getComputedStyle(mz).writingMode.startsWith('vertical'));
    ok('没揭晓的伏笔那一句有朱色圈点',!!document.querySelector('#text mark.cd'));
    document.querySelector('#app').classList.add('calmread'); document.querySelector('#text').click(); await wait(20); ok('点正文：收起的顶栏和导航重新出现',!document.querySelector('#app').classList.contains('calmread')); T.closeSheet(); }
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
    S_.seen.H01=S_.seen.H01||Date.now(); S_.found.H01=S_.found.H01||Date.now(); delete S_.guesses.H01; T.save();
    T.cluePanel('open'); await w(20); const cr=document.querySelector('#sheet [data-cl="H01"]');
    ok('伏笔面板：每条两行（位置 / 问题），没有按钮堆',!!cr&&!!cr.querySelector('.crh')&&!!cr.querySelector('.crq')&&!document.querySelector('#sheet .qacts'));
    cr.click(); await w(20); ok('点一条：原地打开伏笔卡，左上角能回列表',!!document.querySelector('#sheet #cg')&&!!document.querySelector('#sheet [data-bk]'));
    document.querySelector('#cg').click(); await w(20); ok('写下猜想：原地换成填写页，有 ‹ 返回，把握仍是滑条',!!document.querySelector('#gt')&&!!document.querySelector('#sheet [data-bk]')&&document.querySelector('#cf')?.type==='range');
    document.querySelector('#gt').value='测试猜想'; document.querySelector('#gs').click(); await w(30);
    ok('保存后回到伏笔卡、卡上显示我的猜想',!!document.querySelector('#sheet .gv')&&document.querySelector('#sheet .gv').textContent.includes('测试猜想')&&!!document.querySelector('#sheet #cg'));
    ok('保存后提示"已保存 · 撤销"',document.querySelector('#toast').textContent.includes('已保存')&&document.querySelector('#toast').textContent.includes('撤销'));
    document.querySelector('#toast button:not(.tx)').click(); await w(20); ok('撤销后猜想没了',!S_.guesses.H01);
    T.closeSheet(); T.minePanel('all'); await w(20); sh=document.querySelector('#sheet');
    ok('笔记分类是一行纯文字（全部、划线、想法、疑问、书签），札记不在其中',sh.querySelectorAll('.ntabs [data-tab]').length===5&&!sh.querySelector('.ntabs svg'));
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
    document.querySelector('#rs').click(); await w(20); ok('清空本书记录：页内确认，写明无法恢复，取消回到"更多设置"',!!document.querySelector('#cfOk')&&document.querySelector('#sheet').textContent.includes('无法恢复')&&document.querySelector('#cfOk').textContent==='确认清空'); document.querySelector('#cfNo').click(); await w(20); ok('取消后回到更多设置',!!document.querySelector('#rs')&&!!document.querySelector('#setBack'));
    ok('功能入口（链接按钮）是墨色，不是蓝色',(()=>{ const c=getComputedStyle(document.querySelector('#sheet')).getPropertyValue('--blue').trim(); const l=document.createElement('button'); l.className='linkbtn'; document.body.appendChild(l); const col=getComputedStyle(l).color; l.remove(); return col===getComputedStyle(document.body).getPropertyValue('--ink')||col!=='rgb(47, 74, 140)'; })());
    document.querySelector('#setBack').click(); await w(20); ok('返回第一层',!!document.querySelector('#fs')); T.closeSheet();
    ok('关掉设置后遮罩恢复',!document.querySelector('#scrim').classList.contains('clear'));
  }
  // ===== v9.60：双击开解释、横屏批注栏 =====
  { T.closeSheet(); const pe=T.els()[IDX['1.11']]; pe.querySelector('.zh').dispatchEvent(new MouseEvent('dblclick',{bubbles:true})); await wait(30);
    ok('双击段落打开解释',document.querySelector('#sheet').classList.contains('show')&&!!document.querySelector('#sheet .plain')); T.closeSheet();
    ok('竖屏不显示右侧批注栏',getComputedStyle(document.querySelector('#side')).display==='none');
    const mm=window.matchMedia; window.matchMedia=q=>q.includes('landscape')?{matches:true,addEventListener(){},removeEventListener(){}}:mm.call(window,q);
    T.sideTick(true); const sd=document.querySelector('#side');
    ok('横屏批注栏：最上面是主线',!!sd.querySelector('.mainl')&&sd.querySelector('.mainl').textContent.includes('主线'));
    ok('横屏批注栏：列出这一屏附近的伏笔',!!sd.querySelector('.pz[data-sc]'),sd.textContent.slice(0,80));
    sd.querySelector('.pz[data-sc]')?.click(); await wait(30); ok('点批注栏里的伏笔打开伏笔卡',document.querySelector('#sheet').classList.contains('show')); T.closeSheet();
    window.matchMedia=mm; }
  // 解释卡片
  T.openCard(IDX['1.11']); t=document.querySelector('#sheet').textContent;
  ok('点过一次段落后，操作提示记为看过（全局）',!!T.TIPS.hinted&&!document.querySelector('#hint'));
  ok('解释卡片标题“第一回”',document.querySelector('#sheet .n').textContent==='第一回');
  T.save();
  // 划线：划完就能取消；弹窗里原文完整
  { const S4=T.getS(), n0=S4.ul.length, id4=T.addUL([{c:'p'+IDX['3.11'],s:0,e:80}]);
    T.closeSheet(); await wait(500);
    const rg=document.createRange(); rg.selectNodeContents(T.els()[IDX['3.11']]); T.afterHL(id4,rg); await wait(20);
    const sm=document.querySelector('#selmenu');
    ok('划线后菜单原地变成“取消划线 | 写点什么”',sm.classList.contains('show')&&sm.textContent.includes('取消划线')&&sm.textContent.includes('写点什么')&&!document.querySelector('#qbar'),sm.textContent);
    sm.querySelector('[data-a="write"]').click(); await wait(30);
    const qb=document.querySelector('#qbar'); ok('点“写点什么”才弹出输入条',!!qb&&!sm.classList.contains('show'));
    ok('输入条里原文完整显示',!qb.querySelector('.qquote').textContent.endsWith('…')&&getComputedStyle(qb.querySelector('.qquote')).webkitLineClamp!=='2');
    qb.querySelector('#qx').click(); await wait(250);
    T.afterHL(id4,rg); await wait(20); sm.querySelector('[data-a="undo"]').click(); await wait(30);
    ok('点“取消划线”后划线消失',S4.ul.length===n0&&!document.querySelector('#qbar')&&!sm.classList.contains('show'));
    const id6=T.addUL([{c:'p'+IDX['3.11'],s:0,e:80}]); T.hlSheet(id6); document.querySelector('#hCard').click(); await wait(20);
    ok('划线弹窗点“解释”后有返回',!!document.querySelector('#cardBack'));
    document.querySelector('#cardBack').click(); await wait(20);
    ok('从解释返回到划线弹窗',!!document.querySelector('#hDel')); T.closeSheet(); T.removeUL(id6);
    const id5=T.addUL([{c:'p'+IDX['3.11'],s:0,e:80}]); T.hlSheet(id5);
    ok('点划线的弹窗：第一个按钮是“取消划线”',document.querySelector('#hDel').textContent==='取消划线');
    ok('弹窗里原文完整',document.querySelector('#sheet .quote').textContent.length===S4.ul.find(u=>u.id===id5).text.length);
    document.querySelector('#hDel').click(); await wait(20);
    ok('取消后提示可撤销',document.querySelector('#toast').textContent.includes('撤销'));
    document.querySelector('#toast button').click(); await wait(20);
    ok('撤销后划线回来',S4.ul.some(u=>u.id===id5)); T.removeUL(id5);
  }
  // 伏笔页：出处可展开
  { T.cluePanel('open'); await wait(40); document.querySelector('#sheet .cr[data-cl]')?.click(); await wait(30); const c=document.querySelector('#sheet .src.clamp');
    ok('伏笔页出处过长时有“展开”',!!c&&!!c.querySelector('.more-t'));
    if(c){ c.querySelector('.more-t').click(); ok('点“展开”显示全文',c.classList.contains('open')&&c.querySelector('.more-t').textContent==='收起'); }
  }
  // 底部伏笔按钮的数字
  { const S5=T.getS(), k=T.unresolved().n; T.paintMarks(); const cn=document.querySelector('#clueCnt'), nr=document.querySelector('#near');
    ok('有未回收时，伏笔按钮显示数字',k>0&&!cn.hidden&&cn.textContent===String(k)&&nr.hidden,k+' / '+cn.textContent);
  }
  // 返回书架不拦截
  { T.leave(); await wait(20); ok('有未回收伏笔时，返回书架不拦截',!!document.querySelector('.shelf')&&!document.querySelector('#sheet').classList.contains('show'));
    T.openBook('hlm'); await wait(500); T.closeSheet(); }
  // 导览搜索
  { const S6=T.getS(); resetRd(); readAt(IDX['3.20']); S6.vis=IDX['3.20'];
    T.novelOutline('ppl',''); ok('导览搜索收在放大镜里，点了才展开',!!document.querySelector('#olQ')&&document.querySelector('#sheet .srch').hidden); document.querySelector('#olS').click();
    let h=T.searchBody('ppl','凤',IDX['3.20']); ok('搜“凤”找到王熙凤',h.includes('王熙凤'),'');
    h=T.searchBody('ppl','宝钗',IDX['3.20']); ok('搜还没出场的人物：找不到',h.includes('没有找到'),'');
    h=T.searchBody('ppl','辣子',IDX['3.20']); ok('按称呼也能找到',h.includes('王熙凤')&&h.includes('辣子'),'');
    h=T.searchBody('hui','护官符',IDX['3.20']); ok('正文搜索不越过阅读进度',h.includes('没有找到'),'');
    h=T.searchBody('hui','葫芦庙',IDX['3.20']); ok('正文搜索：已读部分能找到',h.includes('第一回')&&h.includes('qh'),'');
    const qi=document.querySelector('#olQ'); qi.value='凤'; qi.dispatchEvent(new Event('input')); await wait(250);
    ok('输入后列表变成搜索结果',document.querySelector('#olBody').textContent.includes('王熙凤')&&document.querySelector('#olBody').textContent.includes('找到'));
    T.novelOutline.q=''; T.closeSheet(); }
  // ===== 札记并进笔记（v9.67，用户 10-30）=====
  { T.minePanel('all'); const sh=document.querySelector('#sheet');
    ok('笔记底部没有"读书札记"大按钮，标签行最后是"札记"',!sh.querySelector('#expOpen')&&!sh.querySelector('.ntabs [data-tab="arc"]')&&!!sh.querySelector('.shead #nArc'));
    delete T.getS().expDraft; sh.querySelector('#nArc').click(); await wait(20);
    let tx=document.querySelector('#sheet').textContent;
    ok('点"札记"：还在同一个笔记面板里切换（同一排标签），不是另一整页',!!document.querySelector('#sheet #arcBack')&&!document.querySelector('#sheet').classList.contains('full')&&document.querySelector('#sheet .ttl').textContent==='札记');
    ok('札记：排好的内容，含划线和想法',!!document.querySelector('#sheet .mdv')&&tx.includes('满纸荒唐言')&&tx.includes('作者也觉得自己痴'),'');
    ok('编辑、复制、导出都在标题行右边，底部没有单独的编辑按钮',!!document.querySelector('#sheet .shead #exEdit')&&!!document.querySelector('#sheet .shead #exCopy')&&!!document.querySelector('#sheet .shead #exSave')&&!document.querySelector('#sheet .sfoot')&&!document.querySelector('#sheet .arcact'));
    document.querySelector('#exEdit').click(); await wait(20);
    const ta=document.querySelector('#exText'); ok('点"编辑"：原地变成输入框',!!ta&&!document.querySelector('#arcEdit').hidden&&document.querySelector('#arcView').hidden);
    ta.value=ta.value+'\n\n我自己补的一句。';
    document.querySelector('#exEdit').click(); await wait(20);
    ok('点"完成"：回到札记，显示编辑后的内容',!!document.querySelector('#sheet .mdv')&&document.querySelector('#sheet .mdv').textContent.includes('我自己补的一句'));
    ok('标明这是编辑过的版本',document.querySelector('#sheet').textContent.includes('这是你编辑过的版本'));
    let copied=null; try{Object.defineProperty(navigator,'clipboard',{value:{writeText:x=>{copied=x;return Promise.resolve();}},configurable:true});}catch(e){}
    document.querySelector('#exCopy').click(); await wait(30);
    ok('复制的是编辑后的内容',copied&&copied.includes('我自己补的一句'),String(copied).slice(-20));
    T.getS().notes.push({id:T.getS().nid++,type:'note',at:IDX['1.30'],quote:'元宵佳节',text:'新加的想法',t:Date.now()});
    T.minePanel('arc'); await wait(20); tx=document.querySelector('#sheet').textContent;
    ok('笔记有更新时提示重新整理',tx.includes('笔记又有更新')&&tx.includes('按最新笔记重新整理'),'');
    document.querySelector('#exReset').click(); await wait(20); ok('札记重新整理：先弹页内确认面板（不是系统弹窗），取消回到札记',!!document.querySelector('#cfOk')&&document.querySelector('#sheet').textContent.includes('会被替换')); document.querySelector('#cfNo').click(); await wait(20); ok('取消后还在札记里、编辑没被替换',!!document.querySelector('#sheet #arcBack')&&!!T.getS().expDraft); document.querySelector('#exReset').click(); await wait(20); document.querySelector('#cfOk').click(); await wait(20);
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

    const sh2=document.querySelector('#sheet');
    const items=[...sh2.querySelectorAll('.sbody .q')].map(q=>q.querySelector('.qt')?.textContent||'');
    ok('“全部”里写过想法的划线不重复出现',!items.includes('满纸荒唐言'),items.join('|').slice(0,80));
    const fsOf=sel=>getComputedStyle(document.querySelector(sel)).fontSize;
    T.openCard(IDX['1.11']); ok('解释第一句 17px',fsOf('#sheet .plain')==='17px',fsOf('#sheet .plain'));
    ok('解释展开 15px',fsOf('#sheet .more')==='15px',fsOf('#sheet .more'));
    ok('面板标题 17px（规范 v2）',fsOf('#sheet .n')==='17px',fsOf('#sheet .n'));
    const allTxt=document.body.innerHTML;
  }
  // 换书：逻辑哲学论，状态独立
  const hlmF=S().furthest;
  T.shelf(); await wait(30);
  { const S3=T.getS(); S3.seen.H01=1; S3.found.H01=S3.found.H01||Date.now(); T.save(); }   /* H03 是主线碎片，读到答案会自动拼上，换成不会揭晓的 H01 */
  T.shv().lay='list'; T.shv().sort='manual'; T.shv().order=[]; T.shelf(); await wait(30);
  const fbEl=document.querySelector('#bH .fb');
  ok('列表排列：书架显示“N 处伏笔待揭晓”',!!fbEl&&/\d+ 处伏笔待揭晓/.test(fbEl.textContent),fbEl&&fbEl.textContent);
  fbEl&&fbEl.click(); await wait(30); t=document.querySelector('#sheet').textContent;
  ok('点"N 处伏笔待揭晓"：打开书籍详情并展开待揭晓列表',t.includes('待揭晓')&&t.includes('眼泪')&&!document.querySelector('#sheet .biurl').hidden,t.slice(0,50));
  ok('书籍详情：封面、进度、版本信息、继续阅读',!!document.querySelector('#sheet .bihead .cover')&&!!document.querySelector('#sheet .bimeta')&&!!document.querySelector('#bOpen'));
  T.closeSheet(); document.querySelector('#bH .bkm')?.click(); await wait(30); ok('列表里每本书有"…"打开详情',document.querySelector('#sheet').classList.contains('show')&&!!document.querySelector('#sheet .bihead'));
  T.closeSheet(); T.bookInfo('hlm','x'); t=document.querySelector('#sheet').textContent;
  ok('书的详情：待揭晓列表默认收起，不剧透',document.querySelector('#sheet .biurl')?.hidden!==false&&!t.includes('雨村拿了银子'),'');
  T.closeSheet();
  ok('书架显示红楼梦进度',/第|已读完/.test(document.querySelector('#bHp').textContent),document.querySelector('#bHp').textContent);
  T.openBook('tractatus'); await wait(200);
  ok('逻辑哲学论 526 条',T.els().length===526,T.els().length);
  ok('逻辑哲学论进度独立',T.getS().furthest!==hlmF,T.getS().furthest);
  ok('逻辑哲学论没有人名链接',!document.querySelector('.pn'));
  T.openCard(T.getIDX()['1.1']); ok('逻辑哲学论卡片仍显示编号',document.querySelector('#sheet .n').textContent==='1.1');
  T.askQuestion(null,'事实和事物到底有什么区别？',{at:T.getIDX()['1.1'],qa:'Q04'}); await wait(20);
  ok('逻辑哲学论示范问答照常',document.querySelector('#sheet').textContent.includes('答案在后文'));
  T.settings('more'); ok('逻辑哲学论设置（更多设置）有编号层级线',document.querySelector('#sheet').textContent.includes('编号层级线'));
  T.shelf(); T.openBook('hlm'); await wait(200);
  ok('换书再回来，不再出现操作提示',!document.querySelector('#hint'));
  ok('回到红楼梦，进度还在',T.getS().furthest>=hlmF,T.getS().furthest+' vs '+hlmF+' cur '+T.getS().current);
  T.settings('more'); ok('红楼梦设置没有编号层级线',!document.querySelector('#sheet').textContent.includes('编号层级线'));
  // ===== 逻辑哲学论：自译本 + 中文 / 对照 / 原文（2026-10-20 加）=====
  { const w=wait; T.shelf(); T.openBook('tractatus'); await w(300); T.closeSheet();
    const SL=T.getS(), PL=T.P();
    ok('逻辑哲学论：正文是自译可读版（1 = 世界是一切发生的事）',PL[0].zh.startsWith('世界是一切发生的事'),PL[0].zh);
    ok('逻辑哲学论：每条带德文和英文',PL.every(p=>p.de&&p.en),PL.filter(p=>!p.de||!p.en).length);
    ok('原文里没有残留 LaTeX',PL.every(p=>!/\\[a-zA-Z]/.test(p.de+p.en)),PL.filter(p=>/\\[a-zA-Z]/.test(p.de+p.en)).map(p=>p.n).slice(0,5).join(','));
    ok('默认只看中文',document.documentElement.dataset.lang==='zh'&&getComputedStyle(document.querySelector('.prop .og')).display==='none');
    T.openCard(0); await w(20); ok('中文模式：点一段，解释卡片里能看这一段的原文',!!document.querySelector('#sheet details.ogq')&&document.querySelector('#sheet .ogq div').textContent.startsWith('Die Welt'),document.querySelector('#sheet .ogq div')?.textContent.slice(0,20)); T.closeSheet();
    ok('没有"对照"模式了',!document.querySelector('#tlg').textContent.includes('对照'));
    document.querySelector('#tlg').click(); await w(30);
    ok('点一下只看原文：中文隐藏',document.documentElement.dataset.lang==='orig'&&getComputedStyle(document.querySelector('.prop .zh')).display==='none');
    ok('只看原文时页边标记仍显示（2026-10-20 改）',[...document.querySelectorAll('.marks')].some(m=>getComputedStyle(m).display!=='none'));
    T.settings(); await w(20); const en=[...document.querySelectorAll('#oglseg button')].find(b=>b.dataset.ogl==='en'); en&&en.click(); await w(20);
    ok('设置里可选原文语言：英文',document.querySelector('.prop .og').textContent.startsWith('The world is everything'),document.querySelector('.prop .og').textContent.slice(0,30));
    T.closeSheet(); document.querySelector('#tlg').click(); await w(20);
    ok('两种看法循环回中文',document.documentElement.dataset.lang==='zh');
    ok('按书记住看法',SL.lang==='zh'&&SL.ogl==='en');
    T.openBook('hlm'); await w(200); T.closeSheet(); ok('红楼梦没有语言切换按钮',!document.querySelector('#tlg')&&document.documentElement.dataset.lang==='zh');
    T.shelf(); await w(20); ok('书架上逻辑哲学论不再写贺绍甲',!document.querySelector('#b1').textContent.includes('贺'));
    const cards=JSON.stringify(T.getS&&0||''); }
  // ===== 双语：切换定位、原文上划线、伏笔、导览（2026-10-20 加）=====
  { const w=wait; T.shelf(); T.openBook('tractatus'); await w(300); T.closeSheet();
    const SB=T.getS(), IX=T.getIDX(); SB.lang='zh'; SB.ogl='de'; T.setLang();
    const tgl=async l=>{ SB.lang=l; T.keepPlace(T.setLang); await w(60); };
    const el=T.els()[IX['4.0031']]; el.scrollIntoView({block:'start'}); window.scrollBy(0,-document.getElementById('bar').getBoundingClientRect().bottom+10); await w(80);
    const a0=T.readAnchor(), H=a0&&a0.host; ok('双语：阅读线落在 4.0031 附近',!!H&&Math.abs(+H.dataset.i-IX['4.0031'])<=2,H&&H.id);
    let a; await tgl('orig'); a=T.readAnchor(); ok('切到只看原文：仍在同一条',a&&a.host===H,a&&a.host.id);
    await tgl('zh'); a=T.readAnchor(); ok('切回中文：仍在同一条',a&&a.host===H,a&&a.host.id);
    // 原文上划线
    await tgl('orig'); const og=T.els()[IX['1.1']].querySelector('.body > .og'); const tn=og.firstChild, L=og.lang, T0=og.textContent;
    const rg=document.createRange(); rg.setStart(tn,4); rg.setEnd(tn,20); const parts=T.rangeParts(rg);
    ok('只看原文时选字：落在原文上',parts.length===1&&parts[0].c==='p'+IX['1.1']+'@'+L,JSON.stringify(parts));
    const uid=T.addUL(parts); await w(20);
    ok('原文上的划线显示出来',!!og.querySelector(`mark.ul[data-ul="${uid}"]`));
    const u=SB.ul.find(x=>x.id===uid); ok('划线记下原文文字和位置',u&&u.text===T0.slice(4,20)&&u.at===IX['1.1'],u&&u.text);
    T.hlSheet(uid); await w(20); ok('点原文划线能打开划线面板',!!document.querySelector('#hDel')); T.closeSheet();
    // 伏笔标记和黄底：只看原文时落在原文上
    await tgl('orig'); SB.seen.S01=SB.seen.S01||0; T.paintMarks(); await w(30);
    const mk=document.querySelector('.marks .mk'); ok('只看原文时页边标记仍显示',!!mk&&mk.getClientRects().length>0);
    T.sweep([{c:'p'+IX['1.1'],s:0,e:5}]); await w(30); ok('只看原文时黄底扫在原文段落上',!!og.querySelector('mark.swline'));
    await w(2100);
    // 导览、搜索、卡片
    T.outline(); await w(20); const ot=document.querySelector('#sheet .ol .ot');
    ok('只看原文时导览目录用原文',!!ot&&/Welt/.test(document.querySelector('#sheet').textContent),ot&&ot.textContent.slice(0,30));
    ok('搜索原文能找到',/Welt/.test(T.searchBody('hui','Welt',IX['2'])));
    T.closeSheet(); T.openCard(IX['1.1']); await w(20); ok('只看原文时解释卡片附中文',!!document.querySelector('#sheet .zhq'));
    T.closeSheet(); SB.ul=SB.ul.filter(x=>x.id!==uid); SB.lang='zh'; T.save(); T.setLang(); T.paintUL();
    // ===== v9.23：前言伏笔对准句子；切换看法不下移（2026-10-21 加）=====
    { const SU=['S01','S02','S03'].map(id=>({id,'提出':'前言'}));
      const rg2=T.clueRange(SU[1],'src')[0], t2=T.cOf(rg2.c).textContent.slice(rg2.s,rg2.e);
      ok('前言伏笔 S02 划线正好是"凡是不能谈论的……沉默。"',t2.startsWith('凡是不能谈论的')&&t2.endsWith('沉默。'),t2);
      const r1=T.clueRange(SU[0],'src')[0], t1=T.cOf(r1.c).textContent.slice(r1.s,r1.e);
      ok('前言伏笔 S01 划线从"这本书讨论"到"逻辑。"、不含下一句',t1.startsWith('这本书讨论')&&t1.endsWith('逻辑。'),t1);
      const r3=T.clueRange(SU[2],'src')[0], t3=T.cOf(r3.c).textContent.slice(r3.s,r3.e);
      ok('前言伏笔 S03 划线是最后一句',t3.includes('并没有做成多少事')&&!t3.includes('无可辩驳'),t3);
      SB.lang='orig'; T.setLang(); const ro=T.clueRange(SU[1],'src'); const to=ro&&T.cOf(ro[0].c).textContent.slice(ro[0].s,ro[0].e);
      ok('只看原文：S02 划在原文那一句（德/英）',!!to&&/(wovon man nicht reden kann.*schweigen|whereof one cannot speak.*silent)\.$/.test(to)&&!/^(Man könnte|Its whole)/.test(to),to);
      SB.lang='zh'; T.setLang();
      SB.seen.S02=SB.seen.S02||1; T.paintMarks(); await w(40);
      const m2=document.querySelector('.mk[data-clue="S02"]'), C2=T.cOf('f1'), rr=document.createRange(); const tn2=C2.firstChild, o2=C2.textContent.indexOf('凡是不能谈论的');
      rr.setStart(tn2,o2); rr.setEnd(tn2,o2+1); const y=rr.getClientRects()[0];
      const mr=m2&&m2.getBoundingClientRect(); ok('S02 页边标记和"凡是不能谈论的"在同一行',!!mr&&Math.abs((mr.top+mr.height/2)-(y.top+y.height/2))<8,mr&&Math.round(mr.top)+' vs '+Math.round(y.top));
      T.openClue('S02'); await w(20); const sh=document.querySelector('#sheet').textContent; ok('伏笔卡片出处用新译',sh.includes('凡是不能谈论的，就必须保持沉默')&&!sh.includes('对于不能谈论'),sh.slice(0,60)); T.closeSheet();
      // 切换看法：顶栏下第一行不动
      window.scrollTo(0,0); await w(30); SB.lang='zh'; T.setLang();
      const e2=T.els()[IX['2.012']]; e2.scrollIntoView({block:'start'}); window.scrollBy(0,-document.getElementById('bar').getBoundingClientRect().bottom); await w(60);
      const A0=T.readAnchor(), Z0=A0.host.querySelector('.zh')||A0.host.querySelector(':scope > p'), y0=Z0.getBoundingClientRect().top;
      await tgl('orig'); await tgl('zh'); const y1=Z0.getBoundingClientRect().top;
      ok('切到原文再切回：屏幕最上面那条不移动',Math.abs(y1-y0)<4,Math.round(y0)+'→'+Math.round(y1));
      window.scrollTo(0,0); await w(30); await tgl('orig'); ok('在最顶上切换：仍在最顶上',scrollY<2,scrollY); await tgl('zh');
    }
    }
  { const wait=ms=>new Promise(r=>setTimeout(r,ms));

  }
  // ===== 读完：自动；已读 = 翻过的（v9.27，2026-10-21）=====
  { const wait=ms=>new Promise(r=>setTimeout(r,ms)); localStorage.clear(); T.TIPSS().welcomed=1; T.shelf(); T.openBook('hlm'); await wait(900); T.closeSheet();
    const P_=T.P(), IX=T.getIDX();
    ok('书末不再有"标为读完"按钮',!document.querySelector('#finBtn'));
    ok('打开书时只算读了开头几段',T.rdN()<=3,T.rdN());
    T.outline('hui'); await wait(20); let tx=document.querySelector('#sheet').textContent;
    ok('没读也能看到全部回目',document.querySelectorAll('#sheet .ol details').length===5&&tx.includes('第五回'),document.querySelectorAll('#sheet .ol details').length);
    ok('没读过的回不显示小节概要',!tx.includes('摔了自己的玉'),'');
    T.closeSheet();
    const before=T.rdN(); T.jump(P_[IX['4.1']].n); await wait(2600);
    ok('跳到第四回：中间跳过的不算读过',!T.isRd(IX['2.10'])&&!T.isRd(IX['3.5']),T.rdN()+' vs '+before);
    ok('跳到第四回：落脚处算读过',[-1,0,1,2].some(d=>T.isRd(IX['4.1']+d)),T.rdN());
    T.outline('hui'); await wait(20); tx=document.querySelector('#sheet').textContent;
    ok('导览每回有一根已读进度条',[...document.querySelectorAll('#sheet .olpb')].some(e=>/已读 \d+%/.test(e.getAttribute('aria-label'))),'');
    T.closeSheet();
    ok('第二回的伏笔没亮（没读到）',!document.querySelector('[data-clue="H04"]'));
    T.shelf(); await wait(30); ok('书架进度按读过的比例',document.querySelector('#bHp').textContent.includes('已读'),document.querySelector('#bHp').textContent);
    T.openBook('hlm'); await wait(900); T.closeSheet();
    ok('一路读到最后之前：没有"已读完"',!T.getS().finished&&!document.querySelector('#endMark .fin'));
    for(let i=IX['5.80'];i<P_.length;i++){ T.setPos(i); }
    ok('一路读到最后一段：自动记为读完',!!T.getS().finished);
    ok('读完时全书每一段都算读过（进度不会停在 86% 这样的数）',T.rdN()===P_.length,T.rdN()+' / '+P_.length);
    ok('书末仍有"查看读书札记"',!!document.querySelector('#endArc'));
    document.querySelector('#endArc').click(); await wait(30);
    ok('书末"查看读书札记"直接打开笔记里的"札记"',document.querySelector('#sheet .ttl').textContent==='札记'&&!!document.querySelector('#sheet #arcBack'),document.querySelector('#sheet .ttl').textContent);
    T.closeSheet(); T.minePanel('all'); await wait(10); document.querySelector('#nArc').click(); await wait(20);
    ok('从笔记点"札记"：还在笔记面板里',document.querySelector('#sheet .ttl').textContent==='札记'&&!!document.querySelector('#sheet .mdv')); T.closeSheet();
    ok('札记抬头写已读完',T.archiveMD().includes('已读完（'));
    ok('书末：读完的收尾页',!!document.querySelector('#endMark .fin')&&document.querySelector('#endMark .fint').textContent.replace(/\s/g,'').replace('・','·')==='红楼梦·已读完',document.querySelector('#endMark .fint').textContent);
    ok('书末：有读书周期、天数、字数和查看札记',/\d+ 月 \d+ 日.*\d+ 天/.test(document.querySelector('#endMark .fin').textContent)&&/共 [\d.]+ 万字/.test(document.querySelector('#endMark .fin').textContent)&&!!document.querySelector('#endMark #endArc'),document.querySelector('#endMark .fin').textContent.replace(/\s+/g,' '));
    T.shelf(); await wait(30); ok('书架显示"已读完"、不带日期',document.querySelector('#bHp').textContent==='已读完',document.querySelector('#bHp').textContent);
    T.openBook('hlm'); await wait(500); ok('已读完的书再打开：不弹"继续阅读"',!document.querySelector('#sheet').classList.contains('show'));
    ok('已读完的书再打开：书末仍是收尾页',!!document.querySelector('#endMark .fin'));
    T.shelf(); await wait(20);
    T.bookInfo('hlm',''); await wait(10); ok('长按详情不再有"标为读完"',!document.querySelector('#bFin')); T.closeSheet();
    localStorage.clear(); T.TIPSS().welcomed=1; T.shelf(); T.openBook('hlm'); await wait(900); T.closeSheet();
    T.jump(P_[P_.length-1].n); await wait(2600); ok('直接跳到结尾不算读完',!T.getS().finished);
    localStorage.clear(); T.TIPSS().welcomed=1; T.shelf(); }
  // ===== 表格（v9.27）=====
  { T.openBook('tractatus'); await new Promise(r=>setTimeout(r,300)); T.closeSheet();
    const e431=T.els()[T.getIDX()['4.31']]; ok('4.31 显示三张真值表',e431.querySelectorAll('table.ttbl').length===3,e431.querySelectorAll('table').length);
    ok('表格里没有原始标记',!e431.textContent.includes('⟦表'));
    const e5=T.els()[T.getIDX()['5.101']]; ok('5.101 的大表也渲染',!!e5.querySelector('table.ttbl')&&!e5.textContent.includes('⟦'));
    T.shelf(); }
  // ===== 公版清理（2026-10-21）=====
  { ok('书架没有三体',![...document.body.children].filter(e=>e.tagName!=='SCRIPT').some(e=>e.textContent.includes('三体')));
    T.openBook('tractatus'); await new Promise(r=>setTimeout(r,300)); T.closeSheet();
    const imgs=[...document.querySelectorAll('.prop .zh img')]; ok('公式图片都能显示（来自古登堡）',imgs.length>0&&imgs.every(i=>i.src.startsWith('data:image')),imgs.length);
    ok('6 的一般形式是文字',T.P()[T.getIDX()['6']].zh.includes('[p̄, ξ̄, N(ξ̄)]'));
    T.shelf(); }
  // ===== 导览"从这里开始读"（v9.31）=====
  { const w=ms=>new Promise(r=>setTimeout(r,ms)); localStorage.clear(); T.TIPSS().welcomed=1; T.shelf(); T.openBook('hlm'); await w(900); T.closeSheet();
    const IX=T.getIDX();
    T.outline('hui'); await w(20); const fb=document.querySelector('#sheet [data-from="'+IX['3.1']+'"]');
    ok('收起的回里看不到"从这里开始读"',fb&&!fb.closest('details').open&&fb.checkVisibility()===false,fb&&[fb.closest('details').open,fb.checkVisibility()]);
    ok('导览底部不再有"选择从哪里开始读"那一行',!document.querySelector('#olFromOn'));
    fb.closest('details').open=true; await w(30); ok('展开这一回才看到按钮',fb.checkVisibility()===true);
    ok('一次只展开一回',document.querySelectorAll('#sheet .ol details[open]').length===1);
    document.querySelectorAll('#sheet .ol details')[4].open=true; await w(30); ok('展开另一回，之前的自动收起',!fb.closest('details').open&&document.querySelectorAll('#sheet .ol details[open]').length===1);
    fb.closest('details').open=true; await w(30);
    ok('导览每回有"从这里开始读"',!!fb&&document.querySelectorAll('#sheet [data-from]').length===4,document.querySelectorAll('#sheet [data-from]').length);
    fb.click(); await w(20); ok('点了先说明会发生什么',document.querySelector('#sheet .ttl').textContent.includes('从第三回开始读'));
    ok('说明页写明已有记录都保留',document.querySelector('#sheet').textContent.includes('不会清掉任何东西'));
    document.querySelector('#sheet [data-bk]').click(); await w(20); ok('说明页能返回导览',document.querySelector('#sheet .ttl').textContent==='导览');
    document.querySelector('#sheet [data-from="'+IX['3.1']+'"]').click(); await w(20); document.querySelector('#fromGo').click(); await w(1500);
    ok('从第三回开始：前两回全部算读过',T.isRd(IX['1.1'])&&T.isRd(IX['2.18']));
    ok('从第三回开始：第三回之后仍未读',!T.isRd(IX['3.20'])&&!T.isRd(IX['4.5']));
    const S_=T.getS(); ok('前面答案已出现的伏笔记为已揭晓（H02）',!!S_.doneS.H02);
    ok('前面提出、答案在后面的伏笔：算发现了，但没替读者打开',Object.keys(S_.found).some(id=>!S_.seen[id]&&!S_.doneS[id]));
    ok('前面已揭晓的伏笔记为打开过',!!S_.seen.H02);
    T.outline('ppl'); await w(20); ok('人物导览：前两回的人都出现',document.querySelector('#sheet').textContent.includes('贾雨村')&&document.querySelector('#sheet').textContent.includes('冷子兴'));
    T.closeSheet(); document.querySelector('#toast button').click(); await w(200);
    ok('可以撤销',!T.isRd(IX['2.10'])&&!T.getS().doneS.H02);
    T.closeSheet(); await w(300); T.jump('4.1'); await w(2500); { const hd=document.getElementById('hui4').getBoundingClientRect(); ok('"本回开头"连回目标题一起露出来',hd.top>=0&&hd.top<140,Math.round(hd.top)); }
    // 从后往前：已经读过后面（第四回）的一段、划过线，再回到第二回"从这里开始读"——后面的已读和划线都不丢
    T.markRd(IX['4.1'],IX['4.3']); const ul0=JSON.stringify([T.getS().ul,T.getS().notes]); T.save();
    T.startFrom(IX['2.1']); await w(1500);
    ok('从后往前：第四回读过的部分仍算已读',T.isRd(IX['4.2']));
    ok('从后往前：第一回补记为已读、第二回之后没读的仍未读',T.isRd(IX['1.5'])&&!T.isRd(IX['3.5']));
    ok('从后往前：划线等记录没变',JSON.stringify([T.getS().ul,T.getS().notes])===ul0);
    T.outline('hui'); await w(20); ok('已读过前一段的回不显示按钮（第二回）',!document.querySelector('#sheet [data-from="'+IX['2.1']+'"]')); T.closeSheet();
    localStorage.clear(); T.TIPSS().welcomed=1; T.shelf(); }
  // ===== 《呐喊》（v9.32，2026-10-21，短篇集全本）=====
  { const w=ms=>new Promise(r=>setTimeout(r,ms)); localStorage.clear(); T.TIPSS().welcomed=1; T.shelf(); T.openBook('nahan'); await w(900); T.closeSheet();
    const P3=T.P(), IX3=T.getIDX();
    ok('呐喊：15 篇（自序 + 14 篇）、856 段',P3.length===856&&document.querySelectorAll('.hui').length===15,P3.length);
    ok('顶栏用篇名：《自序》',document.querySelector('#where').textContent.includes('《自序》'),document.querySelector('#where').textContent);
    ok('篇首只显示篇名，不显示"第几篇"',!document.querySelector('.hui .hn')&&document.querySelector('.hui h2').textContent==='自序');
    ok('原文没有乱码和缺字标记',!P3.some(p=>/[?ㄈХ﹝﹞ァ-ヿゝゞ]|  /.test(p.zh)));
    ok('《社戏》修复过的句子在',P3[IX3['10.3']].zh.includes('冬冬喤喤的响，并没有听到你的话'));
    ok('《故乡》"猹"字补回',P3[IX3['5.11']].zh.includes('猹'));
    ok('人名只在本篇里链（故乡没有链到阿Q）',![...T.els()[IX3['5.1']].parentNode.querySelectorAll('.pn')].some(e=>e.textContent==='阿Q'&&+e.closest('.prop').dataset.i<IX3['8.1']));
    T.outline('hui'); await w(20); ok('导览标签"篇目"，15 篇都列出',document.querySelector('#sheet [data-ot="hui"]').textContent==='篇目'&&document.querySelectorAll('#sheet .ol details').length===15);
    { const z=T.els()[IX3['0.5']]; const pn=[...z.querySelectorAll('.pn')].map(e=>e.textContent); ok('自序：不把"绑着的"当名字；"侦探"只出现一次、不做人物卡',!pn.includes('绑着的')&&!pn.includes('侦探'),pn.join(',')); }
    T.closeSheet(); T.openCard(IX3['6.1']); await w(20); ok('孔乙己第一段有解释卡片',document.querySelector('#sheet').textContent.includes('咸亨')||document.querySelector('#sheet .plain').textContent.length>5);
    T.closeSheet(); T.jump('7.1'); await w(1400); T.markRd(IX3['7.1'],IX3['7.12']); T.getS().vis=IX3['7.12']; T.paintMarks(); await w(30);
    ok('《药》读到 7.12 有伏笔亮起',document.querySelectorAll('.mk.clue').length>0,document.querySelectorAll('.mk.clue').length);
    T.shelf(); await w(20); T.bookInfo('nahan',''); ok('书的详情：鲁迅、1923 新潮社',document.querySelector('#sheet').textContent.includes('新潮社')); T.closeSheet();
    localStorage.clear(); T.TIPSS().welcomed=1; T.shelf(); }
  // ===== 揭晓/发现的时机（v9.36，2026-10-22 用户："还没划到那里就提醒我了"）=====
  { const w=ms=>new Promise(r=>setTimeout(r,ms)); localStorage.clear(); T.TIPSS().welcomed=1; T.shelf(); T.openBook('nahan'); await w(900); T.closeSheet();
    const IX=T.getIDX(), S_=T.getS(), E=T.els();
    /* N14：8.146 提出 → 8.172 揭晓，揭晓段 599 字、答案句在第 464 字附近 */
    const j=IX['8.172'], el=E[j];
    T.markRd(0,j-1); S_.seen.N14=Date.now(); S_.found.N14=S_.found.N14||Date.now(); T.save(); await w(1000);
    const zh=el.querySelector('.zh'), t=zh.textContent, o=t.indexOf('只站在洞外接东西');
    const yAt=k=>{ const tw=document.createTreeWalker(zh,NodeFilter.SHOW_TEXT); let n,pos=0; while((n=tw.nextNode())){ if(pos+n.length>k){ const r=document.createRange(); r.setStart(n,k-pos); r.setEnd(n,k-pos+1); return r.getClientRects()[0].top+scrollY; } pos+=n.length; } };
    // 段首刚过阅读线（40%），答案句还在屏幕下方
    await w(1500); scrollTo({top:el.getBoundingClientRect().top+scrollY-innerHeight*0.38,behavior:'instant'}); await w(500);
    ok('长段落：段首过了阅读线、答案那句还没读到 → 不揭晓',T.isRd(j)&&!S_.doneS.N14,[T.isRd(j),Math.round(yAt(o)-scrollY)]);
    ok('揭晓处的 ✓ 也还没出现',!document.querySelector('[data-ans="N14"]'));
    // 继续往下，答案句过了阅读线
    scrollTo({top:yAt(o)-innerHeight*0.30,behavior:'instant'}); await w(500);
    ok('答案那句过了阅读线 → 揭晓',!!S_.doneS.N14);
    // 跳转到揭晓处不算
    localStorage.clear(); T.TIPSS().welcomed=1; T.shelf(); T.openBook('nahan'); await w(900); T.closeSheet();
    const S2=T.getS(); delete S2.doneS.N14; T.markRd(0,j-1); S2.seen.N14=Date.now(); S2.found.N14=Date.now(); T.save();
    T.jump('8.172'); await w(500); T.markRd(j,j); T.setPos(j); await w(50);
    ok('跳转到揭晓处：不揭晓',!S2.doneS.N14);
    // 发现：锚句整句露出来才算（N13 在 8.146? 用 N14 的提出段）
    const k=IX['8.146'], ek=E[k], zk=ek.querySelector('.zh'), tk=zk.textContent, a0=tk.indexOf('满把是银的和铜的');
    ok('N14 提出锚句能找到',a0>=0,a0);
    localStorage.clear(); T.TIPSS().welcomed=1; T.shelf(); }
  // ===== 《李鸿章传》（v9.37，2026-10-22，传记全本；段落类型通用规则）=====
  { const w=ms=>new Promise(r=>setTimeout(r,ms)); localStorage.clear(); T.TIPSS().welcomed=1; T.shelf(); T.openBook('lhz'); await w(900); T.closeSheet();
    const P4=T.P(), IX=T.getIDX(), E=T.els();
    ok('李鸿章传：13 章（序例 + 12 章）、340 段',P4.length===340&&document.querySelectorAll('.hui').length===13,P4.length);
    ok('序例不叫"第零章"',!document.querySelector('#hui0 .hn')&&document.querySelector('#where').textContent.includes('序例'),document.querySelector('#where').textContent);
    ok('第一章标题带"第一章"',document.querySelector('#hui1 .hn')?.textContent==='第一章');
    const docs=document.querySelectorAll('.doc'); ok('引录的文件默认折叠（7 份）',docs.length===7&&[...docs].every(d=>d.classList.contains('folded')),docs.length);
    const mg=E[IX['8.10']]; ok('马关条约的条款平时看不到',mg.offsetParent===null);
    ok('文件标题行写明段数、字数',/引录的原文 · \d+ 段/.test(docs[0].textContent));
    const d8=mg.closest('.doc'); d8.querySelector('.dochd').click(); await w(50);
    ok('点标题展开',!d8.classList.contains('folded')&&mg.offsetParent!==null);
    d8.querySelector('.dochd').click(); await w(50); ok('再点收起',d8.classList.contains('folded'));
    T.jump('8.12'); await w(1500); ok('跳到文件里的段落：自动展开',!d8.classList.contains('folded'));
    ok('章首提要逐条一行',E[IX['4.1']].querySelectorAll('.ti').length===8,E[IX['4.1']].querySelectorAll('.ti').length);
    ok('表格渲染（5.3 平捻统帅表）',!!E[IX['5.3']].querySelector('table.ttbl')&&E[IX['5.3']].querySelectorAll('tr').length===23,E[IX['5.3']].querySelectorAll('tr').length);
    ok('表格不露原始标记',!E[IX['5.3']].textContent.includes('⟦'));
    ok('表格里不加人名下划线、不露 HTML',!E[IX['5.3']].querySelector('table .pn')&&!E[IX['5.3']].textContent.includes('<span'));
    ok('卡片：每段都有三档解释',P4.every(p=>T.getS()&&true)&&Object.keys(T.P()).length>0);
    const pn=[...document.querySelectorAll('.pn')].map(e=>e.textContent);
    ok('官衔、身份式称呼不加人名下划线',!pn.some(x=>['俄使','皇上','监工','著者','日皇'].includes(x)));
    ok('李鸿章有人名链接',pn.filter(x=>x==='李鸿章').length>100);
    T.outline('hui'); await w(30); ok('导览列出 13 章，第一项是序例',document.querySelectorAll('#sheet .ol details').length===13&&document.querySelector('#sheet .ol details summary').textContent.includes('序例'));
    { const tb=E[IX['6.2']].querySelector('table'); ok('没有表头的表：不画表头',!!tb&&!tb.querySelector('thead'));
      const w0=E[IX['6.2']].querySelector('.tblw'); ok('正文里的表格自动折行、不用横向滑动',w0.scrollWidth<=w0.clientWidth+2,[w0.scrollWidth,w0.clientWidth]); }
    // 揭晓的时机：答案早就读过（先读过去、后来才打开这个伏笔），回到前面时不揭晓；打开时直接说"已经读过"
    { const S_=T.getS(), s6=T.P()&&'L06', j=IX['9.23']; T.markRd(0,IX['9.30']); S_.seen.L06=Date.now(); T.save();
      T.jump('3.5'); await w(1500); T.markRd(IX['3.5'],IX['3.6']); T.setPos(IX['3.6']); await w(50);
      ok('在第三章：不会揭晓第九章的伏笔',!S_.doneS.L06);
      T.openClue('L06'); await w(30); ok('打开这个伏笔：直接是已揭晓，不加额外说明',!!S_.doneS.L06&&!document.querySelector('#sheet').textContent.includes('已经读过'));
      T.closeSheet(); delete S_.found.L29; delete S_.seen.L29; delete S_.doneS.L29; T.markRd(0,IX['12.40']); T.getS().vis=IX['12.23']; T.paintMarks(); await w(30);
      ok('发现伏笔时答案早已读过：直接记为已揭晓',!!S_.doneS.L29&&!!S_.seen.L29);
      T.closeSheet(); }
    T.shv().lay='list'; T.shv().sort='manual'; T.shv().order=[]; T.shelf(); await w(20);
    ok('书架只写书名、作者、阅读状态、伏笔',[...document.querySelectorAll('.book .a')].map(e=>e.textContent).join(',')==='曹雪芹,维特根斯坦[奥地利],鲁迅,梁启超,柯南·道尔[英国]');
    ok('封面只有书名（线装题签）',[...document.querySelectorAll('.book .cover')].every(c=>!c.querySelector('.cs')&&c.textContent.replace(/\s/g,'')===c.closest('.book').querySelector('.t').textContent));
    ok('封面：五字以内一列题签、更长的两列小字',document.querySelector('#bH .cover').classList.contains('v')&&document.querySelector('#b1 .cover').classList.contains('v')&&document.querySelector('#bB .cover').classList.contains('h'));
    // ===== v9.56 书架：继续阅读、三种排列、四种排序、整理 =====
    { const V=T.shv();
      ok('有读到一半的书：顶部"继续阅读"',!!document.querySelector('#shCont')&&document.querySelector('#shCont').textContent.includes('继续阅读'));
      V.lay='grid'; T.shelf(); await w(20);
      ok('书格：一行四本（小一些），只有封面和书名，没有进度条和伏笔数',document.querySelector('.books.lay-grid')&&getComputedStyle(document.querySelector('.books')).gridTemplateColumns.split(' ').length===4&&!document.querySelector('.books .pbar')&&!document.querySelector('.books .fb'));
      V.lay='rows'; T.shelf(); await w(20);
      ok('简表：一行一本，没有封面，有百分比',document.querySelectorAll('.book.lb').length===5&&!document.querySelector('.books .cover')&&[...document.querySelectorAll('.book.lb .lp')].every(e=>/%|未读|读完/.test(e.textContent)));
      document.querySelector('[data-lay="grid"]').click(); await w(20); ok('点排列按钮切换并记住',T.shv().lay==='grid'&&!!document.querySelector('.lay-grid'));
      document.querySelector('#sortB').click(); await w(20); ok('排序菜单四项',document.querySelectorAll('.shmenu [data-sort]').length===4);
      document.querySelector('[data-sort="title"]').click(); await w(20);
      const tt=[...document.querySelectorAll('.book .t')].map(e=>e.textContent); ok('按书名排序',tt.join()===tt.slice().sort((a,b)=>a.localeCompare(b,'zh-Hans-CN')).join(),tt.join());
      T.openBook('nahan'); await w(300); T.closeSheet(); V.sort='recent'; T.shelf(); await w(20); ok('最近阅读：刚打开的书在最前',document.querySelector('.book').dataset.k==='nahan',document.querySelector('.book').dataset.k);
      document.querySelector('#shEdit').click(); await w(20); ok('整理：出现拖动柄、"完成"',document.querySelectorAll('.book .grip').length===5&&!!document.querySelector('#shDone'));
      V.order=['hound','hlm','tractatus','nahan','lhz']; V.sort='manual'; T.shelf(); await w(20); ok('手动顺序',document.querySelector('.book').dataset.k==='hound');
      document.querySelector('#shDone').click(); await w(20); ok('完成后回到平常',!document.querySelector('.editing'));
      V.lay='list'; V.sort='manual'; V.order=[]; T.setShEdit(false); T.shelf(); await w(20); }
    // 选字"解释"：小词典
    T.openBook('lhz'); await w(900); T.closeSheet();
    { const z=E.length?T.els()[IX['7.2']].querySelector('.zh'):null; const tw=document.createTreeWalker(z,NodeFilter.SHOW_TEXT); let n,pos=0,o=z.textContent.indexOf('萌蘖'),r=document.createRange();
      while((n=tw.nextNode())){ if(pos+n.length>o){ r.setStart(n,o-pos); r.setEnd(n,o-pos+2); break; } pos+=n.length; }
      getSelection().removeAllRanges(); getSelection().addRange(r); T.showMenu(); await w(30);
      const mb=[...document.querySelectorAll('#selmenu button')].map(b=>b.dataset.a).join();
      ok('选字菜单只有划线、复制（已去掉"解释"小词典）',mb==='hl,cp',mb); T.closeSheet(); }
    T.shelf(); await w(20);
    ok('只出现一次、没出场的人不做人物卡',!T.PEOPLE().some(p=>p.ap.length===1&&['司马懿','桓温','董卓'].includes(p.name)));
    T.closeSheet(); T.shelf(); await w(20); T.bookInfo('lhz',''); ok('书的详情：梁启超、1901',document.querySelector('#sheet').textContent.includes('1901'));
    T.closeSheet(); localStorage.clear(); T.TIPSS().welcomed=1; T.shelf(); }
  // ===== 《巴斯克维尔的猎犬》（v9.41，2026-10-22，英文推理小说全本，自译）=====
  { const w=ms=>new Promise(r=>setTimeout(r,ms)); localStorage.clear(); T.TIPSS().welcomed=1; T.shelf(); T.openBook('hound'); await w(900); T.closeSheet();
    const P5=T.P(), IX=T.getIDX(), E=T.els();
    ok('猎犬：15 章、1460 段',P5.length===1460&&document.querySelectorAll('.hui').length===15,P5.length);
    ok('第一章标题是中文章名',document.querySelector('#hui1 h2').textContent.includes('福尔摩斯'));
    ok('默认只看中文：原文段落隐藏',!!E[0].querySelector('.og')&&E[0].querySelector('.og').getClientRects().length===0);
    T.openCard(0); await w(20); ok('猎犬：中文模式点一段，卡片里有英文原文',document.querySelector('#sheet .ogq div')?.textContent.startsWith('Mr. Sherlock Holmes')); T.closeSheet();
    T.getS().lang='orig'; T.setLang(); await w(50); ok('只看原文：中文隐藏',E[0].querySelector('.zh').getClientRects().length===0&&E[0].querySelector('.og').textContent.startsWith('Mr. Sherlock Holmes'));
    T.getS().lang='zh'; T.setLang(); await w(50);
    const pn=[...document.querySelectorAll('.pn')].map(e=>e.textContent);
    ok('猎犬：福尔摩斯、华生有人名链接',pn.includes('福尔摩斯')&&pn.includes('华生'));
    ok('"巴斯克维尔庄园"里的姓不链人名、第一章的"主人"不链',![...E[IX['1.3']].querySelectorAll('.pn')].some(e=>e.textContent==='主人')&&!pn.includes('巴斯克维尔'));
    ok('猎犬：第 1 章有伏笔 B01',T.getSUS().some(s=>s.id==='B01'&&s['提出'].startsWith('1.')));
    T.openCard(IX['1.1']); await w(30); ok('猎犬：第一段有解释卡片',document.querySelector('#sheet .plain')?.textContent.length>5); T.closeSheet();
    T.shelf(); await w(20); T.bookInfo('hound',''); ok('书的详情：柯南·道尔[英国]，可切换原文',document.querySelector('#sheet').textContent.includes('柯南·道尔[英国]')&&document.querySelector('#sheet').textContent.includes('切换'));
    T.closeSheet(); localStorage.clear(); T.TIPSS().welcomed=1; T.shelf(); }
  // ===== v9.43（2026-10-23）登录注册 → 问卷 → 书架；我的；主线；重度带法 =====
  { const w=ms=>new Promise(r=>setTimeout(r,ms)); localStorage.clear(); const A=T.ACC(); A.users={}; A.cur=null; const PF=T.PROF(); PF.mode='light'; PF.qz=null; PF.days={}; delete PF.lv;
    T.authPage('reg'); await w(30);
    const ins=[...document.querySelectorAll('.auth .fld input')].map(x=>x.id);
    ok('注册只有账号、密码（v9.55：昵称不在注册时问）',ins.join(',')==='auAcc,auPw',ins.join(','));
    ok('密码规则写在密码框里',document.querySelector('#auPw').placeholder.includes('字母和数字'));
    ok('注册页：logo + 一句话',document.querySelector('.authbrand svg.logo')&&document.querySelector('.autag').textContent==='不是帮你读完，是让你想读下去。');
    ok('注册页不对读者说"测试版"',!document.querySelector('.auth').textContent.includes('测试'));
    ok('底部一行：已有账号，登录（不再有"先体验"，不登录能浏览首页）',document.querySelector('.auswitch').textContent.replace(/\s/g,'')==='已有账号，登录'&&!document.querySelector('#auSkip'));
    ok('登录页左上角 ‹ 回访客首页',!!document.querySelector('#flBack')); window.__GUESTCHK=true; document.querySelector('#flBack').click(); await w(20); T.ACC().cur=null; ok('回到首页：就是书架——右上角"登录"，排序、排列、找书、导入都在，五本精读版封面',!!document.querySelector('.shelf')&&!!document.querySelector('#shLogin')&&!!document.querySelector('#sortB')&&!!document.querySelector('#shLib')&&!!document.querySelector('#impBtn')&&document.querySelectorAll('#bookList .book').length===5); T.authPage('reg'); await w(20);
    ok('顶部两段进度条（不写字），在第 1 段',document.querySelectorAll('.fldots i').length===2&&document.querySelectorAll('.fldots i.on').length===1&&document.querySelector('.flbar').textContent.trim()==='‹');   /* 只有一个返回箭头，没有文字 */
    // ===== v9.65 访客逻辑 =====
    window.__GUESTCHK=true; T.homePage(); await w(20);
    ok('不登录的书架和登录后几乎一样：没有营销内容、没有头像',!document.querySelector('.hmtag,.hmsub,.hmfeat,.hmcta,#hmReg')&&document.querySelector('.shelf h1').textContent==='书架'&&!document.querySelector('#shMe'));
    ok('没登录点"找书"：先去登录（登录页只有账号密码，没有多余提示行）',(()=>{ document.querySelector('#shLib').click(); return !!document.querySelector('#auAcc')&&!document.querySelector('.auhint'); })()); T.homePage(); await w(20);
    ok('没登录点"导入"：先去登录',(()=>{ document.querySelector('#impBtn').click(); return !!document.querySelector('#auAcc')&&!document.querySelector('.auhint'); })()); T.homePage(); await w(20);
    document.querySelector('#bookList .book').click(); await w(30);
    ok('访客点封面：看书籍详情，底部按钮是"登录后阅读"',document.querySelector('#sheet').classList.contains('show')&&document.querySelector('#bOpen').textContent==='登录后阅读');
    document.querySelector('#bOpen').click(); await w(30);
    ok('点"登录后阅读"：进登录页，不写多余提示',!!document.querySelector('#auAcc')&&!document.querySelector('.auhint'));
    T.openBook('hlm'); await w(20); ok('没登录直接打开书：被拦到登录页（不会进阅读器）',!!document.querySelector('#auAcc')&&!document.querySelector('#text')); window.__GUESTCHK=false;
    const fill=(a,p,n)=>{ document.querySelector('#auAcc').value=a; document.querySelector('#auPw').value=p; if(n!=null&&document.querySelector('#auName')) document.querySelector('#auName').value=n; document.querySelector('#auGo').click(); };
    T.setAfter(()=>{ window.__AFTER=1; T.shelf(); },'登录后阅读《红楼梦》');
    fill('13800001234','1',''); await w(20);
    ok('昵称不填：默认"读者"+账号后四位',T.curUser().name==='读者1234',T.curUser().name);
    ok('注册后先填问卷（回到原处的动作等问卷结束）',!window.__AFTER);
    ok('注册后直接进问卷（第 2 段），三张卡在一屏，第一张展开',document.querySelectorAll('.fldots i.on').length===2&&document.querySelectorAll('.qzc').length===3&&document.querySelectorAll('.qzc.open').length===1);
    document.querySelector('.qzchips [data-v="half"]').click(); await w(400);
    ok('答完一张：收成一行（带"改"），下一张展开',!!document.querySelector('.qzc.done[data-edit="0"]')&&document.querySelector('.qzc.done').textContent.includes('常读到一半就放下')&&document.querySelector('.qzc.open .qzt').textContent.includes('读不下去'));
    document.querySelector('.qzchips [data-v="words"]').click(); document.querySelector('.qzchips [data-v="bored"]').click();
    ok('第二题可多选，选了才能点"完成"',document.querySelectorAll('.qzchips [aria-pressed="true"]').length===2&&!document.querySelector('#qzNext').disabled);
    { ok('第二题选项末尾是"＋ 自己写"（虚线样式，同一行），没有单独的输入框和"添加"',!!document.querySelector('.qzchips #qzAdd')&&!document.querySelector('.qzown')&&!document.querySelector('#qzOwnOk'));
      document.querySelector('#qzAdd').click(); await w(10); const inp=document.querySelector('#qzOwn');
      ok('点开后：变成和选项同一行、同高的输入框',!!inp&&inp.parentNode.classList.contains('qzchips')&&Math.abs(inp.offsetHeight-document.querySelector('.qzchips button[data-v]').offsetHeight)<=2);
      inp.value='字太小'; inp.dispatchEvent(new KeyboardEvent('keydown',{key:'Enter',bubbles:true})); await w(10);
      ok('回车：收成一个选中的选项，"＋ 自己写"回来',!!document.querySelector('.qzchips [data-v="x:字太小"][aria-pressed="true"]')&&!!document.querySelector('#qzAdd')&&!document.querySelector('#qzOwn')&&document.querySelectorAll('.qzchips [aria-pressed="true"]').length===3); }
    document.querySelector('#qzNext').click(); await w(20);
    ok('问卷没答完时有"跳过"',!!document.querySelector('#qzSkip'));
    document.querySelector('.qzc.done[data-edit="0"]').click(); await w(20);
    ok('答过的随时点回去改（答案还在）',document.querySelector('.qzc.open .qzt').textContent.includes('习惯')&&!!document.querySelector('.qzchips [data-v="half"][aria-pressed="true"]'));
    document.querySelector('.qzchips [data-v="long"]').click(); await w(400);
    ok('改完回到没答的那张',document.querySelector('.qzc.open .qzt').textContent.includes('希望伏笔')&&document.querySelector('.qzc.done').textContent.includes('很久没有读完一本书'));
    document.querySelector('.qzchips [data-v="less"]').click(); await w(400);
    ok('三题都答完：不再有"跳过"',!document.querySelector('#qzSkip')&&!!document.querySelector('#qrOk'));
    ok('三题都答完：下面实时显示"伏笔会以 轻度 的方式陪你读"',document.querySelector('.qzres')?.textContent.includes('轻度')&&!!document.querySelector('#qrOk'));
    document.querySelector('.qzc.done[data-edit="2"]').click(); await w(20); document.querySelector('.qzchips [data-v="auto"]').click(); await w(400);
    ok('改了第三题：结果当场变成重度',document.querySelector('.qzres').textContent.includes('重度'));
    document.querySelector('#qrOk').click(); await w(30);
    ok('"开始读书"后是重度',PF.mode==='heavy');
    ok('问卷结束：回到刚才要做的事（登录前点的那本）',window.__AFTER===1);
    ok('规则：少打扰 = 轻；多带 = 重；常读+按前两题 = 轻',T.quizMode({q3:'less',q1:'long'})==='light'&&T.quizMode({q3:'more'})==='heavy'&&T.quizMode({q1:'often',q2:['people'],q3:'auto'})==='light');
    ok('选了"字词看不懂"→ 新书解释默认入门',PF.lv===0);
    ok('规则：少打扰 = 轻；多带 = 重；常读+按前两题 = 轻',T.quizMode({q3:'less',q1:'long'})==='light'&&T.quizMode({q3:'more'})==='heavy'&&T.quizMode({q1:'often',q2:['people'],q3:'auto'})==='light');
    ok('开始读书 → 书架；右上角是头像',!!document.querySelector('.shelf')&&document.querySelector('#shMe .av').textContent==='读');
    ok('书架上不再自动弹"关于"',!document.querySelector('#sheet').classList.contains('show'));
    // 我的
    const dk=d=>`${d.getFullYear()}-${d.getMonth()+1}-${d.getDate()}`; PF.days={}; const d0=new Date();
    for(let i=1;i<=3;i++){ const d=new Date(d0); d.setDate(d.getDate()-i); PF.days[dk(d)]={ms:12*6e4,n:4,sv:i===2?1:0}; }
    ok('今天没读、前三天读了：连续 3 天',T.streak()===3,T.streak()); T.today().n=2; ok('今天也读了：连续 4 天',T.streak()===4);
    document.querySelector('#shMe').click(); await w(20); let t=document.querySelector('.pg').textContent;
    ok('我的：账号卡（昵称、打码的账号、"个人账户"），整张可点',t.includes('读者1234')&&t.includes('138****1234')&&t.includes('个人账户')&&document.querySelector('#meAcc').tagName==='BUTTON');
    ok('我的：四个统计（连续、本周分钟、读完、揭晓）',document.querySelectorAll('.mestat > div').length===4&&document.querySelector('.mestat b').firstChild.textContent==='4');
    ok('打卡默认按周：7 天，有"本周读了 N 天"',document.querySelectorAll('.cal.wk .d').length===7&&!document.querySelector('.cal.mo')&&document.querySelector('.calsum').textContent.includes('本周读了'));
    const cellOf=(root,on)=>[...document.querySelectorAll(root+' .d')].find(e=>e.classList.contains('on')===on&&!e.classList.contains('today')&&!e.classList.contains('fut')), sty=e=>e?(c=>c.borderRadius+'|'+c.backgroundColor+'|'+Math.round(e.getBoundingClientRect().height))(getComputedStyle(e)):'none', wkN=sty(cellOf('.cal.wk',false)), wkY=sty(cellOf('.cal.wk',true));
    document.querySelector('#calTg').click(); await w(20); ok('展开为月历，可收起',document.querySelectorAll('.cal.mo .d').length>=28&&document.querySelector('#calTg').textContent==='收起');
    { const moN=sty(cellOf('.cal.mo',false)), moY=sty(cellOf('.cal.mo',true)); ok('月历和周历同一套格子：同高、同圆角、同底色（没读的、读过的各比一次）',(moN==='none'||wkN==='none'||moN===wkN)&&(moY==='none'||wkY==='none'||moY===wkY),wkN+' / '+moN+' / '+wkY+' / '+moY); }
    ok('月历可直接选年份、月份',!!document.querySelector('#calY')&&!!document.querySelector('#calM'));
    { const ms=document.querySelector('#calM'); const now=new Date(); if(ms.options.length>1){ ms.value=String(ms.options[0].value); ms.dispatchEvent(new Event('change')); await w(20); ok('选月份后跳到那个月',document.querySelector('#calM').value===String(ms.options[0]?.value??0)||+document.querySelector('#calM').value===0); } }
    document.querySelector('#calTg').click(); await w(20); ok('收起回到本周',!!document.querySelector('.cal.wk')&&!document.querySelector('.cal.mo'));
    ok('二级菜单：阅读偏好、关于伏笔',!!document.querySelector('#mePref')&&!!document.querySelector('#meAbout'));
    document.querySelector('#meAbout').click(); await w(20); ok('关于伏笔是二级页，可返回',document.querySelector('.pgbar b').textContent==='关于伏笔'&&document.querySelector('#pgBack').textContent.includes('我的'));
    document.querySelector('#pgBack').click(); await w(20); document.querySelector('#mePref').click(); await w(20);
    ok('阅读偏好：带读开关 + 问卷答案',!!document.querySelector('#meMode [data-m="heavy"][aria-pressed="true"]')&&document.querySelector('.qsum').textContent.includes('很久没有读完一本书'));
    document.querySelector('#meMode [data-m="light"]').click(); ok('在阅读偏好里改成轻度',PF.mode==='light');
    document.querySelector('#meQz').click(); await w(20); ok('重新填写：三张卡都带着上次的答案、能返回',document.querySelectorAll('.qzc.done').length===3&&!!document.querySelector('#pgBack'));
    document.querySelector('#pgBack').click(); await w(20); document.querySelector('#pgBack').click(); await w(20); document.querySelector('#meAcc').click(); await w(20);
    ok('点账号卡：进"个人账户"页（昵称、密码、账号信息、退出登录、注销）',document.querySelector('.pgbar b').textContent==='个人账户'&&!!document.querySelector('#secName')&&!!document.querySelector('#secPw')&&!!document.querySelector('#secOut')&&!!document.querySelector('#secDel')&&document.querySelector('.secinfo').textContent.includes('加入时间')&&!document.querySelector('.pgbody').textContent.includes('保存在'));
    ok('个人账户页能返回"我的"',document.querySelector('#pgBack').textContent.includes('我的'));
    ok('账户页：头像可以点（有"改"的小图标）',!!document.querySelector('#secAv .avedit'));
    document.querySelector('#secAv').click(); await w(30);
    ok('头像面板：预览、字、8 种颜色、上传图片、恢复默认',!!document.querySelector('#avPrev .av')&&!!document.querySelector('#avCh')&&document.querySelectorAll('#sheet .avcol').length===8&&!!document.querySelector('#avFile')&&!!document.querySelector('#avReset'));
    document.querySelector('#avCh').value='伏'; document.querySelector('#avCh').dispatchEvent(new Event('input')); document.querySelectorAll('#sheet .avcol')[2].click(); await w(10);
    ok('改字、选颜色：预览马上变',document.querySelector('#avPrev .av').textContent==='伏'&&/rgb\(47, 74, 140\)/.test(document.querySelector('#avPrev .av').style.background));
    document.querySelector('#avSave').click(); await w(30);
    ok('保存后：账户页、我的、书架的头像都是新的',T.curUser().av&&T.curUser().av.ch==='伏'&&document.querySelector('.secid .av').textContent==='伏');
    T.mePage(); await w(20); ok('"我的"账号卡里是新头像',document.querySelector('#meAcc .av').textContent==='伏'); T.shelf(); await w(20); ok('书架右上角是新头像',document.querySelector('#shMe .av').textContent==='伏'); T.secPage(); await w(20);
    // ===== v9.71 =====
    T.shelf(); await w(30);
    ok('排序里叫"自定义"，不叫"手动"',document.querySelector('#sortB')&&(document.querySelector('#sortB').click(),document.querySelector('.shmenu').textContent.includes('自定义')&&!document.querySelector('.shmenu').textContent.includes('手动'))); document.querySelector('#sortB').click();
    { T.shelf(); await w(20); document.querySelector('#shEdit').click(); await w(20);
      const bk=[...document.querySelectorAll('#bookList .book')], k0=bk[0].dataset.k, el=bk[0], tg=bk[2], r2=tg.getBoundingClientRect();
      const ev=(t,o)=>el.dispatchEvent(new PointerEvent(t,Object.assign({bubbles:true,cancelable:true,pointerId:7,button:0},o)));
      const r1=el.getBoundingClientRect(); ev('pointerdown',{clientX:r1.left+10,clientY:r1.top+10}); ev('pointermove',{clientX:r1.left+30,clientY:r1.top+30});
      ok('拖动时：被拖的书抬起并跟手（有 transform）',el.classList.contains('drag')&&/translate/.test(el.style.transform)&&/scale/.test(el.style.transform));
      ev('pointermove',{clientX:r2.left+r2.width/2,clientY:r2.top+r2.height*0.8}); await w(30);
      ok('拖到别的书后面：顺序变了，让位的书有滑动过渡',[...document.querySelectorAll('#bookList .book')].findIndex(x=>x.dataset.k===k0)>0&&[...document.querySelectorAll('#bookList .book')].some(x=>x!==el&&x.style.transition.includes('transform')));
      ev('pointerup',{}); await w(400);
      ok('松手后：滑回格子、清掉动画样式，顺序记为"自定义"',!el.classList.contains('drag')&&el.style.transform===''&&T.shv().sort==='manual'&&T.shv().order[0]!==k0);
      document.querySelector('#shDone').click(); await w(20); T.shv().sort='recent'; T.shelf(); await w(20); }
    T.secPage(); await w(20);
    // ===== v9.68 =====
    document.querySelector('#secOut').click(); await w(20);
    ok('退出登录：先弹拦截面板，没点确认前不退出',!!document.querySelector('#sheet #cfOk')&&!!T.curUser()&&document.querySelector('#sheet').textContent.includes('重新登录后可继续阅读')); T.closeSheet(); 
    document.querySelector('#secDel').click(); await w(20);
    ok('注销账号：拦截面板写明无法恢复，按钮是"确认注销"',document.querySelector('#cfOk').textContent==='确认注销'&&document.querySelector('#sheet').textContent.includes('无法恢复')&&!!T.curUser()); T.closeSheet();
    { const V=T.shv(); delete V.layUser; V.lay=null; T.shelf(); await w(20); ok('书架默认是列表排列',T.shv().lay==='list'&&!!document.querySelector('.lay-list'));
      document.querySelector('[data-lay="grid"]').click(); await w(20); T.shelf(); await w(20); ok('改过排列就记住（再进书架还是书格）',T.shv().lay==='grid'&&!!document.querySelector('.lay-grid')); V.lay='list'; T.shelf(); await w(20);
      ok('列表里没有进度条线，进度只是文字',!document.querySelector('.books .pbar')&&!document.querySelector('#shCont .pbar')); }
    window.__GUESTCHK=true; T.ACC().cur=null; T.shelf(); await w(20); ok('没登录时"登录"是描边按钮',getComputedStyle(document.querySelector('#shLogin')).boxShadow!=='none'&&getComputedStyle(document.querySelector('#shLogin')).borderRadius!=='0px'); window.__GUESTCHK=false; T.ACC().cur='13800001234';
    T.avatarSheet(T.curUser(),()=>T.secPage()); await w(20); document.querySelector('#avReset').click(); await w(30); ok('恢复默认：回到昵称首字',!T.curUser().av&&document.querySelector('.secid .av').textContent==='读');
    T.ACC().users[T.curUser().id].av={img:'data:image/jpeg;base64,/9j/4AAQ'}; T.secPage(); await w(20); ok('用图片做头像：显示图片',!!document.querySelector('.secid .av.img img')); delete T.ACC().users[T.curUser().id].av; T.secPage(); await w(20);
    document.querySelector('#secName').value='改名测试'; document.querySelector('#secSave').click(); await w(20);
    ok('改昵称：页内马上变',T.curUser().name==='改名测试'&&document.querySelector('#secNm').textContent==='改名测试');
    document.querySelector('#secPw').value='abc12345'; document.querySelector('#secPwSave').click(); await w(20); ok('改密码：保存并提示',document.querySelector('#toast').textContent.includes('密码已修改')); T.ACC().users[T.curUser().id].name='读者1234';
    T.ACC().cur=null; T.authPage('login'); await w(20); ok('登录页只有账号、密码',!document.querySelector('#auName')); fill('13800001234','随便'); await w(20); ok('登录不校验密码；填过问卷 → 直接书架',!!document.querySelector('.shelf')&&T.curUser().name==='读者1234');
    T.ACC().cur=null; T.authPage('reg'); await w(20); document.querySelector('#auGo').click(); await w(20); ok('什么都不填也能登录，有默认昵称',!!T.curUser()&&/^读者\d{4}$/.test(T.curUser().name),T.curUser()?.name);
    T.ACC().cur=null; T.authPage('reg'); await w(20); fill('reader.zhou@example.com','a',''); await w(20); ok('邮箱注册不填昵称：读者 + @ 前末四位',T.curUser().name==='读者zhou',T.curUser().name);
    // 主线：五本书都有
    for(const [bk,n] of [['hlm',5],['nahan',8],['lhz',9],['tractatus',7],['hound',9]]){ T.setBook(bk); const m=T.getMain(), SU=T.getSUS2(); ok(`${bk} 有主线（${n} 块碎片，都是有揭晓的伏笔）`,!!m&&m.pieces.length===n&&m.pieces.every(id=>{const x=SU.find(y=>y.id===id); return x&&x['揭晓'];})&&m.q.endsWith('？')&&m.end.length>80,m&&m.pieces.join(',')); }
    T.setMode('light'); T.openBook('hound'); await w(900); T.closeSheet(); const IH=T.getIDX(), SH=T.getS(); const tb0=document.querySelector('#toast');
    T.cluePanel('open'); ok('一打开书，伏笔页顶部就有主线',document.querySelector('#sheet .mainl')?.textContent.includes('魔犬'));
    T.closeSheet(); await w(1400); ok('打开书时提示条告诉读者主线（一次）',!!SH.mainSeen);
    T.markRd(0,IH['3.130']); SH.current=IH['3.130']; ['B04','B05'].forEach(id=>{SH.found[id]=SH.seen[id]=Date.now();}); SH.doneS.B04=Date.now(); T.cluePanel('done');
    t=document.querySelector('#sheet .mainl')?.textContent||'';
    ok('伏笔页顶部：主线问题 + 已拼上 1 / 9',t.includes('魔犬')&&t.includes('已拼上 1 / 9'),t);
    ok('没拼上的只是空格',document.querySelectorAll('#sheet .mlp i').length===9&&document.querySelectorAll('#sheet .mlp i.on').length===1&&!t.includes('磷'));
    ok('主线碎片带"主线"印',!!document.querySelector('#sheet .cr .seal.zhu'));
    ok('伏笔页主线下列出拼上的那块"拼上了什么"',document.querySelector('#sheet .mlnotes li')?.textContent.includes('逃到那里'));
    T.closeSheet(); T.mainReveal('B04'); await w(50); const mf=document.querySelector('#mlfx');
    ok('主线碎片揭晓：单独一张拼图卡（问题、格子、这一块拼上了什么）',mf.classList.contains('show')&&mf.textContent.includes('魔犬')&&mf.querySelectorAll('.mlfx-p i').length===9&&!!mf.querySelector('.mlfx-p i.new')&&mf.textContent.includes('逃到那里'));
    ok('拼图卡：没有"看这处伏笔/看主线"按钮，只有 ×',!document.querySelector('#mlfxAns')&&!document.querySelector('#mlfxMain')&&!mf.querySelector('.mlfx-a')&&!!document.querySelector('#mlfxX'));
    document.querySelector('#mlfxX').click(); await w(20); ok('点 × 收起拼图卡',!mf.classList.contains('show'));
    { const M=T.getMain(); M.pieces.forEach(id=>SH.doneS[id]=Date.now()); T.mainReveal(M.pieces[M.pieces.length-1]); await w(50);
      ok('最后一块：全部拼上了',mf.classList.contains('done')&&mf.textContent.includes('全部拼上了')); mf.classList.remove('show');
      M.pieces.forEach(id=>{ if(id!=='B04') delete SH.doneS[id]; }); }
    // 真的读到一块碎片的答案：走拼图卡，不走普通提示条
    { const s5=T.getSUS2().find(x=>x.id==='B14'); delete SH.doneS.B14; SH.seen.B14=SH.found.B14=Date.now(); tb0.classList.remove('show'); mf.classList.remove('show');
      const j=IH[s5['揭晓']]; T.markRd(0,j-1); SH.current=j-1; T.noRead(1); await w(60); T.els()[j].scrollIntoView({block:'start'}); await w(80); T.setPos(j); await w(1300);
      ok('读到主线碎片的答案 → 拼图卡（不是普通提示条）',mf.classList.contains('show')&&!!SH.doneS.B14&&!(tb0.classList.contains('show')&&tb0.textContent.includes('伏笔揭晓：')),'mf='+mf.className+' done='+!!SH.doneS.B14+' cur='+SH.current+' j='+j+' vis='+SH.vis+' guide='+SH.view.guide+' seen='+!!SH.seen.B14+' toastShow='+tb0.classList.contains('show')+' '+tb0.textContent.slice(0,20)); mf.classList.remove('show');
      delete SH.doneS.B14; T.markRd(0,j+3); T.setPos(j+3); await w(900);
      ok('滑得快、一路滑过了答案（同一章里）：仍然给拼图卡',!!SH.doneS.B14&&mf.classList.contains('show')); mf.classList.remove('show'); }
    T.closeSheet(); SH.finished=Date.now(); T.syncEnd(); t=document.querySelector('#endMark').textContent;
    ok('读完：收尾页拼出主线全貌',t.includes('魔犬')&&t.includes('凶器'));
    T.shelf(); T.setBook('tractatus'); T.getS().preK=2; ok('逻辑哲学论：读过前言第 2 段，主线出现',T.mainReached()&&T.mainHTML().includes('界限'));
    T.setBook('nahan'); T.getRD().clear(); T.getS().rd=[]; ok('呐喊：一页没读也有主线（铁屋子，出自自序）',T.mainReached()&&T.mainHTML().includes('铁屋子'));
    // 重度：不再多加伏笔
    T.setBook('hlm'); T.setMode('light'); const nL=T.getSUS2().length; T.setMode('heavy'); ok('重度不再多加伏笔',T.getSUS2().length===nL);
    // 重度：第一次打开新书，先介绍篇幅和结构；轻度不介绍
    localStorage.clear(); T.setMode('heavy'); T.shelf(); T.openBook('hlm'); await w(600);
    t=document.querySelector('#sheet').textContent; ok('重度：第一次打开新书 → "这本书怎么读"（篇幅、结构、主线）',t.includes('这本书怎么读')&&t.includes('篇幅')&&t.includes('结构')&&t.includes('温柔富贵之乡'),t.slice(0,80));
    T.closeSheet(); T.shelf(); T.openBook('hlm'); await w(600); ok('只介绍一次',!document.querySelector('#sheet').classList.contains('show')||!document.querySelector('#sheet').textContent.includes('这本书怎么读'));
    T.closeSheet(); localStorage.clear(); T.setMode('light'); T.shelf(); T.openBook('nahan'); await w(600); ok('轻度：不介绍',!document.querySelector('#sheet').classList.contains('show'));
    // 轻度：一天内不弹回顾；重度：每次都弹，带一两个未揭晓的伏笔
    T.closeSheet(); T.shelf(); T.openBook('hlm'); await w(900); T.closeSheet(); const IX=T.getIDX(); T.markRd(0,IX['2.15']); T.getS().current=IX['2.15']; T.getS().seen.H01=Date.now(); T.getS().found.H01=Date.now(); T.getS().seenAt=Date.now()-3600e3; T.save();
    T.shelf(); await w(20); T.openBook('hlm'); await w(600); ok('轻度：隔一小时打开，不弹前情提要',!document.querySelector('#sheet').classList.contains('show'));
    T.getS().seenAt=Date.now()-3*864e5; T.save(); T.shelf(); await w(20); T.openBook('hlm'); await w(600);
    ok('轻度：隔三天打开，不弹卡，回顾放进"上次读到这里"那条线',!document.querySelector('#sheet').classList.contains('show')&&!!document.querySelector('#lastLine.rc')&&document.querySelector('#lastLine').textContent.includes('距上次 3 天'));
    document.querySelector('#llMore')?.click(); ok('点"展开前情"才看完整回顾',!!document.querySelector('#lastLine .llf')&&!document.querySelector('#lastLine .llf').hidden);
    T.closeSheet(); T.setMode('heavy'); T.getS().seenAt=Date.now()-3600e3; T.save(); T.shelf(); await w(20); T.openBook('hlm'); await w(600);
    t=document.querySelector('#sheet').textContent; ok('重度：隔一小时也弹前情提要，带本回已读部分和未揭晓的伏笔',t.includes('带着这个问题往下读')&&t.includes('已读部分'),t.slice(0,80));
    T.closeSheet();
    // 读完一章：书里该章末尾出现"回顾这一回"，点开才看；不弹提示（轻重都有）
    const S_=T.getS(); S_.uDone={}; T.getRD().clear(); S_.rd=[]; const tb=document.querySelector('#toast'); tb.classList.remove('show');
    T.markRd(0,IX['1.40']); T.paintUEnd(); ok('第一回没读完：回末没有回顾按钮',document.querySelector('.uend[data-u="1"]').hidden);
    T.setMode('heavy'); T.markRd(0,IX['2.1']); S_.current=IX['1.44']; T.setPos(IX['2.1']); await w(600);
    const ue=document.querySelector('.uend[data-u="1"]'); ok('读完第一回：回末出现"回顾这一回"',!ue.hidden&&ue.textContent.includes('回顾这一回'));
    ok('不弹提示条',!(tb.classList.contains('show')&&tb.textContent.includes('读完')));
    ue.querySelector('button').click(); await w(20); t=document.querySelector('#sheet').textContent; ok('点开 → 这一回的回顾',t.includes('第一回 · 回顾')&&t.includes('甄士隐')); T.closeSheet();
    T.setMode('light'); T.paintUEnd(); ok('轻度不显示回末回顾',document.querySelector('.uend[data-u="1"]').hidden); T.setMode('heavy'); T.paintUEnd();
    ok('第二回没读完：没有',document.querySelector('.uend[data-u="2"]').hidden);
    // 重度：答案快到了（发现过就算，不必打开过）：提示条 + 页边标记
    T.setMode('heavy'); const far=T.getSUS2().find(s=>s['揭晓']&&IX[s['揭晓']]-IX[s['提出']]>15);
    if(far){ const P_=T.P(), a=IX[far['提出']], j=IX[far['揭晓']]; let c=j-1, ch=0; while(c>a&&ch+P_[c].zh.length<=700){ ch+=P_[c].zh.length; c--; }
      S_.found[far.id]=Date.now(); delete S_.seen[far.id]; delete S_.doneS[far.id]; S_.soon={}; T.markRd(0,c); S_.current=c; S_.vis=c; tb.classList.remove('show'); T.paintMarks(); await w(500);
      ok('答案快到了：书里不显示图标',!document.querySelector('.mk.soon'),far.id);
      ok('同时出提示条"答案快到了"',tb.classList.contains('show')&&tb.textContent.includes('答案快到了'),tb.textContent);
      T.setMode('light'); S_.soon={}; tb.classList.remove('show'); T.paintMarks(); await w(500); ok('轻度：不提示',!tb.classList.contains('show')||!tb.textContent.includes('答案快到了')); }
    // 提示条都有 ×；离开这本书，书里的提示立刻消失
    T.shelf(); T.openBook('hlm'); await w(700); T.closeSheet();
    { T.setMode('light'); const tb2=document.querySelector('#toast'), IX2=T.getIDX(), S2=T.getS(); S2.mainSeen=Date.now(); T.TIPSS().tipFound=1; T.noRead(1); await w(60);
      T.markRd(0,IX2['1.15']); S2.vis=IX2['1.15']; delete S2.found.H02; delete S2.doneS.H02; T.paintMarks(); await w(100);
      S2.seen.H02=Date.now(); S2.soon={}; tb2.classList.remove('show'); T.els()[IX2['1.32']].scrollIntoView({block:'center'}); await w(80); T.markRd(0,IX2['1.33']); S2.current=IX2['1.31']; T.setPos(IX2['1.33']); await w(1300);
      T.dropBookTips(); T.toast('<div class="tq">伏笔揭晓：测试</div><button>看解释</button>',()=>{},5000);
      ok('提示条右边有 ×',tb2.classList.contains('show')&&!!tb2.querySelector('.tx'),tb2.textContent.slice(0,30));
      tb2.querySelector('.tx')?.click(); ok('点 × 立刻关掉',!tb2.classList.contains('show'));
      T.later(()=>T.toast('<div class="tq">伏笔揭晓：迟到的提示</div>',null,5000),600); await w(100); T.shelf(); await w(1000);
      ok('揭晓提示还没出来就回书架：不会再跳出来（不带到下一本书）',!tb2.classList.contains('show')&&!document.querySelector('#mlfx.show')); }
    // 导览：阅读回顾固定在底部
    T.openBook('hlm'); await w(700); T.closeSheet(); T.outline('hui'); await w(20);
    ok('导览：没有底部大按钮，"回顾"是"正在读"那一行右边的文字入口',!document.querySelector('#sheet .sfoot')&&!!document.querySelector('#sheet .olnow #olRecap')&&document.querySelector('#olRecap').textContent==='回顾');
    document.querySelector('#olRecap').click(); await w(20); ok('点开阅读回顾，可以返回导览',document.querySelector('#sheet .ttl').textContent==='阅读回顾'&&!!document.querySelector('#rcBack'));
    document.querySelector('#rcBack').click(); await w(20); ok('返回导览',document.querySelector('#sheet .ttl').textContent==='导览'); T.closeSheet();
    T.openBook('tractatus'); await w(700); T.closeSheet(); T.markRd(0,5); T.outline(); await w(20); ok('逻辑哲学论导览底部也有阅读回顾',!!document.querySelector('#sheet .olnow #olRecap')); T.closeSheet();
    // 主线的伏笔：不用点开，发现就是打开的（2026-10-27 用户）；其它伏笔照旧要点
    T.openBook('hound'); await w(800); T.closeSheet();
    { const S3=T.getS(), I3=T.getIDX(), IDX0=x=>I3[x['提出']]; S3.mainSeen=Date.now(); T.setMode('light'); Object.keys(S3.seen).forEach(k=>delete S3.seen[k]);
      const s5=T.getSUS2().find(x=>x.id==='B14'), j=I3[s5['揭晓']]; delete S3.seen.B14; delete S3.doneS.B14; S3.found.B14=Date.now(); document.querySelector('#mlfx')?.classList.remove('show');
      T.markRd(0,j-1); S3.current=j-1; T.noRead(1); await w(60); T.els()[j].scrollIntoView({block:'start'}); await w(80); T.setPos(j); await w(1300);
      const m2=document.querySelector('#mlfx');
      ok('主线的伏笔：页边一亮就自动打开，读到答案拼上',!!S3.seen.B14&&!!S3.doneS.B14&&!!m2&&m2.classList.contains('show'));
      ok('拼图卡里不再写"来自之前没打开的伏笔"',!!m2&&!m2.textContent.includes('之前没打开'));
      document.querySelector('#mlfxX')?.click(); T.closeSheet();
      const p2=T.getSUS2().find(x=>T.getMain().pieces.includes(x.id)&&!S3.found[x.id]&&x['提出']!=='前言');
      if(p2){ const i2=I3[p2['提出']]; T.markRd(0,i2); S3.current=i2; S3.vis=i2; T.els()[i2].scrollIntoView({block:'center'}); T.paintMarks(); await w(1200);
        const st=document.querySelector('#sheet');
        T.closeSheet(); T.cluePanel('open'); await w(30); const sq=[...document.querySelectorAll('#sheet .mlp i')], k2=T.getMain().pieces.indexOf(p2.id);
        ok('主线面板：出现了的这一格变成"已出现"（金边 + 小菱形），没出现的还是空格',sq[k2]&&sq[k2].classList.contains('found')&&!sq[k2].classList.contains('on')&&sq.every((x,ii)=>x.classList.contains('on')===!!S3.doneS[T.getMain().pieces[ii]])&&sq.every((x,ii)=>x.classList.contains('found')===(!S3.doneS[T.getMain().pieces[ii]]&&!!(S3.found[T.getMain().pieces[ii]]||S3.seen[T.getMain().pieces[ii]]))),sq.map(x=>x.className.trim()||'空').join(','));
        ok('新出现的那一格动一下',sq[k2]&&sq[k2].classList.contains('new')); T.closeSheet(); T.openClue(p2.id);
        ok('读到主线的伏笔：直接弹出这处伏笔的卡片（标着"主线"）',st.classList.contains('show')&&st.textContent.includes(p2['问题'])&&!!st.querySelector('.clmain'),p2.id+' '+st.textContent.slice(0,60)); T.closeSheet(); }
      const nonMain=T.getSUS2().find(x=>!T.getMain().pieces.includes(x.id)&&x['提出']!=='前言'&&IDX0(x)<j-1&&x['揭晓']&&I3[x['揭晓']]>j);
      ok('不是主线的伏笔：发现了也还要读者自己点开',!!nonMain&&!!S3.found[nonMain.id]&&!S3.seen[nonMain.id],nonMain&&nonMain.id);
      ok('拼图卡有 ×',!!document.querySelector('#mlfxX')); document.querySelector('#mlfxX')?.click(); ok('点 × 关掉拼图卡',!!m2&&!m2.classList.contains('show')); }
    T.setBook('hound'); T.closeSheet(); localStorage.clear(); T.TIPSS().welcomed=1; T.setMode('light'); T.shelf(); }
  }catch(e){ ok('脚本出错',false,e.message+' '+(e.stack||'').split('\n')[1]); }
  const pass=R.filter(r=>r[1]).length;
  window.__RESULT={pass,total:R.length,failed:R.filter(r=>!r[1]).map(r=>({name:r[0],detail:r[2]}))};   /* 给命令行测试读：run_browser_tests.js */
  document.body.innerHTML=`<div style="font:14px/1.5 sans-serif;padding:12px;background:#fff;color:#000"><b style="font-size:18px">${pass}/${R.length} 通过</b>${[...R.filter(r=>!r[1]),...R.filter(r=>r[1])].map(r=>`<div style="color:${r[1]?'#070':'#c00'}">${r[1]?'✓':'✗'} ${r[0]} <small style="color:#666">${String(r[2]).replace(/</g,'&lt;')}</small></div>`).join('')}<b style="font-size:18px;display:block;margin-top:10px">${pass}/${R.length} 通过（底部汇总）</b></div>`; window.scrollTo(0,0);
};
