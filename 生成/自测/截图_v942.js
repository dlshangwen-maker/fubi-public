/* v9.42 截图用：URL 里的 #quiz / #me / #clue / #end / #uend 决定停在哪个画面（注入方法同自测） */
window.__TEST=async T=>{ const w=ms=>new Promise(r=>setTimeout(r,ms)); localStorage.clear(); const V=window.__SHOT||'me'; const PF=T.PROF(); PF.days={};
  const d0=new Date(); for(let i=0;i<9;i++){ if(i===4) continue; const d=new Date(d0); d.setDate(d.getDate()-i); PF.days[d.getFullYear()+'-'+(d.getMonth()+1)+'-'+d.getDate()]={ms:(10+i*3)*6e4,n:5,sv:i%3===1?1:0}; }
  if(V==='quiz'){ for(const k in T.TIPSS()) delete T.TIPSS()[k]; T.shelf(); await w(500); document.querySelector('#abNext').click(); await w(50);
    document.querySelector('.qzo[data-q="q1"] [data-v="half"]').click(); document.querySelector('.qzo[data-q="q2"] [data-v="people"]').click(); return; }
  T.TIPSS().welcomed=1; await w(500); T.closeSheet(); PF.qz={q1:'half',q2:['people','bored'],q3:'auto'}; T.setMode('heavy');
  if(V==='me'){ T.shelf(); await w(100); T.meSheet(); return; }
  T.TIPSS().hinted=1; T.TIPSS().tipFound=1; T.shelf(); T.openBook('hound'); await w(900); T.closeSheet(); const IX=T.getIDX(), S=T.getS();
  if(V==='clue'){ T.markRd(0,IX['5.140']); S.current=IX['5.140']; ['B01','B02','B03','B04','B05','B06','B07','B08','B09','B10'].forEach(id=>{S.found[id]=S.seen[id]=Date.now();}); ['B01','B02','B04'].forEach(id=>S.doneS[id]=Date.now()); T.save(); T.cluePanel('open'); return; }
  if(V==='end'){ T.markRd(0,T.P().length-1); S.current=T.P().length-1; T.getSUS2().forEach(s=>{S.found[s.id]=S.seen[s.id]=S.doneS[s.id]=Date.now();}); S.started=Date.now()-9*864e5; S.finished=Date.now(); T.save(); T.syncEnd(); T.noRead(3000); setTimeout(()=>{ scrollTo({top:document.body.scrollHeight,behavior:'instant'}); },300); return; }
  if(V==='uend'){ T.markRd(0,IX['3.10']); S.current=IX['3.10']; ['B01','B02','B03','B04'].forEach(id=>{S.found[id]=S.seen[id]=Date.now();}); S.doneS.B01=Date.now(); T.save(); T.paintMarks(); T.noRead(3000); document.querySelector('.uend[data-u="1"]').scrollIntoView({block:'center'}); return; }
};
