"""v9.65 自测：访客首页、登录回到原处、导入页、月历统一、个人账户页。备份 自测_两本书_v965前备份.js / 自测_服务端模式_v965前备份.js"""
import os,shutil
B=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))+'/'
def load(p):
    return open(B+p,encoding='utf-8').read()
def save(p,s):
    open(B+p,'w',encoding='utf-8').write(s)
for p,b in [('生成/自测_两本书.js','生成/自测_两本书_v965前备份.js'),('生成/自测/自测_服务端模式.js','生成/自测/自测_服务端模式_v965前备份.js')]:
    if not os.path.exists(B+b): shutil.copy(B+p,B+b)
s=load('生成/自测_两本书.js')
def rep(a,b):
    global s
    assert s.count(a)==1,(s.count(a),a[:70]); s=s.replace(a,b)
rep("""    ok('底部一行：已有账号，登录 · 先体验',document.querySelector('.auswitch').textContent.replace(/\\s/g,'')==='已有账号，登录·先体验');""",
    """    ok('底部一行：已有账号，登录（不再有"先体验"，不登录能浏览首页）',document.querySelector('.auswitch').textContent.replace(/\\s/g,'')==='已有账号，登录'&&!document.querySelector('#auSkip'));
    ok('登录页左上角 ‹ 回访客首页',!!document.querySelector('#flBack')); document.querySelector('#flBack').click(); await w(20); ok('回到首页：有登录、注册入口和精读版封面',!!document.querySelector('.home')&&!!document.querySelector('#hmReg')&&document.querySelectorAll('.hmbooks .book').length===5); T.authPage('reg'); await w(20);""")
rep("""    ok('有"先体验"',document.querySelector('#auSkip')?.textContent==='先体验');
""","""    // ===== v9.65 访客逻辑 =====
    T.homePage(); await w(20);
    ok('不登录的首页：介绍、三句话、精读版封面、登录入口',!!document.querySelector('.hmtag')&&document.querySelectorAll('.hmfeat .welrow').length===3&&!!document.querySelector('#hmLogin'));
    ok('首页不放"继续阅读"和书架操作',!document.querySelector('#shCont')&&!document.querySelector('#sortB'));
    document.querySelector('.hmbooks .book').click(); await w(30);
    ok('访客点封面：看书籍详情，底部按钮是"登录后阅读"',document.querySelector('#sheet').classList.contains('show')&&document.querySelector('#bOpen').textContent==='登录后阅读');
    document.querySelector('#bOpen').click(); await w(30);
    ok('点"登录后阅读"：进登录页，写明登录后读哪本',!!document.querySelector('#auAcc')&&document.querySelector('.auhint').textContent.includes('登录后阅读《'));
    T.openBook('hlm'); await w(20); ok('没登录直接打开书：被拦到登录页（不会进阅读器）',!!document.querySelector('#auAcc')&&!document.querySelector('#text'));
""")
rep("""    fill('13800001234','1',''); await w(20);
    ok('昵称不填""","""    T.setAfter(()=>{ window.__AFTER=1; T.shelf(); },'登录后阅读《红楼梦》');
    fill('13800001234','1',''); await w(20);
    ok('昵称不填""")
rep("""    ok('注册后直接进问卷（第 2 段）""","""    ok('注册后先填问卷（回到原处的动作等问卷结束）',!window.__AFTER);
    ok('注册后直接进问卷（第 2 段）""")
rep("""    ok('"开始读书"后是重度',PF.mode==='heavy');""","""    ok('"开始读书"后是重度',PF.mode==='heavy');
    ok('问卷结束：回到刚才要做的事（登录前点的那本）',window.__AFTER===1);""")
# 我的：账号卡整张可点 → 个人账户
rep("""    ok('我的：账号卡（昵称、打码的账号），点昵称就能改',t.includes('读者1234')&&t.includes('138****1234')&&!!document.querySelector('#meName'));""",
    """    ok('我的：账号卡（昵称、打码的账号、"个人账户"），整张可点',t.includes('读者1234')&&t.includes('138****1234')&&t.includes('个人账户')&&document.querySelector('#meAcc').tagName==='BUTTON');""")
rep("""    ok('打卡默认按周：7 天',document.querySelectorAll('.week .d').length===7&&!document.querySelector('.cal'));
    document.querySelector('#calTg').click(); await w(20); ok('展开为月历，可收起',document.querySelectorAll('.cal .d').length>=28&&document.querySelector('#calTg').textContent==='收起');""",
    """    ok('打卡默认按周：7 天，有"本周读了 N 天"',document.querySelectorAll('.cal.wk .d').length===7&&!document.querySelector('.cal.mo')&&document.querySelector('.calsum').textContent.includes('本周读了'));
    const wkd=document.querySelector('.cal.wk .d'), wcs=getComputedStyle(wkd), wh=Math.round(wkd.getBoundingClientRect().height);
    document.querySelector('#calTg').click(); await w(20); ok('展开为月历，可收起',document.querySelectorAll('.cal.mo .d').length>=28&&document.querySelector('#calTg').textContent==='收起');
    { const md=document.querySelector('.cal.mo .d'), mcs=getComputedStyle(md); ok('月历和周历同一套格子：同高、同圆角、同底色',Math.round(md.getBoundingClientRect().height)===wh&&mcs.borderRadius===wcs.borderRadius&&mcs.backgroundColor===wcs.backgroundColor,wh+' '+Math.round(md.getBoundingClientRect().height)+' '+wcs.borderRadius+' '+mcs.borderRadius); }""")
rep("""    ok('二级菜单：阅读偏好、关于伏笔；退出登录在最下面',!!document.querySelector('#mePref')&&!!document.querySelector('#meAbout')&&!!document.querySelector('#secOut'));""",
    """    ok('二级菜单：阅读偏好、关于伏笔',!!document.querySelector('#mePref')&&!!document.querySelector('#meAbout'));""")
rep("""document.querySelector('#meName').click(); await w(20);
    ok('点昵称原地变输入框',!!document.querySelector('#secName')); document.querySelector('#secName').value='改名测试'; document.querySelector('#secSave').click(); await w(20);
    ok('保存后昵称改了',T.curUser().name==='改名测试'&&document.querySelector('#meName').textContent.includes('改名测试')); T.ACC().users[T.curUser().id].name='读者1234';""",
    """document.querySelector('#meAcc').click(); await w(20);
    ok('点账号卡：进"个人账户"页（昵称、密码、账号信息、退出登录、注销）',document.querySelector('.pgbar b').textContent==='个人账户'&&!!document.querySelector('#secName')&&!!document.querySelector('#secPw')&&!!document.querySelector('#secOut')&&!!document.querySelector('#secDel')&&document.querySelector('.medl').textContent.includes('加入时间'));
    ok('个人账户页能返回"我的"',document.querySelector('#pgBack').textContent.includes('我的'));
    document.querySelector('#secName').value='改名测试'; document.querySelector('#secSave').click(); await w(20);
    ok('改昵称：页内马上变',T.curUser().name==='改名测试'&&document.querySelector('#secNm').textContent==='改名测试');
    document.querySelector('#secPw').value='abc12345'; document.querySelector('#secPwSave').click(); await w(20); ok('改密码：保存并提示',document.querySelector('#toast').textContent.includes('密码已修改')); T.ACC().users[T.curUser().id].name='读者1234';""")
rep("""document.querySelector('#auSkip').click(); await w(20); ok('什么都不填，点"直接体验"也能进，有默认昵称',""","""document.querySelector('#auGo').click(); await w(20); ok('什么都不填也能登录，有默认昵称',""")
save('生成/自测_两本书.js',s)
# 服务端模式
s=load('生成/自测/自测_服务端模式.js')
rep("""    ok('书架标题右边并列"找书 · 导入"两个小字入口',document.querySelector('.shh .shacts')?.textContent.replace(/\\s/g,'')==='找书·导入'&&!!document.querySelector('.shacts #impFile'));
    ok('书架底部没有大按钮',!document.querySelector('.impbox .btn')&&!document.querySelector('.btn.wide#impBtn'));
    ok('导入能选的格式包括 pdf、epub、mobi',['.pdf','.epub','.mobi'].every(x=>document.querySelector('#impFile').accept.includes(x)));""",
    """    ok('书架标题右边并列"找书 · 导入"两个小字入口',document.querySelector('.shh .shacts')?.textContent.replace(/\\s/g,'')==='找书·导入'&&!!document.querySelector('#impBtn'));
    ok('书架底部没有大按钮',!document.querySelector('.impbox .btn')&&!document.querySelector('.btn.wide#impBtn'));
    document.querySelector('#impBtn').click(); await w(30);
    ok('点"导入"进独立页面（不是直接弹文件选择）：有标题、选择文件、格式说明',document.querySelector('.pgbar b').textContent==='导入'&&!!document.querySelector('#impDrop')&&document.querySelector('.impdrop small').textContent.includes('常用格式')&&document.querySelector('.impdrop small').textContent.includes('MB'));
    ok('导入页：会发生什么三步、版权提醒、去找书',document.querySelectorAll('.impsteps li').length===3&&document.querySelector('.impnote').textContent.includes('有权阅读')&&!!document.querySelector('#impFind'));
    ok('导入能选的格式包括 pdf、epub、mobi',['.pdf','.epub','.mobi'].every(x=>document.querySelector('#impFile').accept.includes(x)));
    { const f=new File(['x'.repeat(10)],'测试书.txt',{type:'text/plain'}); Object.defineProperty(document.querySelector('#impFile'),'files',{value:[f],configurable:true}); document.querySelector('#impFile').dispatchEvent(new Event('change')); await w(400);
      ok('选了文件：页内显示进度或结果（有"去读"）',!!document.querySelector('#impStat .imstat, #impStat.imstat')&&/去读|没能导入|识别|上传/.test(document.querySelector('#impStat').textContent),document.querySelector('#impStat').textContent.slice(0,40)); }
    document.querySelector('#pgBack').click(); await w(30);""")
save('生成/自测/自测_服务端模式.js',s)
print('ok')
