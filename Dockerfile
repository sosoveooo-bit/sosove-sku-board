FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    SKU_BOARD_DATA_DIR=/app/data \
    AI_IMAGE_JAPANESE_FONT_PATH=/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends fonts-noto-cjk \
    && rm -rf /var/lib/apt/lists/*

COPY sku_board/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY sku_board /app/sku_board
COPY shopline_monitor /app/shopline_monitor
COPY open-image-prompts /app/open-image-prompts
RUN mkdir -p /app/data

EXPOSE 8793

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8793/api/health', timeout=3).read()"

CMD ["python", "-m", "sku_board.server", "--host", "0.0.0.0", "--port", "8793"]
