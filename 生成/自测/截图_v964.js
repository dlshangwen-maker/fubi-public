/* v9.64 截图：window.__SHOT = card / clues / clue / guess / reveal / notes / set / outline / info / me / exp / last */
window.__TEST=async T=>{ const w=ms=>new Promise(r=>setTimeout(r,ms)); localStorage.clear(); const V=window.__SHOT; const A=T.ACC(), PF=T.PROF();
  A.users={'13800001234':{name:'读者1234',pw:'x',t:Date.now()-20*864e5}}; A.cur='13800001234'; PF.qz={q1:'often',q2:['people'],q3:'less',t:Date.now()}; T.setMode('light');
  T.TIPSS().hinted=1; T.TIPSS().tipFound=1;
  if(V==='me'){ T.mePage(); return; }
  T.shelf(); T.openBook('hlm'); await w(900); T.closeSheet(); const IX=T.getIDX(), S=T.getS(); S.mainSeen=1;
  T.markRd(0,IX['1.33']); S.current=IX['1.20']; S.vis=IX['1.33'];
  ['H01','H02','H03'].forEach(id=>{ S.found[id]=S.seen[id]=Date.now(); }); S.doneS.H02=Date.now(); S.guesses.H02={text:'英莲会遭难，并连累家里。',conf:6};
  const u=T.addUL([{c:'p'+IX['1.3'],s:0,e:18}]); S.notes.push({id:S.nid++,type:'note',hl:u,parts:[{c:'p'+IX['1.3'],s:0,e:18}],at:IX['1.3'],text:'作者先把自己摆出来，像在说这本书不是闲书。',t:Date.now()});
  S.notes.push({id:S.nid++,type:'q',at:IX['1.9'],text:'一僧一道和梦里的僧道是同一对人吗？',done:false,t:Date.now()}); S.bm[IX['1.12']]=Date.now(); T.save(); T.paintUL(); T.paintMarks();
  document.querySelector('#toast').classList.remove('show');
  if(V==='last'){ S.seenAt=Date.now()-3*864e5; T.save(); T.shelf(); T.openBook('hlm'); await w(900); document.querySelector('#toast').classList.remove('show'); document.querySelector('#llMore')?.click(); document.querySelector('#lastLine')?.scrollIntoView({block:'start'}); window.scrollBy(0,-90); return; }
  if(V==='card'){ T.openCard(IX['1.15']); return; }
  if(V==='clues'){ T.cluePanel('open'); return; }
  if(V==='clue'){ T.openClue('H01',false,()=>T.cluePanel('open')); return; }
  if(V==='guess'){ T.openClue('H01'); await w(20); document.querySelector('#cg').click(); return; }
  if(V==='reveal'){ T.reveal('H02',false,()=>T.cluePanel('done')); return; }
  if(V==='notes'){ T.minePanel('all'); return; }
  if(V==='set'){ T.settings(); return; }
  if(V==='outline'){ T.outline('hui'); return; }
  if(V==='info'){ T.shelf(); await w(30); T.bookInfo('hlm',T.bookStat('hlm').prog); return; }
  if(V==='exp'){ T.exportSheet(); return; }
};
