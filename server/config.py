"""配置：全部从环境变量读，没有就用默认值。部署时只改环境变量（或 .env 文件），不改代码。

FUBI_DATA         数据目录（数据库、上传的书、生成结果）。默认 <项目>/server_data
FUBI_HOST/PORT    监听地址。默认 0.0.0.0:8080
FUBI_ADMIN_EMAILS 管理员账号的邮箱（多个用逗号隔开）。只有登录了这些账号才能打开后台 /admin；不设就不开后台
FUBI_MAX_UPLOAD_MB 单个导入文件上限。默认 50

模型（见 模型.py）：
FUBI_MODEL_PROVIDER  mock（默认，假模型）/ openai（OpenAI 兼容接口：OpenAI、DeepSeek、通义、Kimi、智谱……）/ anthropic
FUBI_MODEL_BASE_URL  接口地址，如 https://api.deepseek.com
FUBI_MODEL_API_KEY   密钥
FUBI_MODEL_NAME      模型名，如 deepseek-flash
FUBI_MODEL_TIMEOUT   单次超时秒数。默认 300
FUBI_MODEL_MAX_TOKENS 单次回答的长度上限（token，含思考内容）。默认 32000；只按实际用量计费，设大不会多花钱
FUBI_MODEL_EFFORT    思考强度：low / high / max。只有思考模式开着时才有效（FUBI_MODEL_THINKING 不能是 disabled）
FUBI_MODEL_THINKING  思考模式开关：不填=厂商默认（DeepSeek 默认开，更贵更慢）；disabled=关；enabled=开
FUBI_MODEL_DAILY_CALLS  每天最多调用多少次（全站），超了就排队到第二天。默认 2000
FUBI_MODEL_BOOK_CALLS   一本书最多调用多少次。默认 400（约 100 万字）
"""
import os
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # Read Book 文件夹

def _load_env_file():
    p=os.environ.get('FUBI_ENV_FILE',os.path.join(ROOT,'server','.env'))
    if not os.path.exists(p): return
    for line in open(p,encoding='utf-8'):
        line=line.strip()
        if not line or line.startswith('#') or '=' not in line: continue
        k,v=line.split('=',1); os.environ.setdefault(k.strip(),v.strip().strip('"').strip("'"))
_load_env_file()

E=os.environ.get
def _version():
    try: return open(os.path.join(ROOT,'VERSION'),encoding='utf-8').read().strip() or 'unknown'
    except OSError: return 'unknown'
VERSION=_version()   # 全项目唯一的版本号：根目录 VERSION 文件
DATA=E('FUBI_DATA',os.path.join(ROOT,'server_data'))
HOST=E('FUBI_HOST','0.0.0.0'); PORT=int(E('FUBI_PORT','8080'))
ADMIN_EMAILS=frozenset(x.strip().lower() for x in E('FUBI_ADMIN_EMAILS','').split(',') if x.strip())   # 后台只认这些邮箱的已登录账号（需要 FUBI_AUTH=1）
MAX_UPLOAD=int(E('FUBI_MAX_UPLOAD_MB','50'))*1024*1024
AUTH=E('FUBI_AUTH','0')=='1'      # 开了：必须登录才能提问、导入、下载、找书；注册要邀请码（见 accounts.py）
SMTP={'host':E('FUBI_SMTP_HOST','smtp.163.com'),'port':int(E('FUBI_SMTP_PORT','465')),'user':E('FUBI_SMTP_USER',''),
      'password':E('FUBI_SMTP_PASS',''),'from':E('FUBI_SMTP_FROM','')}   # 163 邮箱：密码填授权码，不是登录密码
MODEL={
    'provider':E('FUBI_MODEL_PROVIDER','mock'),
    'base_url':E('FUBI_MODEL_BASE_URL',''),
    'api_key':E('FUBI_MODEL_API_KEY',''),
    'name':E('FUBI_MODEL_NAME',''),
    'timeout':int(E('FUBI_MODEL_TIMEOUT','300')),            # 不是流式输出：整段回答生成完才返回，长回答可能要一两分钟
    'max_tokens':int(E('FUBI_MODEL_MAX_TOKENS','32000')),
    'effort':E('FUBI_MODEL_EFFORT',''),                      # 思考强度 low/high/max，只在思考模式开着时有效；空=不发（厂商默认 high）
    'thinking':E('FUBI_MODEL_THINKING',''),                  # 空=不发这个参数（用厂商默认）；disabled=关闭思考模式；enabled=开启
    'daily_calls':int(E('FUBI_MODEL_DAILY_CALLS','2000')),
    'book_calls':int(E('FUBI_MODEL_BOOK_CALLS','400')),
}
# 精编书：项目里已经做好的五本，启动时作为"内置书"加载
TEMPLATE=os.path.join(ROOT,'Demo','模板.html')
PROMPTS=os.path.join(ROOT,'生成','流水线')
def path(*a):
    p=os.path.join(DATA,*a); os.makedirs(os.path.dirname(p),exist_ok=True); return p
