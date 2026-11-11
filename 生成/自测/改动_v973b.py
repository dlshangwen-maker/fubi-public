"""v9.73b：账户页（真账号时）：改密码要填当前密码；退出走接口并刷新；注销要再输一次密码"""
import os
B=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))+'/'
P=B+'Demo/模板.html'
s=open(P,encoding='utf-8').read()
def rep(a,b,n=1):
    global s
    c=s.count(a); assert c==n,(c,a[:80]); s=s.replace(a,b)
rep("""<section class="mebox"><label class="fld"><span>修改密码</span><input id="secPw" type="password" autocomplete="new-password" placeholder="新密码，6～20 位，含字母和数字"></label><button class="btn ghost" id="secPwSave">保存新密码</button></section>""",
"""<section class="mebox">${AUTH?'<label class="fld"><span>当前密码</span><input id="secPwOld" type="password" autocomplete="current-password"></label>':''}<label class="fld"><span>${AUTH?'新密码':'修改密码'}</span><input id="secPw" type="password" autocomplete="new-password" placeholder="${AUTH?'8 位以上，要有字母和数字':'新密码，6～20 位，含字母和数字'}"></label><button class="btn ghost" id="secPwSave">保存新密码</button></section>""")
rep("""<div><span>账号</span><b>${esc(maskAcc(u.id))}</b></div>""","""<div><span>账号</span><b>${esc(AUTH?u.id:maskAcc(u.id))}</b></div>""")
rep("""  $('#secPwSave').onclick=()=>{ const p=$('#secPw').value; if(!p){ $('#secPw').focus(); return; } ACC.users[u.id].pw=pwh(p);""",
"""  if(AUTH){
    $('#secPwSave').onclick=async()=>{ const o=$('#secPwOld').value, p=$('#secPw').value; if(!o){ $('#secPwOld').focus(); return; } if(!p){ $('#secPw').focus(); return; }
      const r=await api('/api/auth/password',{old:o,new:p}); if(!r.ok){ toast(`<div class="tq">${esc(r.error||'没改成功')}</div>`,null,3500); return; }
      $('#secPwOld').value=''; $('#secPw').value=''; toast('<div class="tq">密码已修改，其他设备需要重新登录</div>',null,3000); };
    $('#secOut').onclick=()=>confirmSheet('退出登录？','退出后回到书架。阅读记录和笔记都还在，重新登录就能接着读。','退出登录',async()=>{ await api('/api/auth/logout'); location.reload(); });
    $('#secDel').onclick=()=>{ confirmSheet('注销这个账号？','账号、你导入的书和全部阅读记录都会删除，无法恢复。想只是换个账号读，请用“退出登录”。','继续',()=>{
      openSheet(`<div class="shead"><span class="ttl">输入密码确认</span><button class="x" data-close aria-label="关闭">×</button></div><div class="sbody"><label class="fld"><span>密码</span><input id="delPw" type="password" autocomplete="current-password"></label><p class="aumsg" id="delMsg" role="alert"></p></div><div class="sfoot"><button class="btn ghost" data-close>取消</button><button class="btn dgr" id="delGo" style="margin-left:auto">确认注销</button></div>`);
      $('#delGo').onclick=async()=>{ const r=await api('/api/auth/delete',{password:$('#delPw').value}); if(!r.ok){ $('#delMsg').textContent=r.error||'没成功'; return; } closeSheet(); location.reload(); }; },true); };
    return;
  }
  $('#secPwSave').onclick=()=>{ const p=$('#secPw').value; if(!p){ $('#secPw').focus(); return; } ACC.users[u.id].pw=pwh(p);""")
open(P,'w',encoding='utf-8').write(s); print('ok')
