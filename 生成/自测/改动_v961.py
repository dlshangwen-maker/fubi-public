"""v9.61（10-28 用户截图）：线装封面题签里的书名没和书配好——字偏在题签右边、太小，题签长短固定不随书名变。
改为：题签宽高随书名（按封面宽度等比，cqw），字在题签里居中；5 个字以内一列，更长分两列（右列在前，像真题签）。备份 Demo/模板_v76备份.html。"""
import os
B=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))+'/'
P=B+'Demo/模板.html'
s=open(P,encoding='utf-8').read()
def rep(a,b,n=1):
    global s
    c=s.count(a); assert c==n,(c,a[:80]); s=s.replace(a,b)
rep("""  const n=[...title].length, v=n<=4;   /* 题签：4 个字以内一列，更长的两列小字（类名 v / h 沿用） */
  return `<div class="cover gen ${v?'v':'h'}" style="background:${COVER_C[h%COVER_C.length]}"><span class="ct">${esc(title)}</span></div>`;""",
"""  const cs=[...title], n=cs.length, v=n<=5, k=Math.ceil(n/2);   /* 题签：5 个字以内一列；更长分两列，右列在前（类名 v / h 沿用） */
  const cols=v?[title]:[cs.slice(0,k).join(''),cs.slice(k).join('')];
  return `<div class="cover gen ${v?'v':'h'}" style="background:${COVER_C[h%COVER_C.length]}"><span class="ct">${cols.map(c=>`<i>${esc(c)}</i>`).join('')}</span></div>`;""")
CSS=r'''
/* v9.61 题签：大小随书名、字居中（按封面宽度等比缩放） */
.cover.gen{container-type:inline-size}
.cover.gen .ct,.book.gb .cover.gen .ct,.cont .cover.gen .ct,.cover.gen.h .ct,.book.gb .cover.gen.h .ct,.cont .cover.gen.h .ct{
  left:20cqw;top:10cqw;width:auto;min-height:0;max-height:none;padding:7cqw 4cqw;display:flex;flex-direction:row-reverse;justify-content:center;align-items:flex-start;gap:2cqw;
  writing-mode:horizontal-tb;font-size:15cqw;line-height:1;letter-spacing:0}
.cover.gen .ct i{font-style:normal;writing-mode:vertical-rl;letter-spacing:.18em;margin-bottom:-.18em;line-height:1}
.cover.gen.h .ct,.book.gb .cover.gen.h .ct,.cont .cover.gen.h .ct{font-size:11.5cqw;padding:6cqw 3.5cqw}
'''
rep('</style>',CSS+'</style>')
open(P,'w',encoding='utf-8').write(s); print('ok')
