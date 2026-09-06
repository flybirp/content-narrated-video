#!/bin/bash
# 内容解说视频 一键流水线：edge-tts 合成 → 时间轴 → 渲染 → 混 BGM
# edge-tts 秒级生成，整条流水线几分钟跑完，无需等克隆。
#
# 用法（在 Remotion 工程根目录）：
#   COMP=Video bash scripts/pipeline.sh
set -u

ROOT="${ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
PY="${PY:-python3}"
COMP="${COMP:-Video}"          # Remotion 入口组件名（src/index.ts 里 registerRoot 的组件）
# WorkBuddy 环境需绕过 fs shim；普通环境可留空
ENV=(env -u PYTHONPATH -u NODE_OPTIONS CODEBUDDY_BROKERED_FS_HOOK_ENABLED=0)

cd "$ROOT"

echo "==[1/4] edge-tts 合成口播 =="
"${ENV[@]}" "$PY" scripts/gen_tts.py || exit 1

echo "==[2/4] 生成时间轴 narration.json =="
"${ENV[@]}" "$PY" scripts/gen_narration.py || exit 1

echo "==[3/4] Remotion 渲染 =="
"${ENV[@]}" npx remotion render src/index.ts "$COMP" out/video.mp4 --concurrency=6 || exit 1

echo "==[4/4] 混入背景音乐 =="
"${ENV[@]}" "$PY" scripts/mix_bgm.py out/video.mp4 vo/bgm/bgm.mp3 out/final.mp4 || exit 1

echo "全部完成。成片 -> $ROOT/out/final.mp4"
