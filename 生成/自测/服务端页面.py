"""造一个"服务端模式"的阅读器页面给预览面板测：临时数据目录里导入一本书（第一章生成了卡片和回顾，其余没生成）、一本坏文件（导入失败），
再用 server/app.py 的 page() 生成页面，注入 自测_服务端模式.js。
用法：python3 -I 生成/自测/服务端页面.py   → outputs/自测_服务端.html"""
import os,sys,json,tempfile,glob,re
B=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))+'/'
os.environ.update(FUBI_DATA=tempfile.mkdtemp(prefix='fubi_page_'),FUBI_SYNC_IMPORT='1')
sys.path.insert(0,B+'server')
import config,db,books,pipeline,app
config.MODEL.update(provider='mock')
books.sync_builtin()
dev='testdevice_abcdefgh'
bid=books.import_file(open(B+'server/tests/fixtures/e.md','rb').read(),'测试小说.md',dev,background=False)
books.import_file(b'PK\x03\x04broken','坏文件.epub',dev,background=False)
# 只生成第一章：卡片 + 回顾（模拟"生成到一半"）
T=pipeline.text_of(bid); c=T['章'][0]
pipeline._save(pipeline.chfile(bid,'卡片',1),{a:{lv:{'白话':f'这一章写他收到一封没署名的信（{lv}）。','展开':'测试用的解释。','前置':''} for lv in ('入门','标准','深入')} for a,b in c['单元']})
pipeline._save(pipeline.chfile(bid,'回顾/分',1),{'回':1,'一句话':'他收到一封信。','详细':['他收到一封信。'],'小节':[{'到':c['段'][-1]['id'],'写':'收信'}]})
pipeline.merge_small(bid); pipeline.mark_dirty(bid)
# v9.48：一本带封面的导入书、一本书库的书（加入了书架）、一本书库的书（没加入，测"加入书架"）；书库目录、合并后的章节数据给 fetch 桩用
sys.path.insert(0,B+'server/tests'); import test_v948 as T9
cid=books.import_file(T9.make_epub('有封面的书','某人',T9.EN,cover=T9.jpeg(300,450,(40,70,110))),'cover.epub',dev,background=False)
# 找书：一本已经下载到书架的（古登堡），搜索结果、热门搜索、下载后的书给 fetch 桩用
import search
search.opener=T9.FakeNet(); search._cache.clear()
lib=books.download(dev,'gutenberg','1342','傲慢与偏见','Jane Austen')
found=dict(search.search('傲慢与偏见'),builtin=books.builtin_hits('傲慢与偏见'))
found_hlm=dict(search.search('红楼梦'),builtin=books.builtin_hits('红楼梦'))
found_xy=dict(search.search('西游记'),builtin=[])
hotw=search.hot()
dlid=books.import_file(T9.make_epub('西遊記','吳承恩',[('第一回 靈根育孕源流出',['話說天下四大部洲。'*20]*6)],lang='zh'),'西遊記.epub','other_device',meta={'来源':'wikisource','编号':'西遊記','链接':'https://zh.wikisource.org/wiki/西遊記','书名':'西遊記'},background=False)
dl_payload=app.payload(dlid)
import chapters,shutil,copy
tmpbook=copy.deepcopy(pipeline.text_of(bid))
idmap=chapters.apply(bid,[{'op':'merge','ch':2},{'op':'rename','ch':1,'title':'开头'}]); merged=dict(app.payload(bid),idmap=idmap)
pipeline._save(pipeline.bdir(bid,'全文.json'),tmpbook); db.run('update books set chapters=5 where id=?',(bid,)); shutil.rmtree(pipeline.gen(bid,'卡片'),ignore_errors=True)
pipeline._save(pipeline.chfile(bid,'卡片',1),{a:{lv:{'白话':f'这一章写他收到一封没署名的信（{lv}）。','展开':'测试用的解释。','前置':''} for lv in ('入门','标准','深入')} for a,b in c['单元']})
pipeline.mark_dirty(bid)
h=app.page(dev).replace('"model": false','"model": true',1)   # 测自由提问走模型
key=pipeline.packed(bid)['key']
js=open(B+'生成/自测/自测_服务端模式.js',encoding='utf-8').read()
m=re.search(r'<meta charset=[^>]*>',h,re.I)
J=lambda x:json.dumps(x,ensure_ascii=False).replace('</','<\\/')
pre=''.join(f'window.{k}={J(v)};' for k,v in dict(FUBI_IMP=bid,FUBI_KEY=key,FUBI_COV=cid,FUBI_LIB=lib,FUBI_DL=dlid,__FOUND=found,__FOUND_HLM=found_hlm,__FOUND_XY=found_xy,__HOT=hotw,__DL=dl_payload,__MERGED=merged).items())
h=h[:m.end()]+'<style>body{max-width:390px}</style><script>'+pre+'try{localStorage.clear()}catch(e){}</script><script>'+js+'</script>'+h[m.end():]
OUT=os.environ.get('FUBI_OUT') or (glob.glob('/sessions/*/mnt/outputs/')+[B])[0]
open(OUT+'自测_服务端.html','w',encoding='utf-8').write(h); print('ok',bid,len(h)//1024,'KB')
