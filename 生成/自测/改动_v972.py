"""v9.72（11-02 用户三点之二）：①登录页不再写"登录后阅读《呐喊》"这行；②问卷题目通用化：第一题不预设"厚书"，第二题选项对任何书都成立
（看不懂的地方多 / 内容太多记不住 / 读着读着没劲 / 总被别的事打断），去掉"文言""抓重点"。旧答案 how 映射成 break。备份 模板_v88备份.html"""
import os
B=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))+'/'
P=B+'Demo/模板.html'
s=open(P,encoding='utf-8').read()
def rep(a,b):
    global s
    assert s.count(a)==1,(s.count(a),a[:70]); s=s.replace(a,b)
rep("${AFTER_T?`<p class=\"auhint\">${esc(AFTER_T)}</p>`:''}","")
rep("{k:'q1',t:'拿到一本厚书，你通常……',o:[['often','多半能读完'],['half','读到一半就放下了'],['long','很久没读完过一本了']]}","{k:'q1',t:'你读书的习惯，更像哪一种？',o:[['often','多半能读完'],['half','常读到一半就放下'],['long','很久没读完过一本了']]}")
rep("o:[['words','生僻字词、文言太多'],['people','人物太多，记不住'],['bored','情节慢，读着没劲'],['how','不知道该抓什么重点']]}","o:[['words','有些地方看不懂'],['people','内容太多，记不住'],['bored','读着读着没劲了'],['break','总被别的事打断']]}")
rep("const qlab=(q,v)=>String(v).startsWith('x:')?String(v).slice(2):(q.o.find(o=>o[0]===v)||[])[1];","const qlab=(q,v)=>{ v=v==='how'?'break':v; return String(v).startsWith('x:')?String(v).slice(2):(q.o.find(o=>o[0]===v)||[])[1]||''; };")
rep("(A.q2||[]).some(x=>x==='bored'||x==='how')","(A.q2||[]).some(x=>x==='bored'||x==='break'||x==='how')")
rep("const SHORT={q1:'厚书',q2:'读不下去',q3:'伏笔'};","const SHORT={q1:'习惯',q2:'读不下去',q3:'伏笔'};")
rep("q.k==='q1'?'厚书':q.k==='q2'?'读不下去':'伏笔'","q.k==='q1'?'习惯':q.k==='q2'?'读不下去':'伏笔'")
open(P,'w',encoding='utf-8').write(s)
P=B+'生成/自测_两本书.js'; t=open(P,encoding='utf-8').read()
def rt(a,b):
    global t
    assert t.count(a)==1,(t.count(a),a[:70]); t=t.replace(a,b)
rt("""ok('没登录点"找书"：先去登录（写明登录后找书）',(()=>{ document.querySelector('#shLib').click(); return !!document.querySelector('#auAcc')&&document.querySelector('.auhint').textContent.includes('找书'); })());""","""ok('没登录点"找书"：先去登录（登录页只有账号密码，没有多余提示行）',(()=>{ document.querySelector('#shLib').click(); return !!document.querySelector('#auAcc')&&!document.querySelector('.auhint'); })());""")
rt("""ok('没登录点"导入"：先去登录（写明登录后导入）',(()=>{ document.querySelector('#impBtn').click(); return !!document.querySelector('#auAcc')&&document.querySelector('.auhint').textContent.includes('导入'); })());""","""ok('没登录点"导入"：先去登录',(()=>{ document.querySelector('#impBtn').click(); return !!document.querySelector('#auAcc')&&!document.querySelector('.auhint'); })());""")
rt("""ok('点"登录后阅读"：进登录页，写明登录后读哪本',!!document.querySelector('#auAcc')&&document.querySelector('.auhint').textContent.includes('登录后阅读《'));""","""ok('点"登录后阅读"：进登录页，不写多余提示',!!document.querySelector('#auAcc')&&!document.querySelector('.auhint'));""")
rt("includes('厚书')","includes('习惯')")
open(P,'w',encoding='utf-8').write(t); print('ok')
