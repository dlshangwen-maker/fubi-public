"""生成服务测试：导入一本书 → 排队 → 假模型跑完 → 打包；中断后接着跑；额度用完排到明天；格式错误重试后标失败；依赖顺序。
运行：cd server && python3 -m unittest discover -s tests"""
import os,sys,json,time,unittest,tempfile,shutil
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,os.path.dirname(HERE))
os.environ['FUBI_DATA']=tempfile.mkdtemp(prefix='fubi_pipe_')
import config,db,model,pipeline,books

def fresh():
    db.reset_for_tests(); shutil.rmtree(config.DATA,ignore_errors=True); os.makedirs(config.DATA,exist_ok=True)
def new_book(name='e.md'):
    data=open(os.path.join(HERE,'fixtures',name),'rb').read()
    return books.import_file(data,name,device='dev1',background=False)

class Pipeline(unittest.TestCase):
    def setUp(self): fresh(); config.MODEL.update(provider='mock')
    def test_import_then_generate_then_pack(self):
        b=new_book(); row=books.get(b)
        self.assertEqual(row['status'],'ready'); self.assertEqual(row['chapters'],5)
        pipeline.enqueue(b); self.assertEqual(pipeline.progress(b)['todo'],5*5+1)
        n=pipeline.drain(); self.assertEqual(n,26)
        p=pipeline.progress(b); self.assertEqual(p['done'],26); self.assertEqual(books.get(b)['status'],'ready')
        d=pipeline.packed(b)
        self.assertEqual(len(d['hui']),5); self.assertTrue(d['cards'],'卡片应该打进去了'); self.assertEqual(len(d['recap']),5)
        self.assertTrue(all(pid in d['cards'] for pid in d['units']),'每一段都该有卡片')
        self.assertEqual(d['suspense'],[]); self.assertIsNone(d['main'])
    def test_pack_before_any_generation_is_readable(self):
        b=new_book(); d=pipeline.packed(b)
        self.assertEqual(d['cards'],{}); self.assertEqual(len(d['props']),sum(1 for _ in d['props'])); self.assertTrue(d['props'])
    def test_dependencies(self):
        b=new_book(); pipeline.enqueue(b); order=[]
        while True:
            j=pipeline.next_job()
            if not j: break
            order.append(j['step']+j['unit']); pipeline.run_job(j)
        self.assertLess(max(order.index(f'index{i}') for i in range(1,6)),order.index('merge'))
        self.assertLess(order.index('merge'),min(order.index(f'cards{i}') for i in range(1,6)))
        for i in range(1,6): self.assertLess(order.index(f'cards{i}'),order.index(f'review{i}'))
    def test_resume_after_crash(self):
        b=new_book(); pipeline.enqueue(b); pipeline.drain(limit=8)
        db.run("update jobs set status='running' where id=(select min(id) from jobs where status='todo')")   # 假装跑到一半服务器重启
        before=os.path.getmtime(pipeline.chfile(b,'索引',1))
        pipeline.recover(); pipeline.enqueue(b)            # 再排一次也不会重复
        self.assertEqual(pipeline.progress(b)['total'],26)
        pipeline.drain(); self.assertEqual(pipeline.progress(b)['done'],26)
        self.assertEqual(os.path.getmtime(pipeline.chfile(b,'索引',1)),before,'做完的步骤不该重做')
    def test_quota_waits_until_tomorrow(self):
        b=new_book(); pipeline.enqueue(b)
        orig=model.call
        def boom(*a,**k): raise model.QuotaExceeded('今天的模型调用已到上限')
        model.call=boom
        try: pipeline.drain(limit=3)
        finally: model.call=orig
        p=pipeline.progress(b); self.assertGreater(p['waiting'],0); self.assertEqual(p['failed'],0)
        self.assertIsNone(pipeline.next_job(),'等到明天的任务今天不该再跑') if p['todo']==0 else None
        self.assertEqual(books.get(b)['status'],'generating')
    def test_bad_output_retries_then_fails_and_can_retry(self):
        b=new_book(); pipeline.enqueue(b)
        orig=model.call
        def bad(task,*a,**k):
            if task=='gloss': raise model.BadOutput('少了"词"')
            return orig(task,*a,**k)
        model.call=bad
        try: pipeline.drain()
        finally: model.call=orig
        p=pipeline.progress(b); self.assertEqual(p['failed'],5); self.assertEqual(p['done'],21)
        self.assertEqual(books.get(b)['status'],'ready','其它步骤做完了，书照样能读')
        err=db.one("select err from jobs where book=? and status='failed'",(b,))[0]; self.assertIn('格式',err)
        pipeline.retry_failed(b); pipeline.drain(); self.assertEqual(pipeline.progress(b)['done'],26)
    def test_transient_error_backs_off(self):
        b=new_book(); pipeline.enqueue(b)
        orig=model.call
        def down(*a,**k): raise model.ModelError('模型服务暂时不可用（503）')
        model.call=down
        try: pipeline.drain(limit=1)
        finally: model.call=orig
        j=db.rows("select * from jobs where book=? and tries=1",(b,))[0]
        self.assertEqual(j['status'],'todo'); self.assertGreater(j['t_new'],time.time()+30)
    def test_review_applies_fixes(self):
        b=new_book(); pipeline.enqueue(b)
        orig=model.call
        def fix(task,v,**k):
            if task=='review': return {'改':[{'单元':v['units'][0] if v.get('units') else '1.1','档':'入门','字段':'白话','原因':'剧透','改为':'改过的白话'}],'灰区':[]}
            return orig(task,v,**k)
        model.call=fix
        try: pipeline.drain()
        finally: model.call=orig
        cards=pipeline._load(pipeline.chfile(b,'卡片',1))
        self.assertIn('改过的白话',[c['入门']['白话'] for c in cards.values()])
    def test_prompts_are_filled(self):
        """真正发给模型的内容里：书名、章号、原文、上下文都填进去了，没有残留的 {占位符}"""
        b=new_book(); pipeline.enqueue(b); seen=[]
        orig=model.call
        def spy(task,v,**k):
            import tasks; s,u=tasks.TASKS[task].render(v); seen.append((task,u)); return orig(task,v,**k)
        model.call=spy
        try: pipeline.drain()
        finally: model.call=orig
        import re
        for task,u in seen:
            self.assertIn('e',u); self.assertNotRegex(u,r'\{(书名|N|POS|规则)\}',task)
            self.assertIn('他走进屋里',u,task)
        self.assertTrue(any('【截至这里的人物' in u for t,u in seen if t=='cards_novel'))

if __name__=='__main__': unittest.main()
