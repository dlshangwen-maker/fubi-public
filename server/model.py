"""模型调用层：全站所有用到大模型的地方，都只走这里的 call()。

    call(任务名, 变量, book=书id) -> dict（已按任务的输出格式校验过）

- 任务名对应 tasks.py 里登记的一项：用哪份提示词、怎么填变量、输出要满足什么格式。
- 提供方由配置决定（config.MODEL['provider']）：
    mock       假模型：从已经生成好的数据里取（五本精编书），或按格式给一份占位结果。没有 API 也能把整条线跑通。
    openai     OpenAI 兼容接口（/chat/completions）：OpenAI、DeepSeek、通义千问、Kimi、智谱、硅基流动……填地址、密钥、模型名就能用。
    anthropic  Anthropic 接口（/v1/messages）。
  换模型、换厂商：只改环境变量，不改任何业务代码。
- 每次调用都记账（model_calls 表）：任务、书、提供方、模型、耗时、输入输出字数、成败。全站每天、每本书都有上限，超了抛 QuotaExceeded，
  生成服务会把任务留到之后再跑，不会丢。
- 输出不是合法 JSON、或缺了要的字段 → 自动把错误告诉模型重试一次；还不行抛 BadOutput。
"""
import os,json,re,time,urllib.request,urllib.error,ssl
import config,db

class ModelError(Exception): pass
class QuotaExceeded(ModelError): pass
class BadOutput(ModelError): pass
class Transient(ModelError): pass   # 限流和服务端临时错误：可以稍后重试
class TruncatedOutput(ModelError): pass   # 回答被输出上限截断：重试同样的请求没有用，要拆小任务或调大 FUBI_MODEL_MAX_TOKENS

# ---------------- 提供方 ----------------
def _post(url,headers,body,timeout):
    req=urllib.request.Request(url,data=json.dumps(body).encode('utf-8'),headers={'Content-Type':'application/json',**headers},method='POST')
    try:
        with urllib.request.urlopen(req,timeout=timeout,context=ssl.create_default_context()) as r: return json.loads(r.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        msg=e.read().decode('utf-8','replace')[:500]
        if e.code in (429,500,502,503,504): raise Transient(f'模型服务暂时不可用（{e.code}）：{msg}')
        raise ModelError(f'模型接口报错（{e.code}）：{msg}')
    except urllib.error.URLError as e: raise Transient(f'连不上模型接口：{e.reason}')
    except (TimeoutError,ConnectionError) as e: raise Transient(f'模型接口超时或中断：{type(e).__name__}')

def _with_retry(fn,*a):
    """遇到限流、服务端错误、超时：等 2 秒再试一次（FUBI_MODEL_RETRY_WAIT 可调）。只重试一次，免得读者等太久；生成任务自己另有更长的退避"""
    try: return fn(*a)
    except Transient:
        time.sleep(float(os.environ.get('FUBI_MODEL_RETRY_WAIT','2'))); return fn(*a)

def _openai(system,user,cfg,json_mode):
    url=cfg['base_url'].rstrip('/')+'/chat/completions'
    body={'model':cfg['name'],'messages':[{'role':'system','content':system},{'role':'user','content':user}],'temperature':0.3,
          'max_tokens':cfg.get('max_tokens') or 32000}   # 明确设上限：长回答（一整章的解释卡）不会被厂商的默认上限截断成不完整的 JSON
    if cfg.get('thinking') in ('enabled','disabled'): body['thinking']={'type':cfg['thinking']}   # DeepSeek 的思考模式开关；不配置就不发，用厂商默认
    if cfg.get('effort') in ('low','high','max') and cfg.get('thinking')!='disabled': body['reasoning_effort']=cfg['effort']   # 思考强度：只在思考模式开着时才有意义，关闭思考时不发
    if json_mode: body['response_format']={'type':'json_object'}
    r=_post(url,{'Authorization':'Bearer '+cfg['api_key']},body,cfg['timeout'])
    try: ch=r['choices'][0]; text=ch['message']['content']
    except (KeyError,IndexError,TypeError): raise ModelError('模型返回的格式看不懂：'+json.dumps(r,ensure_ascii=False)[:300])
    if ch.get('finish_reason')=='length': raise TruncatedOutput('模型的回答被截断了（超过输出上限 %d）'%body['max_tokens'])
    if not text: raise ModelError('模型返回了空内容')   # JSON 模式偶尔会返回空字符串，当作一次可重试的错误，而不是"格式不对"
    return text

def _anthropic(system,user,cfg,json_mode):
    url=(cfg['base_url'] or 'https://api.anthropic.com').rstrip('/')+'/v1/messages'
    body={'model':cfg['name'],'max_tokens':8000,'system':system,'messages':[{'role':'user','content':user}],'temperature':0.3}
    r=_post(url,{'x-api-key':cfg['api_key'],'anthropic-version':'2023-06-01'},body,cfg['timeout'])
    try: return ''.join(b.get('text','') for b in r['content'] if b.get('type')=='text')
    except (KeyError,TypeError): raise ModelError('模型返回的格式看不懂：'+json.dumps(r,ensure_ascii=False)[:300])

def _mock(task,vars_,cfg):
    import tasks
    return json.dumps(tasks.TASKS[task].mock(vars_),ensure_ascii=False)

PROVIDERS={'openai':_openai,'anthropic':_anthropic}

# ---------------- 解析和校验 ----------------
# 模型偶尔会把自己的内部特殊符号漏进回答（形如 <|endoftext|>、<|im_end|>）。2026-11-03 线上"检查模型"里出现过，位置在 JSON 中间导致解析失败。
# 更危险的是出现在某句解释的文字里：JSON 仍然合法，符号会原样存进读者看到的解释。所以解析前先检查，有就按"格式有问题"处理，走带错误提示的重试
STRAY=re.compile(r'<\|[^|<>\n]{1,40}\|>')
def find_stray(text): return STRAY.findall(text or '')[:3]
def parse_json(text):
    """模型常在 JSON 外面包 ```json …```，或前后多说一两句；取最外层的 { … } 或 [ … ]"""
    t=text.strip()
    m=re.search(r'```(?:json)?\s*(.*?)```',t,re.S)
    if m: t=m.group(1).strip()
    for a,b in (('{','}'),('[',']')):
        i,j=t.find(a),t.rfind(b)
        if i>=0 and j>i:
            try: return json.loads(t[i:j+1])
            except json.JSONDecodeError: pass
    return json.loads(t)

# ---------------- 记账和上限 ----------------
def _check_quota(book):
    c=config.MODEL
    if c['provider']=='mock': return
    day=time.strftime('%Y-%m-%d')
    n=db.one("select count(*) from model_calls where day=? and provider!='mock'",(day,))[0]
    if n>=c['daily_calls']: raise QuotaExceeded(f'今天的模型调用已到上限（{c["daily_calls"]} 次）')
    if book:
        m=db.one("select count(*) from model_calls where book=? and provider!='mock' and ok=1",(book,))[0]
        if m>=c['book_calls']: raise QuotaExceeded(f'这本书的模型调用已到上限（{c["book_calls"]} 次）')

def _log(task,book,ok,ms,nin,nout,err=''):
    c=config.MODEL
    db.run("insert into model_calls(day,t,task,book,provider,model,ok,ms,chars_in,chars_out,err) values(?,?,?,?,?,?,?,?,?,?,?)",
           (time.strftime('%Y-%m-%d'),time.time(),task,book or '',c['provider'],c['name'] or c['provider'],1 if ok else 0,ms,nin,nout,err[:300]))

# ---------------- 唯一入口 ----------------
def call(task,vars_,book=None,cfg=None):
    import tasks
    cfg=cfg or config.MODEL
    T=tasks.TASKS[task]
    system,user=T.render(vars_)
    _check_quota(book)
    last=None
    for attempt in range(2):
        t0=time.time()
        try:
            if cfg['provider']=='mock': text=_mock(task,vars_,cfg)
            else:
                fn=PROVIDERS.get(cfg['provider'])
                if not fn: raise ModelError('不认识的模型提供方：'+cfg['provider'])
                if not cfg['api_key'] or not cfg['name']: raise ModelError('未配置模型密钥或模型名（FUBI_MODEL_API_KEY / FUBI_MODEL_NAME）')
                text=_with_retry(fn,system,user,cfg,T.json_mode)
        except ModelError as e:
            _log(task,book,False,int((time.time()-t0)*1000),len(system)+len(user),0,str(e)); raise
        ms=int((time.time()-t0)*1000)
        stray=find_stray(text)
        if stray: out=None; problems=['回答里混进了内部符号 '+' '.join(stray)+'，请去掉它们，只输出要求的 JSON']
        else:
            try:
                out=parse_json(text); problems=T.validate(out,vars_)
            except (json.JSONDecodeError,ValueError) as e: out=None; problems=['不是合法的 JSON：'+str(e)[:120]]
        if not problems:
            _log(task,book,True,ms,len(system)+len(user),len(text)); return out
        _log(task,book,False,ms,len(system)+len(user),len(text),'；'.join(problems))
        last=problems
        user=user+'\n\n你上一次的输出有这些问题，请改正后重新输出完整的 JSON：\n- '+'\n- '.join(problems[:12])
    raise BadOutput('；'.join(last[:6]))

VENDORS=(('deepseek','DeepSeek'),('openai.com','OpenAI'),('anthropic','Anthropic'),('dashscope','阿里云百炼（通义千问）'),('moonshot','月之暗面（Kimi）'),('bigmodel','智谱'),('siliconflow','硅基流动'))
# 模型别名 → 官方完整名。来自 DeepSeek 官方文档（用户 2026-11-03 贴的截图）：别名会随厂商升级换成新版本，所以这张表会过时，过时了只是少显示完整名，不影响调用
OFFICIAL={'deepseek-flash':'DeepSeek-V4.1-Flash-1017','deepseek-v4-pro':'DeepSeek-V4-Pro-0813'}
def describe(cfg=None):
    """后台显示用：厂商 · 模型名 · 思考模式。provider 只是接口协议（openai=OpenAI 兼容），不是厂商，所以从接口地址认厂商。"""
    cfg=cfg or config.MODEL
    if cfg['provider']=='mock': return {'vendor':'假模型','model':'','thinking':'','line':'假模型（没有配置真模型）'}
    url=(cfg.get('base_url') or '').lower(); vendor=next((n for k,n in VENDORS if k in url),None) or ('Anthropic' if cfg['provider']=='anthropic' else (url.split('//')[-1].split('/')[0] or '未知厂商'))
    t=cfg.get('thinking') or ''; eff=cfg.get('effort') or ''
    th={'disabled':'思考模式：已关闭','enabled':'思考模式：已开启'+('，强度 '+eff if eff in ('low','high','max') else '')}.get(t)
    if th is None: th='思考模式：厂商默认'+('，强度 '+eff if eff in ('low','high','max') else '')   # 没配置时不替厂商猜它的默认值
    nm=cfg['name'] or '未填模型名'; full=OFFICIAL.get(cfg['name'] or '')
    label=f"{nm}（{full}）" if full else nm
    return {'vendor':vendor,'model':cfg['name'] or '','thinking':th,'line':f"{vendor} · {label} · {th}"}

def health(cfg=None):
    """检查模型能不能用：发一个最小的请求。部署后在后台点一下就知道密钥、地址、模型名对不对。"""
    cfg=cfg or config.MODEL
    if cfg['provider']=='mock': return {'ok':True,'provider':'mock','msg':'正在用假模型（没有配置真模型）'}
    t0=time.time(); text=None; retried=False; TRIES=3
    base={'provider':cfg['provider'],'model':cfg['name']}
    user='输出 {"ok": true}'
    for attempt in range(TRIES):
        # 模型偶尔会在 JSON 里夹进内部符号（如 <|endoftext|>）。11-03 线上出现过一次，11-04 连续两次都出现：
        # 原来重试发的是一模一样的提示，这么短的提示模型基本照抄，第二次大概率复现。
        # 现在和真实任务（call）一样：重试时把上一次的问题告诉模型，最多试 3 次
        try:
            fn=PROVIDERS[cfg['provider']]
            text=_with_retry(fn,'只输出 JSON。',user,cfg,True)
        except Exception as e: return {'ok':False,**base,'msg':str(e)[:300]}   # 连不上、鉴权失败、限流、被截断、空内容：异常信息本身就写清了原因
        ms=int((time.time()-t0)*1000)
        stray=find_stray(text)
        if stray: why='回答里混进了内部符号 '+' '.join(stray)
        else:
            try:
                if parse_json(text).get('ok') is True:
                    return {'ok':True,**base,'ms':ms,'msg':'可以用'+('（回答格式有误，已自动重试 %d 次）'%attempt if retried else '')}
                why='回答不对：'+' '.join(str(text).split())[:100]
            except (ValueError,AttributeError) as e: why='不是合法 JSON（'+str(e)[:60]+'）'
        retried=True
        user='输出 {"ok": true}\n\n你上一次的输出有问题：'+why+'。请改正后，只输出这个 JSON。'
    raw=' '.join(str(text).split())[:200]   # 只取前 200 字，换行压成空格
    return {'ok':False,**base,'ms':ms,'msg':f'能连上，但连续 {TRIES} 次回答都有问题（{why}）。模型原文：「{raw}」'}
