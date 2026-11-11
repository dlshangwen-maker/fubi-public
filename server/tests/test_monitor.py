"""监控告警测试：判定规则（新问题发一次、持续每 6 小时提醒、恢复发一次、服务连续 2 次失败才报）、磁盘/备份/错误检查、真实巡检一次。
运行：cd server && python3 -m unittest discover -s tests"""
import os,sys,json,time,tempfile,shutil,unittest,threading
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,os.path.dirname(HERE))
import config,monitor

H=3600
class Decide(unittest.TestCase):
    def test_new_issue_mails_once_then_silent_then_reminds(self):
        st={'last':0,'issues':{},'fails':0}; t=1_000_000
        m,st=monitor.decide(st,{'disk':'磁盘剩余 5%'},0,t); self.assertEqual(len(m),1); self.assertIn('磁盘',m[0][0])
        m,st=monitor.decide(st,{'disk':'磁盘剩余 5%'},0,t+2*60); self.assertEqual(m,[],'同一个问题 2 分钟后不再发')
        m,st=monitor.decide(st,{'disk':'磁盘剩余 5%'},0,t+5*H); self.assertEqual(m,[],'5 小时内不再发')
        m,st=monitor.decide(st,{'disk':'磁盘剩余 4%'},0,t+6*H+60); self.assertEqual(len(m),1,'持续 6 小时提醒一次'); self.assertIn('磁盘',m[0][1])
    def test_recovery_mail(self):
        t=1_000_000; m,st=monitor.decide({'issues':{},'fails':0},{'backup':'x'},0,t)
        m,st=monitor.decide(st,{},0,t+600); self.assertEqual(len(m),1); self.assertIn('已恢复',m[0][0]); self.assertEqual(st['issues'],{})
        m,st=monitor.decide(st,{},0,t+1200); self.assertEqual(m,[],'恢复后正常就不再发')
    def test_partial_recovery(self):
        t=1_000_000; m,st=monitor.decide({'issues':{},'fails':0},{'backup':'a','disk':'b'},0,t)
        m,st=monitor.decide(st,{'disk':'b'},0,t+60); self.assertEqual(len(m),1); self.assertIn('部分恢复',m[0][0]); self.assertIn('备份',m[0][1])
    def test_service_needs_two_consecutive_failures(self):
        t=1_000_000; st={'issues':{},'fails':0}
        m,st=monitor.decide(st,{'service':'没响应'},1,t); self.assertEqual(m,[],'第一次失败可能只是重启，不报'); self.assertEqual(st['fails'],1)
        m,st=monitor.decide(st,{'service':'没响应'},1,t+120); self.assertEqual(len(m),1); self.assertIn('服务',m[0][0])
        m,st=monitor.decide(st,{},0,t+240); self.assertIn('已恢复',m[0][0]); self.assertEqual(st['fails'],0)
    def test_blip_between_does_not_accumulate(self):
        st={'issues':{},'fails':0}; t=1_000_000
        m,st=monitor.decide(st,{'service':'x'},1,t); m,st=monitor.decide(st,{},0,t+120); m,st=monitor.decide(st,{'service':'x'},1,t+240); self.assertEqual(m,[],'中间好过一次，计数清零')

class Checks(unittest.TestCase):
    def setUp(self):
        self.d=tempfile.mkdtemp(prefix='fubi_mon_'); self.old=(config.DATA,dict(os.environ)); config.DATA=self.d
        os.environ.update(FUBI_BACKUP_DIR=self.d+'/bk',FUBI_LOG_DIR=self.d+'/logs',FUBI_QUIET='1')
    def tearDown(self):
        import db; db.reset_for_tests(); config.DATA=self.old[0]; os.environ.clear(); os.environ.update(self.old[1]); shutil.rmtree(self.d,ignore_errors=True)
    def serve(self,payload):
        from http.server import HTTPServer,BaseHTTPRequestHandler
        class H(BaseHTTPRequestHandler):
            def do_GET(s): b=json.dumps(payload).encode(); s.send_response(200); s.send_header('Content-Length',str(len(b))); s.end_headers(); s.wfile.write(b)
            def log_message(s,*a): pass
        srv=HTTPServer(('127.0.0.1',0),H); threading.Thread(target=srv.serve_forever,daemon=True).start(); self.addCleanup(srv.shutdown); return 'http://127.0.0.1:%d/api/health'%srv.server_port
    def test_down_service_and_missing_backup(self):
        issues,fail=monitor.check_all('http://127.0.0.1:1/api/health'); self.assertEqual(fail,1); self.assertIn('service',issues); self.assertIn('backup',issues)
    def test_healthy_service_database_flag(self):
        issues,fail=monitor.check_all(self.serve({'ok':True})); self.assertEqual(fail,0); self.assertNotIn('service',issues); self.assertNotIn('database',issues)
        issues,_=monitor.check_all(self.serve({'ok':False})); self.assertIn('database',issues)
    def test_disk_low_threshold(self):
        os.environ['FUBI_ALERT_DISK_PCT']='101'; issues,_=monitor.check_all(self.serve({'ok':True})); self.assertIn('disk',issues)
        os.environ['FUBI_ALERT_DISK_PCT']='0'; issues,_=monitor.check_all(self.serve({'ok':True})); self.assertNotIn('disk',issues)
    def test_old_backup_flagged(self):
        os.makedirs(self.d+'/bk'); p=self.d+'/bk/fubi-20200101-000000.tar.gz'; open(p,'w').write('x'); old=time.time()-40*H; os.utime(p,(old,old))
        issues,_=monitor.check_all(self.serve({'ok':True})); self.assertIn('小时前',issues['backup'])
        os.utime(p,None); issues,_=monitor.check_all(self.serve({'ok':True})); self.assertNotIn('backup',issues)
    def test_error_burst_flagged(self):
        import logs; logs.close_for_tests()
        for i in range(5): logs.access('r%d'%i,'GET','/x',500,1)
        logs.close_for_tests(); issues,_=monitor.check_all(self.serve({'ok':True})); self.assertIn('errors',issues)
    def test_run_once_sends_one_mail_and_writes_state(self):
        import accounts; sent=[]; old=accounts.mailer; accounts.mailer=lambda to,s,b: sent.append((to,s)); os.environ['FUBI_ALERT_TO']='a@x.com,b@x.com'; os.environ['FUBI_ALERT_DISK_PCT']='101'
        try:
            url=self.serve({'ok':True}); monitor.run_once(url); n1=len(sent); monitor.run_once(url)
            self.assertEqual(n1,2,'两个收件人各一封'); self.assertEqual(len(sent),n1,'第二次巡检问题没变，不再发')
            st=monitor.load(); self.assertIn('disk',st['issues']); self.assertTrue(st['last']>0)
        finally: accounts.mailer=old
    def test_no_recipients_does_not_crash(self):
        os.environ.pop('FUBI_ALERT_TO',None); old=config.ADMIN_EMAILS; config.ADMIN_EMAILS=frozenset()
        try: self.assertFalse(monitor.send([('s','b')]))
        finally: config.ADMIN_EMAILS=old
if __name__=='__main__': unittest.main()
