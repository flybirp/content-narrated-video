#!/usr/bin/env python3
"""生成「发布资产预览页」：标题候选 + 标签 + 简介 + 横竖封面，base64 内嵌。

从 JSON 配置读取，一键生成 HTML 预览，供发稿前人工过目。

用法:
  python build_publish_page.py --config publish.json --out preview.html

config JSON 格式:
  {
    "title": "爱美客 · 发布资产预览",
    "subtitle": "成片 out/aimeike_final.mp4（4:13）",
    "titles": [
      {"kind": "数字钩子", "text": "...", "note": "抓涨跌幅度，抖音/B站通用"}
    ],
    "tags": ["#财经", "#A股", "#爱美客"],
    "intro": "……（简介正文，不含标签和免责）",
    "disclaimer": "以上为情景推演，不构成投资建议。",
    "covers": [
      {"label": "横版 1280×720（B站）", "path": "cover_横版_16x9.png"}
    ]
  }
"""
import argparse
import base64
import json
import os


def b64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def build(cfg, cfg_path, out):
    HERE = os.path.dirname(os.path.abspath(cfg_path))

    def resolve(p):
        return p if os.path.isabs(p) else os.path.join(HERE, p)

    titles_html = "".join(
        f"""
    <div class="card">
      <div class="tagline">{c.get('kind', '')}</div>
      <div class="t">{c['text']}</div>
      <div class="note">{c.get('note', '')}</div>
    </div>""" for c in cfg["titles"]
    )

    tags = cfg["tags"]
    tags_html = "".join(f'<span class="tag">{t}</span>' for t in tags)

    covers_html = ""
    for c in cfg.get("covers", []):
        data = b64(resolve(c["path"]))
        covers_html += f"""
    <div class="coverbox">
      <div class="clbl">{c['label']}</div>
      <img src="data:image/png;base64,{data}">
    </div>"""

    html = f"""<!DOCTYPE html>
<html lang="zh"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{cfg['title']}</title>
<style>
  body {{ background:#0d1117; color:#e6edf3; font-family:-apple-system,'PingFang SC',sans-serif;
         max-width:860px; margin:0 auto; padding:24px 20px 48px; }}
  h1 {{ font-size:20px; margin:0 0 4px; }}
  .sub {{ color:#8b949e; font-size:13px; margin-bottom:20px; }}
  h2 {{ font-size:15px; margin:26px 0 12px; color:#ffa657; }}
  .card {{ background:#161b22; border:1px solid #30363d; border-radius:10px;
          padding:14px 16px; margin-bottom:12px; }}
  .tagline {{ color:#58a6ff; font-size:12px; margin-bottom:6px; }}
  .t {{ font-size:17px; font-weight:600; line-height:1.5; }}
  .note {{ color:#8b949e; font-size:12.5px; margin-top:6px; }}
  .tag {{ display:inline-block; background:#1f6feb33; color:#58a6ff; border:1px solid #1f6feb55;
         padding:4px 10px; border-radius:14px; font-size:13px; margin:0 8px 8px 0; }}
  .intro {{ background:#161b22; border:1px solid #30363d; border-radius:10px;
          padding:14px 16px; font-size:14px; line-height:1.8; }}
  .dis {{ color:#f85149; font-size:12.5px; margin-top:8px; }}
  .covers {{ display:flex; gap:16px; align-items:flex-start; flex-wrap:wrap; }}
  .coverbox {{ flex:1 1 260px; min-width:240px; }}
  .coverbox img {{ width:100%; border-radius:10px; border:1px solid #30363d; }}
  .clbl {{ color:#8b949e; font-size:12px; margin:6px 0 4px; text-align:center; }}
</style></head><body>
  <h1>{cfg['title']}</h1>
  <div class="sub">{cfg.get('subtitle', '')}</div>

  <h2>① 标题（{len(cfg['titles'])} 候选，挑一个或改）</h2>
  {titles_html}

  <h2>② 自选标签（发前用 WebSearch 验证平台真实热度）</h2>
  <div>{tags_html}</div>

  <h2>③ 视频简介</h2>
  <div class="intro">{cfg['intro']}<br>{tags_html}<div class="dis">{cfg.get('disclaimer', '')}</div></div>

  <h2>④ 封面图</h2>
  <div class="covers">{covers_html}</div>
</body></html>"""

    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"预览页 -> {out} ({os.path.getsize(out) / 1024:.0f} KB)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True, help="publish.json 配置路径")
    ap.add_argument("--out", default="publish_preview.html")
    args = ap.parse_args()

    with open(args.config, encoding="utf-8") as f:
        cfg = json.load(f)
    build(cfg, args.config, args.out)
