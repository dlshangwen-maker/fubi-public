/* v9.55 截图：window.__SHOT = reg / shelf / read（红楼梦第一回读到伏笔） / clues（伏笔页） */
window.__TEST=async T=>{ const w=ms=>new Promise(r=>setTimeout(r,ms)); localStorage.clear(); const V=window.__SHOT; const A=T.ACC(), PF=T.PROF(); A.users={}; A.cur=null; PF.qz=null;
  T.TIPSS().hinted=1; T.TIPSS().tipFound=1;
  if(V==='reg'){ T.authPage('reg'); return; }
  A.users['13800001234']={name:'读者1234',pw:'x',t:Date.now()}; A.cur='13800001234';
  PF.qz={q1:'often',q2:['people'],q3:'less',t:Date.now()}; T.setMode('light');
  if(V==='shelf'){ T.shelf(); return; }
  T.shelf(); T.openBook('hlm'); await w(900); T.closeSheet(); const IX=T.getIDX(), S=T.getS(); S.mainSeen=1; document.querySelector('#toast').classList.remove('show');
  T.markRd(0,IX['1.16']); S.current=IX['1.16']; S.found.H02=Date.now(); S.ul=[]; T.save();
  T.els()[IX['1.15']].scrollIntoView({block:'start'}); await w(600); document.querySelector('#toast').classList.remove('show');
  if(V==='clues'){ T.cluePanel('open'); }
};
