"""v9.74b：标签页图标在 16 像素下要看得清——整体放大约 1.3 倍并居中（viewBox 裁到 8..32 的范围），去掉小细节（虚线、横线）"""
import os,re,urllib.parse
B=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))+'/'
P=B+'Demo/模板.html'
s=open(P,encoding='utf-8').read()
ICON='''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40"><rect width="40" height="40" rx="9" fill="#ECEEE7"/><g transform="translate(20 21) scale(1.28) translate(-20 -20)"><rect x="18.2" y="2.5" width="3.6" height="12" rx="1.3" fill="#1E2622"/><rect x="16.8" y="12.6" width="6.4" height="2.8" rx="1" fill="#1E2622"/><path d="M17.4 15.6H22.6Q26.4 21.5 24.8 28Q23 34 20 38Q17 34 15.2 28Q13.6 21.5 17.4 15.6Z" fill="#B23A2E"/></g></svg>'''
href='data:image/svg+xml,'+urllib.parse.quote(ICON,safe="/:=,' ()")
n=len(re.findall(r'<link rel="icon" type="image/svg\+xml" href="[^"]*">',s)); assert n==1,n
s=re.sub(r'<link rel="icon" type="image/svg\+xml" href="[^"]*">','<link rel="icon" type="image/svg+xml" href="'+href.replace('"','%22')+'">',s)
open(P,'w',encoding='utf-8').write(s); open('/tmp/fav2.svg','w').write(ICON); print('ok')
