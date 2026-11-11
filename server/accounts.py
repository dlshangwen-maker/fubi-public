"""账号：邮箱 + 密码，邀请码注册，会话 cookie，邮箱验证码找回密码。
- 密码只存 scrypt 哈希（带随机盐），不存明文；会话令牌只存哈希，cookie 里的原文丢了就找不回（只能重新登录）。
- 注册必须有邀请码（管理员在后台生成，一码一人）。
- 找回密码：发 6 位验证码到邮箱，15 分钟有效，最多试 5 次；成功后所有已登录的设备都会退出。
- 不告诉陌生人"这个邮箱有没有注册过"（找回密码永远回"如果注册过就会收到"）。
- 数据归属：已登录 = 'u<账号id>'；没登录 = 设备号。注册时把这台设备上的书和阅读记录并入账号。
邮件：配了 FUBI_SMTP_* 就真发（163 邮箱：smtp.163.com:465，密码填"授权码"，不是登录密码）；没配时把邮件内容打在服务日志里（管理员能取，方便内部测试）。"""
import os,re,sys,time,json,hmac,hashlib,secrets,threading,smtplib,ssl
from email.message import EmailMessage
import config,db

SESSION_DAYS=30; COOKIE='fubi_sess'; RESET_MINUTES=15; RESET_TRIES=5
ALPHABET='23456789ABCDEFGHJKLMNPQRSTUVWXYZ'   # 去掉容易看错的 0O1I
_lock=threading.Lock()

class AuthError(Exception):
    def __init__(self,msg,code=400): super().__init__(msg); self.code=code

# ---------------- 密码 ----------------
def _hash(pw,salt=None):
    salt=salt or os.urandom(16)
    return 'scrypt$%s$%s'%(salt.hex(),hashlib.scrypt(pw.encode(),salt=salt,n=2**14,r=8,p=1,dklen=32).hex())
def _verify(pw,stored):
    try: _,s,h=stored.split('$'); c=hashlib.scrypt(pw.encode(),salt=bytes.fromhex(s),n=2**14,r=8,p=1,dklen=32)
    except Exception: return False
    return hmac.compare_digest(c.hex(),h)
_dummy_h=None
def _dummy():
    global _dummy_h
    if _dummy_h is None: _dummy_h=_hash('not-a-real-password-1')
    return _dummy_h   # 邮箱不存在时也算一遍哈希，免得从耗时看出邮箱有没有注册
def check_pw(pw):
    if not isinstance(pw,str) or not (8<=len(pw)<=64) or not re.search('[A-Za-z]',pw) or not re.search(r'\d',pw):
        raise AuthError('密码须为 8～64 位，且同时包含字母和数字')
def _sh(t): return hashlib.sha256(t.encode()).hexdigest()

# ---------------- 邮箱 ----------------
def norm_email(e,strict=True):
    e=str(e or '').strip().lower()
    if strict and (len(e)>120 or not re.fullmatch(r'[^@\s]{1,64}@[^@\s]{1,100}\.[^@\s.]{2,}',e)): raise AuthError('邮箱格式不正确')
    return e
def default_name(email): return '读者'+email.split('@')[0][-4:]

# ---------------- 注册 / 登录 ----------------
def _code(c): return re.sub(r'[^A-Z0-9]','',str(c or '').upper())
def need_agree(agree):
    """登录、注册都必须带上"同意的协议版本"，且必须是当前版本；否则要求重新同意"""
    import policy
    if str(agree or '')!=policy.POLICY_VERSION: raise AuthError('请先阅读并同意《用户协议》和《隐私政策》',428)
def register(email,pw,invite,name='',agree=None):
    need_agree(agree)
    email=norm_email(email); check_pw(pw); code=_code(invite)
    with _lock:
        inv=db.one('select used_by from invites where code=?',(code,))
        if not code or not inv or inv[0] is not None: raise AuthError('邀请码无效或已被使用')
        if db.one('select 1 from users where email=?',(email,)): raise AuthError('该邮箱已注册，请直接登录')
        name=str(name or '').strip()[:12] or default_name(email); now=time.time()
        uid=db.run('insert into users(email,name,pw,t,agreed_ver,agreed_t) values(?,?,?,?,?,?)',(email,name,_hash(pw),now,str(agree),now)).lastrowid
        db.run('update invites set used_by=?,used_t=? where code=?',(uid,now,code))
    return uid
def login(email,pw,agree=None):
    need_agree(agree)
    email=norm_email(email,strict=False)
    r=db.one('select id,pw from users where email=?',(email,))
    ok=_verify(str(pw or ''),r[1] if r else _dummy())
    if not r or not ok: raise AuthError('邮箱或密码错误',401)
    db.run('update users set last_login=?,agreed_ver=?,agreed_t=? where id=?',(time.time(),str(agree),time.time(),r[0])); return r[0]
def adopt_device(uid,dev):
    """把这台设备上的书和阅读记录并入账号"""
    who='u%d'%uid
    db.run("update books set owner=? where owner=? and kind='import'",(who,dev))
    db.run('insert or ignore into progress(device,book,state,t) select ?,book,state,t from progress where device=?',(who,dev))
    db.run('delete from progress where device=?',(dev,))
    db.run('update searches set device=? where device=?',(who,dev))   # 登录前的搜索词也归到账号下，注销时才删得干净

# ---------------- 会话 ----------------
def new_session(uid):
    tok=secrets.token_urlsafe(32); now=time.time()
    db.run('insert into sessions(h,uid,t,exp) values(?,?,?,?)',(_sh(tok),uid,now,now+SESSION_DAYS*86400))
    db.run('delete from sessions where exp<?',(now,)); return tok
def _tok(cookie):
    m=re.search(r'(?:^|;\s*)%s=([A-Za-z0-9_-]{20,80})'%COOKIE,cookie or ''); return m.group(1) if m else None
def user_from_cookie(cookie):
    tok=_tok(cookie)
    if not tok: return None
    r=db.one('select u.id,u.email,u.name,u.av,u.t,s.exp from sessions s join users u on u.id=s.uid where s.h=?',(_sh(tok),))
    if not r or r[5]<time.time(): return None
    try: av=json.loads(r[3] or '{}')
    except ValueError: av={}
    return {'id':r[0],'email':r[1],'name':r[2],'av':av,'t':r[4]}
def logout(cookie):
    tok=_tok(cookie)
    if tok: db.run('delete from sessions where h=?',(_sh(tok),))
def public(u): return {'email':u['email'],'name':u['name'],'av':u['av'],'t':u['t']} if u else None
def cookie_str(tok,clear=False):
    s='%s=%s; Path=/; Max-Age=%d; HttpOnly; SameSite=Lax'%(COOKIE,'' if clear else tok,0 if clear else SESSION_DAYS*86400)
    return s+('; Secure' if os.environ.get('FUBI_COOKIE_SECURE')=='1' else '')

# ---------------- 账号资料 ----------------
def update_profile(uid,name=None,av=None):
    if name is not None:
        name=str(name).strip()[:12]
        if not name: raise AuthError('昵称不能为空')
        db.run('update users set name=? where id=?',(name,uid))
    if av is not None:
        if not isinstance(av,dict): raise AuthError('头像格式不正确')
        av={k:str(av.get(k,''))[:70000] for k in ('ch','c','img') if av.get(k)}
        if av.get('img') and not av['img'].startswith('data:image/'): raise AuthError('头像图片格式不正确')
        s=json.dumps(av,ensure_ascii=False)
        if len(s)>70000: raise AuthError('头像图片过大')
        db.run('update users set av=? where id=?',(s,uid))
def change_password(uid,old,new,cookie=''):
    r=db.one('select pw from users where id=?',(uid,))
    if not r or not _verify(str(old or ''),r[0]): raise AuthError('当前密码错误',403)
    check_pw(new)
    db.run('update users set pw=? where id=?',(_hash(new),uid))
    keep=_tok(cookie); db.run('delete from sessions where uid=? and h!=?',(uid,_sh(keep) if keep else ''))   # 其他设备要重新登录
def delete_account(uid,pw):
    r=db.one('select pw from users where id=?',(uid,))
    if not r or not _verify(str(pw or ''),r[0]): raise AuthError('密码错误',403)
    import books
    who='u%d'%uid
    for (bid,) in db.all("select id from books where kind='import' and owner=?",(who,)): books.delete(bid,who)
    db.run('delete from progress where device=?',(who,)); db.run('delete from sessions where uid=?',(uid,))
    # 隐私政策承诺：注销后删除账号、阅读记录、导入的书、反馈、使用情况记录
    try:
        import feedback,shutil
        feedback._db()
        for (fid,) in db.all('select id from feedback where uid=?',(uid,)): shutil.rmtree(feedback._dir(str(fid)),ignore_errors=True)
        db.run('delete from feedback where uid=?',(uid,))
    except Exception: pass
    db.run('delete from events where uid=?',(uid,)); db.run('delete from searches where device=?',(who,))
    db.run('update invites set used_by=null where used_by=?',(uid,)) if False else None   # 邀请码用过就作废，不退还
    db.run('delete from users where id=?',(uid,))

# ---------------- 找回密码 ----------------
def forgot(email):
    """返回验证码（邮箱没注册过返回 None，对外都一样回复）"""
    email=norm_email(email,strict=False)
    if not db.one('select 1 from users where email=?',(email,)): return None
    code='%06d'%secrets.randbelow(10**6)
    db.run('insert into resets(email,h,exp,tries) values(?,?,?,0) on conflict(email) do update set h=excluded.h,exp=excluded.exp,tries=0',(email,_sh(code+email),time.time()+RESET_MINUTES*60))
    return code
def reset(email,code,pw):
    email=norm_email(email,strict=False); check_pw(pw); bad=AuthError('验证码错误或已过期，请重新获取')
    r=db.one('select h,exp,tries from resets where email=?',(email,))
    if not r or r[1]<time.time(): raise bad
    if r[2]>=RESET_TRIES: db.run('delete from resets where email=?',(email,)); raise AuthError('验证码尝试次数过多，请重新获取')
    if not hmac.compare_digest(r[0],_sh(str(code or '').strip()+email)):
        db.run('update resets set tries=tries+1 where email=?',(email,)); raise bad
    u=db.one('select id from users where email=?',(email,))
    if not u: raise bad
    db.run('update users set pw=? where id=?',(_hash(pw),u[0])); db.run('delete from sessions where uid=?',(u[0],)); db.run('delete from resets where email=?',(email,))
    return u[0]

# ---------------- 邀请码 ----------------
def make_invites(n=1,note=''):
    out=[]
    for _ in range(max(1,min(int(n),20))):
        c=''.join(secrets.choice(ALPHABET) for _ in range(8))
        db.run('insert into invites(code,note,t) values(?,?,?)',(c,str(note)[:40],time.time())); out.append(c)
    return out
def fmt_code(c): return c[:4]+'-'+c[4:]

# ---------------- 发邮件 ----------------
def send_mail(to,subject,body):
    c=config.SMTP
    if not (c['host'] and c['user'] and c['password']):
        sys.stderr.write('[邮件没配置，没有真发] 收件人 %s｜%s\n%s\n'%(to,subject,body)); return False
    m=EmailMessage(); m['Subject']=subject; m['From']=c['from'] or c['user']; m['To']=to; m.set_content(body)
    with smtplib.SMTP_SSL(c['host'],c['port'],context=ssl.create_default_context(),timeout=20) as s:
        s.login(c['user'],c['password']); s.send_message(m)
    return True
mailer=send_mail
def deliver(to,subject,body):
    """后台线程发，不让读者等；失败只写日志（不写密码）。测试里设 FUBI_SYNC_MAIL=1 同步发"""
    def run():
        try: mailer(to,subject,body)
        except Exception as e: sys.stderr.write('邮件发送失败：%s %s\n'%(type(e).__name__,str(e)[:120]))
    if os.environ.get('FUBI_SYNC_MAIL')=='1': run()
    else: threading.Thread(target=run,daemon=True).start()
def reset_mail(code):
    return ('【伏笔】重置密码',
            f'您好，\n\n您正在重置“伏笔”账号的登录密码。本次验证码为：{code}\n\n验证码 {RESET_MINUTES} 分钟内有效，最多可尝试 {RESET_TRIES} 次。\n\n如非本人操作，请忽略此邮件，您的账号不会发生任何变化。\n\n伏笔')
