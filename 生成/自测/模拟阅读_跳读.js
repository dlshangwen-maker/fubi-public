/* 两种不正常的读法：① 快速滑（每次滚 1.5 屏、停 60ms）② 读到中间 → 用导览跳到后面读一会儿 → 跳回来接着读。
   检查：揭晓提示只在答案那句过了阅读线、还在屏幕附近时出现；其余情况答案读过的应"静默已揭晓"（不弹提示）。 */
window.__TEST=async T=>{
  const w=ms=>new Promise(r=>setTimeout(r,ms)), out=[];
  const yOf=(i,sent,end)=>{ const C=T.els()[i]?.querySelector('.zh'); if(!C) return null; const t=C.textContent; let o=sent?t.indexOf(sent):0; if(o<0) o=0; if(end) o+=Math.max(0,(sent||'').length-1);
    const tw=document.createTreeWalker(C,NodeFilter.SHOW_TEXT); let n,p=0; while((n=tw.nextNode())){ if(p+n.length>o){ const r=document.createRange(); r.setStart(n,o-p); r.setEnd(n,o-p+1); const rc=r.getClientRects()[0]; return rc?rc.top:null; } p+=n.length; } return null; };
  const watch=(bk,tag)=>{ const tb=document.querySelector('#toast'); const t=tb&&tb.classList.contains('show')?tb.textContent:''; return t; };
  async function run(bk,mode,steps,step,pause,jumpAt,jumpTo,back){
    localStorage.clear(); T.TIPSS().welcomed=1; T.TIPS.hinted=1; T.TIPS.tipFound=1; T.shelf(); await w(50); T.closeSheet(); T.openBook(bk); await w(800); T.closeSheet();
    scrollTo({top:0,behavior:'instant'}); await w(300);
    const S=T.getS(), IX=T.getIDX(), SUS=T.getSUS(); const seenD={}; let jumped=0; run.y=-1; run.same=0; S.ansSeen=S.ansSeen||{};   /* 静默揭晓会写 ansSeen；先建好，才分得清弹提示还是静默 */
    for(let k=0;k<steps;k++){
      if(jumpAt&&!jumped&&S.current>=IX[jumpAt]){ jumped=1; const here=S.current;
        const go=async n=>{ T.noRead(1200); T.els()[IX[n]].scrollIntoView({block:'start'}); await w(1500); };
        await go(jumpTo);
        for(let q=0;q<12;q++){ scrollBy({top:innerHeight/3,behavior:'instant'}); await w(140); for(const s of SUS) if(S.found[s.id]) S.seen[s.id]=S.seen[s.id]||1; }
        await go(T.P()[here].n); out.push([bk,mode,'—','跳到 '+jumpTo+' 读 4 屏，回到 '+T.P()[here].n,'','','✓']); }
      scrollBy({top:innerHeight*step,behavior:'instant'}); await w(pause);
      { let d=document.getElementById('simst'); if(!d){ d=document.createElement('div'); d.id='simst'; d.style.cssText='position:fixed;top:0;left:0;right:0;z-index:999;background:#ff0;color:#000;font:13px sans-serif;padding:4px'; document.documentElement.appendChild(d); }
        const bad_=out.filter(r=>r[6]!=='✓'); d.style.maxHeight='45vh'; d.style.overflow='auto';
        d.innerHTML=`${bk} ${mode} 第 ${k} 步 · 位置 ${(T.P()[S.current]||{}).n} · 已记 ${out.length} · <b>有问题 ${bad_.length}</b>`+out.map(r=>`<div style="color:${r[6]==='✓'?'#060':'#c00'}">${r.join(' · ')}</div>`).join(''); }
      for(const s of SUS) if(S.found[s.id]) S.seen[s.id]=S.seen[s.id]||Date.now();
      for(const s of SUS){ if(S.doneS[s.id]&&!seenD[s.id]){ seenD[s.id]=1;
          const j=IX[s['揭晓']], y=yOf(j,s['揭晓锚句'],true), tt=(document.querySelector('#toast')?.textContent)||'';
          const announced=!!(S.ansSeen&&!S.ansSeen[s.id]); /* 静默揭晓会同时记 ansSeen */
          const ok=!announced||(y!=null&&y<innerHeight*0.4+4&&y>-innerHeight*0.8);
          out.push([bk,mode,s.id,s['揭晓'],announced?'弹提示':'静默',y==null?'?':Math.round(y),ok?'✓':'✗ 提示时答案不在眼前']); } }
      if(scrollY===run.y){ if(++run.same>=3) break; } else { run.same=0; run.y=scrollY; }
    }
    out.push([bk,mode,'—','结束于 '+(T.P()[S.current]||{}).n,'已发现 '+Object.keys(S.found).length,'已揭晓 '+Object.keys(S.doneS).length,'✓']);
  }
  await run('hlm','跳到后面再回来',260,1/3,110,'1.10','3.10');
  await run('lhz','跳到后面再回来',200,1/3,110,'1.3','9.20');
  const bad=out.filter(r=>r[6]!=='✓');
  let d=document.getElementById('simst'); if(!d){ d=document.createElement('div'); d.id='simst'; document.documentElement.appendChild(d); }
  d.style.cssText='position:fixed;inset:0;z-index:99999;overflow:auto;background:#fff;color:#000;font:13px/1.5 sans-serif;padding:12px';
  d.innerHTML=`<b style="font-size:17px">跳读：${out.length} 条记录，${bad.length} 次有问题</b>`+out.map(r=>`<div style="color:${r[6]==='✓'?'#070':'#c00'}">${r.join(' · ')}</div>`).join('');
};
