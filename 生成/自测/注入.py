"""把测试脚本注入 demo，存到 outputs 里，用预览面板打开就会自动跑。
用法：python3 -I 生成/自测/注入.py <输出文件名.html> <脚本路径（相对 Read Book）>
注意：脚本插在 <meta charset> 后面（插在 <head> 后面会整页乱码），并限宽 390px 模拟手机。"""
import sys,re,os
B=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))+'/'
import glob
OUT=os.environ.get('FUBI_OUT') or (glob.glob('/sessions/*/mnt/outputs/')+[B])[0]   # 沙箱每次会话路径不同：自动找 outputs
name,js=sys.argv[1],sys.argv[2]
h=open(os.environ.get('FUBI_SRC') or B+'生成/自测/单文件版.html',encoding='utf-8').read()
t=open(B+js,encoding='utf-8').read()
m=re.search(r'<meta charset=[^>]*>',h,re.I)
h=h[:m.end()]+'<style>body{max-width:390px}</style><script>'+t+'</script>'+h[m.end():]
open(OUT+name,'w',encoding='utf-8').write(h); print('ok',name)
