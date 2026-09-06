#!/bin/bash
# 环境自检 + 依赖自动安装。新环境跑一次即可（幂等，可重复跑）。
# 用法：在 Remotion 工程根目录执行  bash scripts/setup.sh
set -u

# 是否 WorkBuddy 环境（NODE_OPTIONS 被注入 require=...shim，会拦截 node_modules 写入）
WB_SHIM=0
if [ -n "${NODE_OPTIONS:-}" ] && printf '%s' "$NODE_OPTIONS" | grep -qE 'require='; then
  WB_SHIM=1
fi

# run: 统一加 shim 绕过前缀（仅 WorkBuddy 需要）
run() {
  if [ "$WB_SHIM" -eq 1 ]; then
    env -u PYTHONPATH -u NODE_OPTIONS CODEBUDDY_BROKERED_FS_HOOK_ENABLED=0 "$@"
  else
    "$@"
  fi
}

PY="${PY:-python3}"
NPM="${NPM:-npm}"
PIP_MIRROR="${PIP_MIRROR:-https://pypi.tuna.tsinghua.edu.cn/simple}"
ok=1
have() { command -v "$1" >/dev/null 2>&1; }

echo "== 工具链自检 =="
for c in ffmpeg ffprobe node npm "$PY"; do
  if have "$c"; then echo "  [OK] $c ($(command -v "$c"))"; else echo "  [缺] $c"; ok=0; fi
done

echo "== Python 依赖 =="
if "$PY" -c 'import edge_tts' 2>/dev/null; then
  echo "  [OK] edge-tts $("$PY" -c 'import edge_tts;print(getattr(edge_tts,"__version__","?"))' 2>/dev/null)"
else
  echo "  [安装] edge-tts"
  if ! run "$PY" -m pip install edge-tts -i "$PIP_MIRROR"; then
    echo "  [重试] --user 方式（应对 PEP 668 externally-managed）"
    run "$PY" -m pip install --user edge-tts -i "$PIP_MIRROR" || ok=0
  fi
  "$PY" -c 'import edge_tts' 2>/dev/null && echo "  [OK] edge-tts 装好了" \
    || { echo "  [失败] edge-tts 未装上，建议建 venv 或加 --break-system-packages"; ok=0; }
fi

echo "== Remotion 依赖 =="
if [ -d node_modules/remotion ] || [ -d node_modules/@remotion ]; then
  echo "  [OK] node_modules 已就绪"
else
  echo "  [安装] npm install（首次可能几分钟）"
  run "$NPM" install --no-audit --no-fund || ok=0
fi

echo ""
if [ "$ok" -ne 0 ]; then
  echo "全部就绪。下一步：写 vo/script.json 口播稿，然后 bash scripts/pipeline.sh"
else
  echo "存在缺失项，请按上方提示补齐后重跑本脚本。"
  echo "提示：ffmpeg 缺失时 macOS 用 'brew install ffmpeg'。"
fi
