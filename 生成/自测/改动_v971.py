"""v9.71（11-02 用户五点）：①书架拖动排序：被拖的书跟手（抬起放大+阴影），其他书让位有滑动动画，松手滑回格子；②"手动"改"自定义"；
③问卷"自己写一个"：不再是一个孤零零的输入框+"添加"，而是选项行里最后一个"＋ 自己写"，点开变成同高同圆角的输入框，回车或点别处就收录并选中；
④三题答完不再显示"跳过"；⑤札记的"编辑"和"复制/导出"放在标题行一起。备份 模板_v87备份.html"""
import os,re
B=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))+'/'
P=B+'Demo/模板.html'
s=open(P,encoding='utf-8').read()
def rep(a,b,n=1):
    global s
    c=s.count(a); assert c==n,(c,a[:80]); s=s.replace(a,b)
# ② 自定义
rep("['manual','手动']","['manual','自定义']")
# ④ 跳过
rep("""${first?'<button class="linkbtn" id="qzSkip">跳过</button>':''}""","""${first&&!all?'<button class="linkbtn" id="qzSkip">跳过</button>':''}""")
# ③ 自己写
i=s.index('      ${q.own?`<div class="qzown">'); j=s.index("</div>`:''}",i)+len("</div>`:''}")
s=s[:i]+s[j:]
rep("""}).join('')}</div>
      ${q.m?""","""}).join('')}${q.own?'<button type="button" class="qzadd" id="qzAdd">＋ 自己写</button>':''}</div>
      ${q.m?""") if False else None
# chips 的 join 后追加"自己写"
a=""".map(([v,l])=>`<button data-v="${v}" aria-pressed="${q.m?(A[q.k]||[]).includes(v):A[q.k]===v}">${esc(l)}</button>`).join('')}</div>"""
rep(a,""".map(([v,l])=>`<button data-v="${v}" aria-pressed="${q.m?(A[q.k]||[]).includes(v):A[q.k]===v}">${esc(l)}</button>`).join('')}${q.own?'<button type="button" class="qzadd" id="qzAdd">＋ 自己写</button>':''}</div>""")
rep("document.querySelectorAll('.qzchips button').forEach(b=>b.onclick=()=>{ const v=b.dataset.v;","const bindChip=b=>b.onclick=()=>{ const v=b.dataset.v;")
rep("b.classList.add('pop'); setTimeout(nextOpen,260); });","b.classList.add('pop'); setTimeout(nextOpen,260); };\n  document.querySelectorAll('.qzchips button[data-v]').forEach(bindChip);")
i=s.index("  const own=()=>{ const t=($('#qzOwn').value||'')"); j=s.index("\n",s.index("$('#qzOwnOk')",i))
NEW="""  const mkAdd=()=>{ const b=document.createElement('button'); b.type='button'; b.id='qzAdd'; b.className='qzadd'; b.textContent='＋ 自己写'; b.onclick=openOwn; return b; };
  const openOwn=()=>{ const b=$('#qzAdd'); const inp=document.createElement('input'); inp.id='qzOwn'; inp.className='qzin'; inp.maxLength=12; inp.placeholder='写一个'; inp.setAttribute('aria-label','自己写一个答案'); b.replaceWith(inp); inp.focus(); let fin=false;
    const commit=()=>{ if(fin) return; fin=true; const t=inp.value.trim();
      if(t){ const base=q.o.find(o=>o[1]===t), v=base?base[0]:'x:'+t, a=A[q.k]=A[q.k]||[]; if(!a.includes(v)) a.push(v);
        let ch=[...document.querySelectorAll('.qzchips button[data-v]')].find(x=>x.dataset.v===v);
        if(!ch){ ch=document.createElement('button'); ch.dataset.v=v; ch.textContent=t; bindChip(ch); inp.before(ch); }
        ch.setAttribute('aria-pressed','true'); const nx=$('#qzNext'); if(nx) nx.disabled=false; }
      inp.replaceWith(mkAdd()); };
    inp.addEventListener('keydown',e=>{ if(e.key==='Enter'){ e.preventDefault(); commit(); } }); inp.addEventListener('blur',commit); };
  if($('#qzAdd')) $('#qzAdd').onclick=openOwn;"""
s=s[:i]+NEW+s[j:]
# ⑤ 札记
rep("""<span class="nacts"><button class="linkbtn" id="exCopy">复制</button><button class="linkbtn" id="exSave">导出</button></span>':'<span class="ttl">笔记</span>""","""<span class="nacts"><button class="linkbtn" id="exEdit">编辑</button><button class="linkbtn" id="exCopy">复制</button><button class="linkbtn" id="exSave">导出</button></span>':'<span class="ttl">笔记</span>""")
rep("""\n    <p class="arcact"><button class="linkbtn" id="exEdit">编辑这篇札记</button></p>`;""","`;")
# ① 拖动
i=s.index('function wireShelfDrag'); j=s.index('\n}\n',i)+3
DRAG="""function wireShelfDrag(own){
  /* v9.71：被拖的书跟着手指走（抬起、略放大、有阴影）；挪到别的书上，其他书滑开让位；松手后滑进新位置 */
  const box=$('#bookList'), v=shv(); let drag=null; const EASE='transform .24s cubic-bezier(.2,.8,.2,1)';
  const books=()=>[...box.querySelectorAll('.book')];
  const follow=()=>{ const el=drag.el; el.style.transition='none'; el.style.transform='none'; const n=el.getBoundingClientRect();
    el.style.transform=`translate(${drag.sx+drag.dx-n.left}px,${drag.sy+drag.dy-n.top}px) scale(1.03)`; };
  const flip=mut=>{ const sib=books().filter(x=>x!==drag.el), first=new Map(sib.map(x=>[x,x.getBoundingClientRect()]));
    sib.forEach(x=>{ x.style.transition='none'; x.style.transform=''; }); mut();
    sib.forEach(x=>{ const l=x.getBoundingClientRect(), f=first.get(x), dx=f.left-l.left, dy=f.top-l.top; if(dx||dy) x.style.transform=`translate(${dx}px,${dy}px)`; });
    void box.offsetWidth; sib.forEach(x=>{ x.style.transition=EASE; x.style.transform=''; }); };
  box.querySelectorAll('.book').forEach(el=>{
    el.addEventListener('pointerdown',e=>{ if(e.button>0) return; const r=el.getBoundingClientRect(); drag={el,x:e.clientX,y:e.clientY,sx:r.left,sy:r.top,dx:0,dy:0,moved:false}; el.setPointerCapture(e.pointerId); });
    el.addEventListener('pointermove',e=>{ if(!drag||drag.el!==el) return;
      if(!drag.moved&&Math.hypot(e.clientX-drag.x,e.clientY-drag.y)<6) return; if(!drag.moved){ drag.moved=true; el.classList.add('drag'); }
      e.preventDefault(); drag.dx=e.clientX-drag.x; drag.dy=e.clientY-drag.y;
      const over=document.elementsFromPoint(e.clientX,e.clientY).map(x=>x.closest&&x.closest('.book')).find(x=>x&&x!==el&&box.contains(x));
      if(over){ const r=over.getBoundingClientRect(), after=v.lay==='grid'?(e.clientX>r.left+r.width/2):(e.clientY>r.top+r.height/2), ref=after?over.nextSibling:over;
        if(ref!==el&&el.nextSibling!==ref) flip(()=>box.insertBefore(el,ref)); }
      follow(); });
    const end=()=>{ if(!drag||drag.el!==el) return; const d=drag; drag=null;
      if(d.moved){ v.order=books().map(x=>x.dataset.k); v.sort='manual'; saveProf(true);
        el.style.transition=EASE; el.style.transform=''; setTimeout(()=>{ el.classList.remove('drag'); el.style.transition=''; },250); }
      else { el.classList.remove('drag'); const k=el.dataset.k; if(own(k)){ shSel.has(k)?shSel.delete(k):shSel.add(k); shelf(); } } };
    el.addEventListener('pointerup',end); el.addEventListener('pointercancel',end);
  });
}
"""
s=s[:i]+DRAG+s[j:]
rep(".editing .book.drag{opacity:.9;box-shadow:0 8px 24px rgba(0,0,0,.18);background:var(--paper);z-index:3}",".editing .book{position:relative}.editing .book.drag{box-shadow:0 10px 28px rgba(0,0,0,.2);background:var(--paper);z-index:5;will-change:transform;border-radius:6px}.editing .book.drag .cover{animation:none}")
rep('</style>','\n.qzchips .qzadd{background:transparent;color:var(--mute);box-shadow:none;border:1px dashed var(--faint)}\n.qzchips .qzin{height:40px;width:9em;padding:0 14px;border-radius:6px;border:0;background:var(--sheet);box-shadow:inset 0 0 0 1.5px var(--ink);font-size:var(--t-body);color:var(--ink);font-family:var(--ui)}\n.qzchips .qzin:focus{outline:none}\n</style>')
open(P,'w',encoding='utf-8').write(s); print('ok')
