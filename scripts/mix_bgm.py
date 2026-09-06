#!/usr/bin/env python3
"""把背景音乐混进已渲染好的视频。

成片方案：口播轨（-16 LUFS）保持原样，BGM 压到地板音量（比口播低约 10dB），
首尾淡入淡出。选无强旋律的 House/Ambient 曲目，低音量下不抢人声。

用法:
  python mix_bgm.py out/video.mp4 [bgm.mp3] [out/final.mp4]
"""
import os
import subprocess
import sys


def root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def probe_dur(path: str) -> float:
    out = subprocess.run(
        ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
         '-of', 'csv=p=0', path],
        capture_output=True, text=True, check=True,
    )
    return float(out.stdout.strip())


def main() -> int:
    r = root()
    video = sys.argv[1]
    bgm = sys.argv[2] if len(sys.argv) > 2 else os.path.join(r, 'vo', 'bgm', 'bgm.mp3')
    out = sys.argv[3] if len(sys.argv) > 3 else os.path.join(r, 'out', 'final.mp4')

    total = probe_dur(video)
    print(f'视频 {total:.2f}s  BGM {bgm}')

    # BGM：无限循环再截取视频长度，音量 -10dB，首尾淡入淡出。
    # -stream_loop -1 比 aloop 的 size 参数更稳。
    bgm_af = (
        f"volume=-10dB,"
        f"afade=t=in:st=0:d=2,"
        f"afade=t=out:st={total - 4:.3f}:d=4"
    )
    tmp_bgm = os.path.join('/tmp', 'bgm_ready.wav')
    subprocess.run(
        ['ffmpeg', '-y', '-stream_loop', '-1', '-i', bgm,
         '-t', f'{total:.3f}', '-af', bgm_af,
         '-ar', '48000', '-ac', '1', '-sample_fmt', 's16', tmp_bgm],
        check=True,
    )

    # 混音：视频流 copy，音频 = 口播 + BGM（amix normalize=0 + limiter 防削波）
    fc = (
        "[0:a]aformat=sample_rates=48000:channel_layouts=mono[v];"
        "[1:a]aformat=sample_rates=48000:channel_layouts=mono[b];"
        "[v][b]amix=inputs=2:duration=first:normalize=0,"
        "alimiter=limit=0.95[aout]"
    )
    subprocess.run(
        ['ffmpeg', '-y', '-i', video, '-i', tmp_bgm,
         '-filter_complex', fc,
         '-map', '0:v', '-map', '[aout]',
         '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k',
         '-movflags', '+faststart', out],
        check=True,
    )
    print(f'\n成片 -> {out}  {probe_dur(out):.2f}s  '
          f'({os.path.getsize(out) / 1024 / 1024:.1f} MB)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
