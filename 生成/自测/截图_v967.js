/* v9.67 截图：window.__SHOT = guest / shelf / notes / arc / outline / info / me / sec / set */
window.__TEST=async T=>{ const w=ms=>new Promise(r=>setTimeout(r,ms)); localStorage.clear(); const V=window.__SHOT, A=T.ACC(), PF=T.PROF(); window.__GUESTCHK=true;
  A.users={}; A.cur=null; PF.qz=null;
  if(V==='guest'){ T.shelf(); return; }
  A.users['13800001234']={name:'读者1234',pw:'x',t:Date.now()-20*864e5}; A.cur='13800001234'; PF.qz={q1:'often',q2:['people'],q3:'less',t:Date.now()}; T.setMode('light');
  const dk=d=>d.getFullYear()+'-'+(d.getMonth()+1)+'-'+d.getDate(); const d0=new Date(); for(let i=1;i<=9;i++){ if(i%3===0) continue; const d=new Date(d0); d.setDate(d.getDate()-i); PF.days[dk(d)]={ms:(8+i*3)*6e4,n:4,sv:i===2?1:0}; }
  if(V==='me'){ T.mePage(); return; }
  if(V==='sec'){ T.secPage(); return; }
  T.shelf(); T.openBook('hlm'); await w(900); T.closeSheet(); const IX=T.getIDX(), S=T.getS(); S.mainSeen=1;
  T.markRd(0,IX['1.33']); S.current=IX['1.20']; S.vis=IX['1.33'];
  ['H01','H02'].forEach(id=>{ S.found[id]=S.seen[id]=Date.now(); }); S.doneS.H02=Date.now(); S.guesses.H02={text:'英莲会遭难，并连累家里。',conf:6};
  const u=T.addUL([{c:'p'+IX['1.3'],s:0,e:18}]); S.notes.push({id:S.nid++,type:'note',hl:u,parts:[{c:'p'+IX['1.3'],s:0,e:18}],at:IX['1.3'],text:'作者先把自己摆出来，像在说这本书不是闲书。',t:Date.now()});
  S.notes.push({id:S.nid++,type:'q',at:IX['1.9'],text:'一僧一道和梦里的僧道是同一对人吗？',done:false,t:Date.now()}); T.save(); T.paintUL(); T.paintMarks();
  document.querySelector('#toast').classList.remove('show');
  if(V==='notes'){ T.minePanel('all'); return; }
  if(V==='arc'){ T.minePanel('arc'); return; }
  if(V==='outline'){ T.outline('hui'); return; }
  if(V==='set'){ T.settings('more'); return; }
  if(V==='info'){ T.shelf(); await w(30); T.bookInfo('hlm',T.bookStat('hlm').prog); return; }
  T.shelf();
};
