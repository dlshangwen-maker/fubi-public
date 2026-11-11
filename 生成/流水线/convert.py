import json,sys,re
sys.path.insert(0,'/tmp/hlm_work')
from t2s import conv
d=json.load(open('trad.json'))
# 一对多的字，ICU 有时选错；按词修正（转换后再改回）
FIX=[('干隆','乾隆'),('干坤','乾坤'),('干清宫','乾清宫'),('干净','干净'),
     ('着作','著作'),('显着','显著'),('昭着','昭著'),('着名','著名'),('土着','土著'),
     ('甚么','什么')]
FIX=[f for f in FIX if f[0]!=f[1] and f[0]!='甚么']
def fix(s):
    for a,b in FIX: s=s.replace(a,b)
    s=s.replace('巨集','宏')   # 维基文库录入时“宏”被误转成“巨集”
    s=s.replace('內','内').replace('凭藉','凭借')
    # 底本里“劃”常作“畫”用（如“忽劃一惡狼”），表示“画”的改成“画”；筹划、划船、划破等保留
    for a,b in [('忽划一','忽画一'),('又划一','又画一'),('或划一张','或画一张'),('划一张','画一张'),('划一乘','画一乘'),('比划儿','比画儿'),('不是划的','不是画的'),('界划','界画'),('入划','入画')]:
        s=s.replace(a,b)
    s=s.replace('著','着').replace('着书立','著书立')   # 剩下的“著”几乎都是助词“着”，只有“著书立说”保留
    return s
out=[]
for h in d:
    pc=lambda s:''.join(conv(c) for c in s)   # 逐字转换，避免 ICU 按词替换（察→查、甚么→什么、彷彿→仿佛）
    out.append({'回':h['回'],'回目':fix(pc(h['回目'])),'段':[fix(pc(p)) for p in h['段']]})
json.dump(out,open('simp.json','w'),ensure_ascii=False)
# 审计：转换后仍是繁体字？
alltxt=''.join(p for h in out for p in h['段'])
trad_left=[c for c in set(alltxt) if conv(c)!=c]
print('still-traditional chars:',len(trad_left),''.join(sorted(trad_left))[:200])
# 一对多风险字统计
for c in '干着于后里发云台面系历只志范制谷松斗':
    print(c, alltxt.count(c), end=' | ')
