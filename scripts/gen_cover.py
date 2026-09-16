#!/usr/bin/env python3
"""生成财经/自媒体封面（纯设计型，不抽帧）。

布局：深色底 + 装饰色块 + 可选超大核心数字（视觉锤）+ 大字标题 + 数据行。

注意：封面标题（--title）应由调用方（AI）从发布候选标题里挑「最吸引人」的那条，
不要默认用带数字的那条。--metric（超大数字视觉锤）为可选：只在所选标题本身
带强数字（跌幅/金额/倍数）时才传；悬念/反常识类标题不带数字时省略 --metric 即可。
详见 references/publish-guide.md §4「封面标题怎么选」。

用法:
  python gen_cover.py \
      --title "传统资产正在被重定价" \
      --metric "8万亿" --unit "元" \
      --sub "× 算力底座光纤化 · 中美五个产业信号" \
      --size 1280x720 --accent gold \
      --slug "传统资产重定价-算力光纤化"

--size 支持 16:9(横版 B站) 与 9:16(竖版 抖音/视频号/小红书)。
--accent 强调色：gold(默认) / red(涨) / green(跌)。
--slug 内容概要：提供后自动拼「cover_横版_16x9|cover_竖版_9x16_概要_时间戳.png」，无需手写 --out；
       不传 --slug 也不传 --out 时回退为 cover.png（向后兼容）。
"""
import argparse
import os
import re
from datetime import datetime

from PIL import Image, ImageDraw, ImageFont

FONT_CANDIDATES = [
    "/System/Library/Fonts/PingFang.ttc",               # macOS 苹方
    "/System/Library/Fonts/STHeiti Medium.ttc",
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
    "/System/Library/Fonts/Supplemental/Songti.ttc",
    "C:/Windows/Fonts/msyh.ttc",                        # Windows
    "C:/Windows/Fonts/simhei.ttf",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",  # Linux
]

ACCENTS = {
    "gold": (232, 182, 90),
    "red": (229, 72, 77),     # A 股涨=红
    "green": (48, 164, 108),  # A 股跌=绿
}
BG = (9, 18, 30)            # 深蓝黑
TITLE_COLOR = (240, 246, 255)
SUB_COLOR = (148, 158, 175)


def find_font():
    for p in FONT_CANDIDATES:
        if os.path.exists(p):
            return p
    return None


def load_font(path, size):
    if not path:
        return ImageFont.load_default()
    for idx in (5, 4, 0):  # 苹方 ttc：5=Semibold, 4=Medium, 0=Regular
        try:
            return ImageFont.truetype(path, size, index=idx)
        except Exception:
            continue
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()


def make_cover(title, metric, unit, sub, size, accent, out):
    W, H = size
    acc = ACCENTS[accent]
    portrait = H > W

    # 背景 + 装饰色块（半透明圆，增加设计感不抢字）
    img = Image.new("RGB", (W, H), BG)
    dr = ImageDraw.Draw(img, "RGBA")
    R = int(max(W, H) * 0.55)
    dr.ellipse([W - R, -R // 2, W + R // 2, R], fill=(*acc, 30))
    dr.ellipse([-R // 2, H - R, R // 2, H + R // 2], fill=(88, 166, 255, 22))
    img = img.convert("RGB")
    d = ImageDraw.Draw(img)

    font_path = find_font()
    fnt_metric = load_font(font_path, int(W * 0.22))
    fnt_unit = load_font(font_path, int(W * 0.06))
    fnt_title = load_font(font_path, int(W * 0.08))
    fnt_sub = load_font(font_path, int(W * 0.035))

    pad_x = int(W * 0.07)

    # 估算各元素占高（含行距）
    metric_h = int(W * 0.26) if metric else 0
    title_h = int(W * 0.12) if title else 0
    sub_h = int(W * 0.05) if sub else 0
    gap1 = int(W * 0.05) if metric and title else 0
    gap2 = int(W * 0.04) if (metric or title) and sub else 0
    block_h = metric_h + gap1 + title_h + gap2 + sub_h

    # 内容块垂直居中（竖版略微上移，留出底部安全区）
    y = (H - block_h) // 2
    if portrait:
        y = max(y, int(H * 0.16))

    cursor = y
    if metric:
        d.text((pad_x, cursor), metric, font=fnt_metric, fill=acc)
        mw = d.textlength(metric, font=fnt_metric)
        # 单位与数字底部基线对齐
        d.text((pad_x + mw + int(W * 0.025), cursor + metric_h - int(W * 0.08)),
               unit, font=fnt_unit, fill=acc)
        cursor += metric_h + gap1
    if title:
        d.text((pad_x, cursor), title, font=fnt_title, fill=TITLE_COLOR)
        cursor += title_h + gap2
    if sub:
        d.text((pad_x, cursor), sub, font=fnt_sub, fill=SUB_COLOR)

    # 底部金色细线（收边）
    y_line = H - int(H * 0.07)
    d.line([(pad_x, y_line), (W - pad_x, y_line)], fill=(*acc, 70))

    img.save(out, quality=95)
    print(f'封面 -> {out}  {W}x{H}  ({os.path.getsize(out) / 1024:.0f} KB)')


# 尺寸 → 文件名前缀（用于自动命名，区分横竖版）
SIZE_LABEL = {
    (1280, 720): "cover_横版_16x9",
    (1080, 1920): "cover_竖版_9x16",
}


def slugify(s: str) -> str:
    """把内容概要转成安全文件名片段：空白与文件系统非法字符 → '-'，去首尾连字符。"""
    s = re.sub(r'[\s/\\:*?"<>|]+', '-', s)
    return s.strip('-')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--title', required=True)
    ap.add_argument('--metric', default='')
    ap.add_argument('--unit', default='')
    ap.add_argument('--sub', default='')
    ap.add_argument('--size', default='1280x720')
    ap.add_argument('--accent', default='gold', choices=list(ACCENTS))
    ap.add_argument('--out', default=None, help='自定义输出文件名（覆盖 slug 自动命名）')
    ap.add_argument('--slug', default=None, help='内容概要；提供后自动拼「前缀_概要_时间戳.png」')
    args = ap.parse_args()

    w, h = map(int, args.size.split('x'))
    if args.out:
        out = args.out
    elif args.slug:
        prefix = SIZE_LABEL.get((w, h), f"cover_{w}x{h}")
        ts = datetime.now().strftime("%Y%m%d-%H%M")
        out = f"{prefix}_{slugify(args.slug)}_{ts}.png"
    else:
        out = "cover.png"
    make_cover(args.title, args.metric, args.unit, args.sub, (w, h), args.accent, out)
