"""v9.48：封面、找书（搜索古登堡/维基文库 + 热门搜索 + 下载到书架，我们不存书）、外文书翻译、调整章节。
运行：cd server && python3 -m unittest discover -s tests"""
import os,sys,json,io,zipfile,threading,unittest,tempfile,shutil,urllib.request,urllib.parse,http.cookiejar,time
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,os.path.dirname(HERE))
os.environ.update(FUBI_DATA=tempfile.mkdtemp(prefix='fubi_948_'),FUBI_QUIET='1',FUBI_SYNC_IMPORT='1')
import config,db,app,books,pipeline,importer,chapters,search,model
config.MODEL.update(provider='mock')
FX=os.path.join(HERE,'fixtures'); RAW=os.path.join(config.ROOT,'原始资料')
def fx(n): return open(os.path.join(FX,n),'rb').read()

def make_epub(title,author,chapters_,cover=None,lang='en'):
    """造一本最小的 epub（可带封面图）"""
    b=io.BytesIO(); z=zipfile.ZipFile(b,'w')
    z.writestr('mimetype','application/epub+zip')
    z.writestr('META-INF/container.xml','<container><rootfiles><rootfile full-path="OEBPS/content.opf"/></rootfiles></container>')
    items=''.join(f'<item id="c{i}" href="c{i}.xhtml" media-type="application/xhtml+xml"/>' for i in range(len(chapters_)))
    spine=''.join(f'<itemref idref="c{i}"/>' for i in range(len(chapters_)))
    nav=''.join(f'<navPoint id="n{i}"><navLabel><text>{t}</text></navLabel><content src="c{i}.xhtml"/></navPoint>' for i,(t,_) in enumerate(chapters_))
    cov=''
    if cover: z.writestr('OEBPS/cover.jpg',cover); cov='<item id="cover-img" href="cover.jpg" media-type="image/jpeg" properties="cover-image"/>'
    z.writestr('OEBPS/content.opf',f'<package><metadata><dc:title>{title}</dc:title><dc:creator>{author}</dc:creator><dc:language>{lang}</dc:language></metadata><manifest><item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>{cov}{items}</manifest><spine>{spine}</spine></package>')
    z.writestr('OEBPS/toc.ncx',f'<ncx><navMap>{nav}</navMap></ncx>')
    for i,(t,ps) in enumerate(chapters_): z.writestr(f'OEBPS/c{i}.xhtml','<html><body><h2>'+t+'</h2>'+''.join(f'<p>{p}</p>' for p in ps)+'</body></html>')
    z.close(); return b.getvalue()
def jpeg(w=300,h=450,color=(120,40,40)):
    from PIL import Image
    o=io.BytesIO(); Image.new('RGB',(w,h),color).save(o,'JPEG'); return o.getvalue()
EN=[(f'Chapter {n}',[f'The house stood at the end of the lane in chapter {n}, and nobody had lived there for years. '*3 for _ in range(6)]) for n in (1,2,3)]

def fresh():
    db.reset_for_tests(); shutil.rmtree(config.DATA,ignore_errors=True); os.makedirs(config.DATA,exist_ok=True); books.sync_builtin()

# ---------------- 封面 ----------------
class Cover(unittest.TestCase):
    def setUp(self): fresh()
    def test_epub_cover_extracted_and_resized(self):
        c=importer.cover(make_epub('T','A',EN,cover=jpeg(600,900)),'t.epub')
        from PIL import Image
        im=Image.open(io.BytesIO(c)); self.assertLessEqual(im.size[0],importer.COVER_W); self.assertLessEqual(im.size[1],importer.COVER_H)
    def test_no_cover_or_bad_shape(self):
        self.assertIsNone(importer.cover(make_epub('T','A',EN),'t.epub'))
        self.assertIsNone(importer.cover(make_epub('T','A',EN,cover=jpeg(800,200)),'t.epub'),'横幅不算封面')
        self.assertIsNone(importer.cover(make_epub('T','A',EN,cover=jpeg(40,60)),'t.epub'),'太小（图标）不算封面')
        self.assertIsNone(importer.cover(fx('a_gbk.txt'),'a.txt'))
        self.assertIsNone(importer.cover(fx('f.pdf'),'f.pdf'),'文字版 PDF 第一页满是字，不当封面')
        self.assertIsNone(importer.cover(b'PK\x03\x04junk','x.epub'),'坏文件不报错')
    def test_scanned_pdf_first_page_is_cover(self): self.assertTrue(importer.cover(fx('h_scan.pdf'),'h.pdf'))
    @unittest.skipUnless(os.path.isdir(RAW),'没有原始资料')
    def test_real_books(self):
        got={n:bool(importer.cover(open(os.path.join(RAW,n),'rb').read(),n)) for n in ('巴斯克维尔的猎犬.epub','李鸿章传_中国言实2014.epub','西行漫记_Red_Star_over_China_1968修订版.epub','呐喊.epub','紅樓夢（程乙本）.epub')}
        self.assertEqual(got,{'巴斯克维尔的猎犬.epub':True,'李鸿章传_中国言实2014.epub':True,'西行漫记_Red_Star_over_China_1968修订版.epub':True,'呐喊.epub':False,'紅樓夢（程乙本）.epub':False},
                         '古登堡自动生成的花纹封面、维基文库没有封面的，按书名生成')
    def test_import_saves_cover_and_page_links_it(self):
        bid=books.import_file(make_epub('Book With Cover','Someone',EN,cover=jpeg()),'c.epub','dev1',background=False)
        self.assertTrue(books.get(bid)['meta'].get('cover')); self.assertTrue(os.path.exists(pipeline.bdir(bid,'cover.jpg')))
        self.assertEqual(app.payload(bid)['meta']['cover'],f'/api/books/{bid}/cover')
        bid2=books.import_file(fx('e.md'),'e.md','dev1',background=False); self.assertEqual(app.payload(bid2)['meta']['cover'],'')

# ---------------- 外文书：识别语言、翻译 ----------------
class Translate(unittest.TestCase):
    def setUp(self): fresh()
    def test_language_detection(self):
        self.assertEqual(books.guess_lang(importer.import_book(make_epub('T','A',EN),'t.epub')),'en')
        self.assertEqual(books.guess_lang(importer.import_book(fx('e.md'),'e.md')),'zh')
        de=[('Kapitel 1',['Der Mann ging nach Hause, und die Frau war nicht da. Das ist nicht gut, sagte er zu ihr. '*3]*5)]
        self.assertEqual(books.guess_lang(importer.import_book(make_epub('T','A',de),'t.epub')),'de')
    def test_foreign_book_translated_first_then_generated(self):
        bid=books.import_file(make_epub('The House','Anon',EN),'h.epub','dev1',background=False)
        self.assertTrue(books.get(bid)['meta']['需翻译'])
        d0=pipeline.packed(bid); self.assertTrue(d0.get('untranslated')); self.assertNotIn('orig',d0)
        pipeline.enqueue(bid); p=pipeline.progress(bid); self.assertEqual(p['total'],1+3+1+3*5+1)
        order=[]
        while True:
            j=pipeline.next_job()
            if not j: break
            order.append(j['step']); pipeline.run_job(j)
        self.assertEqual(order[:5],['terms','translate','translate','translate','zh'],'先译名表、逐章翻译，译完才做索引')
        d=pipeline.packed(bid)
        self.assertEqual(d['orig'],[['en','英文']]); self.assertFalse(d['untranslated'])
        self.assertTrue(d['props'][0]['zh'].startswith('（假模型译文）')); self.assertIn('The house stood',d['props'][0]['en'])
        self.assertTrue(os.path.exists(pipeline.bdir(bid,'原文.json')))
    def test_translate_validation(self):
        import tasks
        T=tasks.TASKS['translate']; src={'1.1':'x'*200,'1.2':'y'*100}
        self.assertEqual(T.validate({'1.1':'中'*60,'1.2':'文'*30},{'src':src}),[])
        self.assertTrue(any('少了' in p for p in T.validate({'1.1':'中'*60},{'src':src})))
        self.assertTrue(any('太短' in p for p in T.validate({'1.1':'中','1.2':'文'*30},{'src':src})))
        self.assertTrue(any('多出' in p for p in T.validate({'1.1':'中'*60,'1.2':'文'*30,'9.9':'x'},{'src':src})))

# ---------------- 找书 ----------------
GUT={'count':3,'results':[
  {'id':1342,'title':'Pride and Prejudice','authors':[{'name':'Austen, Jane','birth_year':1775,'death_year':1817}],'languages':['en'],'media_type':'Text','download_count':90000},
  {'id':42671,'title':'Pride and Prejudice: A Play','authors':[{'name':'Jerome, Helen','birth_year':1883,'death_year':1990}],'languages':['en'],'media_type':'Text','download_count':300},
  {'id':999,'title':'Pride (audio)','authors':[],'languages':['en'],'media_type':'Sound','download_count':5}]}
WS={'query':{'search':[{'title':'西遊記','snippet':'<span>西遊記</span>，明代小說','wordcount':800000},{'title':'西遊記/第001回','snippet':'','wordcount':9000},{'title':'西遊記 (消歧義)','snippet':'','wordcount':10}]}}
class FakeNet:
    """假的网络：古登堡书目接口、维基文库搜索接口、两个下载地址"""
    def __init__(self,down=()):
        self.hits=[]; self.down=set(down)
    def __call__(self,req,timeout=0):
        u=req.full_url; self.hits.append(u); host=urllib.parse.urlsplit(u).netloc
        if host in self.down: raise urllib.error.URLError('down')
        if 'gutendex' in u:
            q=urllib.parse.parse_qs(urllib.parse.urlsplit(u).query)['search'][0].lower()
            return io.BytesIO(json.dumps(GUT if 'pride' in q else {'count':0,'results':[]}).encode())
        if 'w/api.php' in u:
            q=urllib.parse.parse_qs(urllib.parse.urlsplit(u).query)['srsearch'][0]
            return io.BytesIO(json.dumps(WS if '西遊記' in q or '西游记' in q else {'query':{'search':[]}}).encode())
        if 'gutenberg.org/ebooks/1342' in u: return io.BytesIO(make_epub('Pride and Prejudice','Jane Austen',EN,cover=jpeg()))
        if 'ws-export' in u: return io.BytesIO(make_epub('西遊記','吳承恩',[('第一回 靈根育孕源流出',['話說天下四大部洲。'*20]*6),('第二回',['悟徹菩提真妙理。'*20]*6)],lang='zh'))
        if 'gutenberg.org/ebooks/' in u: return io.BytesIO(b'<html>not found</html>')
        raise urllib.error.HTTPError(u,404,'nf',{},None)
class Find(unittest.TestCase):
    def setUp(self): fresh(); search._cache.clear(); self.net=FakeNet(); search.opener=self.net
    def tearDown(self): search.opener=None
    def test_public_domain_rule(self):
        y=int(time.strftime('%Y'))
        self.assertTrue(search.pd_ok(y-51)); self.assertFalse(search.pd_ok(y-50)); self.assertTrue(search.pd_ok(None)); self.assertTrue(search.pd_ok(-400))
    def test_search_gutenberg_by_chinese_title(self):
        r=search.search('傲慢与偏见','dev1')['results']
        self.assertTrue(any('gutendex' in u and 'Pride' in urllib.parse.unquote_plus(u) for u in self.net.hits),'中文书名用原名去古登堡搜')
        top=r[0]; self.assertEqual((top['来源'],top['编号'],top['中文名'],top['作者'],top['语言名'],top['可下载'],top['需翻译']),('gutenberg','1342','傲慢与偏见','Jane Austen','英文',True,True))
        play=next(x for x in r if x['编号']=='42671'); self.assertFalse(play['可下载']); self.assertIn('1990 年去世',play['说明']); self.assertIn('2041',play['说明'])
        self.assertFalse(any(x['编号']=='999' for x in r),'有声书不列')
        self.assertEqual(r[-1]['编号'],'42671','不能下载的排在后面')
    def test_search_wikisource_simplified(self):
        r=search.search('西游记','dev1')['results']
        ws=[x for x in r if x['来源']=='wikisource']; self.assertEqual([x['书名'] for x in ws],['西遊記'],'只要作品主页面：不要"书名/第一回"子页面和消歧义页')
        self.assertEqual(ws[0]['语言名'],'中文'); self.assertTrue(ws[0]['可下载'])
    def test_one_source_down_other_still_works(self):
        search.opener=FakeNet(down={'gutendex.com'})
        d=search.search('西游记'); self.assertEqual(d['errors'],['古登堡暂时连不上']); self.assertTrue(d['results'])
        search.opener=FakeNet(down={'gutendex.com','zh.wikisource.org'})
        search._cache.clear(); d=search.search('西游记'); self.assertEqual(d['results'],[]); self.assertEqual(len(d['errors']),2)
    def test_cache(self):
        search.search('傲慢与偏见'); n=len(self.net.hits); search.search('傲慢与偏见'); self.assertEqual(len(self.net.hits),n,'同一个词一天内不重复去来源搜')
    def test_hot(self):
        h=search.hot(); self.assertEqual(len(h),12); self.assertEqual(h[0],'西游记')
        for d in ('a','b','c'): search.search('百年孤独',d)
        search.search('只有一个人搜','a')
        h=search.hot(); self.assertEqual(h[0],'百年孤独','真实搜索多的排前面'); self.assertNotIn('只有一个人搜',h,'至少两台设备搜过才算热门')
    def test_builtin_hits(self):
        self.assertEqual([x['编号'] for x in books.builtin_hits('红楼梦')],['hlm'])
        self.assertEqual([x['编号'] for x in books.builtin_hits('福尔摩斯')],['hound'])
        self.assertEqual([x['编号'] for x in books.builtin_hits('鲁迅')],['nahan'])
        self.assertEqual(books.builtin_hits('不存在的书'),[])
    def test_download_only_builds_url_itself(self):
        self.assertEqual(search.download_url('gutenberg','1342')[0],'https://www.gutenberg.org/ebooks/1342.epub3.images')
        for bad in [('gutenberg','http://evil.com/x'),('gutenberg','12;rm'),('wikisource','a<b>'),('ftp','x'),('wikisource','')]:
            with self.assertRaises(search.SearchError): search.download_url(*bad)
    def test_download_to_shelf(self):
        bid=books.download('dev1','gutenberg','1342','傲慢与偏见','Jane Austen')
        b=books.get(bid); self.assertEqual(b['status'],'ready'); self.assertEqual(b['title'],'傲慢与偏见'); self.assertEqual(b['kind'],'import'); self.assertEqual(b['owner'],'dev1')
        self.assertTrue(b['meta']['需翻译']); self.assertEqual(b['meta']['来源'],'gutenberg'); self.assertTrue(b['meta'].get('cover'))
        self.assertIn(bid,[x['id'] for x in books.shelf('dev1')]); self.assertNotIn(bid,[x['id'] for x in books.shelf('dev2')])
        self.assertEqual(books.download('dev1','gutenberg','1342'),bid,'同一个人再下载一次，还是那本')
        n=len(self.net.hits); bid2=books.download('dev2','gutenberg','1342'); self.assertNotEqual(bid2,bid)
        self.assertEqual(len(self.net.hits),n,'别人下载同一本：用服务器缓存，不再去古登堡下载')
        w=books.download('dev1','wikisource','西遊記','西遊記','')
        wb=books.get(w); self.assertFalse(wb['meta']['需翻译']); self.assertEqual(wb['meta']['链接'],'https://zh.wikisource.org/wiki/西遊記')
        self.assertTrue(pipeline.text_of(w)['章'][0]['标题'].startswith('第一回 灵根'),'繁体转简体')
    def test_mirror_and_format_fallback(self):
        """古登堡主站挂了 → 镜像；epub 没有 → 纯文本"""
        class Net(FakeNet):
            def __call__(s2,req,timeout=0):
                u=req.full_url; s2.hits.append(u)
                if 'www.gutenberg.org' in u: raise urllib.error.URLError('down')
                if 'pglaf' in u and u.endswith('.epub'): raise urllib.error.HTTPError(u,404,'nf',{},None)
                if 'pglaf' in u and u.endswith('.txt'): return io.BytesIO(('CHAPTER I\n\n'+'It is a truth universally acknowledged. '*80+'\n\nCHAPTER II\n\n'+'Mr. Bennet was among the earliest. '*80).encode())
                raise urllib.error.HTTPError(u,404,'nf',{},None)
        search.opener=Net()
        data,fname=search.fetch('gutenberg','1342')
        self.assertEqual(fname,'gutenberg_1342.txt'); self.assertIn(b'universally',data)
        self.assertTrue(any('www.gutenberg.org' in u for u in search.opener.hits)); self.assertTrue(any('pglaf' in u for u in search.opener.hits))
        bid=books.download('dev1','gutenberg','1342','傲慢与偏见'); self.assertEqual(books.get(bid)['chapters'],2,'纯文本照样导入')
    def test_html_error_page_is_not_a_book(self):
        class Net(FakeNet):
            def __call__(s2,req,timeout=0): return io.BytesIO(b'<!DOCTYPE html><html><body>Please verify you are human</body></html>'*50)
        search.opener=Net()
        with self.assertRaises(search.SearchError): search.fetch('wikisource','西遊記')
    def test_same_book_two_sources_merged(self):
        rows=[{'来源':'gutenberg','编号':'23962','书名':'西遊記','中文名':'','作者':'Wu Cheng\'en','语言':'zh','可下载':True,'热度':10},
              {'来源':'wikisource','编号':'西遊記','书名':'西遊記','中文名':'','作者':'','语言':'zh','可下载':True,'热度':5},
              {'来源':'gutenberg','编号':'1342','书名':'Pride and Prejudice','中文名':'傲慢与偏见','作者':'Jane Austen','语言':'en','可下载':True,'热度':9}]
        m=search.merge_sources(rows)
        self.assertEqual(len(m),2); xy=m[0]
        self.assertEqual([x['来源'] for x in xy['源']],['wikisource','gutenberg'],'中文书维基文库在前'); self.assertEqual(xy['来源名'],'维基文库、古登堡计划')
        self.assertEqual(xy['作者'],"Wu Cheng'en",'作者从另一个来源补上')
        self.assertEqual(len(m[1]['源']),1)
    def test_download_tries_next_source(self):
        bid=books.download('dev1','','',sources=[{'来源':'gutenberg','编号':'777'},{'来源':'wikisource','编号':'西遊記'}])
        self.assertEqual(books.get(bid)['meta']['来源'],'wikisource','第一个来源不是电子书，自动用第二个')
        with self.assertRaises(search.SearchError): books.download('dev1','','',sources=[{'来源':'ftp','编号':'x'}])
    def test_preview(self):
        p=search.preview([{'来源':'gutenberg','编号':'1342'}])
        self.assertEqual((p['作者'],p['章数']),('Jane Austen',3)); self.assertTrue(p['开头'][0].startswith('The house stood')); self.assertLessEqual(sum(len(x) for x in p['开头']),900+600)
        self.assertEqual(p['目录'][:2],['Chapter 1','Chapter 2'])
        n=len(self.net.hits); search.preview([{'来源':'gutenberg','编号':'1342'}]); self.assertEqual(len(self.net.hits),n,'预览过的书不再下载')
        bid=books.download('dev1','gutenberg','1342'); self.assertEqual(len(self.net.hits),n,'预览过的书，下载到书架用缓存')
    def test_download_errors(self):
        with self.assertRaises(search.SearchError) as e: books.download('dev1','gutenberg','777')
        self.assertIn('未返回电子书',str(e.exception))
        old=config.MAX_UPLOAD; config.MAX_UPLOAD=1000
        try:
            with self.assertRaises(search.SearchError): books.download('dev1','gutenberg','1342')
        finally: config.MAX_UPLOAD=old

# ---------------- 调整章节 ----------------
class Chapters(unittest.TestCase):
    def setUp(self):
        fresh(); self.b=books.import_file(fx('e.md'),'e.md','dev1',background=False)
        pipeline.enqueue(self.b); pipeline.drain()
    def T(self): return pipeline.text_of(self.b)
    def texts(self): return [s['文'] for c in self.T()['章'] for s in c['段']]
    def test_rename_only(self):
        before=self.texts(); m=chapters.apply(self.b,[{'op':'rename','ch':2,'title':'新的名字'}])
        self.assertEqual(m,{}); self.assertEqual(self.T()['章'][1]['标题'],'新的名字'); self.assertEqual(self.texts(),before)
        self.assertEqual(pipeline.packed(self.b)['hui'][1]['t'],'新的名字')
        self.assertEqual(pipeline.progress(self.b)['done'],26,'改章名不用重新生成')
    def test_merge_keeps_everything(self):
        before=self.texts(); c2=len(self.T()['章'][1]['段'])
        m=chapters.apply(self.b,[{'op':'merge','ch':2}])
        T=self.T(); self.assertEqual(len(T['章']),4); self.assertEqual(self.texts(),before,'段落顺序和内容不变')
        self.assertEqual(m['2.1'],f"1.{len(T['章'][0]['段'])-c2+1}"); self.assertEqual(m['3.1'],'2.1')
        self.assertEqual([c['章'] for c in T['章']],[1,2,3,4]); self.assertTrue(all(s['id'].startswith(f"{c['章']}.") for c in T['章'] for s in c['段']))
        p=pipeline.progress(self.b); self.assertEqual(p['todo'],0,'合并：译文、索引、卡片、回顾都接上，不重新生成'); self.assertEqual(books.get(self.b)['status'],'ready')
        d=pipeline.packed(self.b); self.assertEqual(len(d['hui']),4)
        self.assertTrue(all(pid in d['cards'] for pid in d['units']),'合并后每一段仍有卡片')
        r=d['recap'][0]; self.assertEqual(r['小节'][-1]['到'],T['章'][0]['段'][-1]['id'],'回顾小节的段号改成了新段号')
        self.assertEqual(books.get(self.b)['chapters'],4)
    def test_split_regenerates_only_what_is_cut(self):
        T0=self.T(); c3=T0['章'][2]; at=c3['段'][4]['id']; before=self.texts()
        cut_unit=next((u for u in c3['单元'] if u[0]!=at and c3['段'].index(next(s for s in c3['段'] if s['id']==u[0]))<4<=c3['段'].index(next(s for s in c3['段'] if s['id']==u[1]))),None)
        m=chapters.apply(self.b,[{'op':'split','at':at,'title':'第三章（下）'}])
        T=self.T(); self.assertEqual(len(T['章']),6); self.assertEqual(self.texts(),before)
        self.assertEqual(T['章'][3]['标题'],'第三章（下）'); self.assertEqual(m[at],'4.1'); self.assertEqual(m['4.1'],'5.1')
        p=pipeline.progress(self.b)
        todo={(r[0],r[1]) for r in db.all("select step,unit from jobs where book=? and status!='done'",(self.b,))}
        self.assertTrue({('index','3'),('index','4'),('recap','3'),('recap','4'),('merge','')}<=todo,todo)
        self.assertFalse(any(u in ('1','2','5','6') for s,u in todo),'没动的章不重新生成')
        self.assertNotIn(('gloss','3'),todo,'词语表照搬')
        if cut_unit: self.assertIn(('cards','3'),todo,'被切开的那张卡片要重写')
        self.assertEqual(books.get(self.b)['status'],'generating')
        pipeline.drain(); self.assertEqual(pipeline.progress(self.b)['todo'],0); self.assertEqual(books.get(self.b)['status'],'ready')
        d=pipeline.packed(self.b); self.assertTrue(all(pid in d['cards'] for pid in d['units']))
    def test_combined_and_errors(self):
        chapters.apply(self.b,[{'op':'merge','ch':5},{'op':'rename','ch':1,'title':'序'},{'op':'split','at':'2.3','title':'插曲'}])
        T=self.T(); self.assertEqual([c['标题'] for c in T['章']][:3],['序','第二章 风起二','插曲']); self.assertEqual(len(T['章']),5)
        with self.assertRaises(chapters.EditError): chapters.apply(self.b,[{'op':'merge','ch':1}])
        with self.assertRaises(chapters.EditError): chapters.apply(self.b,[{'op':'split','at':'1.1'}])
        with self.assertRaises(chapters.EditError): chapters.apply(self.b,[{'op':'split','at':'99.1'}])
    def test_foreign_book_keeps_translation(self):
        bid=books.import_file(make_epub('The House','Anon',EN),'h.epub','dev1',background=False); pipeline.enqueue(bid); pipeline.drain()
        zh=[s['文'] for c in pipeline.text_of(bid)['章'] for s in c['段']]
        chapters.apply(bid,[{'op':'merge','ch':2},{'op':'split','at':'3.2','title':'Part'}])
        T=pipeline.text_of(bid); self.assertEqual([s['文'] for c in T['章'] for s in c['段']],zh,'译文不丢')
        self.assertTrue(all(s.get('en') for c in T['章'] for s in c['段']),'每段原文还在')
        self.assertEqual(len(pipeline.original(bid)['章']),len(T['章']),'原文的分章跟着改')
        todo={r[0] for r in db.all("select step from jobs where book=? and status!='done'",(bid,))}
        self.assertNotIn('translate',todo,'调整章节不重新翻译'); self.assertNotIn('terms',todo)

# ---------------- 接口 ----------------
srv=None; URL=''
class Client:
    def __init__(self): self.op=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    def req(self,method,path,body=None,headers=None):
        r=urllib.request.Request(URL+path,data=body,method=method,headers=headers or {})
        try:
            with self.op.open(r,timeout=60) as resp: return resp.status,resp.read(),dict(resp.headers)
        except urllib.error.HTTPError as e: return e.code,e.read(),dict(e.headers)
    def json(self,method,path,obj=None,headers=None):
        c,raw,_=self.req(method,path,json.dumps(obj).encode() if obj is not None else None,headers); return c,json.loads(raw) if raw else None
    def upload(self,name,data): c,raw,_=self.req('POST','/api/import',data,{'X-Filename':urllib.parse.quote(name)}); return json.loads(raw)
class API(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        global srv,URL; fresh(); srv=app.make_server('127.0.0.1',0); URL=f'http://127.0.0.1:{srv.server_port}'; threading.Thread(target=srv.serve_forever,daemon=True).start()
    @classmethod
    def tearDownClass(cls): srv.shutdown()
    def test_cover_endpoint(self):
        a,b=Client(),Client(); bid=a.upload('c.epub',make_epub('Covered','X',EN,cover=jpeg()))['id']
        c,raw,h=a.req('GET',f'/api/books/{bid}/cover'); self.assertEqual(c,200); self.assertEqual(h['Content-Type'],'image/jpeg'); self.assertEqual(raw[:3],b'\xff\xd8\xff')
        self.assertIn('max-age',h['Cache-Control']); self.assertEqual(b.req('GET',f'/api/books/{bid}/cover')[0],404,'别人看不到我导入的书的封面')
        self.assertEqual(a.req('GET','/api/books/hlm/cover')[0],404)
    def test_find_api(self):
        search.opener=FakeNet(); search._cache.clear()
        try:
            a=Client()
            c,d=a.json('GET','/api/hot'); self.assertEqual(c,200); self.assertEqual(len(d['hot']),12)
            c,d=a.json('GET','/api/search?q='+urllib.parse.quote('傲慢与偏见')); self.assertEqual(c,200); self.assertEqual(d['results'][0]['编号'],'1342'); self.assertEqual(d['builtin'],[])
            c,d=a.json('GET','/api/search?q='+urllib.parse.quote('红楼梦')); self.assertEqual([x['编号'] for x in d['builtin']],['hlm'])
            c,d=a.json('POST','/api/download',{'source':'gutenberg','ref':'1342','title':'傲慢与偏见','author':'Jane Austen'}); self.assertEqual(c,200); bid=d['id']
            sh={x['id']:x for x in a.json('GET','/api/shelf')[1]['books']}; self.assertEqual(sh[bid]['title'],'傲慢与偏见')
            c,d=a.json('GET','/api/books/'+bid); self.assertEqual(d['meta']['from'],'gutenberg'); self.assertTrue(d['meta']['foreign']); self.assertTrue(d['meta']['link'].endswith('/1342'))
            self.assertEqual(Client().json('GET','/api/books/'+bid)[0],404,'下载的书只有自己能看')
            self.assertEqual(a.json('POST','/api/download',{'source':'gutenberg','ref':'http://evil.com'})[0],400)
            search.opener=FakeNet(down={'www.gutenberg.org'})
            self.assertEqual(Client().json('POST','/api/download',{'source':'gutenberg','ref':'1342'})[0],200,'已经缓存的书，来源网站挂了也能下载')
            self.assertIn(Client().json('POST','/api/download',{'source':'gutenberg','ref':'5'})[0],(400,502),'主站挂了、镜像也没有：告诉读者下载不了')
            search.opener=FakeNet(); search._cache.clear()
            c,d=a.json('POST','/api/preview',{'sources':[{'来源':'gutenberg','编号':'1342'}]}); self.assertEqual(c,200); self.assertEqual(d['章数'],3); self.assertTrue(d['开头'])
            self.assertEqual(a.json('POST','/api/preview',{'sources':[{'来源':'gutenberg','编号':'http://x'}]})[0],400)
            self.assertEqual(a.json('POST','/api/preview',{})[0],400)
            c,d=a.json('POST','/api/download',{'sources':[{'来源':'gutenberg','编号':'777'},{'来源':'gutenberg','编号':'1342'}],'title':'傲慢与偏见'}); self.assertEqual(c,200,'第一个来源不行，自动用第二个')
            self.assertEqual(a.json('DELETE','/api/books/'+bid)[1]['ok'],True)
        finally: search.opener=None
    def test_chapters_api(self):
        a,b=Client(),Client(); bid=a.upload('e.md',fx('e.md'))['id']
        c,d=a.json('POST',f'/api/books/{bid}/chapters',{'ops':[{'op':'merge','ch':2},{'op':'rename','ch':1,'title':'开头'}]})
        self.assertEqual(c,200); self.assertEqual(len(d['hui']),4); self.assertEqual(d['hui'][0]['t'],'开头'); self.assertIn('idmap',d); self.assertEqual(d['meta']['chapters'],4)
        self.assertEqual(b.json('POST',f'/api/books/{bid}/chapters',{'ops':[]})[0],404)
        self.assertEqual(a.json('POST',f'/api/books/{bid}/chapters',{'ops':[{'op':'merge','ch':1}]})[0],400)
        self.assertEqual(a.json('POST','/api/books/hound/chapters',{'ops':[]})[0],403)

if __name__=='__main__': unittest.main()
