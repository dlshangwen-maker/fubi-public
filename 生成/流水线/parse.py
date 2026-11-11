import re,html,json,sys,glob,os
src=sys.argv[1]; out=sys.argv[2]
files=sorted(glob.glob(src+'/OPS/c*_hong_lou_meng__cheng_yi_ben__di_*.xhtml'),key=lambda f:int(re.search(r'/c(\d+)_',f).group(1)))
CN='零一二三四五六七八九'
def cn2i(s):
    s=s.replace('〇','零').replace('○','零')
    if '十' not in s and '百' not in s:   # 一零零 / 一一九 这种逐位写法
        return int(''.join(str(CN.index(c)) for c in s))
    n=0
    if '百' in s: a,s=s.split('百'); n+= (CN.index(a) if a else 1)*100
    if '十' in s: a,s=s.split('十'); n+= (CN.index(a) if a and a!='零' else (0 if a=='零' else 1))*10
    s=s.replace('零','')
    if s: n+=CN.index(s)
    return n
huis=[]
for f in files:
    t=open(f,encoding='utf-8').read()
    b=t[t.index('<body'):]
    b=re.sub(r'<style.*?</style>','',b,flags=re.S)
    parts=re.split(r'(<h2[^>]*>.*?</h2>)',b,flags=re.S)
    for k in range(1,len(parts),2):
        title=html.unescape(re.sub(r'<[^>]+>','',parts[k])).strip()
        m=re.match(r'第(.+?)回\s*(.*)',title)
        if not m: continue
        body=parts[k+1]
        body=body.split('licenseContainer')[0]
        ps=[]
        for p in re.findall(r'<p[^>]*>(.*?)</p>',body,flags=re.S):
            s=html.unescape(re.sub(r'<[^>]+>','',p)).strip().strip('　').strip()
            if s: ps.append(s)
        huis.append({'回':cn2i(m.group(1)),'回目':m.group(2).strip(),'段':ps})
json.dump(huis,open(out,'w'),ensure_ascii=False)
print(len(huis),[h['回'] for h in huis][:5],'...',[h['回'] for h in huis][-3:])
print('missing',sorted(set(range(1,121))-{h['回'] for h in huis}))
print('chars',sum(len(p) for h in huis for p in h['段']))
for h in huis[:5]: print(h['回'],h['回目'],len(h['段']),sum(len(p) for p in h['段']))
