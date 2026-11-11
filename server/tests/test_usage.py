"""使用情况记录测试：白名单、不记内容、每天/次日回访/每本书统计、批量上限、注销清除、后台看板。
运行：cd server && python3 -m unittest discover -s tests"""
import os,sys,json,time,tempfile,unittest,threading
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,os.path.dirname(HERE))
import config,db,usage

class Unit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d=tempfile.mkdtemp(prefix='fubi_usage_'); cls.old=config.DATA; config.DATA=cls.d; db.reset_for_tests()
    @classmethod
    def tearDownClass(cls): db.reset_for_tests(); config.DATA=cls.old
    def setUp(self): db.run('delete from events')
    def test_whitelist_and_bad_items_dropped(self):
        n=usage.record(1,[{'k':'open'},{'k':'hack'},{'k':'book','b':'hlm'},{'k':'book','b':'../etc'},{'k':'clue','b':'hlm'},'不是字典',{'k':'quiz','v':'q3:less'},{'k':'quiz','v':'随便写点什么内容'}])
        self.assertEqual(n,4); self.assertEqual({r[0] for r in db.all('select kind from events')},{'open','book','clue','quiz'})
    def test_never_stores_text_fields(self):
        usage.record(1,[{'k':'read','b':'hlm','n':35,'s':60,'text':'书的正文','q':'我的提问','note':'我的笔记'}])
        row=db.one('select kind,book,n,extra from events'); self.assertEqual(row,('read','hlm',35,'60')); self.assertNotIn('正文',json.dumps(row,ensure_ascii=False))
    def test_clamps_numbers_and_batch(self):
        usage.record(1,[{'k':'read','b':'hlm','n':999,'s':999999}]); self.assertEqual(db.one('select n,extra from events'),(100,'3600'),'进度不超过 100，一次最多算 1 小时')
        db.run('delete from events'); self.assertEqual(usage.record(1,[{'k':'open'}]*50),20,'一批最多 20 条')
    def test_daily_fills_zero_days(self):
        usage.record(1,[{'k':'open'},{'k':'read','b':'hlm','n':10,'s':120},{'k':'clue','b':'hlm'}]); usage.record(2,[{'k':'open'}])
        d=usage.daily(3); self.assertEqual(len(d),3); self.assertEqual(d[-1]['active'],2); self.assertEqual(d[-1]['minutes'],2); self.assertEqual(d[-1]['clues'],1); self.assertEqual(d[0]['active'],0)
    def test_retention_counts_only_finished_days(self):
        y=time.time()-86400; day=lambda t:time.strftime('%Y-%m-%d',time.localtime(t))
        for uid,days in ((1,[y-86400,y]),(2,[y-86400]),(3,[time.time()])):   # 1：昨天和前天都来了；2：只前天来；3：今天才来
            for t in days: db.run('insert into events(uid,t,day,kind) values(?,?,?,?)',(uid,t,day(t),'open'))
        self.assertEqual(usage.retention(),(2,1),'今天才来的不算；前天来的两人里一人次日回来')
    def test_per_book_and_quiz(self):
        usage.record(1,[{'k':'book','b':'hlm'},{'k':'read','b':'hlm','n':20,'s':60},{'k':'read','b':'hlm','n':50,'s':60}]); usage.record(2,[{'k':'read','b':'hlm','n':10,'s':30}])
        b=usage.per_book()[0]; self.assertEqual((b['book'],b['readers'],b['avg_far'],b['minutes']),('hlm',2,30,2),'平均读到 = 各人最远进度的平均 (50+10)/2')
        usage.record(1,[{'k':'quiz','v':'q3:less'}]); usage.record(1,[{'k':'quiz','v':'q3:more'}]); usage.record(2,[{'k':'quiz','v':'q2:words,people'}])
        self.assertEqual(usage.quiz_dist(),{'q3':{'more':1},'q2':{'words':1,'people':1}},'同一人同一题只算最后一次')
    def test_prune_old(self):
        db.run('insert into events(uid,t,day,kind) values(1,?, ?, ?)',(time.time()-200*86400,'2026-01-01','open')); usage._last_prune[0]=0; usage.record(1,[{'k':'open'}])
        self.assertEqual(db.one('select count(*) from events')[0],1,'超过 180 天的清掉')

if __name__=='__main__': unittest.main()
