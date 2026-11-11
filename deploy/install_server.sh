#!/usr/bin/env bash
# 在服务器上安装或升级伏笔（OpenCloudOS / CentOS 系，需要 root）。
# 用法：bash install_server.sh /root/fubi-0.3.0-dev.tar.gz
# 第一次运行会建好用户、目录、配置文件模板和系统服务；之后每次升级同一条命令。
# 不会动服务器上的其他程序（OpenClaw 等）；不装 Docker；只用 8080 端口。
set -euo pipefail
PKG="${1:?用法：bash install_server.sh <安装包.tar.gz>}"; [ -f "$PKG" ] || { echo "找不到 $PKG"; exit 1; }
[ "$(id -u)" = 0 ] || { echo "需要 root"; exit 1; }
if ss -tln | awk '{print $4}' | grep -q ':8080$' && ! systemctl is-active --quiet fubi; then echo "8080 端口已被别的程序占用，先别装，把这条信息发给作者"; exit 1; fi
id fubi >/dev/null 2>&1 || useradd --system --home-dir /var/lib/fubi --shell /sbin/nologin fubi
mkdir -p /opt/fubi/releases /var/lib/fubi /etc/fubi /var/backups/fubi /var/log/fubi
VER=$(tar -xzOf "$PKG" VERSION); DIR="/opt/fubi/releases/$VER-$(date +%Y%m%d%H%M%S)"
mkdir -p "$DIR"; tar -xzf "$PKG" -C "$DIR" --no-same-owner
chmod -R u=rwX,go=rX "$DIR"; chown -R root:root "$DIR"   # 包里的权限可能是仅所有者可读；程序文件让低权限用户 fubi 能读、不能改
find "$DIR" -name __pycache__ -prune -o -type f -name "*.sh" -exec chmod 755 {} +
if [ ! -f /etc/fubi/fubi.env ]; then
  cp "$DIR/deploy/.env.example" /etc/fubi/fubi.env
  echo "FUBI_DATA=/var/lib/fubi" >> /etc/fubi/fubi.env
  echo "FUBI_HOST=0.0.0.0" >> /etc/fubi/fubi.env; echo "FUBI_PORT=8080" >> /etc/fubi/fubi.env
  echo "已生成 /etc/fubi/fubi.env。模型密钥请用 nano /etc/fubi/fubi.env 自己填，不要发给任何人。"
fi
# 升级时：新版本多出来的配置项，只"追加缺少的"，绝不覆盖你已经填好的（比如密钥、授权码）
for K in FUBI_AUTH FUBI_ADMIN_EMAILS FUBI_SMTP_HOST FUBI_SMTP_PORT FUBI_SMTP_USER FUBI_SMTP_PASS FUBI_SMTP_FROM; do
  if ! grep -q "^$K=" /etc/fubi/fubi.env; then L=$(grep "^$K=" "$DIR/deploy/.env.example" | head -1); [ -n "$L" ] && { echo "$L" >> /etc/fubi/fubi.env; echo "已追加配置项 $K"; }; fi
done
chmod 640 /etc/fubi/fubi.env; chown root:fubi /etc/fubi/fubi.env; chown -R fubi:fubi /var/lib/fubi
# 切换到新版本：current 指向新目录，保留上一版做回滚
PREV=""; if [ -L /opt/fubi/current ]; then T=$(readlink /opt/fubi/current || true); [ -d "$T" ] && [ "$T" != "$DIR" ] && PREV="$T"; fi   # 只认真实存在的上一版，防止指向自己
rm -f /opt/fubi/current; ln -s "$DIR" /opt/fubi/current
[ -n "$PREV" ] && echo "$PREV" > /opt/fubi/previous
chown fubi:fubi /var/backups/fubi /var/log/fubi; chmod 750 /var/backups/fubi /var/log/fubi   # 备份由低权限用户 fubi 写
# 先留一份旧的服务配置：回滚时代码和配置要一起退回去（11-03 的教训：只退代码，新配置配旧代码，服务起不来）
[ -f /etc/systemd/system/fubi.service ] && cp /etc/systemd/system/fubi.service /opt/fubi/fubi.service.prev
# 新配置里声明的"可写目录"必须先存在，否则 systemd 会因为找不到目录直接拒绝启动（status=226/NAMESPACE）。以后再加目录不用改这里
for P in $(grep -E '^ReadWritePaths=' "$DIR/deploy/fubi.service" | head -1 | cut -d= -f2-); do [ -e "$P" ] || { mkdir -p "$P" && chown fubi:fubi "$P" && echo "已创建目录 $P"; }; done
cp "$DIR/deploy/fubi.service" /etc/systemd/system/fubi.service
cp "$DIR/deploy/fubi-backup.service" "$DIR/deploy/fubi-backup.timer" "$DIR/deploy/fubi-monitor.service" "$DIR/deploy/fubi-monitor.timer" /etc/systemd/system/   # 每天 03:30 备份；每 2 分钟巡检
systemctl daemon-reload; systemctl enable fubi >/dev/null 2>&1; systemctl enable --now fubi-backup.timer fubi-monitor.timer >/dev/null 2>&1
systemctl restart fubi
for i in $(seq 1 40); do sleep 2; if curl -fs http://127.0.0.1:8080/api/health >/dev/null 2>&1; then
  echo "✓ 启动成功：$(curl -s http://127.0.0.1:8080/api/health | head -c 200)"; 
  ls -dt /opt/fubi/releases/* | tail -n +4 | xargs -r rm -rf   # 只保留最近 3 个版本
  exit 0; fi; done
echo "✗ 80 秒内没有起来，自动回滚到上一版"
if [ -n "$PREV" ] && [ -d "$PREV" ]; then rm -f /opt/fubi/current; ln -s "$PREV" /opt/fubi/current; [ -f /opt/fubi/fubi.service.prev ] && cp /opt/fubi/fubi.service.prev /etc/systemd/system/fubi.service && systemctl daemon-reload; systemctl restart fubi; echo "已回滚到 $PREV（服务配置也已退回）"; else systemctl stop fubi; echo "没有上一版可回滚，服务已停止"; fi
journalctl -u fubi -n 30 --no-pager; exit 1
