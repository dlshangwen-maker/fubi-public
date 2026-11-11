import re
SUB=str.maketrans('0123456789νnacx+','₀₁₂₃₄₅₆₇₈₉ᵥₙₐ꜀ₓ₊')
SUP=str.maketrans('0123456789νn+','⁰¹²³⁴⁵⁶⁷⁸⁹ᵛⁿ⁺')
def arg(s,i):
    # 读取从 i 开始的 {…}，返回 (内容, 结束位置)
    if i<len(s) and s[i]=='{':
        d=0
        for j in range(i,len(s)):
            if s[j]=='{': d+=1
            elif s[j]=='}':
                d-=1
                if d==0: return s[i+1:j],j+1
    if i<len(s): return s[i],i+1
    return '',i
def cmd(s,name,fn,nargs=1,opt=False):
    out=[];i=0;pat='\\'+name
    while True:
        j=s.find(pat,i)
        if j<0 or (j+len(pat)<len(s) and s[j+len(pat)].isalpha()):
            if j<0: out.append(s[i:]); break
            out.append(s[i:j+len(pat)]); i=j+len(pat); continue
        out.append(s[i:j]); k=j+len(pat)
        if opt and k<len(s) and s[k]=='[': k=s.index(']',k)+1
        while k<len(s) and s[k]==' ': k+=1
        a=[]
        for _ in range(nargs):
            x,k=arg(s,k); a.append(x)
        out.append(fn(*a)); i=k
    return ''.join(out)
def clean(t):
    if '\\' not in t and '{' not in t: return t
    s=t
    for _ in range(3):
        s=cmd(s,'DPtypo',lambda a,b:b,2)
        s=cmd(s,'textit',lambda a:a); s=cmd(s,'Emph',lambda a:a); s=cmd(s,'mbox',lambda a:a); s=cmd(s,'text',lambda a:a)
        s=cmd(s,'phantom',lambda a:'' ); s=cmd(s,'raisebox',lambda a,b:b,2); s=cmd(s,'smash',lambda a:a,1,True)
        s=cmd(s,'binom',lambda a,b:f'C({a},{b})',2); s=cmd(s,'overline',lambda a:a+'\u0304'); s=cmd(s,'bar',lambda a:a+'\u0304')
    s=re.sub(r'_\{([^{}]*)\}',lambda m:m.group(1).translate(SUB) if all(c in '0123456789νnacx+' for c in m.group(1)) else '_'+m.group(1),s)
    s=re.sub(r'\^\{([^{}]*)\}',lambda m:m.group(1).translate(SUP) if all(c in '0123456789νn+' for c in m.group(1)) else '^('+m.group(1)+')',s)
    R={'\\sum\\limits':'Σ','\\sum':'Σ','\\fivedots':' . . . . .','\\times':'×','\\cdot':'·','\\supset':'⊃','\\equiv':'≡','\\sim':'~','\\vee':'∨','\\ldots':'…','\\dots':'…','\\glq':'‚','\\grq':'‘','\\;':' ','\\,':' ','\\ ':' ','\\-':'','\\[':'\n','\\]':'\n','\\\\':'\n','\\{':'{','\\}':'}','\\&':'&'}
    for a,b in R.items(): s=s.replace(a,b)
    s=re.sub(r'\\begin\{[^}]*\}(\[[^\]]*\])?(\{[^}]*\})?|\\end\{[^}]*\}|\\hline|\\noindent|\\centering|\\footnotesize|\\small|\\baselineskip','',s)
    s=re.sub(r'\\[a-zA-Z]+\*?','',s)
    s=s.replace('{','').replace('}','')
    s=re.sub(r'[ \t]+',' ',s); s=re.sub(r'\n\s*\n+','\n',s)
    return s.strip()
if __name__=='__main__':
    import json,sys
    S=json.load(open(sys.argv[1]))
    for p in S['命题']:
        for L in ('de','en'):
            c=clean(p[L])
            if '\\' in p[L]: print(p['n'],L,'|',c[:160])
