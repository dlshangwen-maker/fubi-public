#!/usr/bin/env bash
# 只读检查：不改任何东西，只是看这台服务器能不能装伏笔。把整段输出贴给作者。
# 在腾讯云控制台的"免密登录"网页终端里，整段复制粘贴执行。
echo "== 系统 ==";        grep -E '^(PRETTY_NAME|VERSION_ID)=' /etc/os-release
echo "== 内存 ==";        free -h | head -2
echo "== 磁盘 ==";        df -h / | tail -2
echo "== Docker ==";      (docker --version && docker compose version) 2>&1 | head -3
echo "== 正在运行的容器 =="; docker ps --format '{{.Names}}  {{.Image}}  {{.Ports}}' 2>&1 | head -10
echo "== 已占用的端口 =="; (ss -tlnH 2>/dev/null || netstat -tln 2>/dev/null) | awk '{print $4}' | sed 's/.*://' | sort -un | tr '\n' ' '; echo
echo "== 能不能访问外网 =="
for u in https://github.com https://api.deepseek.com https://pypi.org; do printf '%s  ' "$u"; curl -s -o /dev/null --max-time 8 -w '%{http_code}\n' "$u" || echo 失败; done
echo "== Python/Git =="; python3 --version 2>&1; git --version 2>&1
