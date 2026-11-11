# 伏笔服务端镜像。在 Read Book 文件夹里构建：docker build -f deploy/Dockerfile -t fubi .
# 只用 Python 标准库；系统包是给导入用的：OCR（扫描版 PDF）、LibreOffice（doc/rtf/odt/wps）、calibre（mobi/azw3/fb2）、poppler（pdftoppm/pdftotext）
FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 LANG=C.UTF-8 TZ=Asia/Shanghai
RUN apt-get update && apt-get install -y --no-install-recommends \
      tesseract-ocr tesseract-ocr-chi-sim tesseract-ocr-eng poppler-utils \
      libreoffice-writer-nogui calibre tzdata \
 && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir pypdf opencc-python-reimplemented charset-normalizer
WORKDIR /app
# 只拷服务需要的：服务代码、阅读器模板、精编书的数据和生成脚本、提示词和规则
COPY VERSION VERSION
COPY server/ server/
COPY Demo/模板.html Demo/模板.html
COPY 生成/ 生成/
COPY 文本数据/ 文本数据/
RUN find . -name '*备份*' -prune -exec rm -rf {} + ; find . -name '__pycache__' -prune -exec rm -rf {} + ; rm -rf server/tests/fixtures
ENV FUBI_DATA=/data FUBI_HOST=0.0.0.0 FUBI_PORT=8080
VOLUME /data
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s CMD python3 -c "import urllib.request,json;assert json.load(urllib.request.urlopen('http://127.0.0.1:8080/api/health',timeout=4))['ok']"
CMD ["python3","server/app.py"]
