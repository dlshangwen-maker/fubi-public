"""服务端体验版：不用起服务器，一个 html 文件就能点着试"找书 → 下载到书架 → 读"。
页面就是 server/app.py 生成的那一页（带 window.FUBI），网络请求用桩代替：
  热门搜索、搜索：按 server/hot.json 造结果（来源、语言、能不能下载照真的规则）
  下载：只有《和约的经济后果》（凯恩斯，原始资料里有真书）能真的下载，读到的是真正文；其它书提示"体验版没有联网"
  导入、调整章节：提示"体验版不能用，部署后可以"
用法：python3 生成/build_demo.py 会自动调它；也可以单独跑 python3 -I 生成/自测/体验页.py → Demo/伏笔_demo.html（同时拷一份到 outputs）
2026-10-27 用户："可以合在一起吗"——这个就是唯一给用户的 demo；单文件版（生成/自测/单文件版.html）只给自测用。"""
import os,sys,json,tempfile,glob,re,shutil
B=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))+'/'
os.environ.update(FUBI_DATA=tempfile.mkdtemp(prefix='fubi_try_'),FUBI_SYNC_IMPORT='1')
sys.path.insert(0,B+'server')
import config,db,books,pipeline,app,search
config.MODEL.update(provider='mock')
books.sync_builtin()
dev='trydevice_abcdefgh'
k=books.import_file(open(B+'原始资料/和约的经济后果.epub','rb').read(),'gutenberg_15776.epub','other',meta={'来源':'gutenberg','编号':'15776','链接':'https://www.gutenberg.org/ebooks/15776','书名':'和约的经济后果','作者':'约翰·梅纳德·凯恩斯'},background=False)
db.run("update books set nat='英国' where id=?",(k,))
keynes=app.payload(k)
search.opener=lambda req,timeout=0:open(B+'原始资料/和约的经济后果.epub','rb')
kpv=search.preview([{'来源':'gutenberg','编号':'15776'}])   # 真的预览：书的开头几段
hot=json.load(open(B+'server/hot.json',encoding='utf-8'))['词']
h=app.page(dev)
J=lambda x:json.dumps(x,ensure_ascii=False).replace('</','<\\/')
stub=r"""
window.confirm=()=>true;
(()=>{
const HOT=%HOT%, KEY=%KEY%, KEYNES=%KEYNES%, BUILTIN=%BUILTIN%, KPV=%KPV%;
const n=s=>String(s||'').toLowerCase().replace(/[\s·・.\-—_，,、：:（）()《》“”"'!！?？]+/g,'');
const KR={'来源':'gutenberg','编号':'15776','书名':'The Economic Consequences of the Peace','中文名':'和约的经济后果','作者':'John Maynard Keynes','生卒':'1883—1946','去世':1946,'语言':'en','语言名':'英文','可下载':true,'需翻译':true,'说明':'','链接':'https://www.gutenberg.org/ebooks/15776',
  '主题':['Treaty of Versailles (1919)','Reparations','Economic conditions'],'简介':'1919 年巴黎和会上，凯恩斯是英国财政部的代表。他认为和约对德国的赔款要求无法兑现，会拖垮整个欧洲经济，于是辞职写下这本书。','作者中文':'约翰·梅纳德·凯恩斯','国籍':'英国',
  '内容提要':'"The Economic Consequences of the Peace" by John Maynard Keynes is an economic analysis written in 1919, examining the Treaty of Versailles and its likely effects on Europe.',
  '源':[{'来源':'gutenberg','编号':'15776','名':'古登堡计划','说明':'epub，主站不行时自动换镜像站或纯文本'}],'来源名':'古登堡计划'};
function results(q){
  const nq=n(q), out=[];
  if(['凯恩斯','keynes','和约','和约的经济后果','economicconsequences'].some(w=>nq.includes(n(w))||n(w).includes(nq)&&nq.length>=2)) out.push(KR);
  HOT.forEach(h=>{ if(![h['词'],h['作者'],h['原名']].some(x=>x&&(n(x).includes(nq)||nq.includes(n(x))&&n(x).length>=2))) return;
    const fo=!!h['原名'];
    const G={'来源':'gutenberg','编号':h['词'],'名':'古登堡计划','说明':'epub，主站不行时自动换镜像站或纯文本'}, W={'来源':'wikisource','编号':h['词'],'名':'维基文库','说明':'epub，导出失败时自动换纯文本'};
    const src=fo?[G]:[W,G];
    out.push({'来源':src[0]['来源'],'编号':h['词'],'书名':fo?h['原名']:h['词'],'中文名':fo?h['词']:'','作者':fo?'':h['作者'],'作者中文':h['作者'],'国籍':h['国籍']||'','语言':fo?'en':'zh','语言名':fo?'英文':'中文','可下载':true,'需翻译':fo,'说明':'','链接':'','简介':h['简介']||'',
      '源':src,'来源名':fo?'古登堡计划':'维基文库、古登堡计划'});
    if(fo&&h['词']==='了不起的盖茨比') out.push({'来源':'gutenberg','编号':'x1','书名':'The Great Gatsby: A Study Guide','中文名':'','作者':'Modern Editor','去世':1990,'语言':'en','语言名':'英文','可下载':false,'需翻译':true,'说明':'作者 1990 年去世，在中国大陆还没进入公版（要到 2041 年）','链接':''});
  });
  return out;
}
const J=x=>({ok:true,status:200,json:async()=>x}), E=(c,m)=>({ok:false,status:c,json:async()=>({error:m})});
window.fetch=async(u,o={})=>{
  await new Promise(r=>setTimeout(r,350));
  if(u==='/api/hot') return J({hot:['和约的经济后果',...HOT.map(h=>h['词'])].slice(0,12)});
  if(u.startsWith('/api/search')){ const q=decodeURIComponent(u.split('q=')[1]||''); const nq=n(q);
    return J({q,results:results(q),builtin:BUILTIN.filter(b=>[b['书名'],b['作者']].some(x=>n(x).includes(nq)||nq.includes(n(x)))),errors:[]}); }
  if(u==='/api/preview'){ const b=JSON.parse(o.body); if(b.sources[0]['编号']==='15776') return J(KPV); return E(502,'体验版没有联网，取不到这本书的开头。部署到服务器后，每本书都能先看开头几页'); }
  if(u==='/api/download'){ const b=JSON.parse(o.body); if((b.sources||[]).some(x=>x['编号']==='15776')||b.ref==='15776') return J({id:KEY,status:'ready'}); return E(502,'体验版没有联网，这本下载不了。部署到服务器后，搜到的书都能下载；体验版里可以下载《和约的经济后果》试试'); }
  if(u==='/api/books/'+KEY+'/status') return J({status:'ready'});
  if(u==='/api/books/'+KEY) return J(JSON.parse(JSON.stringify(KEYNES)));
  if(u==='/api/import') return E(400,'体验版不能导入文件。部署到服务器后可以导入 epub、pdf、txt 等十几种格式');
  if(u.endsWith('/chapters')) return E(400,'体验版不能保存章节调整，部署到服务器后可以');
  if(u==='/api/ask') return J({'类型':'书外','回答':'体验版没有接模型。部署并配好模型后，这里会按你的阅读进度回答，不剧透。','引用':[],'回收':'','回收说明':'','回收锚句':''});
  return J({ok:true});
};
window.addEventListener('load',()=>{ try{ localStorage.removeItem('rb_imp_'+KEY); }catch(e){} });
})();
"""
builtin=[{'来源':'builtin','编号':kk,'书名':t,'作者':a,'国籍':nat,'简介':books.BUILTIN_INFO[kk]} for kk,t,a,nat in books.BUILTIN_SHELF]
stub=stub.replace('%KPV%',J(kpv)).replace('%HOT%',J(hot)).replace('%KEY%',J(k)).replace('%KEYNES%',J(keynes)).replace('%BUILTIN%',J(builtin))
m=re.search(r'<meta charset=[^>]*>',h,re.I)
h=h[:m.end()]+'<script>'+stub+'</script>'+h[m.end():]
out=B+'Demo/伏笔_demo.html'
open(out,'w',encoding='utf-8').write(h)
o=os.environ.get('FUBI_OUT') or (glob.glob('/sessions/*/mnt/outputs/')+[''])[0]
if o: shutil.copy(out,o+'伏笔_demo.html')
print('ok',len(h)//1024,'KB')
