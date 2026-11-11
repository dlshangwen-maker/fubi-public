/* 服务端模式的阅读器自测：页面由 server/app.py 的 page() 生成（带 window.FUBI 和一本导入的书），
   预览面板里没有服务器，所以 fetch 用桩代替，只检查阅读器这边的逻辑。
   用法：python3 -I 生成/自测/服务端页面.py  → outputs/自测_服务端.html */
window.confirm=()=>true; window.alert=()=>{};
window.__FETCH=[]; window.fetch=async(u,o={})=>{ window.__FETCH.push([u,o.method||'GET',o.body]);
  const J=x=>({ok:true,status:200,json:async()=>x});
  if(u==='/api/ask') return J({'类型':'读过的','回答':'（桩）答案在你读过的地方。','引用':[],'回收':'','回收说明':'','回收锚句':''});
  if(u==='/api/state') return J({ok:true});
  if(u==='/api/hot') return J({hot:window.__HOT});
  if(u.startsWith('/api/search')){ const q=decodeURIComponent(u.split('q=')[1]); return J(q==='红楼梦'?window.__FOUND_HLM:q==='西游记'?window.__FOUND_XY:q==='傲慢与偏见'?window.__FOUND:{q,results:[],builtin:[],errors:[]}); }
  if(u==='/api/import'){ if(window.__IMPFAIL) return {ok:false,status:400,json:async()=>({error:'文件已损坏，打不开'})}; return J({id:window.FUBI_DL,status:'ready'}); }
  if(u==='/api/download') return J({id:window.FUBI_DL,status:'ready'});
  if(u==='/api/preview') return J({'书名':'西遊記','作者':'吳承恩','章数':1,'字数':1200,'目录':['第一回 灵根育孕源流出'],'开头章':'第一回 灵根育孕源流出','开头':['话说天下四大部洲。话说天下四大部洲。'],'来源':'wikisource','编号':'西遊記'});
  if(u==='/api/books/'+window.FUBI_DL+'/status') return J({status:'ready'});
  if(u==='/api/books/'+window.FUBI_DL) return J(window.__DL);
  if(u.endsWith('/chapters')) return J(JSON.parse(JSON.stringify(window.__MERGED)));
  return J({ok:true}); };
window.__TEST=async T=>{
  const R=[]; const ok=(n,c,x='')=>R.push([n,!!c,x]); const w=ms=>new Promise(r=>setTimeout(r,ms));
  try{
    T.shv().lay='list'; T.shv().sort='manual'; T.shv().order=[]; T.shelf(); await w(50);
    const books=[...document.querySelectorAll('.book')];
    ok('书架：五本精编书 + 两本导入的书 + 一本找书下载的书',books.length===8,books.length);
    ok('导入的书在精编书后面，显示书名',books[5]&&books[5].textContent.includes('测试小说'),books[5]&&books[5].textContent.slice(0,40));
    const covB=books.find(b=>b.textContent.includes('有封面的书'));
    ok('带封面的书：书架上显示书自带的封面',!!covB&&!!covB.querySelector('.cover.img img')&&covB.querySelector('img').getAttribute('src')===`/api/books/${window.FUBI_COV}/cover`);
    ok('没封面的书：按书名生成',!!books[5].querySelector('.cover.gen'));
    const libB=books.find(b=>b.textContent.includes('傲慢与偏见'));
    ok('找书下载的书在书架上，带书自带的封面',!!libB&&!!libB.querySelector('.cover.img'),libB&&libB.textContent.slice(0,40));
    ok('书架标题右边并列"找书 · 导入"两个小字入口',document.querySelector('.shh .shacts')?.textContent.replace(/\s/g,'')==='找书·导入'&&!!document.querySelector('#impBtn'));
    ok('书架底部没有大按钮',!document.querySelector('.impbox .btn')&&!document.querySelector('.btn.wide#impBtn'));
    document.querySelector('#impBtn').click(); await w(30);
    ok('点"导入"进独立页面（不是直接弹文件选择）：有标题、选择文件、格式说明',document.querySelector('.pgbar b').textContent==='导入'&&!!document.querySelector('#impDrop')&&document.querySelector('.impdrop small').textContent.includes('常用格式')&&document.querySelector('.impdrop small').textContent.includes('MB'));
    ok('导入页：会发生什么三步、版权提醒、去找书',document.querySelectorAll('.impsteps li').length===3&&document.querySelector('.impnote').textContent.includes('有权阅读')&&!!document.querySelector('#impFind'));
    ok('导入引导：外文书自动译成中文、按书面语高水准翻译、译完才能读、显示加载中',document.querySelectorAll('.impsteps li')[1].textContent.includes('自动译成中文')&&document.querySelectorAll('.impsteps li')[1].textContent.includes('高水准')&&document.querySelectorAll('.impsteps li')[1].textContent.includes('译完才能读')&&document.querySelectorAll('.impsteps li')[1].textContent.includes('加载中'));
    ok('导入引导：调整章节写真实路径（导览里点"调整章节"），不再说"阅读设置 › 更多设置"',document.querySelectorAll('.impsteps li')[0].textContent.includes('导览')&&!document.querySelector('.impsteps').textContent.includes('更多设置'));
    ok('导入能选的格式包括 pdf、epub、mobi',['.pdf','.epub','.mobi'].every(x=>document.querySelector('#impFile').accept.includes(x)));
    { const pick=async name=>{ const f=new File(['x'.repeat(10)],name,{type:'text/plain'}); Object.defineProperty(document.querySelector('#impFile'),'files',{value:[f],configurable:true}); document.querySelector('#impFile').dispatchEvent(new Event('change')); await w(500); };
      await pick('测试书.txt');
      ok('选了文件：页内显示结果——放进书架，写章数字数，有"去读""再导入一本"',document.querySelector('#impStat').classList.contains('ok')&&document.querySelector('#impStat').textContent.includes('已放进书架')&&!!document.querySelector('#imGo')&&!!document.querySelector('#imMore'),document.querySelector('#impStat').textContent.slice(0,50));
      document.querySelector('#imMore').click(); await w(30); window.__IMPFAIL=true; await pick('坏文件.epub'); window.__IMPFAIL=false;
      ok('导入失败：页内写原因，有"重新选择文件"，不丢页面',document.querySelector('#impStat').classList.contains('failed')&&document.querySelector('#impStat').textContent.includes('已损坏')&&!!document.querySelector('#imRetry'),document.querySelector('#impStat').textContent.slice(0,50)); }
    document.querySelector('#pgBack').click(); await w(30);
    ok('导入失败的书显示原因和"移除"',document.querySelector('.impend.failed')?.textContent.includes('损坏')&&!!document.querySelector('[data-del]'));
    ok('书架底部没有多余提示，也不对读者说"保存在服务器上"这类话',!document.querySelector('.shelf .foot')&&!document.querySelector('.shelf').textContent.includes('服务器')&&!document.querySelector('.shelf').textContent.includes('长按'));
    { const d=JSON.parse(JSON.stringify(window.__DL)); d.meta=Object.assign({},d.meta,{foreign:true,title:'外文测试书',gen:{done:2,total:9}}); d.untranslated=true;
      T.addBusyBook('busy1',d); T.shelf(); await w(20);
      const row=document.querySelector('#bookList .book[data-k="busy1"]');
      ok('外文书没译完：书架上封面有加载中，写明"翻译中"',!!row&&row.classList.contains('busy')&&!!row.querySelector('.ldg')&&row.textContent.includes('翻译中'),row&&row.textContent.slice(0,30));
      if(row){ row.click(); await w(30); ok('点没处理完的书：进不了阅读器，显示书籍详情，按钮不能点',!document.querySelector('#text')&&document.querySelector('#sheet').classList.contains('show')&&document.querySelector('#bOpen').disabled&&document.querySelector('#bOpen').textContent.includes('处理中'),document.querySelector('#bOpen')&&document.querySelector('#bOpen').textContent); }
      T.closeSheet(); d.untranslated=false; T.addBusyBook('busy1',d,true); T.shelf(); await w(20);
      ok('处理完（译完）：自动变成可读',!document.querySelector('#bookList .book[data-k="busy1"]').classList.contains('busy')); }
    T.setShEdit(true); T.shelf(); await w(20); const own=document.querySelector('.book .sel'); ok('整理：自己导入的书可以选中',!!own); T.setShEdit(false); T.shelf(); await w(20);
    const k=window.FUBI_IMP;
    T.bookInfo(k,'尚未开始'); await w(20); let t=document.querySelector('#sheet').textContent;
    ok('导入的书：详情页有来源、篇幅、生成情况',t.includes('你导入的文件')&&t.includes('5 章')&&t.includes('解释与回顾'),t.slice(0,120));
    ok('导入的书：详情页能"从书架移除"',!!document.querySelector('#bDel')); T.closeSheet();
    { const k=window.FUBI_IMP; T.removeBooks([k]); await w(30); ok('移除书：先从书架拿下来，提示条可撤销',!document.querySelector(`.book[data-k="${k}"]`)&&document.querySelector('#toast').textContent.includes('撤销'));
      document.querySelector('#toast button:not(.tx)').click(); await w(30); ok('撤销后书回到书架，没有真的删除',!!document.querySelector(`.book[data-k="${k}"]`)&&!window.__FETCH.some(f=>f[1]==='DELETE'&&f[0].includes(k))); }
    T.openBook(k); await w(500); T.closeSheet();
    const els=T.els(); ok('导入的书能打开、段落都在',els.length>20,els.length);
    ok('章名直接当标题（不写"第几章"再重复）',document.querySelector('#where').textContent.includes('第一章 风起一')||document.querySelector('.hui h2').textContent.includes('第一章'),document.querySelector('#where').textContent);
    // 卡片：第一章生成了，第五章还没有
    T.openCard(0); await w(20); t=document.querySelector('#sheet').textContent;
    ok('生成过解释的段落：正常打开卡片',t.includes('入门')&&t.includes('这一章写'),t.slice(0,80)); T.closeSheet();
    const last=els.length-1; T.openCard(last); await w(20); t=document.querySelector('#sheet').textContent;
    ok('还没生成解释的段落：说明"还没有生成"，不报错',t.includes('还没有生成')&&t.includes('划线'),t.slice(0,80)); T.closeSheet();
    // 记录同步到服务器
    window.__FETCH.length=0; T.markRd(0,5); T.getS().current=5; T.save(); await w(1800);
    const put=window.__FETCH.find(f=>f[0]==='/api/state'&&f[1]==='PUT');
    ok('读了几段：1.5 秒内把记录同步到服务器',!!put&&put[2].includes(T.getS().key||'rb_imp_'),put?put[2].slice(0,60):'没有请求');
    ok('同步的是这本书的记录',!!put&&JSON.parse(put[2])[window.FUBI_KEY]&&JSON.parse(put[2])[window.FUBI_KEY].rd.length>=6);
    // 自由提问：没有预先写好的回答 → 问服务器
    window.__FETCH.length=0; T.askQuestion(null,'他为什么要拆那封信？',{at:5}); await w(300);
    ok('自由提问发到服务器 /api/ask，带书和阅读位置',window.__FETCH.some(f=>f[0]==='/api/ask'&&JSON.parse(f[2]).book===k&&JSON.parse(f[2]).pos));
    t=document.querySelector('#sheet').textContent;
    ok('自动生成的回答显示出来，并注明"自动生成，可能有误"',t.includes('（桩）答案在你读过的地方')&&t.includes('自动生成'),t.slice(0,100));
    ok('问过的回答记在这本书里（下次打开还在）',(T.getS().aiqa||[]).length===1);
    T.closeSheet();
    // 找书：只有搜索框 + 热门搜索；搜到的书下载到书架
    T.shelf(); document.querySelector('#shLib').click(); await w(300);
    ok('找书：页面只有搜索框和热门搜索',!!document.querySelector('#libQ')&&document.querySelector('.libh')?.textContent==='热门搜索'&&document.querySelectorAll('.hotw button').length===12,document.querySelectorAll('.hotw button').length);
    ok('找书：没有书单、分组',!document.querySelector('.fbook')&&!document.querySelector('.libg'));
    ok('找书：左上角能回书架',document.querySelector('#pgBack')?.textContent.includes('书架'));
    [...document.querySelectorAll('.hotw button')].find(b=>b.textContent==='西游记').click(); await w(300);
    ok('点热门搜索词就搜这个词',document.querySelector('#libQ').value==='西游记'&&window.__FETCH.some(f=>f[0]==='/api/search?q='+encodeURIComponent('西游记')));
    let rows=[...document.querySelectorAll('.fbook')], pv=rows[0]?rows[0].textContent:'';
    ok('搜索结果直接显示书的信息和介绍（不用点开，不显示原文）',pv.includes('西遊記')&&pv.includes('唐僧师徒')&&!pv.includes('话说天下四大部洲')&&!document.querySelector('#sheet').classList.contains('show'),pv.slice(0,80));
    const srcs=[...rows[0].querySelectorAll('.fsrc')];
    ok('下面直接列出几个下载来源，每个有自己的"下载"',srcs.length>=1&&srcs.every(x=>x.querySelector('[data-dl]'))&&rows[0].querySelector('.fsh')?.textContent==='下载来源',srcs.map(x=>x.textContent).join('|'));
    ok('结果：书名、来源、语言',rows.length===1&&rows[0].textContent.includes('西遊記')&&rows[0].textContent.includes('维基文库')&&rows[0].textContent.includes('中文'),rows.map(r=>r.textContent.slice(0,30)).join('|'));
    window.__FETCH.length=0; rows[0].querySelector('[data-dl]').click(); await w(500);
    const dl=window.__FETCH.find(f=>f[0]==='/api/download');
    ok('下载到书架：发几个来源（按顺序试），只有来源和编号、不发网址',!!dl&&JSON.parse(dl[2]).sources[0]['来源']==='wikisource'&&JSON.parse(dl[2]).sources[0]['编号']==='西遊記'&&!/http/.test(dl[2]),dl&&dl[2]);
    ok('下载完：变成"已在书架上 · 去读"，提示可以去读',document.querySelector('.fbook').textContent.includes('已在书架上')&&document.querySelector('#toast').textContent.includes('已下载到书架'),document.querySelector('.fbook').textContent.slice(-20)+' | '+document.querySelector('#toast').textContent);
    const q=document.querySelector('#libQ'); q.value='傲慢与偏见'; document.querySelector('#libF').dispatchEvent(new Event('submit',{cancelable:true})); await w(300);
    rows=[...document.querySelectorAll('.fbook')];
    ok('外文书：中文名在上、原名在下，写"下载后翻译成中文"',rows[0]&&rows[0].querySelector('b').textContent==='傲慢与偏见'&&rows[0].textContent.includes('Pride and Prejudice')&&rows[0].textContent.includes('下载后翻译成中文'));
    ok('已经下载过的书显示"已在书架上"',rows[0]&&rows[0].textContent.includes('已在书架上'));
    const off=rows.find(r=>r.classList.contains('off'));
    ok('作者去世不满 50 年：列出来但不能下载，写明原因',!!off&&!off.querySelector('[data-dl]')&&off.textContent.includes('还没进入公版'),off&&off.textContent.slice(0,80));
    q.value='红楼梦'; document.querySelector('#libF').dispatchEvent(new Event('submit',{cancelable:true})); await w(300);
    ok('搜到精编书：排最前，"精读版"、"已在书架上"',document.querySelector('.fbook')?.textContent.includes('精读版')&&document.querySelector('.fbook').textContent.includes('已在书架上'));
    q.value='哈利波特'; document.querySelector('#libF').dispatchEvent(new Event('submit',{cancelable:true})); await w(300);
    ok('搜不到：说明能搜到什么，指向导入',document.querySelector('.libnone')?.textContent.includes('哈利波特')&&document.querySelector('.lib').textContent.includes('导入'));
    q.value=''; q.dispatchEvent(new Event('input')); await w(50);
    ok('清空搜索框：回到热门搜索',!!document.querySelector('.hotw'));
    document.querySelector('#pgBack').click(); await w(100);
    ok('回到书架，新下载的书在书架上',[...document.querySelectorAll('.book')].some(b=>b.textContent.includes('西遊記')));
    T.bookInfo(window.FUBI_LIB,'尚未开始'); await w(20); t=document.querySelector('#sheet').textContent;
    ok('下载的书：详情写"从古登堡计划下载（公版），中文由本应用从原文翻译"',t.includes('从古登堡计划下载')&&t.includes('从原文翻译'),t.slice(0,120));
    ok('外文书还没翻译：详情写"尚未翻译"',t.includes('尚未翻译'));
    T.closeSheet();
    // 调整章节（只有自己导入的书）
    T.openBook('hound'); await w(400); T.closeSheet(); T.settings('more'); await w(20);
    ok('精编书：设置里没有"调整章节"',!document.querySelector('#chEdit')); T.closeSheet();
    { const dd=JSON.parse(JSON.stringify(window.__DL)); dd.untranslated=false; dd.meta=Object.assign({},dd.meta,{foreign:false}); T.addBusyBook(window.FUBI_LIB,dd,true); }   /* 下载的外文书译完后才能读 */
    T.shelf(); T.openBook(window.FUBI_LIB); await w(400); T.closeSheet(); T.settings('more'); await w(20);
    ok('下载的书：设置里也有"调整章节"',!!document.querySelector('#chEdit')); T.closeSheet();
    T.shelf(); T.openBook(k); await w(400); T.closeSheet(); T.settings('more'); await w(20);
    ok('导入的书：设置里有"调整章节"',!!document.querySelector('#chEdit'));
    T.closeSheet(); T.outline('hui'); await w(20); ok('导入的书：导览里也有"调整章节"（章节分得不准？）',!!document.querySelector('#olChap')); T.closeSheet(); T.settings('more'); await w(20);
    document.querySelector('#chEdit').click(); await w(20);
    const rowsC=[...document.querySelectorAll('#sheet .chrow')];
    ok('调整章节：每章一行，章名可改，从第二章起能"并入上一章"',rowsC.length===5&&!rowsC[0].querySelector('[data-merge]')&&!!rowsC[1].querySelector('[data-merge]'),rowsC.length);
    rowsC[0].querySelector('.chname').value='开头'; rowsC[1].querySelector('[data-merge]').click();
    ok('点"并入上一章"：这一行变灰，可以取消',rowsC[1].classList.contains('merged')&&rowsC[1].textContent.includes('取消合并'));
    { const S0=T.getS(); T.markRd(0,12); S0.notes.push({id:S0.nid++,type:'q',at:3,text:'测试',rv:'2.3',done:false,t:Date.now()}); T.save(); }
    window.__FETCH.length=0; document.querySelector('#chSave').click(); await w(400);
    const cf=window.__FETCH.find(f=>f[0].endsWith('/chapters'));
    ok('保存：发出合并 + 改名两条',!!cf&&JSON.parse(cf[2]).ops.some(o=>o.op==='merge'&&o.ch===2)&&JSON.parse(cf[2]).ops.some(o=>o.op==='rename'&&o.title==='开头'),cf&&cf[2]);
    ok('保存后：书里变成 4 章，第一章叫"开头"',T.getS()&&document.querySelectorAll('.hui').length===4&&document.querySelector('.hui h2').textContent.includes('开头'),document.querySelectorAll('.hui').length);
    ok('保存后：读过的段落不变（按段落先后记的）',T.getRD().size>=13);
    const mq=T.getS().notes.find(n=>n.text==='测试');
    ok('保存后：按段号记的答案位置跟着改（2.3 → 新段号）',!!mq&&mq.rv===window.__MERGED.idmap['2.3']&&mq.rv!=='2.3',mq&&mq.rv);
    T.openCard(T.els().length-1); await w(20);
    ok('解释卡片底部有"从这里分章"',!!document.querySelector('#cSplit')); T.closeSheet();
    // 精编书照常
    T.shelf(); T.openBook('hound'); await w(600); T.closeSheet();
    ok('精编书照常打开',T.els().length>500,T.els().length);
    T.openCard(3); await w(20); ok('精编书卡片照常',document.querySelector('#sheet').textContent.includes('入门')); T.closeSheet();
    T.shelf();
  }catch(e){ ok('脚本出错',false,e.message+' '+(e.stack||'').split('\n')[1]); }
  const pass=R.filter(r=>r[1]).length;
  window.__RESULT={pass,total:R.length,failed:R.filter(r=>!r[1]).map(r=>({name:r[0],detail:r[2]}))};   /* 给命令行测试读：run_browser_tests.js */
  document.body.innerHTML=`<div style="font:14px/1.5 sans-serif;padding:12px;background:#fff;color:#000"><b style="font-size:18px">服务端模式 ${pass}/${R.length} 通过</b>${[...R.filter(r=>!r[1]),...R.filter(r=>r[1])].map(r=>`<div style="color:${r[1]?'green':'red'}">${r[1]?'✓':'✗'} ${r[0]} <small style="color:#666">${String(r[2]).replace(/</g,'&lt;')}</small></div>`).join('')}</div>`;
  setTimeout(()=>window.scrollTo(0,0),50);
};
