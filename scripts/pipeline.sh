#!/bin/bash
# 内容解说视频 一键流水线：edge-tts 合成 → 时间轴 → 渲染 → 混 BGM
# edge-tts 秒级生成，整条流水线几分钟跑完，无需等克隆。
#
# 用法（在 Remotion 工程根目录）：
#   COMP=Video bash scripts/pipeline.sh
#   COMP=Video SLUG="传统资产重定价-算力光纤化" bash scripts/pipeline.sh
#   （传 SLUG=内容概要，成片名自动带「时间戳+概要」；不传则输出 out/final.mp4）
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
MIX_ARGS=(out/video.mp4 vo/bgm/bgm.mp3)
if [ -n "${SLUG:-}" ]; then
  MIX_ARGS+=(--slug "$SLUG")
else
  MIX_ARGS+=(out/final.mp4)
fi
"${ENV[@]}" "$PY" scripts/mix_bgm.py "${MIX_ARGS[@]}" || exit 1

echo "全部完成。成片 -> $ROOT/out/final.mp4（若传 SLUG 则为 out/final_<概要>_<时间戳>.mp4）"
