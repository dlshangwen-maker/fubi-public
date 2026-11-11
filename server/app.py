"""接口服务：只用 Python 标准库（不装任何第三方包也能跑；部署时前面放 nginx/Caddy 做 HTTPS）。

启动：  python3 server/app.py            （默认 http://0.0.0.0:8080 ，配置见 config.py）
页面：  /             阅读器（就是 Demo/模板.html；精编书 + 这台设备导入的书 + 这台设备的阅读记录，一次给全）
        /admin  后台（仅管理员账号登录后可见）：模型能不能用、今天调用了多少、生成队列、失败的任务（可重试）
接口（JSON）：
  GET    /api/health                 服务、数据库、模型、队列是否正常（部署后先看这个）
  GET    /api/shelf                  书架：精编书 + 我导入的书（带生成进度）
  GET    /api/books/<id>             一本书的全部数据（阅读器格式）
  GET    /api/books/<id>/status      导入/生成进度
  POST   /api/import                 导入：请求体 = 文件内容；文件名放在请求头 X-Filename（URL 编码）
  DELETE /api/books/<id>             从书架删掉我导入的书
  GET    /api/state   PUT /api/state 阅读记录（划线、想法、进度……）按设备存在服务器上；账号以后接上时把设备号换成用户
  POST   /api/event                  使用情况上报（要登录；白名单事件，见 usage.py）
  GET    /api/policy/terms|privacy    用户协议、隐私政策正文（公开）
  POST   /api/feedback/image         反馈：上传一张图片（请求体 = 图片内容），返回临时编号
  POST   /api/feedback               反馈：{"text":…,"page":…,"images":[临时编号…]}（要登录；后台 /admin 里看）
  POST   /api/ask                    自由提问（实时调模型；没配真模型时假模型回一句占位）
  GET    /api/search?q=              找书：精编书 + 古登堡 + 维基文库的搜索结果（我们不存书）
  GET    /api/hot                    热门搜索
  POST   /api/preview                预览：{"sources":[{"来源":…,"编号":…},…]} → 书名、作者、章数、字数、目录、开头几段
  POST   /api/download               下载到书架：{"sources":[…],"title":…,"author":…}（几个来源按顺序试；旧写法 source/ref 也认）→ 和导入一样处理
设备号：第一次打开时服务器发一个随机号（cookie fubi_dev，存一年）。
"""
import os,sys,json,time,re,gzip,secrets,threading,urllib.parse,html,traceback
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import config,db,books,pipeline,model,importer,search,ratelimit,accounts,feedback,logs,policy,usage

VERSION=config.VERSION
ADMIN_FAVICON='''<link rel="icon" type="image/svg+xml" href="data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 40 40%22%3E%3Crect width=%2240%22 height=%2240%22 rx=%229%22 fill=%22%231E2622%22/%3E%3Cg transform=%22translate(20 21) scale(1.28) translate(-20 -20)%22%3E%3Crect x=%2218.2%22 y=%222.5%22 width=%223.6%22 height=%2212%22 rx=%221.3%22 fill=%22%23ECEEE7%22/%3E%3Crect x=%2216.8%22 y=%2212.6%22 width=%226.4%22 height=%222.8%22 rx=%221%22 fill=%22%23ECEEE7%22/%3E%3Cpath d=%22M17.4 15.6H22.6Q26.4 21.5 24.8 28Q23 34 20 38Q17 34 15.2 28Q13.6 21.5 17.4 15.6Z%22 fill=%22%23B23A2E%22/%3E%3C/g%3E%3C/svg%3E">'''   # 后台标签页图标：阅读器标志的反色版（深底），和阅读器的标签页一眼能分开
STATE_MAX=5*1024*1024          # 一台设备的阅读记录最多 5MB
_tpl=None
def template():
    global _tpl
    if _tpl is None or os.environ.get('FUBI_DEV')=='1':
        _tpl=open(config.TEMPLATE,encoding='utf-8').read()
    return _tpl
_builtin_js=None
def builtin_js():
    """精编书的数据（几 MB）只序列化一次"""
    global _builtin_js
    if _builtin_js is None:
        _builtin_js={k:json.dumps(v,ensure_ascii=False) for k,v in books.builtin_data().items()}
    return _builtin_js

def payload(bid):
    """读者自己的书（导入的、找书下载的）给阅读器的数据 = 打包数据 + meta（书名、封面、来源、生成进度……书架和详情页用）"""
    b=books.get(bid)
    if not b or b['kind']=='builtin' or b['status'] in ('parsing','failed'): return None
    d=books.data(bid)
    if not d: return None
    m=b['meta']
    return dict(d,meta={'cover':f"/api/books/{bid}/cover" if m.get('cover') else '','title':b['title'],'author':b['author'],'nat':b['nat'],'kind':b['kind'],
        'chars':b['chars'],'chapters':b['chapters'],'gen':pipeline.progress(bid),'genst':pipeline.status(bid),'src':b['src'],'from':m.get('来源',''),'link':m.get('链接',''),'foreign':bool(m.get('需翻译')),'lang':m.get('语言','zh')})

def page(device,user=None):
    """阅读器页面：精编书 + 我导入的（已经能读的）书 + 服务器上存的阅读记录"""
    parts=[f'"{k}":{v}' for k,v in builtin_js().items()]
    for b in books.shelf(device):
        if b['kind']=='builtin': continue
        d=payload(b['id'])
        if d: parts.append(json.dumps(b['id'])+':'+json.dumps(d,ensure_ascii=False))
    data='{"books":{'+','.join(parts)+'}}'
    state={r[0]:json.loads(r[1]) for r in db.all('select book,state from progress where device=?',(device,))}
    boot={'server':True,'auth':config.AUTH,'user':accounts.public(user),'policy':policy.POLICY_VERSION,'version':VERSION,'model':config.MODEL['provider']!='mock','state':state,'formats':importer.supported(),'maxMB':config.MAX_UPLOAD//1024//1024,
          'pending':[{'id':b['id'],'title':b['title'],'status':b['status'],'err':b.get('err','')} for b in books.shelf(device) if b['kind']=='import' and b['status'] in ('parsing','failed')]}
    t=template().replace('%%DATA%%',data.replace('</','<\\/'))
    return t.replace('<script id="data"','<script>window.FUBI='+json.dumps(boot,ensure_ascii=False).replace('</','<\\/')+'</script>\n<script id="data"',1)

# ---------------- 后台页面 ----------------
def usage_html():
    e=html.escape; t=usage.totals()
    if not t['events']: return '<p>暂无记录。读者开始使用后，这里会显示近 14 天的活跃人数、读书分钟、点开伏笔次数、次日回访和每本书的读者数。</p>'
    rows=''.join(f"<tr><td>{d['day'][5:]}</td><td>{d['active']}</td><td>{d['minutes']}</td><td>{d['clues']}</td></tr>" for d in reversed(usage.daily(14)))
    tot,back=usage.retention(); ret=f"{back} / {tot}（{round(back*100/tot)}%）" if tot else '数据不足（需要有人隔天再来）'
    names={b[0]:b[1] for b in books.BUILTIN_SHELF}   # BUILTIN_SHELF 每项是 (编号, 书名, 作者, 国籍)：书名是第 2 项，第 3 项是作者
    names.update({r[0]:r[1] for r in db.all("select id,title from books where kind!='builtin'")})   # 读者导入/下载的书也显示书名，不显示编号
    bk=''.join(f"<tr><td>{e(names.get(x['book'],x['book']))}</td><td>{x['readers']}</td><td>{x['avg_far']}%</td><td>{x['minutes']}</td></tr>" for x in usage.per_book()) or '<tr><td colspan=4>暂无</td></tr>'
    qd=usage.quiz_dist(); qz=' · '.join(f"{e(q)}：{'，'.join(f'{e(a)} {n}' for a,n in sorted(v.items()))}" for q,v in sorted(qd.items())) or '暂无'
    return f'''<p>共 {t['users']} 位读者有记录。次日回访：{ret}。</p>
<table><tr><th>日期</th><th>活跃人数</th><th>读书分钟</th><th>点开伏笔</th></tr>{rows}</table>
<table><tr><th>书</th><th>读者数</th><th>平均读到</th><th>总分钟</th></tr>{bk}</table>
<p>问卷：{qz}</p><p><small>只记行为，不记书的正文、提问和笔记的内容；注销账号时一并删除。</small></p>'''
def feedback_html():
    L=feedback.list_all()
    if not L: return '<p>暂无反馈。</p>'
    e=html.escape; out=[]
    for f in L:
        try: imgs=json.loads(f['imgs'] or '[]')
        except ValueError: imgs=[]
        pics=''.join(f'<a href="/admin/feedback/{f["id"]}/{e(n)}" target=_blank><img src="/admin/feedback/{f["id"]}/{e(n)}" style="height:72px;margin:4px 6px 0 0;border:1px solid #ddd"></a>' for n in imgs)
        act='done">标记已处理' if f['status']=='new' else 'reopen">重新打开'
        meta=f"{time.strftime('%m-%d %H:%M',time.localtime(f['t']))} · {e(f['email'])} · {e(feedback.PAGES.get(f['page'],'其他'))} · v{e(f['ver'])}"
        out.append(f'<div style="border-top:1px solid #ddd;padding:8px 0;{"opacity:.55" if f["status"]!="new" else ""}"><small>{meta}</small><div style="white-space:pre-wrap">{e(f["text"])}</div>{pics}<form method=post action="/admin/feedback/{f["id"]}/{act}</button></form></div>')
    return ''.join(out)
def monitor_line():
    import monitor; st=monitor.load()
    if not st.get('last'): return '<b>还没有巡检记录</b>（每 2 分钟自动巡检一次；部署后几分钟内应出现）'
    age=(time.time()-st['last'])/60; stale=age>10
    when=time.strftime('%m-%d %H:%M',time.localtime(st['last']))
    if stale: return f'<span class="bad">最近一次巡检是 {when}（{age:.0f} 分钟前），巡检可能已停止</span>。检查：systemctl status fubi-monitor.timer'
    iss=st.get('issues',{})
    if not iss: return f'<span class="ok">正常</span>　最近一次巡检 {when}'
    L=monitor.LABEL; return '<span class="bad">有异常</span>：'+'；'.join(html.escape(L.get(k,k)+'：'+v['msg']) for k,v in iss.items())+f'　（巡检 {when}）'
def backup_line():
    import backup as bk
    try: L=bk.latest()
    except OSError: L=None
    if not L: return '<b>还没有备份</b>（每天 03:30 自动备份；也可以在服务器上运行 python3 server/backup.py backup）'
    age=(time.time()-L[1])/3600; cls='' if age<30 else ' class=bad'
    return f'<span{cls}>最近一次备份：{time.strftime("%Y-%m-%d %H:%M",time.localtime(L[1]))}（{age:.0f} 小时前）</span>　现有 {len(bk.list_backups())} 份，保留最近 {bk.keep_n()} 份。'
def admin_page():
    h=model.health() if 'check' in _q.get() else {'msg':'（点击“检查模型”后才会发起一次真实请求）','ok':None,'provider':config.MODEL['provider'],'model':config.MODEL['name']}
    day=time.strftime('%Y-%m-%d')
    calls=db.rows("select task,count(*) n,sum(ok) ok,sum(chars_in) cin,sum(chars_out) cout,avg(ms) ms from model_calls where day=? group by task",(day,))
    q={s:n for s,n in db.all("select status,count(*) from jobs group by status")}
    failed=db.rows("select j.id,j.book,b.title,j.step,j.unit,j.tries,j.err from jobs j left join books b on b.id=j.book where j.status='failed' order by j.id desc limit 50")
    bks=db.rows("select id,title,kind,status,chars,chapters,owner from books where kind!='builtin' order by t desc limit 50")
    e=html.escape
    row=lambda cells:'<tr>'+''.join(f'<td>{e(str(c))}</td>' for c in cells)+'</tr>'
    # ---- 各页签的内容（先各自拼好，最后放进页面）----
    mail_cfg=('发件账号 <b>'+e(str(config.SMTP['user']))+'</b> · 服务器 '+e(str(config.SMTP['host']))+':'+e(str(config.SMTP['port']))) if (config.SMTP['host'] and config.SMTP['user'] and config.SMTP['password']) else '<b>邮件未配置</b>（需设置 FUBI_SMTP_HOST / FUBI_SMTP_USER / FUBI_SMTP_PASS）'
    mailres=_q.get().get('mailres','')
    nfb=feedback.count_new(); failed_n=len(failed)
    tot=usage.totals(); n_users=db.one('select count(*) from users')[0]; n_inv=db.one('select count(*) from invites where used_by is null')[0]
    overview=f'''<div class=cards>
<div class=card><small>读者账号</small><b>{n_users}</b></div>
<div class=card><small>未使用的邀请码</small><b>{n_inv}</b></div>
<div class="card{' warn' if nfb else ''}"><small>未处理反馈</small><b>{nfb}</b></div>
<div class="card{' warn' if failed_n else ''}"><small>失败的任务</small><b>{failed_n}</b></div></div>
<h2>运行状态</h2><p>监控：{monitor_line()}</p><p>备份：{backup_line()}</p>
<h2>模型</h2><p><b>{e(model.describe()['line'])}</b> ·
<span class="{'ok' if h.get('ok') else 'bad' if h.get('ok') is False else ''}">{e(h.get('msg',''))}</span>
<form method=get action="/admin#overview" style="display:inline"><input type=hidden name=check value=1><button>检查模型</button></form></p>
<p>今日（{day}）调用上限 {config.MODEL['daily_calls']} 次；单本书调用上限 {config.MODEL['book_calls']} 次。</p>
<table><tr><th>任务</th><th>次数</th><th>成功</th><th>输入字数</th><th>输出字数</th><th>平均耗时</th></tr>{''.join(row([c['task'],c['n'],c['ok'],c['cin'],c['cout'],f"{(c['ms'] or 0)/1000:.1f}s"]) for c in calls) or '<tr><td colspan=6>今日暂无调用</td></tr>'}</table>
<h2>邮件</h2><p>{mail_cfg}</p>
{('<p><b>'+e(mailres)+'</b></p>') if mailres else ''}<form method=post action="/admin/testmail"><input name=to type=email placeholder="收件邮箱" size=24> <button>发送测试邮件</button></form>'''
    usage_tab=usage_html()
    feedback_tab=feedback_html()
    invites=f'''<p>每个邀请码仅可注册一个账号，使用后即失效。{'账号功能已开启' if config.AUTH else '<b>账号功能未开启</b>（需设置 FUBI_AUTH=1）'}。</p>
<form method=post action="/admin/invite"><input name=note placeholder="备注（发放对象）" size=14> <input name=n value=1 size=2> 个 <button>生成邀请码</button></form>
<table><tr><th>邀请码</th><th>备注</th><th>状态</th></tr>{''.join(row([accounts.fmt_code(i['code']),i['note'],('已被 '+str(i['email'])+' 使用') if i['used_by'] else '未使用']) for i in db.rows('select i.code,i.note,i.used_by,u.email from invites i left join users u on u.id=i.used_by order by i.t desc limit 50')) or '<tr><td colspan=3>暂无</td></tr>'}</table>'''
    booktab=f'''<p>生成队列：{' · '.join(f'{k} {v}' for k,v in q.items()) or '无'}　自动生成：{'开启' if pipeline.generation_on() else '关闭（使用模拟模型时不自动生成）'}</p>
<h3>失败的任务</h3><form method=post action="/admin/retry"><button>全部重试</button></form>
<table><tr><th>书</th><th>步骤</th><th>次数</th><th>原因</th></tr>{''.join(row([f['title'] or f['book'],f['step']+' '+f['unit'],f['tries'],f['err'][:300]]) for f in failed) or '<tr><td colspan=4>无</td></tr>'}</table>
<h3>导入的书</h3><table><tr><th>书</th><th>类型</th><th>状态</th><th>字数</th><th>章</th><th>生成进度</th></tr>{''.join(row([b['title'],b['kind'],b['status'],b['chars'],b['chapters'],'{done}/{total}'.format(**pipeline.progress(b['id']))]) for b in bks) or '<tr><td colspan=6>无</td></tr>'}</table>'''
    TABS=[('overview','概览',overview,''),('usage','使用情况',usage_tab,''),('feedback','反馈',feedback_tab,str(nfb) if nfb else ''),('invites','邀请码',invites,''),('books','书籍与生成',booktab,str(failed_n) if failed_n else '')]
    nav=''.join(f'<a href="#{k}" data-t="{k}">{t}{f"<i>{b}</i>" if b else ""}</a>' for k,t,_,b in TABS)
    body=''.join(f'<section id="{k}" data-t="{k}"><h2>{t}</h2>{c}</section>' if k!='overview' else f'<section id="{k}" data-t="{k}">{c}</section>' for k,t,c,_ in TABS)
    return f'''<!doctype html><meta charset=utf-8><meta name=viewport content="width=device-width">{ADMIN_FAVICON}<title>伏笔 · 后台</title>
<style>body{{font:14px/1.6 system-ui,sans-serif;max-width:960px;margin:24px auto;padding:0 16px;color:#222}}table{{border-collapse:collapse;width:100%;margin:8px 0 24px}}td,th{{border-bottom:1px solid #ddd;padding:4px 8px;text-align:left;vertical-align:top}}.ok{{color:#2a7}}.bad{{color:#c33}}button{{font:inherit;padding:4px 12px}}small{{color:#888}}
h1{{margin:0 0 12px}}nav.tabs{{display:flex;gap:4px;border-bottom:1px solid #ddd;margin:0 0 16px;position:sticky;top:0;background:#fff;z-index:2;overflow-x:auto}}
nav.tabs a{{padding:8px 14px;color:#555;text-decoration:none;border-bottom:2px solid transparent;margin-bottom:-1px;white-space:nowrap}}nav.tabs a.on{{color:#111;border-bottom-color:#111;font-weight:600}}nav.tabs a:hover{{color:#111}}
nav.tabs i{{font-style:normal;background:#c33;color:#fff;border-radius:9px;font-size:11px;padding:0 6px;margin-left:6px}}
.cards{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:0 0 8px}}.card{{border:1px solid #ddd;border-radius:6px;padding:10px 14px}}.card b{{display:block;font-size:24px;font-weight:600}}.card.warn{{border-color:#c33}}.card.warn b{{color:#c33}}
@media (max-width:640px){{.cards{{grid-template-columns:repeat(2,1fr)}}}}
section h2{{margin:8px 0 12px}}</style>
<h1>伏笔 · 后台 <small>v{VERSION}</small></h1>
<nav class=tabs>{nav}</nav>
{body}
<script>/* 页签：用网址里的 # 记住当前页；没有脚本时整页依次显示，也能用 */
(function(){{var T=[].map.call(document.querySelectorAll('nav.tabs a'),function(a){{return a.dataset.t}});
function show(){{var h=(location.hash||'#'+T[0]).slice(1); if(T.indexOf(h)<0) h=T[0];
document.querySelectorAll('section[data-t]').forEach(function(s){{s.hidden=s.dataset.t!==h}});
document.querySelectorAll('nav.tabs a').forEach(function(a){{a.classList.toggle('on',a.dataset.t===h)}}); window.scrollTo(0,0);}}
addEventListener('hashchange',show); show();}})();</script>'''

class _Q(threading.local):
    def get(self): return getattr(self,'q',{})
_q=_Q()

# ---------------- 请求处理 ----------------
class H(BaseHTTPRequestHandler):
    server_version='fubi/'+VERSION
    protocol_version='HTTP/1.1'
    def log_message(self,fmt,*a):
        pass   # 访问日志由 route() 统一记成 JSON（见 logs.py）；http.server 自带的那行含查询串和完整地址，不再输出
    def log_error(self,fmt,*a):
        # http.server 自己报的：畸形请求、不认识的协议版本、CONNECT 等——都是对方发来的垃圾（公网上的扫描程序常见），
        # 不是我们的错，记成警告；记成 error 会被监控当成"服务器错误"，天天误报
        logs.warn('HTTP 层：'+(fmt%a))
    # ---- 工具 ----
    def device(self):
        c=self.headers.get('Cookie','')
        m=re.search(r'(?:^|;\s*)fubi_dev=([A-Za-z0-9_-]{16,64})',c)
        if m: self._newdev=None; return m.group(1)
        self._newdev=secrets.token_urlsafe(18); return self._newdev
    def _drain(self):
        """请求带了内容却没被读（被 401、429 等提前拒绝）时，把它读掉；太大就关掉这条连接。
        否则同一条连接上的下一个请求会读到残留内容，得到一个看不懂的 400——这就是"注册第一次提示没成功、再点才成功"的原因"""
        if getattr(self,'_body_read',False) or getattr(self,'_drained',False): return
        self._drained=True
        try: n=int(self.headers.get('Content-Length') or 0)
        except ValueError: n=0
        if n<=0: return
        if n<=2*1024*1024: self.rfile.read(n)
        else: self.close_connection=True
    def send(self,code,body,ctype='application/json; charset=utf-8',extra=None):
        self._drain()
        if isinstance(body,(dict,list)): body=json.dumps(body,ensure_ascii=False)
        if isinstance(body,str): body=body.encode('utf-8')
        gz='gzip' in self.headers.get('Accept-Encoding','') and len(body)>2048 and not ctype.startswith('image/')
        if gz: body=gzip.compress(body,5)
        self._status=code; self.send_response(code)
        if getattr(self,'_rid',None): self.send_header('X-Request-Id',self._rid)
        self.send_header('Content-Type',ctype); self.send_header('Content-Length',str(len(body)))
        if gz: self.send_header('Content-Encoding','gzip')
        if 'Cache-Control' not in (extra or {}): self.send_header('Cache-Control','no-store')
        self.send_header('X-Content-Type-Options','nosniff')
        if getattr(self,'_newdev',None): self.send_header('Set-Cookie',f'fubi_dev={self._newdev}; Path=/; Max-Age=31536000; SameSite=Lax; HttpOnly')
        for k,v in (extra or {}).items(): self.send_header(k,v)
        try:
            self.end_headers()
            if self.command!='HEAD': self.wfile.write(body)
        except ConnectionError:
            # 对方在收到响应前断开了（扫描程序、读者关了页面、网络断了）：不是服务器的错。
            # 记成 499（没有响应可发，也不再重试写），否则会被当成 500 并触发监控告警
            self._status=499; self.close_connection=True
    def err(self,code,msg): self.send(code,{'error':msg})
    def body(self,limit):
        n=int(self.headers.get('Content-Length') or 0)
        if n>limit: raise ValueError(f'太大了（上限 {limit//1024//1024}MB）')
        self._body_read=True
        return self.rfile.read(n) if n else b''
    def admin_ok(self):
        """后台只认"已登录且邮箱在 FUBI_ADMIN_EMAILS 里"的账号；不再有口令。cookie 是 SameSite=Lax，别的网站发来的 POST 带不上登录状态"""
        return bool(self.user) and self.user['email'].lower() in config.ADMIN_EMAILS
    # ---- 账号 ----
    def auth(self,method,path,dev,ip):
        if not config.AUTH: return self.err(404,'账号功能未开启')
        if method!='POST': return self.err(405,'请求方式不正确')
        a=json.loads(self.body(70000) or b'{}'); cookie=self.headers.get('Cookie','')
        email=str(a.get('email','')).strip().lower()[:120]
        try:
            if path=='/api/auth/register':
                ratelimit.check('register','ip:'+ip)
                uid=accounts.register(email,a.get('password'),a.get('invite'),a.get('name',''),a.get('agree'))
                accounts.adopt_device(uid,self.device()); tok=accounts.new_session(uid)
                return self.send(200,{'ok':True},extra={'Set-Cookie':accounts.cookie_str(tok)})
            if path=='/api/auth/login':
                ratelimit.check('login','ip:'+ip); ratelimit.check('loginmail','mail:'+email)
                uid=accounts.login(email,a.get('password'),a.get('agree'))
                accounts.adopt_device(uid,self.device()); tok=accounts.new_session(uid)
                return self.send(200,{'ok':True},extra={'Set-Cookie':accounts.cookie_str(tok)})
            if path=='/api/auth/logout':
                accounts.logout(cookie); return self.send(200,{'ok':True},extra={'Set-Cookie':accounts.cookie_str('',clear=True)})
            if path=='/api/auth/forgot':
                ratelimit.check('forgot','ip:'+ip); ratelimit.check('forgot','mail:'+email)
                code=accounts.forgot(email)
                if code: accounts.deliver(email,*accounts.reset_mail(code))
                return self.send(200,{'ok':True,'msg':'验证码已发送，请前往邮箱查看，15 分钟内有效'})
            if path=='/api/auth/reset':
                ratelimit.check('reset','ip:'+ip); ratelimit.check('reset','mail:'+email)
                accounts.reset(email,a.get('code'),a.get('password')); return self.send(200,{'ok':True})
            if not self.user: return self.err(401,'请先登录')
            if path=='/api/auth/profile':
                accounts.update_profile(self.user['id'],a.get('name'),a.get('av')); return self.send(200,{'ok':True})
            if path=='/api/auth/password':
                accounts.change_password(self.user['id'],a.get('old'),a.get('new'),cookie); return self.send(200,{'ok':True})
            if path=='/api/auth/delete':
                accounts.delete_account(self.user['id'],a.get('password'))
                return self.send(200,{'ok':True},extra={'Set-Cookie':accounts.cookie_str('',clear=True)})
            return self.err(404,'地址不存在')
        except accounts.AuthError as e: return self.err(e.code,str(e))
    # ---- 路由 ----
    def do_HEAD(self): self.do_GET()
    def do_GET(self): self.route('GET')
    def do_POST(self): self.route('POST')
    def do_PUT(self): self.route('PUT')
    def do_DELETE(self): self.route('DELETE')
    def route(self,method):
        self._rid=logs.new_rid(); self._status=0; self.user=None; t0=time.time(); self._dev=''
        try: self._route(method)
        finally:
            try: logs.access(self._rid,method,self.path,self._status,int((time.time()-t0)*1000),(self.user or {}).get('id'),self._dev,ratelimit.client_ip(self.headers,self.client_address[0]))
            except Exception: pass
    def _route(self,method):
        u=urllib.parse.urlsplit(self.path); path=u.path; _q.q={k:v[0] for k,v in urllib.parse.parse_qs(u.query).items()}
        self._body_read=False; self._drained=False
        dev=self.device(); ip=ratelimit.client_ip(self.headers,self.client_address[0])
        self.user=accounts.user_from_cookie(self.headers.get('Cookie','')) if config.AUTH else None
        if self.user: dev='u%d'%self.user['id']   # 登录后，书和阅读记录都归账号；没登录是设备号
        self._dev=dev
        try:
            kind=None
            if path=='/api/ask': kind='ask'
            elif path in ('/api/search','/api/preview'): kind='search'
            elif path=='/api/download': kind='download'
            elif path=='/api/import': kind='import'
            if path not in ('/api/health','/api/state'):   # 健康检查和同步阅读记录不限（页面会频繁发）
                ratelimit.check('general',ip)
            if kind:
                ratelimit.check(kind,'ip:'+ip); ratelimit.check(kind,'dev:'+dev)
            if method=='GET' and path in ('/','/index.html'): return self.send(200,page(dev,self.user),'text/html; charset=utf-8')
            if path.startswith('/api/auth/'): return self.auth(method,path,dev,ip)
            if config.AUTH and not self.user and (path in ('/api/search','/api/preview','/api/download','/api/import','/api/ask') or (path=='/api/state' and method!='GET')):
                return self.err(401,'请先登录')   # 没登录只能看书架和精编书；不能提问、找书、导入，也不存阅读记录
            if method=='GET' and path=='/api/health': return self.send(200,health())
            if method=='GET' and path=='/api/shelf': return self.send(200,{'books':books.shelf(dev)})
            if method=='GET' and path=='/api/hot': return self.send(200,{'hot':search.hot()})
            if method=='GET' and path=='/api/search':
                q=_q.get().get('q','')
                r=search.search(q,dev); return self.send(200,dict(r,builtin=books.builtin_hits(q)))
            if method=='POST' and path=='/api/preview':
                req=json.loads(self.body(4096) or b'{}')
                srcs=[x for x in (req.get('sources') or []) if isinstance(x,dict)][:4]
                if not srcs: return self.err(400,'缺少来源')
                try:
                    for x in srcs: search.candidates(str(x.get('来源','')),str(x.get('编号','')))
                    return self.send(200,search.preview([{'来源':str(x['来源']),'编号':str(x['编号'])} for x in srcs]))
                except search.SearchError as e: return self.err(400,str(e))
                except importer.ImportError_ as e: return self.err(422,'该书籍文件无法解析：'+str(e))
                except OSError: return self.err(502,'来源网站暂时无法连接，请稍后重试')
            if method=='POST' and path=='/api/download':
                req=json.loads(self.body(4096) or b'{}')
                try: bid=books.download(dev,str(req.get('source','')),str(req.get('ref','')),str(req.get('title',''))[:80],str(req.get('author',''))[:60],sources=req.get('sources'))
                except search.SearchError as e: return self.err(400,str(e))
                except OSError: return self.err(502,'来源网站暂时无法连接，请稍后重试')
                return self.send(200,{'id':bid,'status':books.get(bid)['status']})
            m=re.fullmatch(r'/api/books/([A-Za-z0-9_-]{1,40})/cover',path)
            if m and method=='GET':
                b=books.visible(m.group(1),dev); p=pipeline.bdir(m.group(1),'cover.jpg') if b else ''
                if not b or not os.path.exists(p): return self.err(404,'暂无封面')
                return self.send(200,open(p,'rb').read(),'image/jpeg',extra={'Cache-Control':'private, max-age=86400'})
            m=re.fullmatch(r'/api/books/([A-Za-z0-9_-]{1,40})/chapters',path)
            if m and method=='POST':
                b=books.visible(m.group(1),dev)
                if not b: return self.err(404,'书籍不存在')
                if b['kind']!='import': return self.err(403,'精编书不可调整章节')
                if b['status'] in ('parsing','failed'): return self.err(409,'该书籍暂不可调整章节')
                import chapters
                ops=json.loads(self.body(65536) or b'{}').get('ops') or []
                try: idmap=chapters.apply(m.group(1),ops[:200])
                except chapters.EditError as e: return self.err(400,str(e))
                return self.send(200,dict(payload(m.group(1)),idmap=idmap))
            m=re.fullmatch(r'/api/books/([A-Za-z0-9_-]{1,40})(/status)?',path)
            if m:
                bid=m.group(1); b=books.visible(bid,dev)
                if not b: return self.err(404,'书籍不存在')
                if method=='DELETE': return self.send(200,{'ok':books.delete(bid,dev)}) if b['kind']=='import' else self.err(403,'精编书不可删除')
                if m.group(2): return self.send(200,{'id':bid,'status':b['status'],'title':b['title'],'err':b['meta'].get('err',''),'gen':pipeline.progress(bid),'genst':pipeline.status(bid),'chapters':b['chapters'],'chars':b['chars']})
                d=books.data(bid) if b['kind']=='builtin' else payload(bid)
                return self.send(200,d) if d else self.err(409,'该书籍正在导入' if b['status']=='parsing' else (b['meta'].get('err') or '该书籍导入失败'))
            if method=='POST' and path=='/api/import':
                name=urllib.parse.unquote(self.headers.get('X-Filename','') or 'book')
                data=self.body(config.MAX_UPLOAD)
                if not data: return self.err(400,'未收到文件')
                bid=books.import_file(data,name,dev,background=not os.environ.get('FUBI_SYNC_IMPORT'))
                return self.send(200,{'id':bid,'status':books.get(bid)['status']})
            if path=='/api/state':
                if method=='GET': return self.send(200,{r[0]:json.loads(r[1]) for r in db.all('select book,state from progress where device=?',(dev,))})
                if method in ('PUT','POST'):   # POST：页面关闭时 sendBeacon 只能发 POST
                    d=json.loads(self.body(STATE_MAX) or b'{}')
                    if not isinstance(d,dict): return self.err(400,'格式不正确')
                    for k,v in d.items():
                        if not re.fullmatch(r'rb_[A-Za-z0-9_]{1,60}',k): continue
                        if v is None: db.run('delete from progress where device=? and book=?',(dev,k)); continue
                        db.run('insert into progress(device,book,state,t) values(?,?,?,?) on conflict(device,book) do update set state=excluded.state,t=excluded.t',(dev,k,json.dumps(v,ensure_ascii=False),time.time()))
                    return self.send(200,{'ok':True})
            if path=='/api/event' and method=='POST':
                if not self.user: return self.err(401,'请先登录')
                ratelimit.check('event','u%d'%self.user['id'])
                a=json.loads(self.body(16384) or b'{}'); return self.send(200,{'ok':True,'n':usage.record(self.user['id'],a.get('events'))})
            m=re.fullmatch(r'/api/policy/(terms|privacy)',path)
            if m and method=='GET': return self.send(200,policy.get(m.group(1)))
            if path in ('/api/feedback','/api/feedback/image') and method=='POST':
                if not self.user: return self.err(401,'请先登录')
                try:
                    if path.endswith('/image'):
                        ratelimit.check('fbimage','u%d'%self.user['id'])
                        return self.send(200,{'id':feedback.save_temp(self.user['id'],self.body(feedback.MAX_IMAGE_BYTES+1024))})
                    ratelimit.check('feedback','u%d'%self.user['id'])
                    a=json.loads(self.body(16384) or b'{}')
                    fid=feedback.submit(self.user,a.get('text'),a.get('page'),VERSION,a.get('images') or [])
                    return self.send(200,{'ok':True,'id':fid})
                except feedback.FeedbackError as e: return self.err(e.code,str(e))
            if method=='POST' and path=='/api/ask': return self.send(200,ask(dev,json.loads(self.body(65536) or b'{}')))
            if path=='/admin' and method=='GET':
                if not self.admin_ok(): return self.send(403,'后台仅限管理员账号访问。请先在首页登录管理员账号，再打开本页。','text/plain; charset=utf-8')
                return self.send(200,admin_page(),'text/html; charset=utf-8')
            if path=='/admin/invite' and method=='POST':
                if not self.admin_ok(): return self.err(403,'无权限')
                f={k:v[0] for k,v in urllib.parse.parse_qs((self.body(4096) or b'').decode('utf-8','ignore')).items()}   # 表单体里的备注和个数
                try: n=int(f.get('n','1') or 1)
                except ValueError: n=1
                accounts.make_invites(n,f.get('note',''))
                return self.send(303,'',extra={'Location':'/admin#invites'})
            if path=='/admin/testmail' and method=='POST':
                if not self.admin_ok(): return self.err(403,'无权限')
                f={k:v[0] for k,v in urllib.parse.parse_qs((self.body(4096) or b'').decode('utf-8','ignore')).items()}
                try:
                    to=accounts.norm_email(f.get('to',''))
                    res='测试邮件已发送至 '+to if accounts.mailer(to,'【伏笔】测试邮件','这是一封测试邮件。如您收到此邮件，说明邮件发送配置正常。\n\n伏笔')is not False else '未发送：邮件未配置'
                except accounts.AuthError as e: res=str(e)
                except Exception as e: res='发送失败：%s %s'%(type(e).__name__,str(e)[:200])
                return self.send(303,'',extra={'Location':'/admin?mailres='+urllib.parse.quote(res)+'#overview'})
            m=re.fullmatch(r'/admin/feedback/(\d+)/([1-3]\.(?:png|jpg|gif|webp))',path)
            if m and method=='GET':
                if not self.admin_ok(): return self.err(403,'无权限')
                p=feedback.image_path(m.group(1),m.group(2))
                if not p: return self.err(404,'图片不存在')
                ct={'png':'image/png','jpg':'image/jpeg','gif':'image/gif','webp':'image/webp'}[p.rsplit('.',1)[1]]
                return self.send(200,open(p,'rb').read(),ct,extra={'Content-Disposition':'inline','Content-Security-Policy':"default-src 'none'; sandbox"})
            m=re.fullmatch(r'/admin/feedback/(\d+)/(done|reopen)',path)
            if m and method=='POST':
                if not self.admin_ok(): return self.err(403,'无权限')
                feedback.mark_done(m.group(1),m.group(2)=='done'); return self.send(303,'',extra={'Location':'/admin#feedback'})
            if path=='/admin/retry' and method=='POST':
                if not self.admin_ok(): return self.err(403,'无权限')
                pipeline.retry_failed(); return self.send(303,'',extra={'Location':'/admin#books'})
            return self.err(404,'地址不存在')
        except importer.ImportError_ as e: return self.err(400,str(e))
        except (ValueError,json.JSONDecodeError) as e: return self.err(400,str(e)[:200])
        except ratelimit.Limited as e: return self.send(429,{'error':str(e)},extra={'Retry-After':str(e.retry)})
        except model.QuotaExceeded as e: return self.err(429,str(e))
        except model.ModelError as e: return self.err(503,str(e)[:300])
        except Exception as e:
            logs.error('%s: %s\n%s'%(type(e).__name__,str(e)[:300],traceback.format_exc()[-1500:]),self._rid)
            return self.err(500,'服务器出现错误，请稍后重试（编号 %s）'%self._rid)

def health():
    t0=time.time(); ok=True
    try: db.one('select 1')
    except Exception: ok=False
    q={s:n for s,n in db.all("select status,count(*) from jobs group by status")}
    return {'ok':ok,'version':VERSION,'db_ms':int((time.time()-t0)*1000),'model':{'provider':config.MODEL['provider'],'name':config.MODEL['name'] or None,'configured':config.MODEL['provider']=='mock' or bool(config.MODEL['api_key'] and config.MODEL['name'])},
            'generation':pipeline.generation_on(),'queue':q,'builtin':len(books.BUILTIN_SHELF),'formats':importer.supported()}

def ask(dev,req):
    """自由提问：读者读到 pos（段号），问 q（可带划线的文字 hl）。只给模型读者读过的部分里相关的段落"""
    bid=str(req.get('book','')); q=str(req.get('q','')).strip()[:500]; pos=str(req.get('pos',''))
    b=books.visible(bid,dev)
    if not b or not q: raise ValueError('缺少书籍或问题')
    d=books.data(bid); props=d['props']; IX={p['n']:i for i,p in enumerate(props)}
    if pos not in IX: raise ValueError('阅读位置无效')
    upto=props[:IX[pos]+1]
    words=set(re.findall(r'[一-鿿]{2}|[A-Za-z]{4,}',q+(req.get('hl') or '')))
    scored=sorted(upto,key=lambda p:-sum(p['zh'].count(w) for w in words))[:12]
    near=upto[-6:]
    seen=[]; [seen.append(p) for p in sorted(scored+near,key=lambda p:IX[p['n']]) if p not in seen]
    text='\n'.join(f"{p['n']}　{p['zh'][:600]}" for p in seen)
    m=b['meta']; kind=m.get('类型','小说') if b['kind']!='builtin' else {'lhz':'非虚构','tractatus':'非虚构','nahan':'短篇集'}.get(bid,'小说')
    import tasks
    v={'书名':b['title'],'POS':pos,'规则':'见下面的【不剧透规则】','rule_text':tasks.RULE(kind),'划线说明':('（他划了这句：'+req['hl'][:300]+'）') if req.get('hl') else '',
       'text':text+'\n\n【读者的问题】\n'+q}
    out=model.call('ask',v,book=bid)
    if out.get('回收') and out['回收'] not in IX: out['回收']=''
    return out

# ---------------- 启动 ----------------
def make_server(host=None,port=None):
    books.sync_builtin(); pipeline.recover()
    books.builtin_data(); builtin_js()             # 启动时先把精编书算好，第一个读者不用等
    return ThreadingHTTPServer((host or config.HOST,port if port is not None else config.PORT),H)

def start_workers(n=None):
    stop=threading.Event()
    for _ in range(n or int(os.environ.get('FUBI_WORKERS','2'))): pipeline.Worker(stop).start()
    return stop

if __name__=='__main__':
    srv=make_server(); stop=start_workers()
    print(f'伏笔 v{VERSION} 已启动：http://{config.HOST}:{config.PORT}/   模型：{config.MODEL["provider"]} {config.MODEL["name"]}   数据：{config.DATA}',flush=True)
    try: srv.serve_forever()
    except KeyboardInterrupt: pass
    finally: stop.set(); srv.server_close()
