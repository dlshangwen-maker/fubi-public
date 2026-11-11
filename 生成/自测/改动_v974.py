"""v9.74（11-02 用户两点）：①书籍详情底部那句不重要的小提示整条删掉；②浏览器标签页图标（favicon）用伏笔自己的标志
（内嵌 SVG，纸色底圆角方块 + 墨色笔身 + 朱色水滴，不额外多一个文件）。备份 模板_v90备份.html"""
import os,urllib.parse
B=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))+'/'
P=B+'Demo/模板.html'
s=open(P,encoding='utf-8').read()
def rep(a,b,n=1):
    global s
    c=s.count(a); assert c==n,(c,a[:80]); s=s.replace(a,b)
i=s.index("    <p class=\"mini\" style=\"margin-top:16px\">${b.imported?'解释和回顾都以你的阅读进度为界。'"); j=s.index("</p></div>\n  <div class=\"sfoot\">${b.imported?",i)
s=s[:i]+"  </div>\n  <div class=\"sfoot\">${b.imported?"+s[j+len("</p></div>\n  <div class=\"sfoot\">${b.imported?"):]
ICON='''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40"><rect width="40" height="40" rx="9" fill="#ECEEE7"/><clipPath id="u"><rect width="40" height="25"/></clipPath><clipPath id="d"><rect y="26.6" width="40" height="14"/></clipPath><rect x="18.4" y="2.5" width="3.2" height="11" rx="1.2" fill="#1E2622"/><rect x="17.2" y="12.6" width="5.6" height="2.4" rx=".8" fill="#1E2622"/><g clip-path="url(#u)"><path d="M17.4 15H22.6Q26 21 24.6 27.5Q23 33.5 20 38Q17 33.5 15.4 27.5Q14 21 17.4 15Z" fill="#B23A2E"/></g><g clip-path="url(#d)"><path d="M24.6 27.5Q23 33.5 20 38Q17 33.5 15.4 27.5" fill="none" stroke="#B23A2E" stroke-width="1.4" stroke-dasharray="1.8 1.8" stroke-linecap="round"/></g><path d="M5 25.8H35" stroke="#1E2622" stroke-width="1.6" stroke-linecap="round"/></svg>'''
href='data:image/svg+xml,'+urllib.parse.quote(ICON,safe="/:=,' ()")
rep('<meta name="theme-color" content="#ECEEE7">\n','<meta name="theme-color" content="#ECEEE7">\n<link rel="icon" type="image/svg+xml" href="'+href.replace('"',"%22")+'">\n')
open(P,'w',encoding='utf-8').write(s); print('ok',len(href))
