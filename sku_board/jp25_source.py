"""Literal Japanese bullet sections for JP25; Japanese commas are not point boundaries."""
import re

MAIN = re.compile(r"^(?:主なポイント|主な特徴|メインポイント|主要ポイント|主な売りポイント)\s*[：:]?$")
DETAIL = re.compile(r"^(?:サブポイント|その他のポイント|ディテール|補足ポイント)\s*[：:]?$")
STOP = re.compile(r"^(?:图片要求|图像要求|严格注意|严格要求|全局要求|设计要求|视觉要求|输出要求|配色|模特要求|"
                  r"产品名称|商品名|画像(?:の)?(?:要件|条件|仕様)|デザイン(?:の)?(?:要件|条件)|モデル(?:の)?条件|"
                  r"注意事項|サイズ表|权威背书|認証|保証|レビュー|お客様の声)")
ITEM = re.compile(r"^\s*(?:\d+[.．、)）]\s*|[·・•●\-*]\s*)(.+)$")


def structured_points(source):
    """Return a recognized section's complete records, otherwise defer to the legacy parser."""
    lines = str(source or "").replace("\r", "\n").splitlines()
    if not any(MAIN.fullmatch(line.strip()) or DETAIL.fullmatch(line.strip()) for line in lines):
        return []
    result, kind, current = [], "", None

    def flush():
        nonlocal current
        if current:
            title, body = current
            description = "\n".join(body).strip()
            result.append({"kind": kind, "title": title, "description": description,
                           "sourceVerbatim": title + ("\n" + description if description else ""),
                           "sourceProvided": True, "sourceType": "selling_point"})
        current = None

    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        if MAIN.fullmatch(line) or DETAIL.fullmatch(line):
            flush()
            kind = "main" if MAIN.fullmatch(line) else "detail"
            continue
        if STOP.match(line):
            flush()
            kind = ""
            continue
        if not kind:
            continue
        item = ITEM.match(line)
        if item:
            flush()
            current = (item.group(1).strip(), [])
        elif current:
            current[1].append(line)
    flush()
    return result
