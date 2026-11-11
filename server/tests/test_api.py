"""接口测试：真的起一个服务（随机端口），用 HTTP 请求走一遍读者会做的每件事。
运行：cd server && python3 -m unittest discover -s tests"""
import os,sys,json,threading,unittest,tempfile,urllib.request,urllib.parse,http.cookiejar,gzip,time
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,os.path.dirname(HERE))
os.environ.update(FUBI_DATA=tempfile.mkdtemp(prefix='fubi_api_'),FUBI_QUIET='1',FUBI_SYNC_IMPORT='1')
for _k in ('IMPORT','DOWNLOAD','ASK','SEARCH','GENERAL'): os.environ.setdefault('FUBI_RL_'+_k,'100000/60')   # 业务测试不受限流影响；限流自己的测试单独设置
import config,db,app,pipeline,model
config.MODEL.update(provider='mock')

srv=None; URL=''
def setUpModule():
    global srv,URL
    db.reset_for_tests(); srv=app.make_server('127.0.0.1',0); URL=f'http://127.0.0.1:{srv.server_port}'
    threading.Thread(target=srv.serve_forever,daemon=True).start()
def tearDownModule(): srv.shutdown()

class Client:
    """一台设备：自己的 cookie"""
    def __init__(self): self.op=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    def req(self,method,path,body=None,headers=None):
        r=urllib.request.Request(URL+path,data=body,method=method,headers=headers or {})
        try:
            with self.op.open(r,timeout=60) as resp: raw=resp.read(); code=resp.status; h=dict(resp.headers)
        except urllib.error.HTTPError as e: raw=e.read(); code=e.code; h=dict(e.headers)
        if h.get('Content-Encoding')=='gzip': raw=gzip.decompress(raw)
        return code,raw,h
    def json(self,method,path,obj=None,**kw):
        code,raw,_=self.req(method,path,json.dumps(obj).encode() if obj is not None else kw.get('data'),kw.get('headers'))
        return code,json.loads(raw) if raw else None
    def upload(self,name,data=None):
        data=data if data is not None else open(os.path.join(HERE,'fixtures',name),'rb').read()
        return self.json('POST','/api/import',data=data,headers={'X-Filename':urllib.parse.quote(name)})

class RateLimit(unittest.TestCase):
    def setUp(self):
        import ratelimit,search,io; self.rl=ratelimit; ratelimit.reset(); os.environ['FUBI_RL_SEARCH']='3/60'
        # 搜索会去访问古登堡和维基文库。不换成假网络时：本机没外网立刻失败，GitHub 上有外网但第一次可能很慢，
        # 第 4 次请求时第 1 次的记录已滑出 60 秒窗口，就不被限流了（11-04 在 GitHub 上出现过 200!=429）
        self._so=search.opener; search._cache.clear()
        search.opener=lambda req,timeout=0: io.BytesIO(json.dumps({'count':0,'results':[],'query':{'search':[]}}).encode())
    def tearDown(self):
        import search; search.opener=self._so; search._cache.clear()
        os.environ['FUBI_RL_SEARCH']='100000/60'; self.rl.reset()
    def test_search_limited_with_chinese_message_and_retry_after(self):
        a=Client()
        for _ in range(3): self.assertEqual(a.json('GET','/api/search?q=abc')[0],200)
        c,raw,h=a.req('GET','/api/search?q=abc'); self.assertEqual(c,429)
        msg=json.loads(raw)['error']; self.assertIn('搜索请求过于频繁',msg); self.assertIn('后重试',msg); self.assertIn('每分钟最多 3 次',msg); self.assertTrue(int(h.get('Retry-After','0'))>=1)
    def test_health_and_state_not_limited(self):
        a=Client(); os.environ['FUBI_RL_GENERAL']='2/60'
        try:
            for _ in range(10): self.assertEqual(a.json('GET','/api/health')[0],200)
        finally: os.environ['FUBI_RL_GENERAL']='100000/60'
    def test_window_slides(self):
        self.rl.reset()
        for i in range(3): self.rl.check('search','x',now=100+i)
        with self.assertRaises(self.rl.Limited): self.rl.check('search','x',now=110)
        self.rl.check('search','x',now=100+61)   # 窗口过了就恢复
    def test_other_users_not_affected(self):
        self.rl.reset()
        for _ in range(3): self.rl.check('search','dev:a')
        with self.assertRaises(self.rl.Limited): self.rl.check('search','dev:a')
        self.rl.check('search','dev:b')
    def test_forwarded_header_ignored_unless_trusted(self):
        os.environ.pop('FUBI_TRUST_PROXY',None); self.assertEqual(self.rl.client_ip({'X-Forwarded-For':'9.9.9.9'},'1.2.3.4'),'1.2.3.4')
        os.environ['FUBI_TRUST_PROXY']='1'
        try: self.assertEqual(self.rl.client_ip({'X-Forwarded-For':'9.9.9.9, 5.5.5.5'},'1.2.3.4'),'9.9.9.9')
        finally: os.environ.pop('FUBI_TRUST_PROXY',None)

class API(unittest.TestCase):
    def setUp(self): import ratelimit; ratelimit.reset()   # 每个测试从零开始计数（测试里会连续导入很多次，生产的限制不变）
    def test_health(self):
        c,d=Client().json('GET','/api/health')
        self.assertEqual(c,200); self.assertTrue(d['ok']); self.assertEqual(d['builtin'],5); self.assertIn('pdf',d['formats'])
    def test_page_has_builtin_books_and_boot_info(self):
        a=Client(); c,raw,h=a.req('GET','/',headers={'Accept-Encoding':'gzip'})
        t=raw.decode(); self.assertEqual(c,200); self.assertEqual(h.get('Content-Encoding'),'gzip')
        self.assertIn('window.FUBI=',t); self.assertIn('"hound":',t); self.assertIn('fubi_dev=',h.get('Set-Cookie',''))
        self.assertNotIn('%%DATA%%',t)
    def test_builtin_book_same_as_demo(self):
        c,d=Client().json('GET','/api/books/hound')
        f=os.path.join(config.ROOT,'生成','自测','单文件版.html')
        if not os.path.exists(f):   # 干净克隆（如 GitHub 上）没有这个生成物：先生成，只要单文件版、不要读原始电子书的合并版
            import subprocess,sys; subprocess.run([sys.executable,'-I',os.path.join(config.ROOT,'生成','build_demo.py')],check=True,env=dict(os.environ,FUBI_NO_BUNDLE='1',PYTHONWARNINGS='ignore'),stdout=subprocess.DEVNULL)
        demo=open(f,encoding='utf-8').read()
        data=json.loads(demo.split('<script id="data" type="application/json">')[1].split('</script>')[0].replace('<\\/','</'))
        self.assertEqual(d,data['books']['hound'],'服务端给的精编书必须和 demo 完全一样')
    def test_import_flow_and_privacy(self):
        a,b=Client(),Client()
        c,r=a.upload('c.docx'); self.assertEqual(c,200); bid=r['id']; self.assertEqual(r['status'],'ready')
        c,r2=a.upload('c.docx'); self.assertEqual(r2['id'],bid,'同一个人重复导入同一个文件，不重复建书')
        ids=[x['id'] for x in a.json('GET','/api/shelf')[1]['books']]; self.assertIn(bid,ids); self.assertEqual(len(ids),6)
        self.assertNotIn(bid,[x['id'] for x in b.json('GET','/api/shelf')[1]['books']],'别人看不到我导入的书')
        self.assertEqual(b.json('GET','/api/books/'+bid)[0],404)
        c,d=a.json('GET','/api/books/'+bid); self.assertEqual(c,200); self.assertEqual(len(d['hui']),5); self.assertTrue(d['imported'])
        self.assertEqual(a.json('GET',f'/api/books/{bid}/status')[1]['chapters'],5)
        t=a.req('GET','/')[1].decode(); self.assertIn(json.dumps(bid),t,'书页面里带上我导入的书')
        self.assertEqual(b.json('DELETE','/api/books/'+bid)[0],404)
        self.assertEqual(a.json('DELETE','/api/books/hound')[0],403)
        self.assertEqual(a.json('DELETE','/api/books/'+bid)[1]['ok'],True)
        self.assertEqual(a.json('GET','/api/books/'+bid)[0],404)
    def test_bad_imports(self):
        a=Client()
        c,r=a.upload('x.txt',b''); self.assertEqual(c,400)
        c,r=a.upload('broken.epub',b'PK\x03\x04garbage'); self.assertEqual(c,200)
        st=a.json('GET',f"/api/books/{r['id']}/status")[1]; self.assertEqual(st['status'],'failed'); self.assertIn('损坏',st['err'])
        self.assertEqual(a.json('GET','/api/books/'+r['id'])[0],409)
        old=config.MAX_UPLOAD; config.MAX_UPLOAD=10
        try: self.assertEqual(a.upload('a_gbk.txt')[0],400)
        finally: config.MAX_UPLOAD=old
    def test_state_sync_per_device(self):
        a,b=Client(),Client()
        a.json('PUT','/api/state',{'rb_demo_hlm_v1':{'furthest':9,'notes':[{'text':'笔记'}]},'not_allowed':{'x':1}})
        self.assertEqual(a.json('GET','/api/state')[1],{'rb_demo_hlm_v1':{'furthest':9,'notes':[{'text':'笔记'}]}})
        self.assertEqual(b.json('GET','/api/state')[1],{})
        a.json('POST','/api/state?m=put',{'rb_demo_hlm_v1':{'furthest':12}})        # sendBeacon 用 POST
        self.assertEqual(a.json('GET','/api/state')[1]['rb_demo_hlm_v1']['furthest'],12)
        self.assertIn('"rb_demo_hlm_v1": {"furthest": 12}',a.req('GET','/')[1].decode(),'打开页面时直接带上服务器上的记录')
        a.json('PUT','/api/state',{'rb_demo_hlm_v1':None}); self.assertEqual(a.json('GET','/api/state')[1],{})
    def test_ask(self):
        a=Client(); c,d=a.json('POST','/api/ask',{'book':'hound','q':'这根手杖是谁的？','pos':'1.5'})
        self.assertEqual(c,200); self.assertIn(d['类型'],('读过的','后面有','书外','书里没有')); self.assertTrue(d['回答'])
        self.assertEqual(a.json('POST','/api/ask',{'book':'hound','q':'x','pos':'99.99'})[0],400)
        self.assertEqual(a.json('POST','/api/ask',{'book':'nope','q':'x','pos':'1.1'})[0],400)
    def test_ask_only_sends_what_reader_has_read(self):
        """发给模型的原文里，不能有读者还没读到的段落"""
        seen=[]; orig=model.call
        def spy(task,v,**k): seen.append(v['text']); return orig(task,v,**k)
        model.call=spy
        try: Client().json('POST','/api/ask',{'book':'hound','q':'巴斯克维尔 猎犬 是谁','pos':'2.10'})
        finally: model.call=orig
        nums=[l.split('　')[0] for l in seen[0].split('\n') if '　' in l and l[0].isdigit()]
        self.assertTrue(nums); self.assertTrue(all(tuple(map(int,n.split('.')))<=(2,10) for n in nums),nums)
    def test_ask_model_down(self):
        orig=model.call
        def down(*a,**k): raise model.ModelError('模型服务暂时不可用（503）')
        model.call=down
        try: c,d=Client().json('POST','/api/ask',{'book':'hound','q':'x','pos':'1.1'})
        finally: model.call=orig
        self.assertEqual(c,503); self.assertIn('暂时不可用',d['error'])
    def test_admin_closed_when_accounts_off(self):
        a=Client(); self.assertEqual(a.req('GET','/admin')[0],403); self.assertEqual(a.req('GET','/admin?token=t0k')[0],403,'口令方式已取消')
    def test_generation_shows_up_in_book(self):
        a=Client(); bid=a.upload('e.md')[1]['id']
        pipeline.enqueue(bid); pipeline.drain()
        d=a.json('GET','/api/books/'+bid)[1]; self.assertTrue(d['cards']); self.assertEqual(len(d['recap']),5)
        sh={x['id']:x for x in a.json('GET','/api/shelf')[1]['books']}; self.assertEqual(sh[bid]['gen']['done'],26)
    def test_unknown_and_traversal(self):
        a=Client()
        self.assertEqual(a.req('GET','/api/nothing')[0],404)
        self.assertEqual(a.req('GET','/api/books/..%2F..%2Fetc')[0],404)
        self.assertEqual(a.req('GET','/../server/config.py')[0],404)

if __name__=='__main__': unittest.main()
