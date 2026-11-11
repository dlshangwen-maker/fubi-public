/* v9.46 截图：window.__SHOT = reg / quiz / quizdone / toast / ol / ml */
window.__TEST=async T=>{ const w=ms=>new Promise(r=>setTimeout(r,ms)); localStorage.clear(); const V=window.__SHOT; const A=T.ACC(), PF=T.PROF(); A.users={}; A.cur=null; PF.qz=null;
  T.TIPSS().hinted=1; T.TIPSS().tipFound=1;
  if(V==='reg'){ T.authPage('reg'); return; }
  A.users['13800001234']={name:'读者1234',pw:'x',t:Date.now()}; A.cur='13800001234';
  if(V==='quiz'){ T.quizPage({first:true}); await w(20); document.querySelector('.qzchips [data-v="half"]').click(); await w(400); document.querySelector('.qzchips [data-v="people"]').click(); return; }
  if(V==='quizdone'){ T.quizPage({first:true}); await w(20); document.querySelector('.qzchips [data-v="half"]').click(); await w(400); document.querySelector('.qzchips [data-v="people"]').click(); document.querySelector('#qzNext').click(); await w(20); document.querySelector('.qzchips [data-v="auto"]').click(); return; }
  PF.qz={q1:'half',q2:['people'],q3:'auto',t:Date.now()}; T.setMode('heavy');
  T.shelf(); T.openBook('hlm'); await w(900); T.closeSheet(); const IX=T.getIDX(), S=T.getS(); S.mainSeen=1; document.querySelector('#toast').classList.remove('show');
  if(V==='toast'){ T.markRd(0,IX['1.33']); T.noRead(3000); T.els()[IX['1.32']].scrollIntoView({block:'start'}); await w(100); document.querySelector('#toast').classList.remove('show'); T.reveal&&0;
    const t=document.querySelector('#toast'); t.innerHTML=''; await w(10); window.__x=1; S.seen.H02=1; S.doneS.H02=0; return; }
  if(V==='ol'){ T.markRd(0,IX['3.20']); S.current=IX['3.20']; T.outline('hui'); return; }
};
