"""日志：每行一条 JSON，写到标准输出（systemd 会收进 journalctl），同时落盘、按天轮转、保留 30 天。

访问日志字段：t(时间) rid(请求编号) m(方法) p(路径，不含查询串) s(状态码) ms(耗时毫秒) u(账号 id，没登录为空) d(设备号前 4 位) ip(地址，抹去末段)
错误日志字段：t level msg rid（带请求编号，能和访问日志对上）
不记：请求内容、查询串、Cookie、邮箱、书的正文、提问内容。

文件位置：FUBI_LOG_DIR（默认 <数据目录>_logs），文件名 fubi-YYYY-MM-DD.log；保留天数 FUBI_LOG_KEEP_DAYS（默认 30）。
查看：  tail -f /var/log/fubi/fubi-$(date +%F).log      查某个请求： grep 请求编号 /var/log/fubi/*.log
"""
import os,sys,json,time,threading,secrets,re
import config

_lock=threading.Lock(); _cur={'day':'','f':None}
def log_dir(): return os.environ.get('FUBI_LOG_DIR') or config.DATA.rstrip('/')+'_logs'
def keep_days():
    try: return max(1,int(os.environ.get('FUBI_LOG_KEEP_DAYS','30')))
    except ValueError: return 30

def new_rid(): return secrets.token_hex(4)

def mask_ip(ip):
    """抹去末段：1.2.3.4 → 1.2.3.0；IPv6 保留前三组"""
    ip=str(ip or '')
    if ':' in ip: return ':'.join(ip.split(':')[:3])+'::'
    p=ip.split('.')
    return '.'.join(p[:3]+['0']) if len(p)==4 else ''

def safe_path(path):
    """只留路径，去掉查询串；路径里长串的数字/字母（书号、反馈号）原样保留，因为它们不是个人信息"""
    return str(path or '').split('?',1)[0][:200]

def _open(day):
    d=log_dir(); os.makedirs(d,exist_ok=True)
    return open(os.path.join(d,'fubi-%s.log'%day),'a',encoding='utf-8')

def _prune():
    d=log_dir(); cut=time.time()-keep_days()*86400
    try: names=os.listdir(d)
    except OSError: return
    for n in names:
        if re.fullmatch(r'fubi-\d{4}-\d\d-\d\d\.log',n):
            p=os.path.join(d,n)
            try:
                if os.path.getmtime(p)<cut: os.remove(p)
            except OSError: pass

def write(rec):
    """写一行：标准输出一份，文件一份。写文件失败不影响服务"""
    rec=dict(rec); rec.setdefault('t',time.strftime('%Y-%m-%dT%H:%M:%S%z'))
    line=json.dumps(rec,ensure_ascii=False,separators=(',',':'))
    if os.environ.get('FUBI_QUIET')!='1':
        try: sys.stderr.write(line+'\n')
        except Exception: pass
    if os.environ.get('FUBI_LOG_FILE','1')=='0': return
    day=time.strftime('%Y-%m-%d')
    with _lock:
        try:
            if _cur['day']!=day:
                if _cur['f']:
                    try: _cur['f'].close()
                    except OSError: pass
                _cur['f']=_open(day); _cur['day']=day; _prune()
            _cur['f'].write(line+'\n'); _cur['f'].flush()
        except OSError: pass

def access(rid,method,path,status,ms,uid=None,dev='',ip=''):
    write({'rid':rid,'m':method,'p':safe_path(path),'s':status,'ms':ms,'u':uid or '','d':str(dev)[:4],'ip':mask_ip(ip)})

def error(msg,rid=''):
    write({'level':'error','rid':rid,'msg':str(msg)[:2000]})

def warn(msg,rid=''):
    """值得留底、但不是我们出了问题的事（对方发来畸形请求等）。监控不数它"""
    write({'level':'warn','rid':rid,'msg':str(msg)[:2000]})

def close_for_tests():
    with _lock:
        if _cur['f']:
            try: _cur['f'].close()
            except OSError: pass
        _cur['f']=None; _cur['day']=''

def recent_errors(minutes=10):
    """最近 N 分钟的 5xx 数量（今天的日志文件里数）。给监控用"""
    p=os.path.join(log_dir(),'fubi-%s.log'%time.strftime('%Y-%m-%d'))
    if not os.path.exists(p): return 0
    cut=time.time()-minutes*60; n=0
    try:
        with open(p,'rb') as f:
            f.seek(0,2); size=f.tell(); start=max(0,size-2*1024*1024); f.seek(start)   # 只看末尾 2 MB，够 10 分钟用
            lines=f.read().decode('utf-8','ignore').splitlines()
            if start>0: lines=lines[1:]   # 从文件中间读起时，第一行可能只有半截，丢掉；从头读就是完整的，不能丢
            for raw in lines:
                try: r=json.loads(raw)
                except ValueError: continue
                if r.get('s',0)>=500 or r.get('level')=='error':
                    try: ts=time.mktime(time.strptime(r['t'][:19],'%Y-%m-%dT%H:%M:%S'))
                    except Exception: continue
                    if ts>=cut: n+=1
    except OSError: return 0
    return n
