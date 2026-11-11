"""本机巡检与邮件告警（A7）。由 systemd 定时器每 2 分钟运行一次（deploy/fubi-monitor.timer），每次跑完就退出。

检查项：
  service   服务是否在响应（请求本机 /api/health）。连续 2 次失败才告警，避免重启瞬间误报
  database  /api/health 返回的数据库是否正常
  disk      数据所在磁盘剩余空间，低于 FUBI_ALERT_DISK_PCT（默认 15%）告警
  backup    最近一次备份距今是否超过 30 小时
  errors    最近 10 分钟的 5xx 错误是否 ≥ FUBI_ALERT_5XX（默认 5 次）
  model     今天的模型调用是否已用掉 90% 的上限（只有接了真模型才检查）

告警规则：
  出现新问题 → 发一封邮件；问题持续 → 每 6 小时提醒一次；问题消失 → 发一封"已恢复"。
  收件人：FUBI_ALERT_TO（多个用逗号隔开；不设就用 FUBI_ADMIN_EMAILS）。发件用服务本身的邮件配置（FUBI_SMTP_*）。
  状态记在 <数据目录>/monitor.json，后台页面读它显示"最近一次巡检"和"当前异常"。

整台服务器宕机时，本机程序自己也停了，发不出告警。要防这一点，需要一个在外面的拨测服务（见 deploy/部署清单.md "整机宕机告警"）。

用法：python3 server/monitor.py            巡检一次（给定时器用）
      python3 server/monitor.py --test      发一封测试告警邮件，确认收得到
"""
import os,sys,json,time,shutil,urllib.request
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import config

REMIND_SEC=6*3600; FAILS_NEEDED=2
def state_path(): return os.path.join(config.DATA,'monitor.json')
def load():
    try: return json.load(open(state_path(),encoding='utf-8'))
    except (OSError,ValueError): return {'last':0,'issues':{},'fails':0}
def save(st):
    os.makedirs(config.DATA,exist_ok=True); tmp=state_path()+'.tmp'
    with open(tmp,'w',encoding='utf-8') as f: json.dump(st,f,ensure_ascii=False)
    os.replace(tmp,state_path())

def recipients():
    raw=os.environ.get('FUBI_ALERT_TO','') or ','.join(sorted(config.ADMIN_EMAILS))
    return [x.strip() for x in raw.split(',') if x.strip()]

def check_all(health_url=None,now=None):
    """返回 {检查项: 问题描述}，没问题的不出现。health_url 可注入，测试用"""
    now=now or time.time(); issues={}; st_fail=0
    url=health_url or 'http://127.0.0.1:%d/api/health'%config.PORT
    h=None
    try:
        with urllib.request.urlopen(url,timeout=10) as r: h=json.loads(r.read())
    except Exception as e: st_fail=1; issues['service']='服务没有响应（%s）'%type(e).__name__
    if h is not None and not h.get('ok'): issues['database']='数据库异常'
    try:
        u=shutil.disk_usage(config.DATA if os.path.exists(config.DATA) else '/'); pct=u.free*100/u.total
        limit=float(os.environ.get('FUBI_ALERT_DISK_PCT','15'))
        if pct<limit: issues['disk']='磁盘剩余 %.0f%%（剩 %.1f GB），低于 %.0f%%'%(pct,u.free/1e9,limit)
    except OSError: pass
    try:
        import backup
        L=backup.latest()
        if L is None: issues['backup']='还没有任何备份'
        elif now-L[1]>30*3600: issues['backup']='最近一次备份是 %d 小时前'%((now-L[1])//3600)
    except Exception: pass
    try:
        import logs
        n=logs.recent_errors(10); lim=int(os.environ.get('FUBI_ALERT_5XX','5'))
        if n>=lim: issues['errors']='最近 10 分钟有 %d 次服务器错误'%n
    except Exception: pass
    try:
        if config.MODEL['provider']!='mock':
            import db
            used=db.one('select count(*) from model_calls where day=?',(time.strftime('%Y-%m-%d'),))[0]; cap=config.MODEL['daily_calls']
            if cap and used>=cap*0.9: issues['model']='今天的模型调用已用 %d / %d'%(used,cap)
    except Exception: pass
    return issues,st_fail

LABEL={'service':'服务','database':'数据库','disk':'磁盘','backup':'备份','errors':'错误','model':'模型额度'}
def decide(st,issues,fails,now):
    """根据上次状态和这次结果，决定要不要发信。返回 (要发的邮件列表[(标题,正文)], 新状态)"""
    prev=st.get('issues',{}); mails=[]
    # 服务检查：连续失败达到次数才算数
    st_fails=(st.get('fails',0)+1) if fails else 0
    if 'service' in issues and st_fails<FAILS_NEEDED: issues=dict(issues); issues.pop('service')
    new={k:v for k,v in issues.items() if k not in prev}
    still={k:v for k,v in issues.items() if k in prev and now-prev[k].get('alerted',0)>=REMIND_SEC}
    gone=[k for k in prev if k not in issues]
    cur={k:{'msg':v,'since':prev.get(k,{}).get('since',now),'alerted':prev.get(k,{}).get('alerted',0)} for k,v in issues.items()}
    if new or still:
        lines=['%s：%s'%(LABEL.get(k,k),v) for k,v in {**new,**still}.items()]
        others=['%s：%s'%(LABEL.get(k,k),v['msg']) for k,v in cur.items() if k not in new and k not in still]
        body='伏笔服务器出现问题：\n\n'+'\n'.join(lines)+('\n\n仍在持续：\n'+'\n'.join(others) if others else '')+'\n\n时间：'+time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(now))+'\n查看日志：journalctl -u fubi -n 100 --no-pager'
        mails.append(('【伏笔】服务器告警：'+'、'.join(LABEL.get(k,k) for k in {**new,**still}),body))
        for k in {**new,**still}: cur[k]['alerted']=now
    if gone and not issues:
        mails.append(('【伏笔】已恢复','之前的问题已全部恢复：'+'、'.join(LABEL.get(k,k) for k in gone)+'\n时间：'+time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(now))))
    elif gone:
        mails.append(('【伏笔】部分恢复','已恢复：'+'、'.join(LABEL.get(k,k) for k in gone)+'\n仍在持续：'+'、'.join(LABEL.get(k,k) for k in issues)))
    return mails,{'last':now,'issues':cur,'fails':st_fails}

def send(mails):
    import accounts
    to=recipients()
    if not to: sys.stderr.write('[告警没有收件人] 请设置 FUBI_ALERT_TO 或 FUBI_ADMIN_EMAILS\n'); return False
    ok=True
    for subj,body in mails:
        for addr in to:
            try: accounts.mailer(addr,subj,body)
            except Exception as e: ok=False; sys.stderr.write('告警邮件发送失败：%s %s\n'%(type(e).__name__,str(e)[:120]))
    return ok

def run_once(health_url=None,now=None):
    now=now or time.time(); st=load(); issues,fails=check_all(health_url,now); mails,new=decide(st,issues,fails,now)
    if mails: send(mails)
    save(new); return new

def main(argv):
    if '--test' in argv:
        ok=send([('【伏笔】测试告警','这是一封测试告警邮件。收到它，说明告警邮件配置正常。')]); print('✓ 已发送' if ok else '✗ 发送失败，见上面的错误'); return 0 if ok else 1
    new=run_once(); bad=new['issues']
    print('巡检完成：%s'%('正常' if not bad else '；'.join('%s：%s'%(LABEL.get(k,k),v['msg']) for k,v in bad.items()))); return 0
if __name__=='__main__': sys.exit(main(sys.argv))
