// 阅读器浏览器自测：用无头浏览器打开注入了测试脚本的页面，读 window.__RESULT，有失败就退出码 1。
// 用法：node scripts/run_browser_tests.js          （需要先 npm i -D playwright && npx playwright install chromium）
// 状态：未在作者的沙箱里验证过（沙箱装不了 playwright）；第一次在你电脑或 GitHub Actions 上跑时，如果报错，把输出发给我。
const {chromium}=require('playwright'); const {execFileSync}=require('child_process'); const path=require('path'), fs=require('fs'), os=require('os');
const ROOT=path.join(__dirname,'..');
const SUITES=[
  {name:'阅读器（单文件版）',expect:462,make:()=>{ const out=path.join(os.tmpdir(),'fubi_suite1.html');
    execFileSync('python3',['-I',path.join(ROOT,'生成','自测','注入.py'),path.basename(out),'生成/自测_两本书.js'],{env:{...process.env,FUBI_OUT:os.tmpdir()+'/'},cwd:ROOT}); return out; }},
  {name:'阅读器（服务端模式）',expect:64,make:()=>{ const out=path.join(os.tmpdir(),'fubi_suite2.html');
    execFileSync('python3',['-I',path.join(ROOT,'生成','自测','服务端页面.py')],{env:{...process.env,FUBI_OUT:os.tmpdir()+'/'},cwd:ROOT}); return path.join(os.tmpdir(),'自测_服务端.html'); }},
];
(async()=>{ const br=await chromium.launch(); let bad=0;
  for(const s of SUITES){ const file=s.make(); if(!fs.existsSync(file)){ console.log('✗',s.name,'没生成测试页面',file); bad++; continue; }
    const ctx=await br.newContext({viewport:{width:390,height:844}}), pg=await ctx.newPage(); pg.on('pageerror',async e=>{
      /* 页面错误：除了消息，还打印调用栈、出错那一行的源码、以及最近记下的一项测试，方便在 CI 日志里直接定位 */
      const last=await pg.evaluate(()=>window.__LAST).catch(()=>'?'); const st=(e.stack||'').split('\n').slice(0,5).join(' | ');
      console.log('  页面错误：',e.message,'\n    调用栈：',st,'\n    最近记下的测试：',last);
      try{ const m=(e.stack||'').match(/\.html:(\d+):(\d+)/); if(m){ const ln=fs.readFileSync(file,'utf8').split('\n')[+m[1]-1]||''; const c=+m[2]; console.log('    出错处源码：',ln.slice(Math.max(0,c-90),c+60).replace(/\s+/g,' ')); } }catch(_){} });
    await pg.goto('file://'+file);
    try{ await pg.waitForFunction(()=>window.__RESULT,null,{timeout:600000}); }catch(e){ console.log('✗',s.name,'超时，没有结果'); bad++; await ctx.close(); continue; }
    const r=await pg.evaluate(()=>window.__RESULT); console.log((r.failed.length?'✗ ':'✓ ')+s.name+`  ${r.pass}/${r.total}`);
    r.failed.forEach(f=>console.log('   ✗',f.name,f.detail||'')); if(r.failed.length) bad++;
    await ctx.close(); }
  await br.close(); process.exit(bad?1:0); })();
