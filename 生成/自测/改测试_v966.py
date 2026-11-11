"""v9.66 自测：访客首页改成书架、账户页信息区、头像。"""
import os,shutil
B=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))+'/'
P=B+'生成/自测_两本书.js'
if not os.path.exists(B+'生成/自测_两本书_v966前备份.js'): shutil.copy(P,B+'生成/自测_两本书_v966前备份.js')
s=open(P,encoding='utf-8').read()
def rep(a,b):
    global s
    assert s.count(a)==1,(s.count(a),a[:70]); s=s.replace(a,b)
rep("ok('回到首页：有登录、注册入口和精读版封面',!!document.querySelector('.home')&&!!document.querySelector('#hmReg')&&document.querySelectorAll('.hmbooks .book').length===5);",
    "ok('回到首页：就是一个书架——右上角\"登录\"、五本精读版封面',!!document.querySelector('.home')&&!!document.querySelector('#hmLogin')&&document.querySelectorAll('.hmbooks .book').length===5);")
rep("ok('不登录的首页：介绍、三句话、精读版封面、登录入口',!!document.querySelector('.hmtag')&&document.querySelectorAll('.hmfeat .welrow').length===3&&!!document.querySelector('#hmLogin'));",
    "ok('不登录的首页不做营销页：没有大标题、介绍、大按钮',!document.querySelector('.hmtag,.hmsub,.hmfeat,.hmcta,#hmReg')&&document.querySelector('.home h1').textContent==='书架');")
# 账户页
rep("&&!!document.querySelector('#secDel')&&document.querySelector('.medl').textContent.includes('加入时间'));",
    "&&!!document.querySelector('#secDel')&&document.querySelector('.secinfo').textContent.includes('加入时间')&&!document.querySelector('.pgbody').textContent.includes('保存在'));")
# 头像
rep("    document.querySelector('#secName').value='改名测试'; document.querySelector('#secSave').click(); await w(20);",
    """    ok('账户页：头像可以点（有"改"的小图标）',!!document.querySelector('#secAv .avedit'));
    document.querySelector('#secAv').click(); await w(30);
    ok('头像面板：预览、字、8 种颜色、上传图片、恢复默认',!!document.querySelector('#avPrev .av')&&!!document.querySelector('#avCh')&&document.querySelectorAll('#sheet .avcol').length===8&&!!document.querySelector('#avFile')&&!!document.querySelector('#avReset'));
    document.querySelector('#avCh').value='伏'; document.querySelector('#avCh').dispatchEvent(new Event('input')); document.querySelectorAll('#sheet .avcol')[2].click(); await w(10);
    ok('改字、选颜色：预览马上变',document.querySelector('#avPrev .av').textContent==='伏'&&/rgb\\(47, 74, 140\\)/.test(document.querySelector('#avPrev .av').style.background));
    document.querySelector('#avSave').click(); await w(30);
    ok('保存后：账户页、我的、书架的头像都是新的',T.curUser().av&&T.curUser().av.ch==='伏'&&document.querySelector('.secid .av').textContent==='伏');
    T.mePage(); await w(20); ok('"我的"账号卡里是新头像',document.querySelector('#meAcc .av').textContent==='伏'); T.shelf(); await w(20); ok('书架右上角是新头像',document.querySelector('#shMe .av').textContent==='伏'); T.secPage(); await w(20);
    T.avatarSheet(T.curUser(),()=>T.secPage()); await w(20); document.querySelector('#avReset').click(); await w(30); ok('恢复默认：回到昵称首字',!T.curUser().av&&document.querySelector('.secid .av').textContent==='读');
    T.ACC().users[T.curUser().id].av={img:'data:image/jpeg;base64,/9j/4AAQ'}; T.secPage(); await w(20); ok('用图片做头像：显示图片',!!document.querySelector('.secid .av.img img')); delete T.ACC().users[T.curUser().id].av; T.secPage(); await w(20);
    document.querySelector('#secName').value='改名测试'; document.querySelector('#secSave').click(); await w(20);""")
open(P,'w',encoding='utf-8').write(s); print('ok')
