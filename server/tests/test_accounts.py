"""账号测试：真的起服务（开账号），走一遍 注册→登录→数据归属→改资料→改密码→找回→注销，以及各种不该成功的情况。
运行：cd server && python3 -m unittest discover -s tests"""
import os,sys,json,threading,unittest,tempfile,urllib.request,urllib.parse,http.cookiejar,time
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,os.path.dirname(HERE))
os.environ.setdefault('FUBI_DATA',tempfile.mkdtemp(prefix='fubi_acct_')); os.environ.update(FUBI_QUIET='1',FUBI_SYNC_IMPORT='1')
for _k in ('IMPORT','DOWNLOAD','ASK','SEARCH','GENERAL','LOGIN','LOGINMAIL','REGISTER','FORGOT','RESET','FEEDBACK','FBIMAGE','EVENT'): os.environ.setdefault('FUBI_RL_'+_k,'100000/60')
import config,db,app,accounts,ratelimit
MAILS=[]; srv=None; URL=''; _saved={}
def setUpModule():
    """开关只在这个文件的测试期间生效，结束后还原，免得影响同一进程里别的测试文件（它们测的是没开账号的服务）"""
    global srv,URL
    _saved.update(auth=config.AUTH,mailer=accounts.mailer,mail=os.environ.get('FUBI_SYNC_MAIL'),admins=config.ADMIN_EMAILS)
    config.AUTH=True; config.ADMIN_EMAILS=frozenset({'boss@x.com'}); config.MODEL.update(provider='mock'); os.environ['FUBI_SYNC_MAIL']='1'
    accounts.mailer=lambda to,subj,body: MAILS.append((to,subj,body))
    db.reset_for_tests(); srv=app.make_server('127.0.0.1',0); URL=f'http://127.0.0.1:{srv.server_port}'
    threading.Thread(target=srv.serve_forever,daemon=True).start()
def tearDownModule():
    srv.shutdown(); srv.server_close()
    config.AUTH=_saved['auth']; accounts.mailer=_saved['mailer']; config.ADMIN_EMAILS=_saved['admins']
    if _saved['mail'] is None: os.environ.pop('FUBI_SYNC_MAIL',None)
    else: os.environ['FUBI_SYNC_MAIL']=_saved['mail']
class C:
    def __init__(self): self.jar=http.cookiejar.CookieJar(); self.op=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.jar))
    def req(self,method,path,body=None,headers=None):
        r=urllib.request.Request(URL+path,data=body,method=method,headers=headers or {})
        try:
            with self.op.open(r,timeout=60) as resp: raw=resp.read(); code=resp.status; h=dict(resp.headers)
        except urllib.error.HTTPError as e: raw=e.read(); code=e.code; h=dict(e.headers)
        return code,raw,h
    def j(self,method,path,obj=None,headers=None):
        c,raw,h=self.req(method,path,json.dumps(obj).encode() if obj is not None else None,headers)
        try: return c,json.loads(raw) if raw else None
        except ValueError: return c,raw.decode()
    def post(self,path,**o):
        import policy
        if path in ('/api/auth/register','/api/auth/login') and 'agree' not in o: o['agree']=policy.POLICY_VERSION   # 默认视为已同意；要测没同意时显式传 agree=None
        return self.j('POST',path,o)
    def has_cookie(self,name): return any(c.name==name for c in self.jar)
def invite(): return accounts.make_invites(1)[0]
PW='abcd1234'

class KeepAlive(unittest.TestCase):
    """复现 11-02 用户遇到的"注册第一次提示没成功、再点一次才成功"：
    没登录时页面会在后台 PUT /api/state，服务端以 401 拒绝却没读掉请求内容；同一条连接上的下一个请求（用户点注册）
    就会把残留的内容当成请求行，得到一个不是 JSON 的错误。"""
    def setUp(self): ratelimit.reset()
    def _conn(self):
        import http.client; h,p=URL.replace('http://','').split(':'); return http.client.HTTPConnection(h,int(p),timeout=20)
    def test_rejected_request_with_unread_body_does_not_break_next_request_on_same_connection(self):
        c=self._conn(); big=json.dumps({'rb_x':{'a':'x'*3000}}).encode()
        c.request('PUT','/api/state',body=big,headers={'Content-Type':'application/json'}); r=c.getresponse(); r.read(); self.assertEqual(r.status,401)
        c.request('POST','/api/auth/login',body=json.dumps({'email':'nobody@x.com','password':'abcd1234','agree':__import__('policy').POLICY_VERSION}).encode(),headers={'Content-Type':'application/json'})
        r=c.getresponse(); raw=r.read()
        self.assertEqual(r.status,401,raw[:120]); self.assertEqual(json.loads(raw)['error'],'邮箱或密码错误')
    def test_rate_limited_post_does_not_poison_connection_either(self):
        c=self._conn(); os.environ['FUBI_RL_GENERAL']='1/60'
        try:
            c.request('POST','/api/auth/login',body=b'{}',headers={'Content-Type':'application/json'}); c.getresponse().read()
            c.request('POST','/api/auth/login',body=json.dumps({'email':'a@x.com','password':'x'*3000,'agree':__import__('policy').POLICY_VERSION}).encode(),headers={'Content-Type':'application/json'}); r=c.getresponse(); r.read(); self.assertEqual(r.status,429)
        finally: os.environ['FUBI_RL_GENERAL']='100000/60'; ratelimit.reset()
        c.request('POST','/api/auth/login',body=json.dumps({'email':'nobody@x.com','password':'abcd1234','agree':__import__('policy').POLICY_VERSION}).encode(),headers={'Content-Type':'application/json'}); r=c.getresponse(); raw=r.read()
        self.assertEqual(r.status,401,raw[:120])

class Auth(unittest.TestCase):
    def setUp(self): ratelimit.reset(); MAILS.clear()
    def test_register_requires_valid_unused_invite(self):
        a=C(); c,r=a.post('/api/auth/register',email='a1@x.com',password=PW,invite='WRONGCODE'); self.assertEqual(c,400); self.assertIn('邀请码',r['error'])
        code=invite(); c,r=a.post('/api/auth/register',email='a1@x.com',password=PW,invite=code); self.assertEqual(c,200); self.assertTrue(a.has_cookie('fubi_sess'))
        b=C(); c,r=b.post('/api/auth/register',email='b1@x.com',password=PW,invite=code); self.assertEqual(c,400,'一个码只能用一次')
        c,r=b.post('/api/auth/register',email='A1@X.com',password=PW,invite=invite()); self.assertEqual(c,400); self.assertIn('已注册',r['error'],'邮箱不分大小写')
    def test_invite_code_case_and_dash_forgiving(self):
        code=invite(); typed=(code[:4]+'-'+code[4:]).lower()
        c,r=C().post('/api/auth/register',email='cc@x.com',password=PW,invite=typed); self.assertEqual(c,200)
    def test_bad_email_and_weak_passwords(self):
        a=C()
        for em,pw,word in [('notanemail',PW,'邮箱'),('w1@x.com','short1','密码'),('w2@x.com','onlyletters','密码'),('w3@x.com','12345678','密码')]:
            c,r=a.post('/api/auth/register',email=em,password=pw,invite=invite()); self.assertEqual(c,400,em+pw); self.assertIn(word,r['error'])
    def test_login_logout_and_session(self):
        a=C(); a.post('/api/auth/register',email='l1@x.com',password=PW,invite=invite())
        t=a.req('GET','/')[1].decode(); self.assertIn('"user": {"email": "l1@x.com"',t); self.assertIn('"auth": true',t)
        a.post('/api/auth/logout'); self.assertNotIn('"user": {"email"',a.req('GET','/')[1].decode())
        b=C(); c,r=b.post('/api/auth/login',email='l1@x.com',password='wrongpass1'); self.assertEqual(c,401); self.assertEqual(r['error'],'邮箱或密码错误')
        c,r=b.post('/api/auth/login',email='nobody@x.com',password=PW); self.assertEqual(c,401); self.assertEqual(r['error'],'邮箱或密码错误','不泄露邮箱有没有注册')
        c,r=b.post('/api/auth/login',email='l1@x.com',password=PW); self.assertEqual(c,200)
    def test_password_not_stored_plain_and_token_stored_hashed(self):
        a=C(); a.post('/api/auth/register',email='h1@x.com',password=PW,invite=invite())
        pw=db.one('select pw from users where email=?',('h1@x.com',))[0]; self.assertTrue(pw.startswith('scrypt$')); self.assertNotIn(PW,pw)
        tok=[c.value for c in a.jar if c.name=='fubi_sess'][0]; self.assertFalse(db.one('select 1 from sessions where h=?',(tok,)),'库里不能是令牌原文')
    def test_anonymous_cannot_use_costly_or_writing_endpoints(self):
        a=C()
        for m,p in [('POST','/api/ask'),('POST','/api/import'),('POST','/api/download'),('POST','/api/preview'),('GET','/api/search?q=a'),('PUT','/api/state')]:
            c,_=a.j(m,p,{} if m!='GET' else None); self.assertEqual(c,401,p)
        self.assertEqual(a.j('GET','/api/health')[0],200); self.assertEqual(a.j('GET','/api/shelf')[0],200)
    def test_data_belongs_to_account_and_is_private(self):
        a=C(); a.post('/api/auth/register',email='d1@x.com',password=PW,invite=invite())
        c,r=a.j('POST','/api/import',None,{'X-Filename':'c.docx'}) if False else (0,0)
        data=open(os.path.join(HERE,'fixtures','c.docx'),'rb').read()
        c,raw,_=a.req('POST','/api/import',data,{'X-Filename':'c.docx'}); self.assertEqual(c,200); bid=json.loads(raw)['id']
        a.j('PUT','/api/state',{'rb_x':{'furthest':3}})
        b=C(); b.post('/api/auth/register',email='d2@x.com',password=PW,invite=invite())
        self.assertNotIn(bid,[x['id'] for x in b.j('GET','/api/shelf')[1]['books']],'别人的账号看不到')
        a2=C(); a2.post('/api/auth/login',email='d1@x.com',password=PW)
        self.assertIn(bid,[x['id'] for x in a2.j('GET','/api/shelf')[1]['books']],'换设备登录同一个账号，书还在')
        self.assertEqual(a2.j('GET','/api/state')[1].get('rb_x'),{'furthest':3},'阅读记录跟着账号')
    def test_device_data_adopted_on_register(self):
        a=C(); a.req('GET','/'); self.assertFalse(a.has_cookie('fubi_sess'))
        dev=[c.value for c in a.jar if c.name=='fubi_dev'][0]
        import books; bid=books.import_file(open(os.path.join(HERE,'fixtures','c.docx'),'rb').read(),'c.docx',dev,background=False)
        db.run("insert into progress(device,book,state,t) values(?,?,?,?)",(dev,'rb_old','{"furthest":9}',time.time()))
        a.post('/api/auth/register',email='ad@x.com',password=PW,invite=invite())
        self.assertIn(bid,[x['id'] for x in a.j('GET','/api/shelf')[1]['books']]); self.assertEqual(a.j('GET','/api/state')[1].get('rb_old'),{'furthest':9})
    def test_profile_and_password_change(self):
        a=C(); a.post('/api/auth/register',email='p1@x.com',password=PW,invite=invite()); a2=C(); a2.post('/api/auth/login',email='p1@x.com',password=PW)
        self.assertEqual(a.post('/api/auth/profile',name='新昵称',av={'ch':'伏','c':'#2F4A8C'})[0],200)
        t=a.req('GET','/')[1].decode(); self.assertIn('新昵称',t)
        self.assertEqual(a.post('/api/auth/profile',av={'img':'javascript:alert(1)'})[0],400,'头像图片只收 data:image')
        self.assertEqual(a.post('/api/auth/password',old='wrong1234',new='newpass99')[0],403)
        self.assertEqual(a.post('/api/auth/password',old=PW,new='newpass99')[0],200)
        self.assertEqual(a2.j('POST','/api/ask',{'q':'x','book':'hlm','pos':'1.1'})[0],401,'改密码后其他设备要重新登录'); self.assertNotEqual(a.j('GET','/api/shelf')[0],401)
        self.assertEqual(C().post('/api/auth/login',email='p1@x.com',password=PW)[0],401); self.assertEqual(C().post('/api/auth/login',email='p1@x.com',password='newpass99')[0],200)
    def test_forgot_and_reset(self):
        a=C(); a.post('/api/auth/register',email='f1@x.com',password=PW,invite=invite())
        c,r=C().post('/api/auth/forgot',email='nobody@x.com'); self.assertEqual(c,200); self.assertFalse(MAILS,'没注册的邮箱不发信，但回复一样')
        c,r2=C().post('/api/auth/forgot',email='f1@x.com'); self.assertEqual(c,200); self.assertEqual(r,r2); self.assertEqual(len(MAILS),1)
        to,subj,body=MAILS[0]; self.assertEqual(to,'f1@x.com'); import re; code=re.search(r'验证码为：(\d{6})',body).group(1)
        c,r=C().post('/api/auth/reset',email='f1@x.com',code='000000' if code!='000000' else '111111',password='brandnew1'); self.assertEqual(c,400)
        c,r=C().post('/api/auth/reset',email='f1@x.com',code=code,password='short'); self.assertEqual(c,400)
        c,r=C().post('/api/auth/reset',email='f1@x.com',code=code,password='brandnew1'); self.assertEqual(c,200)
        self.assertEqual(C().post('/api/auth/login',email='f1@x.com',password='brandnew1')[0],200)
        self.assertEqual(C().post('/api/auth/reset',email='f1@x.com',code=code,password='another123')[0],400,'验证码只能用一次')
        self.assertEqual(a.j('POST','/api/ask',{'q':'x','book':'hlm','pos':'1.1'})[0],401,'重置后旧会话作废')
    def test_reset_code_locks_after_too_many_wrong_tries(self):
        a=C(); a.post('/api/auth/register',email='f2@x.com',password=PW,invite=invite()); C().post('/api/auth/forgot',email='f2@x.com')
        import re; code=re.search(r'验证码为：(\d{6})',MAILS[-1][2]).group(1); wrong='000000' if code!='000000' else '111111'
        for _ in range(5): C().post('/api/auth/reset',email='f2@x.com',code=wrong,password='brandnew1')
        c,r=C().post('/api/auth/reset',email='f2@x.com',code=code,password='brandnew1'); self.assertEqual(c,400,'试错 5 次后正确的也作废'); self.assertIn('重新获取',r['error'])
    def test_reset_code_expires(self):
        a=C(); a.post('/api/auth/register',email='f3@x.com',password=PW,invite=invite()); C().post('/api/auth/forgot',email='f3@x.com')
        import re; code=re.search(r'验证码为：(\d{6})',MAILS[-1][2]).group(1); db.run('update resets set exp=? where email=?',(time.time()-1,'f3@x.com'))
        self.assertEqual(C().post('/api/auth/reset',email='f3@x.com',code=code,password='brandnew1')[0],400)
    def test_delete_account_removes_everything(self):
        a=C(); a.post('/api/auth/register',email='x1@x.com',password=PW,invite=invite())
        a.req('POST','/api/import',open(os.path.join(HERE,'fixtures','c.docx'),'rb').read(),{'X-Filename':'c.docx'}); a.j('PUT','/api/state',{'rb_y':{'a':1}})
        uid=db.one('select id from users where email=?',('x1@x.com',))[0]
        self.assertEqual(a.post('/api/auth/delete',password='wrong1234')[0],403); self.assertEqual(a.post('/api/auth/delete',password=PW)[0],200)
        self.assertFalse(db.one('select 1 from users where id=?',(uid,))); self.assertFalse(db.one('select 1 from books where owner=?',('u%d'%uid,))); self.assertFalse(db.one('select 1 from progress where device=?',('u%d'%uid,)))
        self.assertEqual(C().post('/api/auth/login',email='x1@x.com',password=PW)[0],401)
    def test_login_rate_limit_per_mail(self):
        a=C(); a.post('/api/auth/register',email='r1@x.com',password=PW,invite=invite()); os.environ['FUBI_RL_LOGINMAIL']='3/600'
        try:
            for _ in range(3): self.assertEqual(C().post('/api/auth/login',email='r1@x.com',password='wrongpass1')[0],401)
            c,r=C().post('/api/auth/login',email='r1@x.com',password=PW); self.assertEqual(c,429); self.assertIn('登录请求过于频繁',r['error'])
        finally: os.environ['FUBI_RL_LOGINMAIL']='100000/60'
    def _admin(self):
        a=C()
        if a.post('/api/auth/register',email='boss@x.com',password=PW,invite=invite())[0]!=200: a.post('/api/auth/login',email='boss@x.com',password=PW)   # 同一模块里数据库不重置：第一次注册，之后登录
        a.op=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(a.jar),type('NoRedir',(urllib.request.HTTPRedirectHandler,),{'redirect_request':lambda *x,**k:None})); return a
    FORM={'Content-Type':'application/x-www-form-urlencoded'}
    def test_admin_only_for_listed_account(self):
        self.assertEqual(C().req('GET','/admin')[0],403,'没登录')
        self.assertEqual(C().req('GET','/admin?token=t0k')[0],403,'口令方式已取消')
        u=C(); u.post('/api/auth/register',email='plain@x.com',password=PW,invite=invite())
        self.assertEqual(u.req('GET','/admin')[0],403,'普通账号不能进')
        self.assertEqual(u.req('POST','/admin/invite',b'n=1',self.FORM)[0],403); self.assertEqual(u.req('POST','/admin/testmail',b'to=a@x.com',self.FORM)[0],403); self.assertEqual(u.req('POST','/admin/retry',b'',self.FORM)[0],403)
        a=self._admin(); c,raw,_=a.req('GET','/admin'); self.assertEqual(c,200); self.assertIn('生成队列',raw.decode()); self.assertNotIn('token=',raw.decode(),'页面里不再带口令')
    def test_admin_can_make_invites_via_form(self):
        a=self._admin(); body=urllib.parse.urlencode({'note':'给小王','n':'2'}).encode(); n0=db.one('select count(*) from invites')[0]
        c,_,h=a.req('POST','/admin/invite',body,self.FORM); self.assertEqual(c,303); self.assertEqual(h['Location'],'/admin#invites')
        self.assertEqual(db.one('select count(*) from invites')[0],n0+2); self.assertTrue(db.one("select 1 from invites where note='给小王'"))
        self.assertIn('邀请码',a.req('GET','/admin')[1].decode())
    def test_resend_replaces_previous_code(self):
        import re; C().post('/api/auth/register',email='rs@x.com',password=PW,invite=invite())
        C().post('/api/auth/forgot',email='rs@x.com'); C().post('/api/auth/forgot',email='rs@x.com'); self.assertEqual(len(MAILS),2)
        c1,c2=[re.search(r'验证码为：(\d{6})',m[2]).group(1) for m in MAILS]
        if c1!=c2: self.assertEqual(C().post('/api/auth/reset',email='rs@x.com',code=c1,password='another123')[0],400,'重新发送后旧验证码作废')
        self.assertEqual(C().post('/api/auth/reset',email='rs@x.com',code=c2,password='another123')[0],200,'新验证码可用')
    def test_admin_test_mail(self):
        a=self._admin(); H=self.FORM; body=lambda to:urllib.parse.urlencode({'to':to}).encode()
        c,_,h=a.req('POST','/admin/testmail',body('t@x.com'),H); self.assertEqual(c,303); self.assertEqual(MAILS[-1][0],'t@x.com'); self.assertEqual(MAILS[-1][1],'【伏笔】测试邮件'); self.assertIn('mailres=',h['Location']); n=len(MAILS)
        c,_,h=a.req('POST','/admin/testmail',body('bad'),H); self.assertEqual(c,303); self.assertEqual(len(MAILS),n,'邮箱格式不对不发信'); self.assertIn(urllib.parse.quote('邮箱格式不正确'),h['Location'])
        old=accounts.mailer
        def boom(*x): raise OSError('smtp down')
        accounts.mailer=boom
        try: c,_,h=a.req('POST','/admin/testmail',body('t@x.com'),H); self.assertIn(urllib.parse.quote('发送失败'),h['Location']); self.assertIn(urllib.parse.quote('smtp down'),h['Location'],'后台要能看到真实错误')
        finally: accounts.mailer=old
        page=a.req('GET','/admin?mailres='+urllib.parse.quote('测试邮件已发送至 t@x.com'))[1].decode(); self.assertIn('发送测试邮件',page); self.assertIn('测试邮件已发送至 t@x.com',page)
    # ---- 使用情况上报接口 ----
    def test_event_endpoint_needs_login_and_filters(self):
        self.assertEqual(C().post('/api/event',events=[{'k':'open'}])[0],401)
        u=self._user('ev1@x.com'); c,r=u.post('/api/event',events=[{'k':'open'},{'k':'evil'},{'k':'read','b':'hlm','n':12,'s':30}]); self.assertEqual(c,200); self.assertEqual(r['n'],2)
        uid=db.one('select id from users where email=?',('ev1@x.com',))[0]; self.assertEqual(db.one('select count(*) from events where uid=?',(uid,))[0],2)
    def test_event_rate_limited(self):
        u=self._user('ev2@x.com'); os.environ['FUBI_RL_EVENT']='2/60'
        try:
            self.assertEqual(u.post('/api/event',events=[{'k':'open'}])[0],200); self.assertEqual(u.post('/api/event',events=[{'k':'open'}])[0],200); self.assertEqual(u.post('/api/event',events=[{'k':'open'}])[0],429)
        finally: os.environ['FUBI_RL_EVENT']='100000/60'
    def test_admin_usage_shows_book_title_not_author(self):
        u=self._user('ev4@x.com'); u.post('/api/event',events=[{'k':'book','b':'hound'},{'k':'read','b':'hound','n':17,'s':60}])
        page=self._admin().req('GET','/admin')[1].decode(); self.assertIn('巴斯克维尔的猎犬',page,'显示书名'); self.assertNotIn('<td>柯南·道尔</td>',page,'不能把作者当书名')
    def test_admin_page_shows_monitor_state(self):
        import monitor; old=monitor.state_path; p=os.path.join(config.DATA,'mon_test.json'); monitor.state_path=lambda:p
        try:
            a=self._admin(); self.assertIn('还没有巡检记录',a.req('GET','/admin')[1].decode())
            json.dump({'last':time.time(),'issues':{},'fails':0},open(p,'w')); self.assertIn('正常',a.req('GET','/admin')[1].decode())
            json.dump({'last':time.time(),'issues':{'disk':{'msg':'磁盘剩余 5%','since':1,'alerted':1}},'fails':0},open(p,'w')); pg=a.req('GET','/admin')[1].decode(); self.assertIn('有异常',pg); self.assertIn('磁盘剩余 5%',pg)
            json.dump({'last':time.time()-3600,'issues':{},'fails':0},open(p,'w')); self.assertIn('巡检可能已停止',a.req('GET','/admin')[1].decode())
        finally: monitor.state_path=old; os.path.exists(p) and os.remove(p)
    def test_admin_page_shows_usage(self):
        u=self._user('ev3@x.com'); u.post('/api/event',events=[{'k':'open'},{'k':'read','b':'hlm','n':40,'s':180}])
        page=self._admin().req('GET','/admin')[1].decode(); self.assertIn('使用情况',page); self.assertIn('次日回访',page); self.assertIn('只记行为',page)
    # ---- 协议与政策 ----
    def test_policy_texts_public_and_versioned(self):
        import policy
        for n,t in (('terms','用户协议'),('privacy','隐私政策')):
            c,r=C().j('GET','/api/policy/'+n); self.assertEqual(c,200); self.assertEqual(r['title'],t); self.assertEqual(r['version'],policy.POLICY_VERSION); self.assertTrue(len(r['sections'])>=6)
        self.assertEqual(C().j('GET','/api/policy/other')[0],404)
        import re; page=C().req('GET','/')[1].decode(); boot=json.loads(re.search(r'window\.FUBI=(\{.*?\})</script>',page,re.S).group(1)); self.assertEqual(boot['policy'],policy.POLICY_VERSION,'页面要知道当前协议版本')
    def test_register_and_login_require_current_agreement(self):
        import policy
        a=C(); c,r=a.post('/api/auth/register',email='ag1@x.com',password=PW,invite=invite(),agree=None); self.assertEqual(c,428); self.assertIn('同意',r['error'])
        c,r=a.post('/api/auth/register',email='ag1@x.com',password=PW,invite=invite(),agree='1999-01-01'); self.assertEqual(c,428,'旧版本不算')
        self.assertFalse(db.one('select 1 from users where email=?','ag1@x.com'.split()),'没同意就不建账号')
        c,r=a.post('/api/auth/register',email='ag1@x.com',password=PW,invite=invite()); self.assertEqual(c,200)
        row=db.one('select agreed_ver,agreed_t from users where email=?',('ag1@x.com',)); self.assertEqual(row[0],policy.POLICY_VERSION); self.assertTrue(row[1]>0,'留痕：同意的版本和时间')
        b=C(); c,r=b.post('/api/auth/login',email='ag1@x.com',password=PW,agree=None); self.assertEqual(c,428); self.assertEqual(b.j('POST','/api/ask',{'q':'x','book':'hlm','pos':'1.1'})[0],401,'没同意不能登录：登录后才能提问')
        c,r=b.post('/api/auth/login',email='ag1@x.com',password=PW,agree='1999-01-01'); self.assertEqual(c,428,'政策升级后，老版本的同意作废，要重新同意')
        self.assertEqual(b.post('/api/auth/login',email='ag1@x.com',password=PW)[0],200)
    def test_wrong_password_checked_before_agreement_does_not_leak(self):
        b=C(); c,r=b.post('/api/auth/login',email='nobody@x.com',password=PW,agree=None); self.assertEqual(c,428,'没同意时一律先要求同意，不暴露邮箱有没有注册')
    def test_searches_before_login_move_to_account_and_get_deleted(self):
        accounts.adopt_device(0,'devX') if False else None
        u=C(); db.run('insert into searches(q,device,t) values(?,?,?)',('登录前搜的','devX',time.time()))
        uid=accounts.register('sr1@x.com',PW,invite(),'',__import__('policy').POLICY_VERSION); accounts.adopt_device(uid,'devX')
        self.assertEqual(db.one('select device from searches where q=?',('登录前搜的',))[0],'u%d'%uid)
        db.run('delete from sessions where uid=?',(uid,)); accounts.delete_account(uid,PW); self.assertIsNone(db.one('select 1 from searches where q=?',('登录前搜的',)),'注销后一并删除')
    def test_delete_account_removes_feedback_events_searches(self):
        import feedback,usage,search
        u=self._user('del1@x.com'); tid=json.loads(self._upload(u,self.PNG)[1])['id']; fid=u.post('/api/feedback',text='要被删掉',images=[tid])[1]['id']
        uid=db.one('select id from users where email=?',('del1@x.com',))[0]; db.run('insert into events(uid,t,day,kind) values(?,?,?,?)',(uid,time.time(),'2026-11-03','open'))
        db.run('insert into searches(q,device,t) values(?,?,?)',('红楼梦','u%d'%uid,time.time()))
        self.assertTrue(os.path.isdir(feedback._dir(str(fid))))
        self.assertEqual(u.post('/api/auth/delete',password=PW)[0],200)
        self.assertIsNone(db.one('select 1 from feedback where uid=?',(uid,))); self.assertIsNone(db.one('select 1 from events where uid=?',(uid,))); self.assertIsNone(db.one('select 1 from searches where device=?',('u%d'%uid,))); self.assertFalse(os.path.isdir(feedback._dir(str(fid))),'反馈图片文件也删')
    # ---- 反馈 ----
    PNG=b'\x89PNG\r\n\x1a\n'+b'\x00'*64
    def _user(self,email):
        u=C(); u.post('/api/auth/register',email=email,password=PW,invite=invite()); return u
    def _upload(self,u,data):
        return u.req('POST','/api/feedback/image',data,{'Content-Type':'application/octet-stream'})
    def test_feedback_needs_login_and_text(self):
        self.assertEqual(C().post('/api/feedback',text='x')[0],401); self.assertEqual(self._upload(C(),self.PNG)[0],401)
        u=self._user('fb0@x.com'); c,r=u.post('/api/feedback',text='   '); self.assertEqual(c,400); self.assertIn('反馈内容',r['error'])
        c,r=u.post('/api/feedback',text='字'*2001); self.assertEqual(c,400)
    def test_feedback_text_and_images_roundtrip(self):
        u=self._user('fb1@x.com'); ids=[]
        for _ in range(2):
            c,raw,_=self._upload(u,self.PNG); self.assertEqual(c,200); ids.append(json.loads(raw)['id'])
        c,r=u.post('/api/feedback',text='书架上的详情图标看不清',page='shelf',images=ids); self.assertEqual(c,200)
        row=db.one('select uid,email,text,page,imgs,status from feedback where id=?',(r['id'],)); self.assertEqual(row[1],'fb1@x.com'); self.assertEqual(row[3],'shelf'); self.assertEqual(len(json.loads(row[4])),2); self.assertEqual(row[5],'new')
        c,r2=u.post('/api/feedback',text='再用同一张图',images=ids); self.assertEqual(c,400,'图片只能用一次（提交后临时文件已移走）')
    def test_feedback_image_rules(self):
        u=self._user('fb2@x.com')
        self.assertEqual(self._upload(u,b'GIF89a'+b'0'*10)[0],200,'GIF 可以')
        c,raw,_=self._upload(u,b'<html><script>alert(1)</script></html>'); self.assertEqual(c,400,'网页文件改名成图片也不收')
        c,raw,_=self._upload(u,self.PNG+b'0'*(3*1024*1024)); self.assertEqual(c,400); self.assertIn('3 MB',json.loads(raw)['error'])
        self.assertEqual(self._upload(u,b'')[0],400)
        ids=[json.loads(self._upload(u,self.PNG)[1])['id'] for _ in range(4)]
        c,r=u.post('/api/feedback',text='太多',images=ids); self.assertEqual(c,400); self.assertIn('最多',r['error'])
    def test_feedback_cannot_use_others_temp_image(self):
        a=self._user('fb3@x.com'); b=self._user('fb4@x.com'); tid=json.loads(self._upload(a,self.PNG)[1])['id']
        c,r=b.post('/api/feedback',text='偷用别人的图',images=[tid]); self.assertEqual(c,400,'临时编号带账号 id，别人用不了')
        c,r=b.post('/api/feedback',text='路径穿越',images=['../../etc/passwd']); self.assertEqual(c,400)
    def test_feedback_rate_limited(self):
        u=self._user('fb5@x.com'); os.environ['FUBI_RL_FEEDBACK']='2/60'
        try:
            self.assertEqual(u.post('/api/feedback',text='一')[0],200); self.assertEqual(u.post('/api/feedback',text='二')[0],200)
            c,r=u.post('/api/feedback',text='三'); self.assertEqual(c,429); self.assertIn('提交反馈请求过于频繁',r['error'])
        finally: os.environ['FUBI_RL_FEEDBACK']='100000/60'
    def test_admin_sees_feedback_and_images_only_admin(self):
        u=self._user('fb6@x.com'); tid=json.loads(self._upload(u,self.PNG)[1])['id']
        fid=u.post('/api/feedback',text='后台能看到<b>这条</b>',page='reader',images=[tid])[1]['id']
        a=self._admin(); page=a.req('GET','/admin')[1].decode()
        self.assertIn('后台能看到&lt;b&gt;这条&lt;/b&gt;',page,'文字要转义，不能当网页执行'); self.assertIn('fb6@x.com',page); self.assertIn('阅读页',page)
        c,raw,h=a.req('GET',f'/admin/feedback/{fid}/1.png'); self.assertEqual(c,200); self.assertEqual(h['Content-Type'],'image/png'); self.assertEqual(raw,self.PNG)
        self.assertEqual(u.req('GET',f'/admin/feedback/{fid}/1.png')[0],403,'普通账号看不了'); self.assertEqual(C().req('GET',f'/admin/feedback/{fid}/1.png')[0],403)
        c,_,h=a.req('POST',f'/admin/feedback/{fid}/done',b'',self.FORM); self.assertEqual(c,303); self.assertEqual(db.one('select status from feedback where id=?',(fid,))[0],'done')
        self.assertEqual(u.req('POST',f'/admin/feedback/{fid}/reopen',b'',self.FORM)[0],403)
    def test_mail_failure_does_not_break_reset_request(self):
        a=C(); a.post('/api/auth/register',email='m1@x.com',password=PW,invite=invite())
        old=accounts.mailer
        def boom(*x): raise OSError('smtp down')
        accounts.mailer=boom
        try: self.assertEqual(C().post('/api/auth/forgot',email='m1@x.com')[0],200)
        finally: accounts.mailer=old
if __name__=='__main__': unittest.main()
