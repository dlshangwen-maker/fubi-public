"""反馈：读者发文字（可带图片），管理员在后台看。

  表 feedback        一条反馈：谁、什么时候、文字、哪个版本、从哪个页面发的、状态（new / done）
  图片               存在 <数据目录>/feedback/<反馈id>/<序号>.<扩展名>；一条最多 3 张，每张最多 3 MB，
                     只收 PNG / JPEG / WebP / GIF，并按文件开头的字节判断类型（不信文件名和请求头）
  流程               先 POST /api/feedback/image 逐张上传，拿到临时编号；再 POST /api/feedback 提交文字和临时编号。
                     没提交的临时图片 24 小时后清掉
  隐私               只记账号 id、邮箱（后台要能回复）、版本、页面名；不记阅读内容
"""
import os,re,time,secrets,json
import db,config

MAX_TEXT=2000; MAX_IMAGES=3; MAX_IMAGE_BYTES=3*1024*1024
SNIFF=((b'\x89PNG\r\n\x1a\n','png'),(b'\xff\xd8\xff','jpg'),(b'GIF87a','gif'),(b'GIF89a','gif'))
PAGES={'reader':'阅读页','shelf':'书架','me':'我的','find':'找书','import':'导入','other':'其他'}

class FeedbackError(Exception):
    def __init__(self,msg,code=400): super().__init__(msg); self.code=code

def _init():
    db.run('''create table if not exists feedback(
      id integer primary key autoincrement, uid integer, email text default '', text text not null,
      page text default '', ver text default '', imgs text default '[]', status text default 'new', t real)''')
    db.run('create index if not exists feedback_t on feedback(t)')
_ready=False
def _db():
    global _ready
    if not _ready: _init(); _ready=True

def _dir(*a):
    return config.path('feedback',*a)

def kind_of(data):
    """按文件开头判断图片类型；不是支持的类型返回 None"""
    for sig,ext in SNIFF:
        if data.startswith(sig): return ext
    if data[:4]==b'RIFF' and data[8:12]==b'WEBP': return 'webp'
    return None

def save_temp(uid,data):
    """逐张上传：存成临时文件，返回临时编号"""
    if not data: raise FeedbackError('未收到图片')
    if len(data)>MAX_IMAGE_BYTES: raise FeedbackError('图片不能超过 3 MB')
    ext=kind_of(data)
    if not ext: raise FeedbackError('仅支持 PNG、JPEG、WebP、GIF 图片')
    _sweep()
    tid='%d-%s'%(uid,secrets.token_urlsafe(9).replace('_','a').replace('-','b'))
    with open(_dir('tmp',tid+'.'+ext),'wb') as f: f.write(data)
    return tid

def _sweep():
    d=os.path.dirname(_dir('tmp','x'))
    now=time.time()
    for n in os.listdir(d):
        p=os.path.join(d,n)
        try:
            if now-os.path.getmtime(p)>86400: os.remove(p)
        except OSError: pass

def _find_temp(uid,tid):
    if not re.fullmatch(r'%d-[A-Za-z0-9]{6,20}'%uid,str(tid)): return None
    d=os.path.dirname(_dir('tmp','x'))
    for ext in ('png','jpg','gif','webp'):
        p=os.path.join(d,tid+'.'+ext)
        if os.path.exists(p): return p
    return None

def submit(user,text,page='',ver='',image_ids=()):
    _db()
    text=str(text or '').strip()
    if not text: raise FeedbackError('请填写反馈内容')
    if len(text)>MAX_TEXT: raise FeedbackError('反馈内容不能超过 %d 字'%MAX_TEXT)
    ids=[x for x in list(image_ids or [])][:MAX_IMAGES+1]
    if len(ids)>MAX_IMAGES: raise FeedbackError('最多添加 %d 张图片'%MAX_IMAGES)
    srcs=[]
    for t in ids:
        p=_find_temp(user['id'],t)
        if not p: raise FeedbackError('有图片已过期，请重新添加')
        srcs.append(p)
    page=page if page in PAGES else 'other'; ver=str(ver or '')[:40]
    cur=db.run('insert into feedback(uid,email,text,page,ver,t) values(?,?,?,?,?,?)',(user['id'],user['email'],text,page,ver,time.time()))
    fid=cur.lastrowid; names=[]
    for i,p in enumerate(srcs):
        ext=p.rsplit('.',1)[1]; dst=_dir(str(fid),'%d.%s'%(i+1,ext))
        os.replace(p,dst); names.append('%d.%s'%(i+1,ext))
    db.run('update feedback set imgs=? where id=?',(json.dumps(names),fid))
    return fid

def list_all(limit=100):
    _db()
    return db.rows('select id,uid,email,text,page,ver,imgs,status,t from feedback order by (status="new") desc, t desc limit ?',(limit,))

def mark_done(fid,done=True):
    _db(); db.run('update feedback set status=? where id=?',('done' if done else 'new',int(fid)))

def image_path(fid,name):
    if not re.fullmatch(r'[1-3]\.(png|jpg|gif|webp)',name): return None
    p=_dir(str(int(fid)),name)
    return p if os.path.exists(p) else None

def count_new():
    _db(); return db.one('select count(*) from feedback where status="new"')[0]
