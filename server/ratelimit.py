"""限流：按"客户端地址"和"设备"两个维度，各自在滑动窗口里数请求次数，超了就拒绝（429 + 中文提示）。
内存里实现，单进程够用（服务只跑一个进程）；重启后计数清零。

规则（可用环境变量调整，格式 次数/秒数，多条用逗号隔开）。11-02 用户："太松，再严一点"，所以默认值偏紧，试用时再按反馈放宽：
  ask      自由提问        FUBI_RL_ASK       默认 5/60 + 30/86400（每分钟 5 次、每天 30 次）
  search   找书、预览      FUBI_RL_SEARCH    默认 10/60 + 100/86400
  download 下载            FUBI_RL_DOWNLOAD  默认 3/3600（每小时 3 本）
  import   导入文件        FUBI_RL_IMPORT    默认 3/3600
  general  其他所有接口    FUBI_RL_GENERAL   默认 300/60（正常阅读远低于这个数，只防脚本刷）
  login    登录（按地址）  FUBI_RL_LOGIN     默认 10/600；登录（按邮箱）FUBI_RL_LOGINMAIL 默认 5/600
  register 注册            FUBI_RL_REGISTER  默认 5/3600
  forgot   找回密码发码    FUBI_RL_FORGOT    默认 3/3600（按邮箱、按地址各算）
  reset    用验证码改密码  FUBI_RL_RESET      默认 10/3600
客户端地址：服务前面如果有反向代理（Caddy 等），要设 FUBI_TRUST_PROXY=1，才会读 X-Forwarded-For；直接对外时不信这个头（否则可伪造）。
"""
import os,time,threading,collections
LOCK=threading.Lock(); HITS=collections.defaultdict(collections.deque)
DEFAULTS={'ask':'5/60,30/86400','search':'10/60,100/86400','download':'3/3600','import':'3/3600','general':'300/60',
          'login':'10/600','loginmail':'5/600','register':'5/3600','forgot':'3/3600','reset':'10/3600',
          'feedback':'5/3600,20/86400','fbimage':'15/3600','event':'30/60'}
NAMES={'ask':'提问','search':'搜索','download':'下载','import':'导入','general':'操作','login':'登录','loginmail':'登录','register':'注册','forgot':'找回密码','reset':'改密码','feedback':'提交反馈','fbimage':'上传图片','event':'使用记录上报'}
def _per(w): return {60:'每分钟',600:'每 10 分钟',3600:'每小时',86400:'每天'}.get(w,f'每 {w} 秒')
def _wait(sec): return f'{sec} 秒' if sec<90 else f'{(sec+59)//60} 分钟' if sec<5400 else f'{(sec+3599)//3600} 小时'
def message(kind,n,w,retry):
    """写清楚：哪类操作、要等多久、上限是多少；用书面语"""
    if w>=86400: return f'今日{NAMES[kind]}次数已达上限（{_per(w)}最多 {n} 次），请明日再试'
    return f'{NAMES[kind]}请求过于频繁，请 {_wait(retry)}后重试（{_per(w)}最多 {n} 次）'
class Limited(Exception):
    def __init__(self,msg,retry): super().__init__(msg); self.retry=retry
def rules(kind):
    spec=os.environ.get('FUBI_RL_'+kind.upper(),DEFAULTS[kind])
    return [(int(a),int(b)) for a,b in (x.split('/') for x in spec.split(',') if x.strip())]
def check(kind,who,now=None):
    """who：用来区分的字符串（地址或设备号）。超限抛 Limited，没超限就记一次。"""
    now=now if now is not None else time.time(); rs=rules(kind)
    with LOCK:
        qs=[HITS[(kind,who,w)] for _,w in rs]
        for (n,w),q in zip(rs,qs):
            while q and q[0]<=now-w: q.popleft()
            if len(q)>=n:
                retry=max(1,int(q[0]+w-now)+1); raise Limited(message(kind,n,w,retry),retry)
        for q in qs: q.append(now)
        if len(HITS)>20000:   # 防止内存无限长：清掉空的队列
            for k in [k for k,v in HITS.items() if not v]: HITS.pop(k,None)
def reset(): 
    with LOCK: HITS.clear()
def client_ip(headers,peer):
    if os.environ.get('FUBI_TRUST_PROXY')=='1':
        x=(headers.get('X-Forwarded-For') or '').split(',')[0].strip()
        if x: return x
    return peer
