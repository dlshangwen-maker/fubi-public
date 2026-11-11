p='生成/自测_两本书.js'; s=open(p).read()
def R(a,b):
    global s; assert s.count(a)==1,a[:70]; s=s.replace(a,b)
R("    ok('顶部只有两个节点（账号、问卷），在第 1 个',document.querySelectorAll('.flsteps li:not(.ln)').length===2&&document.querySelector('.flsteps li.cur').textContent.includes('账号'));",
  "    ok('顶部两段进度条（不写字），在第 1 段',document.querySelectorAll('.fldots i').length===2&&document.querySelectorAll('.fldots i.on').length===1&&!document.querySelector('.flbar').textContent.trim());")
a=s.index("    ok('注册后直接进问卷（第 2 个节点），问卷里自己的 1 / 3'"); b=s.index("    ok('选了\"字词看不懂\"→ 新书解释默认入门',PF.lv===0);")
s=s[:a]+r"""    ok('注册后直接进问卷（第 2 段），三张卡在一屏，第一张展开',document.querySelectorAll('.fldots i.on').length===2&&document.querySelectorAll('.qzc').length===3&&document.querySelectorAll('.qzc.open').length===1);
    document.querySelector('.qzchips [data-v="half"]').click(); await w(400);
    ok('答完一张：收成一行（带"改"），下一张展开',!!document.querySelector('.qzc.done[data-edit="0"]')&&document.querySelector('.qzc.done').textContent.includes('读到一半放下')&&document.querySelector('.qzc.open .qzt').textContent.includes('卡在'));
    document.querySelector('.qzchips [data-v="words"]').click(); document.querySelector('.qzchips [data-v="bored"]').click();
    ok('第二题可多选，选了才能点"好了"',document.querySelectorAll('.qzchips [aria-pressed="true"]').length===2&&!document.querySelector('#qzNext').disabled);
    document.querySelector('#qzNext').click(); await w(20);
    document.querySelector('.qzc.done[data-edit="0"]').click(); await w(20);
    ok('答过的随时点回去改（答案还在）',document.querySelector('.qzc.open .qzt').textContent.includes('平时')&&!!document.querySelector('.qzchips [data-v="half"][aria-pressed="true"]'));
    document.querySelector('.qzchips [data-v="long"]').click(); await w(400);
    ok('改完回到没答的那张',document.querySelector('.qzc.open .qzt').textContent.includes('怎样陪你')&&document.querySelector('.qzc.done').textContent.includes('很久没读完'));
    document.querySelector('.qzchips [data-v="less"]').click(); await w(400);
    ok('三题都答完：下面实时显示"伏笔会以 轻度 的方式陪你读"',document.querySelector('.qzres')?.textContent.includes('轻度')&&!!document.querySelector('#qrOk'));
    document.querySelector('.qzc.done[data-edit="2"]').click(); await w(20); document.querySelector('.qzchips [data-v="auto"]').click(); await w(400);
    ok('改了第三题：结果当场变成重度',document.querySelector('.qzres').textContent.includes('重度'));
    document.querySelector('#qrOk').click(); await w(30);
    ok('"开始读书"后是重度',PF.mode==='heavy');
    ok('规则：少打扰 = 轻；多带 = 重；常读+按前两题 = 轻',T.quizMode({q3:'less',q1:'long'})==='light'&&T.quizMode({q3:'more'})==='heavy'&&T.quizMode({q1:'often',q2:['people'],q3:'auto'})==='light');
"""+s[b:]
R("    document.querySelector('#qrOk').click(); await w(30);\n    ok('开始读书 → 书架","    ok('开始读书 → 书架")
R("document.querySelector('#meQz').click(); await w(20); ok('重新填写：一屏一题，带着上次的答案、能返回',document.querySelectorAll('.qzo [aria-pressed=\"true\"]').length===1&&!!document.querySelector('#pgBack'));",
  "document.querySelector('#meQz').click(); await w(20); ok('重新填写：三张卡都带着上次的答案、能返回',document.querySelectorAll('.qzc.done').length===3&&!!document.querySelector('#pgBack'));")
R("    T.setMode('light'); T.paintUEnd(); ok('轻度也有回末回顾',!document.querySelector('.uend[data-u=\"1\"]').hidden);",
  "    T.setMode('light'); T.paintUEnd(); ok('轻度不显示回末回顾',document.querySelector('.uend[data-u=\"1\"]').hidden); T.setMode('heavy'); T.paintUEnd();")
R("    T.markRd(0,IX['2.1']); S_.current=IX['1.44']; T.setPos(IX['2.1']); await w(600);","    T.setMode('heavy'); T.markRd(0,IX['2.1']); S_.current=IX['1.44']; T.setPos(IX['2.1']); await w(600);")
a=s.index("    T.setBook('hound'); T.closeSheet(); localStorage.clear(); T.TIPSS().welcomed=1; T.setMode('light'); T.shelf(); }")
s=s[:a]+r"""    // 提示条都有 ×；离开这本书，书里的提示立刻消失
    T.shelf(); T.openBook('hlm'); await w(700); T.closeSheet();
    { const tb2=document.querySelector('#toast'), IX2=T.getIDX(), S2=T.getS(); S2.mainSeen=Date.now(); T.TIPSS().tipFound=1; T.noRead(1); await w(60);
      T.markRd(0,IX2['1.15']); S2.vis=IX2['1.15']; delete S2.found.H02; delete S2.doneS.H02; T.paintMarks(); await w(100);
      S2.seen.H02=Date.now(); tb2.classList.remove('show'); T.markRd(0,IX2['1.33']); S2.current=IX2['1.31']; T.setPos(IX2['1.33']); await w(1300);
      ok('揭晓提示条右边有 ×',tb2.classList.contains('show')&&!!tb2.querySelector('.tx'),tb2.textContent.slice(0,30));
      tb2.querySelector('.tx')?.click(); ok('点 × 立刻关掉',!tb2.classList.contains('show'));
      delete S2.doneS.H02; S2.current=IX2['1.31']; T.setPos(IX2['1.33']); await w(200); T.shelf(); await w(1300);
      ok('揭晓提示还没出来就回书架：不会再跳出来（不带到下一本书）',!tb2.classList.contains('show')&&!document.querySelector('#mlfx.show')); }
    // 导览：阅读回顾固定在底部
    T.openBook('hlm'); await w(700); T.closeSheet(); T.outline('hui'); await w(20);
    ok('导览：阅读回顾固定在底部（不在目录里）',!!document.querySelector('#sheet .sfoot.olfoot #olRecap')&&!document.querySelector('#olBody #olRecap'));
    document.querySelector('#olRecap').click(); await w(20); ok('点开阅读回顾，可以返回导览',document.querySelector('#sheet .ttl').textContent==='阅读回顾'&&!!document.querySelector('#rcBack'));
    document.querySelector('#rcBack').click(); await w(20); ok('返回导览',document.querySelector('#sheet .ttl').textContent==='导览'); T.closeSheet();
    T.openBook('tractatus'); await w(700); T.closeSheet(); T.markRd(0,5); T.outline(); await w(20); ok('逻辑哲学论导览底部也有阅读回顾',!!document.querySelector('#sheet .olfoot #olRecap')); T.closeSheet();
    // 主线的伏笔没打开过：读到答案照样拼上，卡片里说明这一块来自哪个问题
    T.openBook('hound'); await w(800); T.closeSheet();
    { const S3=T.getS(), I3=T.getIDX(); S3.mainSeen=Date.now(); T.setMode('light');
      const s5=T.getSUS2().find(x=>x.id==='B14'), j=I3[s5['揭晓']]; delete S3.seen.B14; delete S3.doneS.B14; S3.found.B14=Date.now(); document.querySelector('#mlfx')?.classList.remove('show');
      T.markRd(0,j-1); S3.current=j-1; T.noRead(1); await w(60); T.els()[j].scrollIntoView({block:'start'}); await w(80); T.setPos(j); await w(1300);
      const m2=document.querySelector('#mlfx');
      ok('主线的伏笔没打开过：读到答案照样拼上',!!S3.doneS.B14&&!!m2&&m2.classList.contains('show'));
      ok('拼图卡里说明这一块来自之前没打开的伏笔',!!m2&&m2.textContent.includes('之前没打开')&&m2.textContent.includes('哀号'));
      ok('拼图卡有 ×',!!document.querySelector('#mlfxX')); document.querySelector('#mlfxX')?.click(); ok('点 × 关掉拼图卡',!!m2&&!m2.classList.contains('show')); }
"""+s[a:]
open(p,'w').write(s); print('ok')
