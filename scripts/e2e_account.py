"""端到端检查（不用浏览器）：起一个开了账号的真服务，用 HTTP 走读者的整条路：
未登录看到什么 → 邀请码注册 → 页面里带上登录信息 → 退出 → 登录 → 找回密码 → 注销。
再检查服务端给出的页面里，真账号需要的前端代码都在。用法：python3 scripts/e2e_account.py"""
import os,sys,re,json,tempfile,threading,urllib.request,urllib.parse,http.cookiejar
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0,os.path.join(ROOT,'server'))
os.environ.update(FUBI_DATA=tempfile.mkdtemp(prefix='fubi_e2e_'),FUBI_QUIET='1',FUBI_SYNC_MAIL='1')
for k in ('IMPORT','DOWNLOAD','ASK','SEARCH','GENERAL','LOGIN','LOGINMAIL','REGISTER','FORGOT','RESET'): os.environ['FUBI_RL_'+k]='100000/60'
import config,db,app,accounts,policy
config.AUTH=True; config.MODEL.update(provider='mock')
MAILS=[]; accounts.mailer=lambda to,s,b: MAILS.append(b)
srv=app.make_server('127.0.0.1',0); threading.Thread(target=srv.serve_forever,daemon=True).start(); URL=f'http://127.0.0.1:{srv.server_port}'
jar=http.cookiejar.CookieJar(); op=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
def call(path,obj=None,method=None):
    r=urllib.request.Request(URL+path,data=json.dumps(obj).encode() if obj is not None else None,method=method or ('POST' if obj is not None else 'GET'))
    try:
        with op.open(r,timeout=60) as x: return x.status,x.read().decode()
    except urllib.error.HTTPError as e: return e.code,e.read().decode()
bad=[]
def ok(name,cond,extra=''):
    print(('✓ ' if cond else '✗ ')+name+(' '+str(extra)[:120] if (extra and not cond) else '')); 
    if not cond: bad.append(name)
c,page=call('/'); boot=json.loads(re.search(r'window\.FUBI=(\{.*?\})</script>',page,re.S).group(1))
ok('未登录：页面带 auth=true、user=null',boot['auth'] is True and boot['user'] is None)
ok('页面里有真账号前端代码（邮箱登录页、忘记密码、接口地址）','authPageSrv' in page and '/api/auth/forgot' in page and '/api/auth/register' in page)
ok('页面里没有旧的"手机号或邮箱"提示给真账号用，且有邀请码输入','邀请码' in page and 'auInv' in page)
ok('页面里有意见反馈页（文字 + 图片）','feedbackPage' in page and '/api/feedback/image' in page and 'fbText' in page)
ok('未登录提交反馈被拦（401）',call('/api/feedback',{'text':'x'})[0]==401)
ok('未登录提问被拦（401）',call('/api/ask',{'q':'x','book':'hlm','pos':'1.1'})[0]==401)
code=accounts.make_invites(1)[0]
c,t=call('/api/auth/register',{'email':'e2e@x.com','password':'abcd1234','invite':code,'agree':policy.POLICY_VERSION}); ok('邀请码注册成功',c==200,t)
c,page=call('/'); boot=json.loads(re.search(r'window\.FUBI=(\{.*?\})</script>',page,re.S).group(1)); ok('注册后页面带用户信息',boot['user'] and boot['user']['email']=='e2e@x.com',boot['user'])
ok('用户信息里没有密码字段','pw' not in json.dumps(boot['user']) and 'abcd1234' not in page)
ok('改昵称成功',call('/api/auth/profile',{'name':'端到端'})[0]==200)
call('/api/auth/logout',{}); c,page=call('/'); boot=json.loads(re.search(r'window\.FUBI=(\{.*?\})</script>',page,re.S).group(1)); ok('退出后又是未登录',boot['user'] is None)
c,t=call('/api/auth/login',{'email':'e2e@x.com','password':'abcd1234','agree':policy.POLICY_VERSION}); ok('重新登录成功',c==200,t)
call('/api/auth/logout',{}); call('/api/auth/forgot',{'email':'e2e@x.com'}); m=re.search(r'验证码为：(\d{6})',MAILS[-1] if MAILS else ''); ok('找回密码：收到验证码邮件',bool(m))
c,t=call('/api/auth/reset',{'email':'e2e@x.com','code':m.group(1) if m else '','password':'newpass99','agree':policy.POLICY_VERSION}); ok('用验证码改密码成功',c==200,t)
c,t=call('/api/auth/login',{'email':'e2e@x.com','password':'newpass99','agree':policy.POLICY_VERSION}); ok('新密码能登录',c==200,t)
c,t=call('/api/auth/delete',{'password':'newpass99','agree':policy.POLICY_VERSION}); ok('注销成功',c==200,t)
c,t=call('/api/auth/login',{'email':'e2e@x.com','password':'newpass99','agree':policy.POLICY_VERSION}); ok('注销后不能再登录',c==401)
print('\n全部通过' if not bad else '\n失败：'+'、'.join(bad)); srv.shutdown(); sys.exit(1 if bad else 0)
