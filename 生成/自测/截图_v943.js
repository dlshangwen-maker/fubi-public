/* v9.43 截图：window.__SHOT = reg / quiz / me / month / pref / guide / soon / unit */
window.__TEST=async T=>{ const w=ms=>new Promise(r=>setTimeout(r,ms)); localStorage.clear(); const V=window.__SHOT; const A=T.ACC(), PF=T.PROF(); A.users={}; A.cur=null; PF.days={}; PF.qz=null;
  const d0=new Date(); for(let i=0;i<20;i++){ if(i===4||i===11) continue; const d=new Date(d0); d.setDate(d.getDate()-i); PF.days[d.getFullYear()+'-'+(d.getMonth()+1)+'-'+d.getDate()]={ms:(8+i*2)*6e4,n:5,sv:i%3===1?1:0}; }
  T.TIPSS().hinted=1; T.TIPSS().tipFound=1;
  if(V==='reg'){ T.authPage('reg'); return; }
  A.users['13800001234']={name:'周小舟',pw:'x',t:Date.now()-6*864e5}; A.cur='13800001234';
  if(V==='quiz'){ T.quizPage({first:true}); await w(30); document.querySelector('.qzo[data-q="q1"] [data-v="half"]').click(); return; }
  PF.qz={q1:'half',q2:['people','bored'],q3:'auto',t:Date.now()}; T.setMode('heavy');
  if(V==='me'){ T.mePage(); return; }
  if(V==='month'){ T.mePage(); await w(20); document.querySelector('#calTg').click(); return; }
  if(V==='pref'){ T.prefPage(); return; }
  if(V==='guide'){ T.shelf(); T.openBook('hound'); return; }
  T.shelf(); T.openBook('hound'); await w(900); T.closeSheet(); const IX=T.getIDX(), S=T.getS(), P=T.P();
  if(V==='soon'){ const j=IX['10.25']; let c=j-1,ch=0; while(ch+P[c].zh.length<=700){ ch+=P[c].zh.length; c--; }
    T.markRd(0,c-1); S.found.B07=Date.now(); T.save(); T.noRead(1500); T.els()[c].scrollIntoView({block:'center'}); await w(1700); for(let k=0;k<5;k++){ scrollBy(0,90); await w(200); } return; }
  if(V==='unit'){ T.markRd(0,IX['2.1']); S.current=IX['1.62']; S.uDone={}; T.noRead(1); await w(60); T.els()[IX['2.1']].scrollIntoView({block:'start'}); scrollBy(0,-80); await w(100); T.setPos(IX['2.1']); return; }
};
