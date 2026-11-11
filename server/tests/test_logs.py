"""日志测试：JSON 行、不含查询串/邮箱/Cookie、IP 抹末段、请求编号对得上、按天轮转保留 N 天、500 带编号。
运行：cd server && python3 -m unittest discover -s tests"""
import os,sys,json,time,tempfile,shutil,unittest,threading,urllib.request
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,os.path.dirname(HERE))
import logs

class Unit(unittest.TestCase):
    def setUp(self):
        self.d=tempfile.mkdtemp(prefix='fubi_log_'); self.old={k:os.environ.get(k) for k in ('FUBI_LOG_DIR','FUBI_QUIET','FUBI_LOG_FILE','FUBI_LOG_KEEP_DAYS')}
        os.environ.update(FUBI_LOG_DIR=self.d,FUBI_QUIET='1',FUBI_LOG_FILE='1'); logs.close_for_tests()
    def tearDown(self):
        logs.close_for_tests(); shutil.rmtree(self.d,ignore_errors=True)
        for k,v in self.old.items():
            if v is None: os.environ.pop(k,None)
            else: os.environ[k]=v
    def lines(self):
        p=os.path.join(self.d,'fubi-%s.log'%time.strftime('%Y-%m-%d')); return [json.loads(x) for x in open(p,encoding='utf-8').read().splitlines()]
    def test_access_line_is_json_and_private(self):
        logs.access('ab12cd34','POST','/api/auth/login?email=a@b.com&token=zzz',200,12,7,'u7-device-xyz','203.0.113.45')
        r=self.lines()[0]; self.assertEqual(r['p'],'/api/auth/login','查询串不进日志'); self.assertEqual(r['ip'],'203.0.113.0'); self.assertEqual(r['d'],'u7-d'); self.assertEqual(r['rid'],'ab12cd34'); self.assertEqual(r['s'],200)
        self.assertNotIn('a@b.com',json.dumps(r)); self.assertNotIn('zzz',json.dumps(r))
    def test_ipv6_masked(self): self.assertEqual(logs.mask_ip('2001:db8:85a3:8d3:1319:8a2e:370:7348'),'2001:db8:85a3::'); self.assertEqual(logs.mask_ip(''),'')
    def test_rotation_keeps_only_n_days(self):
        os.environ['FUBI_LOG_KEEP_DAYS']='30'
        old=os.path.join(self.d,'fubi-2020-01-01.log'); keep=os.path.join(self.d,'fubi-2099-01-01.log'); other=os.path.join(self.d,'notes.txt')
        for p in (old,keep,other): open(p,'w').write('x')
        past=time.time()-40*86400; os.utime(old,(past,past)); os.utime(other,(past,past))
        logs.write({'msg':'触发一次打开今天的文件'}); logs.close_for_tests(); logs.write({'msg':'再来一次'})
        self.assertFalse(os.path.exists(old),'超过 30 天的日志删掉'); self.assertTrue(os.path.exists(keep)); self.assertTrue(os.path.exists(other),'不是日志文件的不动')
    def test_write_failure_does_not_raise(self):
        os.environ['FUBI_LOG_DIR']='/proc/不能写的地方'; logs.close_for_tests(); logs.write({'msg':'x'})
    def test_recent_errors_does_not_drop_first_line(self):
        logs.access('r1','GET','/b',500,1); self.assertEqual(logs.recent_errors(10),1,'文件里只有一行时，这一行也要算')
    def test_recent_errors_counts_5xx_only(self):
        logs.access('r1','GET','/a',200,1); logs.access('r2','GET','/b',500,1); logs.access('r3','GET','/c',404,1); logs.error('boom','r4')
        self.assertEqual(logs.recent_errors(10),2)

class Server(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import config,db,app
        cls.d=tempfile.mkdtemp(prefix='fubi_logs_'); cls._old=(config.DATA,os.environ.get('FUBI_LOG_DIR'),os.environ.get('FUBI_QUIET'))
        config.DATA=cls.d; os.environ.update(FUBI_LOG_DIR=cls.d+'/logs',FUBI_QUIET='1',FUBI_LOG_FILE='1')   # config.DATA 导入时就读好了，这里直接改
        for k in ('IMPORT','DOWNLOAD','ASK','SEARCH','GENERAL'): os.environ.setdefault('FUBI_RL_'+k,'100000/60')
        logs.close_for_tests(); db.reset_for_tests()
        cls.srv=app.make_server('127.0.0.1',0); cls.URL=f'http://127.0.0.1:{cls.srv.server_port}'; threading.Thread(target=cls.srv.serve_forever,daemon=True).start()
    @classmethod
    def tearDownClass(cls):
        import config,db
        cls.srv.shutdown(); cls.srv.server_close(); logs.close_for_tests(); db.reset_for_tests(); config.DATA=cls._old[0]
        for k,v in zip(('FUBI_LOG_DIR','FUBI_QUIET'),cls._old[1:]):
            if v is None: os.environ.pop(k,None)
            else: os.environ[k]=v
        shutil.rmtree(cls.d,ignore_errors=True)
    def lines(self):
        p=os.path.join(self.d,'logs','fubi-%s.log'%time.strftime('%Y-%m-%d')); return [json.loads(x) for x in open(p,encoding='utf-8').read().splitlines() if x.strip()]
    def test_request_id_header_matches_log(self):
        r=urllib.request.urlopen(self.URL+'/api/health?secret=abc'); rid=r.headers['X-Request-Id']; self.assertTrue(rid)
        time.sleep(0.2); m=[x for x in self.lines() if x.get('rid')==rid]; self.assertEqual(len(m),1); self.assertEqual(m[0]['p'],'/api/health'); self.assertEqual(m[0]['s'],200); self.assertNotIn('abc',json.dumps(m[0]))
    def test_protocol_garbage_is_warn_not_error(self):
        """公网扫描程序发来的畸形请求、CONNECT 等：留一条警告，但不能被监控当成"服务器错误"（11-04 线上天天误报）"""
        import socket
        before=logs.recent_errors(10)
        for raw in (b'CONNECT example.com:443 HTTP/1.1\r\n\r\n', b'GET / HTTP/9.9\r\n\r\n', b'\x16\x03\x01\x02\x00\x01\x00\x01\xfc\x03\x03\r\n\r\n'):
            s=socket.create_connection(('127.0.0.1',self.srv.server_port),timeout=5); s.sendall(raw)
            try: s.recv(4096)
            except OSError: pass
            s.close()
        time.sleep(0.3); L=self.lines(); W=[x for x in L if x.get('level')=='warn' and 'HTTP 层' in x.get('msg','')]
        self.assertGreaterEqual(len(W),2,'畸形请求留警告：%s'%[x.get('msg') for x in L[-6:]])
        self.assertFalse([x for x in L if x.get('level')=='error' and 'HTTP 层' in x.get('msg','')],'不记成 error')
        self.assertEqual(logs.recent_errors(10),before,'监控不数它们')
    def test_client_disconnect_is_not_a_server_error(self):
        """对方在收到响应前断开（ConnectionReset / BrokenPipe）：记 499，不是 500，也不留 error"""
        import app
        before=logs.recent_errors(10); old=app.H.end_headers
        def boom(self):
            if self.path.startswith('/api/health?probe=drop'): raise ConnectionResetError(104,'Connection reset by peer')
            return old(self)
        app.H.end_headers=boom
        try:
            try: urllib.request.urlopen(self.URL+'/api/health?probe=drop',timeout=5)
            except Exception: pass   # 对方（这里是测试客户端）没拿到响应，正是要模拟的情形
        finally: app.H.end_headers=old
        time.sleep(0.3); L=self.lines(); m=[x for x in L if x.get('p')=='/api/health' and x.get('s') in (499,500)]
        self.assertTrue(m and all(x['s']==499 for x in m),'记成 499：%s'%m)
        self.assertFalse([x for x in L if x.get('level')=='error' and 'ConnectionReset' in x.get('msg','')],'不留 error 和调用栈')
        self.assertEqual(logs.recent_errors(10),before)
        self.assertEqual(urllib.request.urlopen(self.URL+'/api/health').status,200,'之后服务照常')
    def test_500_has_request_id_and_stack_in_log(self):
        import books
        old=books.shelf
        def boom(*a): raise RuntimeError('故意出错')
        books.shelf=boom
        try:
            try: urllib.request.urlopen(self.URL+'/api/shelf'); self.fail('应该是 500')
            except urllib.error.HTTPError as e:
                self.assertEqual(e.code,500); rid=e.headers['X-Request-Id']; body=json.loads(e.read())['error']; self.assertIn(rid,body,'读者看到的提示里带编号')
        finally: books.shelf=old
        time.sleep(0.2); L=self.lines(); err=[x for x in L if x.get('level')=='error' and x.get('rid')==rid]; self.assertEqual(len(err),1); self.assertIn('RuntimeError',err[0]['msg']); self.assertTrue([x for x in L if x.get('rid')==rid and x.get('s')==500])
if __name__=='__main__': unittest.main()
