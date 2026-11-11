/* 模拟阅读：从头一屏一屏往下读（每次滚 1/3 屏，停 120ms），记录每条伏笔"发现"和"揭晓"那一刻：
   发现时：提出锚句是否整句在屏幕上（底部导航上方）；揭晓时：揭晓锚句的句末是否已经过了阅读线（40%）、而且还在屏幕上。
   每本书只跑到 MAXP 段（全本太长），用法同自测：注入 window.__TEST */
window.__TEST=async T=>{
  const w=ms=>new Promise(r=>setTimeout(r,ms)), out=[], MODES=['light','heavy'], BOOKS=[['hlm',214],['nahan',260],['lhz',190],['tractatus',140],['hound',260]];
  for(const MODE of MODES){ if(T.setMode) T.setMode(MODE);
  const nav=()=>innerHeight-(document.querySelector('.nav')?.offsetHeight||0)-16;
  const yOf=(i,sent,end)=>{ const C=T.els()[i]?.querySelector('.zh'); if(!C) return null; const t=C.textContent; let o=sent?t.indexOf(sent):0; if(o<0) o=0; if(end) o+=Math.max(0,(sent||'').length-1);
    const tw=document.createTreeWalker(C,NodeFilter.SHOW_TEXT); let n,p=0; while((n=tw.nextNode())){ if(p+n.length>o){ const r=document.createRange(); r.setStart(n,o-p); r.setEnd(n,o-p+1); const rc=r.getClientRects()[0]; return rc?rc.top:null; } p+=n.length; } return null; };
  for(const [bk,MAXP] of BOOKS){
    localStorage.clear(); T.TIPSS().welcomed=1; T.TIPS.hinted=1; T.TIPS.tipFound=1; T.getS&&0; if(T.setMode) T.setMode(MODE); T.shelf(); await w(50); T.closeSheet(); T.openBook(bk); await w(800); T.closeSheet();
    scrollTo({top:0,behavior:'instant'}); await w(400);
    const S=T.getS(), IX=T.getIDX(), SUS=T.getSUS2?T.getSUS2():T.getSUS(), P_=i=>T.P()[i].n; const seenF={}, seenD={};
    let last=-1;
    for(let k=0;k<4000;k++){
      scrollBy({top:innerHeight/3,behavior:'instant'}); await w(120);
      /* 读者看到伏笔就点开（这样才会有揭晓） */
      for(const s of SUS){ if(S.found[s.id]&&!seenF[s.id]){ seenF[s.id]=1;
          const i=IX[s['提出']], y=s['提出']==='前言'?0:yOf(i,s['提出锚句'],true);
          out.push([MODE+'·'+bk,s.id,'发现',s['提出'],y==null?'?':Math.round(y),y!=null&&y<nav()&&y>-40?'✓':'✗ 不在屏幕上']);
          S.seen[s.id]=S.seen[s.id]||Date.now(); T.save(); } }
      for(const s of SUS){ if(S.doneS[s.id]&&!seenD[s.id]){ seenD[s.id]=1;
          const j=IX[s['揭晓']], y=yOf(j,s['揭晓锚句'],true);
          const ok=y!=null&&y<innerHeight*0.65+4&&y>-innerHeight*0.6;
          out.push([MODE+'·'+bk,s.id,'揭晓',s['揭晓'],y==null?'?':Math.round(y/innerHeight*100)+'%',ok?'✓':(y>innerHeight*0.65?'✗ 太早（答案还在屏幕下方）':'✗ 太晚')]); } }
      /* 重度："答案快到了"标记那一刻，答案必须还在后面（没读到），而且不超过约两页 */
      for(const [id,x] of Object.entries(S.soon||{})){ if(seenD['soon'+id]) continue; seenD['soon'+id]=1; const s=SUS.find(y=>y.id===id); if(!s) continue; const j=IX[s['揭晓']];
        out.push([MODE+'·'+bk,id,'快到了',P_(x.i)+'→'+s['揭晓'],'',j>x.i&&!S.doneS[id]?'✓':'✗ 答案已读过']); }
      const c=S.current; if(c>=MAXP||(c===last&&k>5&&scrollY+innerHeight>=document.body.scrollHeight-5)) break; last=c;
    }
  }
  }
  const bad=out.filter(r=>r[5]!=='✓');
  document.body.innerHTML=`<div style="font:13px/1.5 sans-serif;padding:12px;background:#fff;color:#000"><b style="font-size:17px">模拟阅读（轻/重）：${out.length} 次，${bad.length} 次有问题</b><div>揭晓时答案句在屏幕的位置（平均）：${(()=>{const v=out.filter(r=>r[2]==='揭晓'&&String(r[4]).endsWith('%')).map(r=>parseInt(r[4])); return v.length?Math.round(v.reduce((a,b)=>a+b,0)/v.length)+'%':'-';})()}（原来 40% 以上才揭晓）</div><div>${MODES.map(m=>m+'：发现 '+out.filter(r=>r[0].startsWith(m)&&r[2]==='发现').length+' · 揭晓 '+out.filter(r=>r[0].startsWith(m)&&r[2]==='揭晓').length+' · 快到了 '+out.filter(r=>r[0].startsWith(m)&&r[2]==='快到了').length).join('<br>')}</div>${(bad.length?bad:out.slice(0,30)).map(r=>`<div style="color:${r[5]==='✓'?'#070':'#c00'}">${r.join(' · ')}</div>`).join('')}</div>`;
};
