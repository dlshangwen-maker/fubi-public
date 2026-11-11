"""备份与恢复（只用标准库）。

备份什么：数据库 fubi.db（用 SQLite 自带的在线备份，服务不用停，也不会拷到写了一半的文件）
          + books/（读者导入的书和生成结果）。不备份 cache/（下载缓存，丢了可以重新下）和 builtin.json（由代码生成）。
备份到哪：FUBI_BACKUP_DIR（默认 <数据目录>_backups），每次一个 fubi-年月日-时分秒.tar.gz，保留最近 FUBI_BACKUP_KEEP 份（默认 14）。
每次备份做完都会：对备份出来的数据库跑完整性检查，再把压缩包重新打开读一遍；任何一步不通过就删掉这份、报错退出（退出码 1）。

用法（在项目根目录，用服务的同一个用户和同一份环境变量）：
  python3 server/backup.py backup                 做一份备份并清理旧的
  python3 server/backup.py list                   列出现有备份
  python3 server/backup.py verify <压缩包>        只检查一份备份能不能用
  python3 server/backup.py restore <压缩包> --yes 恢复到数据目录。**先停服务**。当前的 fubi.db 和 books/ 不会被删除，
                                                  会挪到 <数据目录>/_恢复前_<时间>/ 里，恢复错了还能挪回来。
注意：备份和数据在同一块盘上，只能防误删和数据库损坏，防不了整台服务器丢失；要防后者，需要把备份目录再同步到别处（见 deploy/部署清单.md）。
"""
import os,sys,time,glob,shutil,sqlite3,tarfile,tempfile
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import config

PREFIX='fubi-'; SUFFIX='.tar.gz'
def backup_dir(): return os.environ.get('FUBI_BACKUP_DIR') or config.DATA.rstrip('/')+'_backups'
def keep_n():
    try: return max(3,int(os.environ.get('FUBI_BACKUP_KEEP','14')))
    except ValueError: return 14

def _check_db(path):
    c=sqlite3.connect(path)
    try:
        r=c.execute('pragma integrity_check').fetchall()
        if r!=[('ok',)]: raise RuntimeError('数据库完整性检查没通过：'+str(r[:3]))
        return {t:c.execute(f'select count(*) from "{t}"').fetchone()[0] for (t,) in c.execute("select name from sqlite_master where type='table' and name not like 'sqlite_%'")}
    finally: c.close()

def list_backups(d=None):
    d=d or backup_dir()
    return sorted(glob.glob(os.path.join(d,PREFIX+'*'+SUFFIX)))

def latest(d=None):
    """最近一份备份：(路径, 时间戳)，没有返回 None。后台页面用它提示"多久没备份了" """
    L=list_backups(d)
    return (L[-1],os.path.getmtime(L[-1])) if L else None

def verify(archive):
    """打开压缩包，把数据库解出来检查完整性，再确认所有文件都能读完。返回各表行数"""
    with tempfile.TemporaryDirectory() as t:
        with tarfile.open(archive,'r:gz') as tf:
            names=tf.getnames()
            if 'fubi.db' not in names: raise RuntimeError('压缩包里没有 fubi.db')
            for m in tf.getmembers():
                if m.name.startswith('/') or '..' in m.name.split('/'): raise RuntimeError('压缩包里有不安全的路径：'+m.name)
                if m.isfile(): tf.extractfile(m).read()   # 读完整个文件，压缩包损坏会在这里报错
            tf.extract('fubi.db',t)
        return _check_db(os.path.join(t,'fubi.db'))

def backup(d=None,data=None):
    d=d or backup_dir(); data=data or config.DATA
    src=os.path.join(data,'fubi.db')
    if not os.path.exists(src): raise RuntimeError('找不到数据库：'+src)
    os.makedirs(d,exist_ok=True)
    name=PREFIX+time.strftime('%Y%m%d-%H%M%S')+SUFFIX; final=os.path.join(d,name); tmp=final+'.part'
    try:
        with tempfile.TemporaryDirectory(dir=d) as t:
            snap=os.path.join(t,'fubi.db')
            s=sqlite3.connect(src,timeout=60); o=sqlite3.connect(snap)
            try: s.backup(o)   # 在线备份：服务正在写也没关系
            finally: o.close(); s.close()
            _check_db(snap)
            with tarfile.open(tmp,'w:gz') as tf:
                tf.add(snap,arcname='fubi.db')
                bd=os.path.join(data,'books')
                if os.path.isdir(bd): tf.add(bd,arcname='books')
        verify(tmp); os.replace(tmp,final)
    except BaseException:
        for p in (tmp,):
            try: os.remove(p)
            except OSError: pass
        raise
    for old in list_backups(d)[:-keep_n()]:
        try: os.remove(old)
        except OSError: pass
    return final

def restore(archive,data=None):
    data=data or config.DATA
    verify(archive)   # 先确认这份备份是好的，再动现有数据
    os.makedirs(data,exist_ok=True)
    aside=os.path.join(data,'_恢复前_'+time.strftime('%Y%m%d-%H%M%S')); moved=[]
    for n in ('fubi.db','fubi.db-wal','fubi.db-shm','books'):
        p=os.path.join(data,n)
        if os.path.exists(p):
            os.makedirs(aside,exist_ok=True); shutil.move(p,os.path.join(aside,n)); moved.append(n)
    with tarfile.open(archive,'r:gz') as tf:
        for m in tf.getmembers():
            if m.name.startswith('/') or '..' in m.name.split('/'): raise RuntimeError('压缩包里有不安全的路径：'+m.name)
        tf.extractall(data)
    return _check_db(os.path.join(data,'fubi.db')),(aside if moved else '')

def main(argv):
    if len(argv)<2 or argv[1] not in ('backup','list','verify','restore'): print(__doc__); return 2
    cmd=argv[1]
    try:
        if cmd=='backup':
            p=backup(); print('✓ 备份完成：%s（%.1f MB），现有 %d 份'%(p,os.path.getsize(p)/1e6,len(list_backups())))
        elif cmd=='list':
            for p in list_backups(): print('%s  %.1f MB'%(os.path.basename(p),os.path.getsize(p)/1e6))
            if not list_backups(): print('（还没有备份）')
        elif cmd=='verify':
            if len(argv)<3: print('用法：verify <压缩包>'); return 2
            print('✓ 这份备份可用：',verify(argv[2]))
        else:
            if len(argv)<4 or argv[3]!='--yes': print('恢复会替换当前数据（旧数据会挪到 _恢复前_… 目录，不会删）。确认请加 --yes。先停服务：systemctl stop fubi'); return 2
            rows,aside=restore(argv[2]); print('✓ 已恢复：',rows); print('旧数据放在：',aside or '（原来没有数据）'); print('现在启动服务：systemctl start fubi')
    except Exception as e:
        sys.stderr.write('✗ %s失败：%s %s\n'%({'backup':'备份','list':'列出','verify':'检查','restore':'恢复'}[cmd],type(e).__name__,e)); return 1
    return 0
if __name__=='__main__': sys.exit(main(sys.argv))
