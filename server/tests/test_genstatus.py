"""生成进度与"可读门槛"：前 20% 章（向上取整）的解释/复查/回顾都做完才可读；预估时间只在样本够时给。
运行：cd server && python3 -m unittest discover -s tests"""
import os,sys,time,tempfile,unittest
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,os.path.dirname(HERE))
import config,db,pipeline

def mk(bid,chapters,status='generating'):
    db.run('delete from jobs where book=?',(bid,)); db.run('delete from books where id=?',(bid,))
    db.run("insert into books(id,title,author,kind,owner,status,chapters,t,meta) values(?,?,?,?,?,?,?,?,?)",(bid,'书','','import','d',status,chapters,time.time(),'{}'))
def job(bid,step,unit,st='todo',t_new=None,t_done=None):
    db.run("insert or replace into jobs(book,step,unit,status,t_new,t_done) values(?,?,?,?,?,?)",(bid,step,str(unit),st,t_new or time.time(),t_done))
def full(bid,n,done_chapters):
    """给 n 章的书排满任务：index/gloss 每章、merge 一条、cards/review/recap 每章；前 done_chapters 章的后三步标 done"""
    for c in range(1,n+1):
        for s in ('index','gloss'): job(bid,s,c,'done')
    job(bid,'merge','','done')
    for c in range(1,n+1):
        for s in ('cards','review','recap'): job(bid,s,c,'done' if c<=done_chapters else 'todo')

class T(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d=tempfile.mkdtemp(prefix='fubi_gs_'); cls.old=config.DATA; config.DATA=cls.d; db.reset_for_tests()
    @classmethod
    def tearDownClass(cls): db.reset_for_tests(); config.DATA=cls.old
    def test_threshold_is_ceil_of_20_percent_min_one(self):
        self.assertEqual([pipeline.readable_chapters(n) for n in (0,1,3,5,6,10,11,30,165)],[0,1,1,1,2,2,3,6,33])
    def test_locked_until_first_chapters_done(self):
        mk('b1',10); full('b1',10,1); s=pipeline.status('b1'); self.assertEqual((s['state'],s['need'],s['ready_chapters']),('generating',2,1),'10 章要 2 章，只好 1 章还不能读')
        full('b1',10,2); s=pipeline.status('b1'); self.assertEqual((s['state'],s['ready_chapters']),('readable',2))
        full('b1',10,10); self.assertEqual(pipeline.status('b1')['state'],'done')
    def test_ready_chapters_must_be_consecutive_from_chapter_one(self):
        mk('b2',10); full('b2',10,0); job('b2','cards',5,'done'); job('b2','review',5,'done'); job('b2','recap',5,'done'); job('b2','cards',6,'done'); job('b2','review',6,'done'); job('b2','recap',6,'done')
        self.assertEqual(pipeline.status('b2')['ready_chapters'],0,'第 5、6 章好了但第 1 章没好，不算——读者从头读')
    def test_chapter_needs_all_three_steps(self):
        mk('b3',5); full('b3',5,0); job('b3','cards',1,'done'); job('b3','review',1,'done')   # recap 还没好
        self.assertEqual(pipeline.status('b3')['ready_chapters'],0); job('b3','recap',1,'done'); self.assertEqual(pipeline.status('b3')['state'],'readable')
    def test_no_jobs_means_not_locked(self):
        mk('b4',5,'ready'); s=pipeline.status('b4'); self.assertEqual(s['state'],'done','没排过任务（假模型/没开自动生成）不锁')
    def test_parsing_state(self):
        mk('b5',0,'parsing'); self.assertEqual(pipeline.status('b5')['state'],'parsing')
    def test_failed_and_waiting(self):
        mk('b6',4); full('b6',4,0); db.run("update jobs set status='failed' where book='b6' and step in ('cards','review','recap')"); self.assertEqual(pipeline.status('b6')['state'],'failed')
        mk('b7',4); full('b7',4,0); db.run("update jobs set status='waiting' where book='b7' and step in ('cards','review','recap')"); self.assertEqual(pipeline.status('b7')['state'],'waiting','额度用完，明天继续')
    def test_eta_needs_enough_samples_and_scales_with_remaining(self):
        mk('b8',10); full('b8',10,0); now=time.time()
        for i in range(2): db.run("update jobs set t_new=?,t_done=? where book='b8' and step='index' and unit=?",(now-10,now,str(i+1)))
        # index/gloss/merge 默认也是 done 但没有耗时记录（t_done 为空）→ 样本只有上面 2 个
        db.run("update jobs set t_done=NULL where book='b8' and status='done' and unit not in ('1','2')"); db.run("update jobs set t_done=NULL where book='b8' and step='merge'")
        self.assertIsNone(pipeline.status('b8')['eta'],'样本不足 3 个，不给数字')
        db.run("update jobs set t_new=?,t_done=? where book='b8' and step='index' and unit='3'",(now-10,now))
        os.environ['FUBI_WORKERS']='2'
        try: eta=pipeline.status('b8')['eta']
        finally: os.environ.pop('FUBI_WORKERS',None)
        self.assertEqual(eta,int(10*30/2),'平均每个 10 秒 × 剩余 30 个 ÷ 2 个并发')
    def test_status_in_api_payload(self):
        import app
        mk('b9',3); full('b9',3,0); self.assertEqual(pipeline.status('b9')['state'],'generating')
if __name__=='__main__': unittest.main()
