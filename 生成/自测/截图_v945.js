/* v9.45 截图：window.__SHOT = reg / quiz / piece / last / uend / clue */
window.__TEST=async T=>{ const w=ms=>new Promise(r=>setTimeout(r,ms)); localStorage.clear(); const V=window.__SHOT; const A=T.ACC(), PF=T.PROF(); A.users={}; A.cur=null; PF.qz=null;
  T.TIPSS().hinted=1; T.TIPSS().tipFound=1;
  if(V==='reg'){ T.authPage('reg'); return; }
  A.users['13800001234']={name:'读者1234',pw:'x',t:Date.now()}; A.cur='13800001234';
  if(V==='quiz'){ T.quizPage({first:true}); await w(20); document.querySelector('.qzo [data-v="half"]').click(); await w(350); document.querySelector('.qzo [data-v="people"]').click(); return; }
  PF.qz={q1:'half',q2:['people'],q3:'auto',t:Date.now()}; T.setMode('light');
  T.shelf(); T.openBook('hound'); await w(900); T.closeSheet(); const IX=T.getIDX(), S=T.getS(), M=T.getMain(); S.mainSeen=1; document.querySelector('#toast').classList.remove('show');
  if(V==='piece'){ ['B04','B07','B22'].forEach(id=>S.doneS[id]=S.seen[id]=S.found[id]=Date.now()); T.markRd(0,IX['10.60']); T.noRead(3000); T.els()[IX['10.58']].scrollIntoView({block:'start'}); await w(200); T.mainReveal('B22'); return; }
  if(V==='last'){ M.pieces.forEach(id=>S.doneS[id]=S.seen[id]=S.found[id]=Date.now()); T.markRd(0,IX['15.12']); T.noRead(3000); T.els()[IX['15.10']].scrollIntoView({block:'start'}); await w(200); T.mainReveal('B05'); await w(1800); return; }
  if(V==='uend'){ T.markRd(0,IX['2.2']); T.paintUEnd(); T.noRead(3000); document.querySelector('.uend[data-u="1"]').scrollIntoView({block:'center'}); return; }
  if(V==='clue'){ ['B04','B07','B22','B14'].forEach(id=>S.doneS[id]=S.seen[id]=S.found[id]=Date.now()); T.markRd(0,IX['12.80']); S.current=IX['12.80']; T.cluePanel('done'); return; }
};
