"""查重：用指纹（不含原文）检查一个 JSON/文本文件里有没有和受版权保护译本连续 10 字以上相同的片段。
用法：python3 -I check_similar.py <指纹.json> <要查的文件> [排除文件（如我们自己的译文.json，里面出现的片段不算）]"""
import json,re,sys,hashlib
F=json.load(open(sys.argv[1])); n=F['片段长']; S=set(F['指纹'])
s=re.sub(r'⟦[^⟧]*⟧|\s','',open(sys.argv[2]).read())
ex=re.sub(r'⟦[^⟧]*⟧|\s','',open(sys.argv[3]).read()) if len(sys.argv)>3 else ''
hits=[]; i=0
while i<=len(s)-n:
    if hashlib.sha1(s[i:i+n].encode()).hexdigest()[:12] in S and s[i:i+n] not in ex:
        j=i+n
        while j<len(s) and hashlib.sha1(s[j-n+1:j+1].encode()).hexdigest()[:12] in S: j+=1
        hits.append(s[i:j]); i=j
    else: i+=1
print(f'{len(hits)} 处与指纹重合（≥{n} 字）'); [print('  ',h) for h in hits[:50]]
