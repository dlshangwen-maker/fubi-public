"""备份与恢复测试：往返一致、损坏的压缩包被拒绝、保留份数、恢复前的旧数据不被删。
运行：cd server && python3 -m unittest discover -s tests"""
import os,sys,time,sqlite3,tempfile,shutil,unittest
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,os.path.dirname(HERE))
import backup

def make_data(root,n=1):
    os.makedirs(os.path.join(root,'books','b1'),exist_ok=True); open(os.path.join(root,'books','b1','a.txt'),'w',encoding='utf-8').write('书')
    c=sqlite3.connect(os.path.join(root,'fubi.db')); c.execute('pragma journal_mode=wal'); c.execute('create table if not exists t(x)')
    for i in range(n): c.execute('insert into t values(?)',(i,))
    c.commit(); return c   # 连接不关：模拟服务正在运行、数据还在 WAL 里
class Backup(unittest.TestCase):
    def setUp(self): self.d=tempfile.mkdtemp(prefix='fubi_bk_'); self.data=os.path.join(self.d,'data'); self.out=os.path.join(self.d,'out'); os.makedirs(self.data)
    def tearDown(self): shutil.rmtree(self.d,ignore_errors=True)
    def test_roundtrip_while_db_open(self):
        c=make_data(self.data,3); p=backup.backup(self.out,self.data)
        self.assertEqual(backup.verify(p)['t'],3,'服务开着、数据还在 WAL 里，备份也要完整')
        c.execute('insert into t values(99)'); c.commit(); c.close(); os.remove(os.path.join(self.data,'books','b1','a.txt'))
        rows,aside=backup.restore(p,self.data)
        self.assertEqual(rows['t'],3); self.assertTrue(os.path.exists(os.path.join(self.data,'books','b1','a.txt')))
        old=sqlite3.connect(os.path.join(aside,'fubi.db')).execute('select count(*) from t').fetchone()[0]; self.assertEqual(old,4,'恢复前的旧数据挪到旁边，没有删')
    def test_corrupt_archive_rejected_and_nothing_replaced(self):
        c=make_data(self.data,2); p=backup.backup(self.out,self.data); c.close()
        bad=os.path.join(self.out,'fubi-bad.tar.gz'); open(bad,'wb').write(open(p,'rb').read()[:150])
        with self.assertRaises(Exception): backup.verify(bad)
        with self.assertRaises(Exception): backup.restore(bad,self.data)
        self.assertEqual(sqlite3.connect(os.path.join(self.data,'fubi.db')).execute('select count(*) from t').fetchone()[0],2,'坏备份恢复失败时，现有数据原样不动')
        self.assertFalse([n for n in os.listdir(self.data) if n.startswith('_恢复前_')])
    def test_keep_only_latest_n_and_no_part_files(self):
        make_data(self.data).close(); os.environ['FUBI_BACKUP_KEEP']='3'
        try:
            for _ in range(5): backup.backup(self.out,self.data); time.sleep(1.05)
        finally: os.environ.pop('FUBI_BACKUP_KEEP',None)
        self.assertEqual(len(backup.list_backups(self.out)),3); self.assertFalse([n for n in os.listdir(self.out) if n.endswith('.part')])
        self.assertEqual(backup.latest(self.out)[0],backup.list_backups(self.out)[-1])
    def test_missing_db_is_an_error_not_an_empty_backup(self):
        with self.assertRaises(RuntimeError): backup.backup(self.out,self.data)
        self.assertFalse(backup.list_backups(self.out))
    def test_cli_exit_codes(self):
        self.assertEqual(backup.main(['backup.py']),2); self.assertEqual(backup.main(['backup.py','restore','x']),2,'恢复不带 --yes 不动手')
        self.assertEqual(backup.main(['backup.py','verify','/不存在.tar.gz']),1)
if __name__=='__main__': unittest.main()
