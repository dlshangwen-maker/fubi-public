/* v9.44 截图：window.__SHOT = reg / q1 / q2 / done / me / month / clue / card */
window.__TEST=async T=>{ const w=ms=>new Promise(r=>setTimeout(r,ms)); localStorage.clear(); const V=window.__SHOT; const A=T.ACC(), PF=T.PROF(); A.users={}; A.cur=null; PF.days={}; PF.qz=null;
  const d0=new Date(); for(let i=0;i<70;i++){ if(i%5===4) continue; const d=new Date(d0); d.setDate(d.getDate()-i); PF.days[d.getFullYear()+'-'+(d.getMonth()+1)+'-'+d.getDate()]={ms:(8+i%9*3)*6e4,n:5,sv:i%4===1?1:0}; }
  T.TIPSS().hinted=1; T.TIPSS().tipFound=1;
  if(V==='reg'){ T.authPage('reg'); return; }
  A.users['13800001234']={name:'读者1234',pw:'x',t:Date.now()-80*864e5}; A.cur='13800001234';
  if(V==='q1'){ T.quizPage({first:true}); return; }
  if(V==='q2'){ T.quizPage({first:true}); await w(20); document.querySelector('.qzo [data-v="half"]').click(); await w(350); document.querySelector('.qzo [data-v="people"]').click(); return; }
  if(V==='done'){ PF.qz={q1:'half',q2:['people'],q3:'auto'}; T.setMode('heavy'); T.quizResult('heavy',true); return; }
  PF.qz={q1:'half',q2:['people','bored'],q3:'auto',t:Date.now()}; T.setMode('light');
  if(V==='me'){ T.mePage(); return; }
  if(V==='month'){ T.mePage(); await w(20); document.querySelector('#calTg').click(); return; }
  T.shelf(); T.openBook(V==='clue'?'nahan':'hound'); await w(900); T.closeSheet();
  if(V==='clue'){ T.cluePanel('open'); return; }
  if(V==="card"){ T.openCard(3); await w(50); const d=document.querySelector("#sheet details.ogq"); if(d){ d.open=true; d.scrollIntoView({block:"center"}); } return; }
};
