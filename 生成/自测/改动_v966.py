"""v9.66（10-30 用户三点）：
① 访客首页不要"营销页"（用户："不要这么刻意"）：没登录打开就是一个书架——logo、右上角"登录"、精读版封面、一行小字；去掉大标题、产品介绍、三条说明、大按钮。
② 个人账户页：账号信息区改成和"我的"一致的分隔行列表（账号 / 加入时间），去掉"数据：阅读记录保存在服务器上"（用户：给用户看这个干啥）；退出登录、注销账号间距理顺；确认框里也不再提"保存在设备上"。
③ 头像可以改：账户页点头像 → 选一个字 + 8 种颜色，或上传自己的图片（裁成正方形缩到 160px 存在本机）；有"恢复默认"；书架右上角、"我的"、账户页同步。
备份 Demo/模板_v81备份.html。函数体在 改动_v966_片段.js。"""
import os,re
B=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))+'/'
P=B+'Demo/模板.html'
s=open(P,encoding='utf-8').read()
FR={}; cur=None
for line in open(os.path.dirname(os.path.abspath(__file__))+'/改动_v966_片段.js',encoding='utf-8').read().split('\n'):
    m=re.match(r'^### (\S+)',line)
    if m: cur=m.group(1); FR[cur]=[]; continue
    if cur: FR[cur].append(line)
FR={k:'\n'.join(v).strip('\n')+'\n' for k,v in FR.items()}
def rep(a,b,n=1):
    global s
    c=s.count(a); assert c==n,(c,a[:90]); s=s.replace(a,b)
def fn(name):
    global s
    i=s.index('\nfunction '+name+'(')+1; j=s.index('\n}\n',i)+2
    s=s[:i]+FR[name]+s[j:]
fn('homePage'); fn('secPage')
# 头像：替换原来的一行 avatarHTML，并加上 avatarSheet
i=s.index("const avatarHTML=(u,cls='')=>"); j=s.index('\n',i)+1
s=s[:i]+FR['avatar']+s[j:]
rep('</style>',FR['css']+'</style>')
rep("if(window.__TEST) setTimeout(()=>window.__TEST({","if(window.__TEST) setTimeout(()=>window.__TEST({avatarSheet,avatarHTML,")
open(P,'w',encoding='utf-8').write(s); print('ok')
