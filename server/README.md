# 伏笔 · 服务端（第二阶段骨架，v0.2.0，2026-10-26）

## 它做什么

一台服务器上跑一个程序，读者用手机浏览器打开就能用：

- **书架**：五本精编书（伏笔、主线、解释都有）+ 读者自己的书（导入的文件、找书下载的公版书）。书自带封面的（epub、扫描版 PDF）显示封面。
- **找书**：书架标题右边"找书 · 导入"。只有搜索框和热门搜索——**我们不存书**：服务器替读者去古登堡计划、维基文库搜，读者点"下载到书架"，服务器下载后和导入的文件一样处理。作者去世不满 50 年的书列出来但不能下载。点结果看书的信息和介绍，下面列出下载来源，每个都能单独下载；同一本书有几个来源、每个来源有几条下载路（主站、镜像、epub、纯文本），一条不行自动换下一条。外文书先翻译（译名表 → 逐章翻译），译完才生成解释。
- **调整章节**：读者自己的书（导入的、下载的）分章不对，可以改章名、合并、在某一段前分章；已经生成的解释尽量保留，只重做被切开的部分。
- **导入**：epub、txt、pdf（文字版和扫描版）、docx、doc、rtf、odt、wps、html、md、mobi、azw3、fb2。导入的书只有导入的人能看到。
- **阅读记录**：划线、想法、进度存在服务器上，按设备区分（账号以后再做）。
- **生成**：导入的书自动排队生成解释卡片、剧透复查、回顾、词语表。中断了会从断点接着跑。
- **自由提问**：读者问的问题如果没有预先写好的回答，就交给模型，按阅读进度回答，不剧透。
- **后台**：用管理员账号（`FUBI_ADMIN_EMAILS` 里的邮箱）登录后打开 `/admin`，能看到模型能不能用、今天调用了多少次、生成队列、失败的任务（可以重试）。

## 给了模型 API 就能跑

改 `deploy/.env` 里的三行，重启就行，代码一行都不用动：

```
FUBI_MODEL_PROVIDER=openai                  # DeepSeek、通义、Kimi、智谱、OpenAI 都选 openai；Claude 选 anthropic
FUBI_MODEL_BASE_URL=https://api.deepseek.com
FUBI_MODEL_API_KEY=sk-...
FUBI_MODEL_NAME=deepseek-flash
```

重启后打开后台，点"检查模型"，看到"可以用"就说明通了。没配模型时是"假模型"：所有功能照常能用，只是导入的书暂时没有解释。

## 部署（一条命令）

在 Read Book 文件夹里：

```
cp deploy/.env.example deploy/.env      # 然后改 .env
docker compose -f deploy/docker-compose.yml up -d --build
```

装好后打开 `http://服务器地址:8080/`。数据都在 `deploy/data/` 里，备份这个文件夹就行。要用 HTTPS 就看 `deploy/Caddyfile`。

不用 Docker 也能跑，只要有 Python 3.10 以上：`python3 server/app.py`（没有第三方依赖。装了 pypdf、opencc 会更好；扫描版 PDF 需要 tesseract，doc 文件需要 LibreOffice，mobi 需要 calibre）。

## 找书

`server/search.py`。搜索走两个公开接口：古登堡的书目查询 Gutendex（https://gutendex.com）、维基文库的 MediaWiki 搜索；下载走古登堡的 epub 和维基文库官方导出工具 ws-export。地址都能用环境变量换（`FUBI_GUTENDEX`、`FUBI_WIKISOURCE_API`、`FUBI_WSEXPORT`）。服务器只按"来源 + 编号"自己拼下载地址，不接受读者传来的网址。同一本书 30 天内只真的下载一次，多个读者共用。热门搜索：没有记录时用 `server/hot.json`，有了以后按最近 30 天的真实搜索次数排。

## 测试

```
cd server && python3 -m unittest discover -s tests     # 87 项：模型层、导入（每种格式 + 8 本真书）、生成队列、接口
```

阅读器的测试（在预览面板里跑）：
- `python3 生成/build_demo.py` 生成给用户的 demo `Demo/伏笔_demo.html`（服务端页面 + 网络桩，不用服务器就能点）和只给自测用的 `生成/自测/单文件版.html`。
- `python3 -I 生成/自测/注入.py 自测.html 生成/自测_两本书.js` 跑单文件版，374 项。
- `python3 -I 生成/自测/服务端页面.py` 跑服务端模式（找书、封面、调整章节等），49 项。

## 文件

| 文件 | 做什么 |
|---|---|
| `app.py` | 接口服务、阅读器页面、后台 |
| `books.py` | 书架：精编书、读者自己的书 |
| `search.py` / `hot.json` | 找书：搜索、热门搜索、下载 |
| `importer.py` | 把各种格式转成全文.json |
| `pipeline.py` | 生成队列：拆任务、排队、续跑、打包 |
| `model.py` | 模型调用层，唯一入口 `call()` |
| `tasks.py` | 每种模型任务用哪份提示词、怎么校验 |
| `packer.py` | 打包成阅读器格式（demo 也用这一份） |
| `db.py` / `config.py` | 数据库（SQLite）、配置（环境变量） |
| `chapters.py` | 调整章节（改名、合并、分章；已生成的内容跟着搬） |

## 还没做的（按计划）

- 账号：用户定了等上线前和验证码一起做。现在按设备区分，以后把设备号换成用户 id 就行，`progress` 表已经留好了。
- 导入的书自动出伏笔和主线：要等精编书攒够样本。现在读者可以自己划线提问，记成"我发现的伏笔"。
- 阅读器的自动测试搬到服务器上用无头浏览器跑：沙箱里装不了浏览器，部署后再做。
