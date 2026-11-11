#!/usr/bin/env bash
# 打安装包：bash scripts/make_release.sh   →  dist/fubi-<版本>.tar.gz
# 服务器连不上 GitHub，所以用"本机打包 → 上传 → 服务器解压"。包里只放运行需要的东西，
# 不放：带版权的原始电子书、密钥、测试、手工备份、浏览器测试页面。
set -euo pipefail; cd "$(dirname "$0")/.."
V=$(cat VERSION); OUT="dist/fubi-$V.tar.gz"; mkdir -p dist
tar --mode='u=rwX,go=rX' --owner=0 --group=0 --exclude='__pycache__' --exclude='*备份*' --exclude='server/tests' --exclude='生成/自测' --exclude='server_data' --exclude='*.pyc' \
    -czf "$OUT" VERSION server Demo/模板.html 生成 文本数据 deploy/install_server.sh deploy/fubi.service deploy/fubi-backup.service deploy/fubi-backup.timer deploy/fubi-monitor.service deploy/fubi-monitor.timer deploy/.env.example
echo "$OUT  $(du -h "$OUT" | cut -f1)  版本 $V"
