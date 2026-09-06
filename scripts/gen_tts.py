#!/usr/bin/env python3
"""用 edge-tts（微软 Azure 神经网络语音，免费/无需 key/秒级）批量合成口播。

读 vo/script.json 的 segments，逐段合成到 public/vo/<id>.mp3，
再 loudnorm 统一响度 -16 LUFS / TP -1.5dB，48k 单声道。

常用中文语音（`python -c "import asyncio,edge_tts;asyncio.run(edge_tts.list_voices())"`
可列全量，按 Locale 过滤 zh-CN / zh-TW / zh-HK）：
  女声：zh-CN-XiaoxiaoNeural(晓晓) zh-CN-XiaoyiNeural(晓伊)
        zh-TW-HsiaoChenNeural(晓臻) zh-TW-HsiaoYuNeural(晓雨)
  男声：zh-CN-YunxiNeural(云希) zh-CN-YunyangNeural(云扬) zh-CN-YunjianNeural(云健)
        zh-TW-YunJheNeural

用法:
  python gen_tts.py [--voice zh-CN-XiaoxiaoNeural] [--rate +0%] [--skip-existing]
"""
import argparse
import asyncio
import json
import os
import subprocess

import edge_tts

DEFAULT_VOICE = 'zh-CN-XiaoxiaoNeural'


def root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


async def synth_one(seg, voice, rate, out_mp3):
    c = edge_tts.Communicate(seg['text'], voice=voice, rate=rate)
    await c.save(out_mp3)


def loudnorm(raw, out):
    subprocess.run(
        ['ffmpeg', '-y', '-v', 'error', '-i', raw,
         '-af', 'loudnorm=I=-16:TP=-1.5:LRA=11',
         '-ar', '48000', '-ac', '1', '-b:a', '128k', out],
        check=True,
    )


def dur_of(path):
    out = subprocess.run(
        ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
         '-of', 'csv=p=0', path],
        capture_output=True, text=True, check=True,
    )
    return float(out.stdout.strip())


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--voice', default=DEFAULT_VOICE)
    ap.add_argument('--rate', default='+0%')
    ap.add_argument('--skip-existing', action='store_true')
    args = ap.parse_args()

    r = root()
    cfg = json.load(open(os.path.join(r, 'vo', 'script.json'), encoding='utf-8'))
    outdir = os.path.join(r, 'public', 'vo')
    os.makedirs(outdir, exist_ok=True)

    # 若 script.json 顶层有 voice/rate，可覆盖命令行默认
    voice = cfg.get('voice') or args.voice
    rate = cfg.get('rate') or args.rate

    segs = cfg['segments']
    for i, seg in enumerate(segs, 1):
        sid = seg['id']
        out = os.path.join(outdir, f'{sid}.mp3')
        if args.skip_existing and os.path.exists(out):
            print(f'[{i}/{len(segs)}] {sid} 已存在，跳过', flush=True)
            continue
        raw = os.path.join('/tmp', f'{sid}_raw.mp3')
        await synth_one(seg, voice, rate, raw)
        loudnorm(raw, out)
        d = dur_of(out)
        print(f'[{i}/{len(segs)}] {sid} {len(seg["text"])}字 -> {d:.2f}s',
              flush=True)

    print(f'完成 {len(segs)} 段，voice={voice} rate={rate}，输出 {outdir}')


if __name__ == '__main__':
    asyncio.run(main())
