"""导入测试：每种格式各一份样本（tests/fixtures/），加上 原始资料/ 里真实的 epub 和 PDF。
运行：cd server && python3 -m unittest discover -s tests
样本是脚本生成的五章小说（"第一章 风起一"……），每种格式都应该读出同样的五章。"""
import os,sys,io,zipfile,shutil,unittest,re
HERE=os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0,os.path.dirname(HERE))
import importer
FX=os.path.join(HERE,'fixtures')
RAW=os.path.join(os.path.dirname(os.path.dirname(HERE)),'原始资料')
FIVE=['第一章 风起一','第二章 风起二','第三章 风起三','第四章 风起四','第五章 风起五']
def imp(name,data=None): return importer.import_book(data if data is not None else open(os.path.join(FX,name),'rb').read(),name)
def check_shape(t,b):
    """全文.json 的格式：章号从 1 连续、段号"章.段"、单元覆盖全部段落、没有空段、段不超长"""
    for i,c in enumerate(b['章'],1):
        t.assertEqual(c['章'],i)
        t.assertTrue(c['段'])
        for k,s in enumerate(c['段'],1):
            t.assertEqual(s['id'],f'{i}.{k}'); t.assertTrue(s['文'].strip()); t.assertLessEqual(len(s['文']),importer.PARA_MAX+400)
        ids=[s['id'] for s in c['段']]
        t.assertEqual(c['单元'][0][0],ids[0]); t.assertEqual(c['单元'][-1][1],ids[-1])

class Formats(unittest.TestCase):
    def five(self,name,first_para_ok=True):
        b=imp(name); check_shape(self,b)
        self.assertEqual([c['标题'] for c in b['章']][-5:],FIVE,name)
        self.assertGreater(b['导入']['字数'],9000)
        return b
    def test_txt_gbk_hard_wrapped(self):
        b=self.five('a_gbk.txt')
        self.assertTrue(all(len(s['文'])>60 for s in b['章'][1]['段']),'硬换行没接回去')
    def test_txt_without_headings_cut_by_size(self):
        b=imp('b_nohead.txt'); check_shape(self,b)
        self.assertEqual(b['章'][0]['标题'],'第1部分'); self.assertGreaterEqual(len(b['章']),4)
    def test_docx(self): self.five('c.docx')
    def test_html_ignores_script(self):
        b=self.five('d.html'); self.assertNotIn('alert','\n'.join(s['文'] for c in b['章'] for s in c['段']))
    def test_md(self): self.five('e.md')
    def test_epub_from_pandoc(self): self.five('i.epub')
    def test_pdf_text_strips_header_footer(self):
        b=self.five('f.pdf'); txt='\n'.join(s['文'] for c in b['章'] for s in c['段'])
        self.assertNotIn('某出版社',txt)
        self.assertFalse(re.search(r'[。”]\d+他',txt),'页码混进了正文')
    def test_pdf_english(self):
        b=imp('g_en.pdf'); check_shape(self,b)
        self.assertEqual([c['标题'] for c in b['章']],['Chapter 1','Chapter 2','Chapter 3'])
        self.assertIn('the lane, and nobody',b['章'][0]['段'][0]['文'])
    @unittest.skipUnless(shutil.which('soffice') or shutil.which('libreoffice'),'没装 LibreOffice')
    def test_old_word_and_rtf(self):
        for n in ('c.doc','c.rtf'): self.five(n)
    @unittest.skipUnless(shutil.which('tesseract') and shutil.which('pdftoppm'),'没装 tesseract')
    def test_scanned_pdf_ocr_english(self):
        b=imp('j_scan_en.pdf'); self.assertEqual(len(b['章']),3); self.assertIn('house stood',b['章'][0]['段'][0]['文'])
    @unittest.skipUnless(shutil.which('tesseract') and shutil.which('pdftoppm'),'没装 tesseract')
    def test_scanned_pdf_chinese_needs_language_pack(self):
        langs=os.popen('tesseract --list-langs 2>&1').read()
        if 'chi_sim' in langs:
            b=imp('h_scan.pdf'); self.assertIn('信封',''.join(s['文'] for c in b['章'] for s in c['段']))
        else:
            with self.assertRaises(importer.ImportError_) as e: imp('h_scan.pdf')
            self.assertIn('文字识别',str(e.exception))

class Safety(unittest.TestCase):
    def test_zip_bomb_rejected(self):
        buf=io.BytesIO()
        with zipfile.ZipFile(buf,'w',zipfile.ZIP_DEFLATED) as z:
            z.writestr('META-INF/container.xml','<x/>'); z.writestr('big.bin',b'\0'*(importer.MAX_UNZIP+1))
        with self.assertRaises(importer.ImportError_): imp('bomb.epub',buf.getvalue())
    def test_garbage_gives_friendly_error(self):
        with self.assertRaises(importer.ImportError_): imp('x.epub',b'PK\x03\x04not a zip really')
        with self.assertRaises(importer.ImportError_): imp('empty.txt',b'   \n\n ')
    def test_filename_not_used_as_path(self):
        b=imp('../../etc/passwd.txt','第一章 开始\n他来了。'.encode()); self.assertEqual(b['导入']['文件'],'passwd.txt')
    def test_unknown_extension_sniffed(self):
        b=imp('book',open(os.path.join(FX,'f.pdf'),'rb').read()); self.assertEqual(b['导入']['格式'],'pdf')
    def test_supported_list(self):
        for x in ('epub','txt','pdf','docx','doc','mobi','azw3','html','md','rtf'): self.assertIn(x,importer.supported())

@unittest.skipUnless(os.path.isdir(RAW),'没有 原始资料 文件夹')
class RealBooks(unittest.TestCase):
    """真实的书：分章数大致对、没有超长章、没有只剩标题的空章"""
    def book(self,name):
        b=importer.import_book(open(os.path.join(RAW,name),'rb').read(),name); check_shape(self,b); return b
    def sizes(self,b): return [sum(len(s['文']) for s in c['段']) for c in b['章']]
    def test_hongloumeng_120_chapters_traditional_to_simplified(self):
        b=self.book('紅樓夢（程乙本）.epub'); ts=[c['标题'] for c in b['章']]
        hui=[t for t in ts if re.match(r'第.{1,4}回 ',t)]
        self.assertGreaterEqual(len(hui),118); self.assertTrue(any('甄士隐' in t for t in ts),'没转成简体')
        self.assertFalse(any(re.fullmatch(r'第.+回\s*至第.+回',t) for t in ts),'"第一回至第十回"这种分卷标题不该单独成章')
    def test_hound_15_chapters(self):
        b=self.book('巴斯克维尔的猎犬.epub')
        self.assertEqual(sum(1 for c in b['章'] if c['标题'].startswith('Chapter')),15)
    def test_li_hongzhang(self):
        b=self.book('李鸿章传_中国言实2014.epub'); self.assertTrue(any('绪论' in c['标题'] for c in b['章']))
    def test_nahan_badly_made_epub(self):
        """古登堡的《呐喊》epub 目录只有一条、标题全是普通段落：靠"找漏掉的短标题"分出各篇"""
        b=self.book('呐喊.epub'); ts=[c['标题'] for c in b['章']]
        for t in ('狂人日记','故乡','第一章序','第九章大团圆','白光'): self.assertIn(t,ts)
        self.assertLessEqual(max(self.sizes(b)),15000)
    def test_big_books_no_giant_chapters(self):
        for n in ('罗马帝国衰亡史.epub','西行漫记_Red_Star_over_China_1968修订版.epub','科学的基础.epub','和约的经济后果.epub'):
            b=self.book(n); sz=self.sizes(b)
            self.assertLessEqual(max(sz),45000,n); self.assertGreaterEqual(min(sz),importer.TINY,n)
            self.assertFalse(any(re.fullmatch(r'ch\d+_fn\d+\w?',c['标题']) for c in b['章']),'注释条目不该成章')
    def test_pdf_wittgenstein(self):
        b=self.book('逻辑哲学论.pdf'); self.assertGreater(len(b['章']),5)

if __name__=='__main__': unittest.main()
