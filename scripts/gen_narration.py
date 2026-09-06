#!/usr/bin/env python3
"""从口播音频目录读每段真实时长，配合 vo/script.json 的 scene/text，生成 src/narration.json。

单一数据源原则：口播稿在 vo/script.json，音频时长是唯一时间基准，
字幕 + 场景帧数全部由它派生（src/timeline.ts 消费 narration.json）。

用法:
  python gen_narration.py [public/vo]
"""
import json
import os
import subprocess
import sys


def root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def dur(path: str) -> float:
    out = subprocess.run(
        ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
         '-of', 'csv=p=0', path],
        capture_output=True, text=True, check=True,
    )
    return float(out.stdout.strip())


def find_audio(audio_dir: str, sid: str):
    for ext in ('.mp3', '.wav', '.m4a'):
        p = os.path.join(audio_dir, f'{sid}{ext}')
        if os.path.exists(p):
            return p
    return None


def main() -> int:
    r = root()
    audio_dir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(r, 'public', 'vo')
    script_path = os.path.join(r, 'vo', 'script.json')
    narration_path = os.path.join(r, 'src', 'narration.json')

    cfg = json.load(open(script_path, encoding='utf-8'))
    recs = []
    total = 0.0
    for seg in cfg['segments']:
        sid, scene, text = seg['id'], seg['scene'], seg['text']
        audio = find_audio(audio_dir, sid)
        if not audio:
            print(f'缺音频: {sid}', file=sys.stderr)
            return 1
        d = dur(audio)
        recs.append({'id': sid, 'scene': scene, 'text': text, 'dur': round(d, 3)})
        total += d
        print(f'{sid} {scene:<24} {len(text):>4}字  {d:6.2f}s')

    with open(narration_path, 'w', encoding='utf-8') as f:
        json.dump(recs, f, ensure_ascii=False, indent=2)

    print(f'\n总语音时长 {total:.1f}s  段数 {len(recs)}')
    print(f'narration -> {narration_path}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
