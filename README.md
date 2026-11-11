# 伏笔

伏笔是一个不剧透的读书工具：不替读者读书，陪读者把原文读完。

读者读到哪里，系统就只讲到哪里。点开任意一段，可以看到入门、标准、深入三档解释，内容只依据这一段及之前的原文生成。书里埋下的问题会在页边标成"伏笔"，读到答案处自动揭晓；每本书有一条主线，揭晓一处伏笔就拼上一块。放下一段时间再打开，会先回顾上次读到哪里、前面讲了什么。读完留下的划线、想法和猜想，整理成读书札记。

读者也可以导入自己的书（epub、txt、pdf、docx 等十几种格式），由模型逐步生成解释和回顾；读书时提出的问题，由模型按当前阅读进度回答，不涉及后文。

## 现状

当前版本 0.3.0-dev，处于邀请制的小范围试用阶段。账号（邮箱加邀请码）、用户协议与隐私政策、使用情况记录、日志、监控告警、每日备份、意见反馈和管理后台都已具备。书架上有五本精编书：《红楼梦》《逻辑哲学论》《呐喊》《李鸿章传》《巴斯克维尔的猎犬》，均为公有领域作品，伏笔、主线和逐段解释是预先做好的。

目前没有域名和 HTTPS，登录密码是明文传输，所以只适合在认识的少数人之间试用，不适合对外公开。

## 技术概览

服务端用 Python 标准库写成，基于多线程 HTTP 服务，不依赖任何框架；数据存在 SQLite 里。阅读器是单个 HTML 文件（`Demo/模板.html`，原生 JavaScript，没有构建工具），书的数据由 `server/packer.py` 打包后嵌进页面。

所有模型调用都从 `server/model.py` 的 `call()` 进出。它支持 OpenAI 兼容接口和 Anthropic 接口，换模型只改环境变量；没有配置模型时使用假模型，其余功能照常可用。每次调用都会记账，全站每日调用数和单本书调用数都有上限。

只用标准库就能启动。以下依赖是可选的，缺少时对应功能会降级或提示：

```
pypdf  opencc-python-reimplemented  charset-normalizer  pillow     # Python 包
tesseract + poppler                                                # 扫描版 PDF 文字识别
LibreOffice                                                        # doc、rtf、odt、wps
calibre                                                            # mobi、azw3、fb2
```

## 目录

```
server/        服务端。app.py 是入口；model.py 模型调用；pipeline.py 生成队列；
               importer.py 导入；accounts.py 账号；monitor.py 监控；backup.py 备份
Demo/模板.html  阅读器（单文件）
生成/          内容生产：build_demo.py 打包脚本、流水线提示词、各书生成结果、自测脚本
文本数据/       各书全文
deploy/        安装脚本、systemd 单元、部署清单；另有 Docker 文件
scripts/       一键测试、打包、端到端检查
实验/ 样稿/     早期的提问边界实验和界面样稿，与运行无关
```

## 本地运行

需要 Python 3.10 或以上。在仓库根目录执行：

```
python3 server/app.py
```

然后打开 `http://127.0.0.1:8080`。数据默认存在 `server_data/`，可以用 `FUBI_DATA` 改位置，用 `FUBI_PORT` 改端口。默认使用假模型，不需要任何密钥。

要接真实模型，设置下面几个环境变量，再到后台点"检查模型"：

```
FUBI_MODEL_PROVIDER=openai          # DeepSeek、通义、Kimi、智谱、OpenAI 都选 openai；Claude 选 anthropic
FUBI_MODEL_BASE_URL=...
FUBI_MODEL_API_KEY=...
FUBI_MODEL_NAME=...
```

## 测试

一条命令跑完全部：

```
bash scripts/test_all.sh
```

它依次做四件事：构建测试用页面，跑服务端单元测试，用 node 做阅读器启动检查，用无头浏览器跑阅读器自测。第四步需要 playwright：

```
npm i --no-save playwright && npx playwright install chromium
```

没有安装 playwright 时，第四步会跳过并提示。服务端测试也可以单独跑：

```
cd server && python3 -m unittest discover -s tests
```

每次推送，GitHub Actions 会自动跑同一套测试（`.github/workflows/test.yml`）。注意：完整的演示页 `Demo/伏笔_demo.html` 需要本机的原始电子书（`原始资料/`，带版权，不入库），所以自动测试只构建不含它的单文件版。

写会走找书或下载的测试时，要先给 `search.opener` 装上假网络，否则测试会真的访问外网，结果取决于网速。

## 打包与部署

```
bash scripts/make_release.sh
```

生成 `dist/fubi-<版本号>.tar.gz`。线上服务器用 `deploy/install_server.sh` 解压并切换版本，用 systemd 管理服务，升级失败会自动回退到上一版。完整步骤和备份、恢复、告警的说明在 `deploy/部署清单.md`。

仓库里还保留了 Docker 的配置（`deploy/Dockerfile`、`deploy/docker-compose.yml`），但线上实际没有使用，近期也没有验证过。

## 配置

所有配置都走环境变量，完整列表和说明见 `deploy/.env.example` 与 `server/config.py` 开头的注释。常用的有：

```
FUBI_AUTH=1                  开启账号（邮箱加邀请码注册）
FUBI_ADMIN_EMAILS            可以进入 /admin 后台的邮箱，逗号分隔
FUBI_SMTP_*                  发信（找回密码、告警邮件）
FUBI_MODEL_DAILY_CALLS       全站每日模型调用上限
FUBI_MODEL_BOOK_CALLS        单本书的模型调用上限
FUBI_WORKERS                 同时跑几个生成任务
```

密钥和 `.env` 只放在服务器上，不要提交到仓库。`.gitignore` 已排除密钥、运行数据、原始电子书、手工备份和生成物。

## 文档

| 文件 | 内容 |
|---|---|
| `想做的功能清单.md` | 讨论过但还没做的功能 |
| `发布约定.md` | 版本号、分支、发布前检查、回滚 |
| `CHANGELOG.md` | 版本变更记录 |
| `deploy/部署清单.md` | 第一次部署、升级、备份与恢复 |
| `生成/流水线/流水线总说明.md` | 内容生成流水线：每一步做什么、提示词在哪里 |
| `伏笔标准_v1.1.md` | 什么算伏笔，怎么筛 |
| `提问回答边界_v1.md` | 读者提问时，哪些能答、怎么答才不剧透 |
| `设计规范_v2.md` | 界面设计规范 |
| `伏笔_产品方案_v2.0.md` | 产品方案 |

`server/README.md` 写于第二阶段，部分内容已经过时（例如账号、测试数量），以本文和代码为准。

## 使用说明

本仓库公开仅供查看和评阅，没有附带开源许可证：未经许可，不得复制、修改或分发其中的代码和内容。
