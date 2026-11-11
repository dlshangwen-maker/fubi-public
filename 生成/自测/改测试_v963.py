"""v9.63 交互重做第二批：自测跟着改 + 新增。"""
import os
B=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))+'/'
P=B+'生成/自测_两本书.js'
s=open(P,encoding='utf-8').read()
def rep(a,b):
    global s
    assert s.count(a)==1,(s.count(a),a[:70]); s=s.replace(a,b)
rep("""    ok('导览显示各回已读比例',/已读 \\d+%/.test(tx),'');""","""    ok('导览每回有一根已读进度条',[...document.querySelectorAll('#sheet .olpb')].some(e=>/已读 \\d+%/.test(e.getAttribute('aria-label'))),'');""")
rep("""    T.novelOutline('ppl',''); ok('导览有搜索框',!!document.querySelector('#olQ'));""","""    T.novelOutline('ppl',''); ok('导览搜索收在放大镜里，点了才展开',!!document.querySelector('#olQ')&&document.querySelector('#sheet .srch').hidden); document.querySelector('#olS').click();""")
rep("""    ok('我的：账号卡（昵称、打码的账号、账号与安全）',t.includes('读者1234')&&t.includes('138****1234')&&document.querySelector('#meAcc').textContent.includes('账号与安全'));""",
    """    ok('我的：账号卡（昵称、打码的账号），点昵称就能改',t.includes('读者1234')&&t.includes('138****1234')&&!!document.querySelector('#meName'));""")
rep("""    ok('二级菜单：阅读偏好、关于伏笔；账号与安全只从顶部账号卡进',!!document.querySelector('#mePref')&&!!document.querySelector('#meAbout')&&!document.querySelector('#meSec'));""",
    """    ok('二级菜单：阅读偏好、关于伏笔；退出登录在最下面',!!document.querySelector('#mePref')&&!!document.querySelector('#meAbout')&&!!document.querySelector('#secOut'));""")
rep("""    document.querySelector('#pgBack').click(); await w(20); document.querySelector('#pgBack').click(); await w(20); document.querySelector('#meAcc').click(); await w(20);
    ok('账号与安全：昵称、账号、退出登录',!!document.querySelector('#secName')&&!!document.querySelector('#secOut'));""",
    """    document.querySelector('#pgBack').click(); await w(20); document.querySelector('#pgBack').click(); await w(20); document.querySelector('#meName').click(); await w(20);
    ok('点昵称原地变输入框',!!document.querySelector('#secName')); document.querySelector('#secName').value='改名测试'; document.querySelector('#secSave').click(); await w(20);
    ok('保存后昵称改了',T.curUser().name==='改名测试'&&document.querySelector('#meName').textContent.includes('改名测试')); T.ACC().users[T.curUser().id].name='读者1234';""")
rep("""    ok('轻度：隔三天打开，弹前情提要（不列伏笔）',document.querySelector('#sheet').classList.contains('show')&&!document.querySelector('#sheet').textContent.includes('带着这'));""",
    """    ok('轻度：隔三天打开，不弹卡，回顾放进"上次读到这里"那条线',!document.querySelector('#sheet').classList.contains('show')&&!!document.querySelector('#lastLine.rc')&&document.querySelector('#lastLine').textContent.includes('距上次 3 天'));
    document.querySelector('#llMore')?.click(); ok('点"展开前情"才看完整回顾',!!document.querySelector('#lastLine .llf')&&!document.querySelector('#lastLine .llf').hidden);""")
# 书的详情
rep("""  fbEl&&fbEl.click(); await wait(30); t=document.querySelector('#sheet').textContent;
  ok('点开显示未揭晓列表',t.includes('未揭晓')&&t.includes('眼泪'),t.slice(0,50));""",
    """  fbEl&&fbEl.click(); await wait(30); t=document.querySelector('#sheet').textContent;
  ok('点"N 处伏笔待揭晓"：打开书籍详情并展开待揭晓列表',t.includes('待揭晓')&&t.includes('眼泪')&&!document.querySelector('#sheet .biurl').hidden,t.slice(0,50));
  ok('书籍详情：封面、进度、版本信息、继续阅读',!!document.querySelector('#sheet .bihead .cover')&&!!document.querySelector('#sheet .bimeta')&&!!document.querySelector('#bOpen'));
  T.closeSheet(); document.querySelector('#bH .bkm')?.click(); await wait(30); ok('列表里每本书有"…"打开详情',document.querySelector('#sheet').classList.contains('show')&&!!document.querySelector('#sheet .bihead'));""")
rep("""  ok('书的详情里不显示伏笔',!t.includes('伏笔未回收')&&!t.includes('雨村拿了银子')&&!t.includes('未回收的伏笔'),'');""",
    """  ok('书的详情：待揭晓列表默认收起，不剧透',document.querySelector('#sheet .biurl')?.hidden!==false&&!t.includes('雨村拿了银子'),'');""")
open(P,'w',encoding='utf-8').write(s)
# 服务端模式：账号与安全没了；书的详情
P2=B+'生成/自测/自测_服务端模式.js'
s=open(P2,encoding='utf-8').read()
open(P2,'w',encoding='utf-8').write(s)
print('ok')
