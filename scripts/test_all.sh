#!/usr/bin/env bash
# 一条命令跑完全部测试。用法：bash scripts/test_all.sh      任何一步红了就停，退出码非 0。
set -euo pipefail; cd "$(dirname "$0")/.."
echo "== 1/4 构建测试页面 ==";          FUBI_NO_BUNDLE=1 python3 生成/build_demo.py | tail -1   # 只生成测试用的单文件版；完整 demo 要读原始电子书，本机用 python3 生成/build_demo.py
echo "== 2/4 服务端单元测试 ==";        (cd server && rc=0; python3 -m unittest discover -s tests > /tmp/fubi_unit.log 2>&1 || rc=$?; grep -E '^(ERROR|FAIL):' /tmp/fubi_unit.log || true; tail -3 /tmp/fubi_unit.log | grep -vE 'ResourceWarning' || true; if [ "$rc" != 0 ]; then echo '---- 失败详情（日志最后 80 行）----'; tail -80 /tmp/fubi_unit.log; fi; exit $rc)
echo "== 3/4 阅读器启动检查（node） =="; node 生成/自测/启动检查_node.js | tail -3
echo "== 4/4 阅读器浏览器自测 ==";      if command -v npx >/dev/null && node -e "require('playwright')" 2>/dev/null; then node scripts/run_browser_tests.js; else echo "（没装 playwright，跳过；装法：npm i -D playwright && npx playwright install chromium）"; fi
echo "全部通过"
