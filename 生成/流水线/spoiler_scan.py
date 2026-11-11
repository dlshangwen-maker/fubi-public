"""事后剧透扫描：卡片里出现的人名/别称/概念，是否早于它在原文中出现的位置；是否有暗示后文的字眼。"""
import json,re,sys
B=sys.argv[1]
k=lambda p:tuple(int(x) for x in p.split('.'))
cards=json.load(open(f'{B}/卡片_合并.json'))
idx=json.load(open(f'{B}/索引_合并.json'))
TXT=json.load(open(f'../文本数据/{B}/全文.json'))
SEG={s['id']:s['文'] for h in TXT['回'] for s in h['段']}
# 所有名字（标准名 + 别称），记录最早可见位置；太泛的称呼跳过
GENERIC=set('我 他 她 姐姐 妹妹 哥哥 母亲 父亲 女儿 太太 老爷 姑娘 丫头 小女 小婿 女婿 夫人 老太太 仙子 仙姑 丽人 和尚 道人 老僧 公子 小姐 奶母 嫂子 嫂 舅舅 舅母 姨娘 姨母 外祖母 祖母 表兄 兄弟 内侄 少奶奶 老先生 岳丈 妻子 孩子 女子 此女子 小童 官府 官儿 一僧 一道 那僧 道 僧 外甥 有人 小的 故人 祖父 大舅 他母亲 石头 琏二 内人 父 弟 吾兄'.split())
names={}
for e in idx['人物']:
    for a in e['别称']:
        w=a['称']
        if len(w)<2 or w in GENERIC: continue
        if w not in names or k(a['从'])<k(names[w][0]): names[w]=(a['从'],e['名'])
    nm=e['名']; vis=e.get('名可显示从')
    if len(nm)>=2 and nm not in GENERIC and vis and (nm not in names or k(vis)<k(names[nm][0])): names[nm]=(vis,nm)
# 全书人物名（索引里没有的，即前五回没出现的重要人物）
LATER='史湘云 湘云 妙玉 巧姐 香菱 贾芸 小红 平儿 鸳鸯 紫鹃 尤二姐 尤三姐 柳湘莲 夏金桂 宝琴 邢岫烟 李纹 李绮 贾环 赵姨娘 智能 秦钟 贾瑞 金钏 玉钏 司棋 芳官 龄官 蒋玉菡 北静王 刘姥姥 板儿 甄宝玉 贾芹 贾蔷 傻大姐 潇湘妃子 蘅芜君 怡红公子 绛洞花主 大观园 怡红院 潇湘馆 蘅芜苑 稻香村 栊翠庵 元妃 省亲 抄家 出家 黛玉之死 焚稿 掉包 中举'.split()
LATER=[w for w in LATER if w not in ('出家',)]
HINT=['注定','终将','最终','结局','悲剧','伏笔','预示','暗示了','早逝','应验','后文']   # “后来”“将来”“出家”“死去”多是原文本身的用法，太吵，交给人工抽查
# 一个名字如果是更早出现的别称的一部分（“警幻仙子”含“警幻”，“表兄薛蟠”含“薛蟠”），以更早的为准
allnames=list(names.items())
for w,(pos,who) in allnames:
    for w2,(pos2,who2) in allnames:
        if w in w2 and who==who2 and k(pos2)<k(names[w][0]): names[w]=(pos2,who)
# 原文本身出现过的词（如“鸳鸯枕”里的“鸳鸯”）：在该位置之前原文已出现，就不算后文人物
def in_text_before(w,sid):
    for s,tx in SEG.items():
        if k(s)<=k(sid) and w in tx: return True
    return False
hits=[]
for sid,card in cards.items():
    for lv,f in card.items():
        for fld,t in f.items():
            for w,(pos,who) in names.items():
                if w in t and k(pos)>k(sid) and w not in SEG.get(sid,''):
                    hits.append((sid,lv,fld,'未出场名',w,f'{who} 要到 {pos}',t[:60]))
            for w in LATER:
                if w in t and not in_text_before(w,sid): hits.append((sid,lv,fld,'后文人物/事物',w,'',t[:60]))
            for w in HINT:
                if w in t: hits.append((sid,lv,fld,'暗示字眼',w,'',t[max(0,t.index(w)-25):t.index(w)+20]))
json.dump(hits,open(f'{B}/剧透扫描.json','w'),ensure_ascii=False,indent=1)
from collections import Counter
print('命中',len(hits),Counter(h[3] for h in hits))
for h in hits: print(h)
