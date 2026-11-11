"""v9.70：蓝色只留给读者自己写的内容（想法/划线/书签/猜想/我发现的）；功能入口、状态文字、折叠标题改墨色；书末"查看读书札记"去大按钮。备份 模板_v86备份.html"""
import os
B=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))+'/'
P=B+'Demo/模板.html'
s=open(P,encoding='utf-8').read()
def rep(a,b):
    global s
    assert s.count(a)==1,(s.count(a),a[:70]); s=s.replace(a,b)
rep(".binfo .p{font-size:var(--t-aux);color:var(--blue);",".binfo .p{font-size:var(--t-aux);color:var(--ink2);")
rep(".pvsum summary{font-size:var(--t-aux);color:var(--blue);",".pvsum summary{font-size:var(--t-aux);color:var(--ink);")
rep(".pvtoc summary{font-size:var(--t-aux);color:var(--blue);",".pvtoc summary{font-size:var(--t-aux);color:var(--ink);")
rep(".qacts button{font-size:var(--t-aux);color:var(--blue);",".qacts button{font-size:var(--t-aux);color:var(--ink);")
rep("line-height:1.4;color:var(--blue);padding:3px 0 3px 10px;white-space:nowrap}","line-height:1.4;color:var(--ink);padding:3px 0 3px 10px;white-space:nowrap}")
rep(".qundo{font-size:var(--t-aux);color:var(--blue);",".qundo{font-size:var(--t-aux);color:var(--ink);")
rep(".src .more-t{font-family:var(--ui);font-size:var(--t-tag);color:var(--blue);",".src .more-t{font-family:var(--ui);font-size:var(--t-tag);color:var(--ink);")
rep(".qzr b{color:var(--blue)}",".qzr b{color:var(--ink)}")
rep(".ogq summary{font-size:var(--t-aux);color:var(--blue);",".ogq summary{font-size:var(--t-aux);color:var(--ink);")
rep(".qzt b{color:var(--blue)}",".qzt b{color:var(--ink)}")
rep(".qzc .qze{font-size:var(--t-tag);color:var(--blue)}",".qzc .qze{font-size:var(--t-tag);color:var(--ink2)}")
rep(".qzrh b{color:var(--blue)}",".qzrh b{color:var(--ink)}")
rep(".nr .nrm.txt{width:auto;font-size:var(--t-tag);color:var(--blue);",".nr .nrm.txt{width:auto;font-size:var(--t-tag);color:var(--ink2);")
rep(".fmore summary{list-style:none;font-size:var(--t-tag);color:var(--blue);",".fmore summary{list-style:none;font-size:var(--t-tag);color:var(--ink);")
rep(".shmenu button[aria-checked=true]{color:var(--blue)}",".shmenu button[aria-checked=true]{color:var(--ink);font-weight:600}")
rep(".seg button[aria-pressed=true]{background:var(--field);color:var(--blue);",".seg button[aria-pressed=true]{background:var(--field);color:var(--ink);")
rep(".hint{font-family:var(--ui);font-size:var(--t-aux);color:var(--blue);",".hint{font-family:var(--ui);font-size:var(--t-aux);color:var(--ink2);")
open(P,'w',encoding='utf-8').write(s); print('ok')
