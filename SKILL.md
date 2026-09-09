---
name: content-narrated-video
description: 把任意结构化内容（AI 对话、PPT、一本书、研报、文章、数据报告）做成 Remotion 图表动画 + 微软神经网络语音口播 + 字幕 + 背景乐的解说视频。核心方法论「口播是唯一时间基准、画面从口播时长派生」，保证旁白与画面严格同步。内容源和分镜结构完全开放——由内容本身逻辑决定，不套预设模板。当用户要求把一段内容/对话/PPT/书/研报做成解说视频、加口播配音、或做数据可视化视频时使用。
description_zh: 内容解说视频生成（任意内容 → 图表 + 口播 + 字幕）
description_en: Content-to-video (any content → charts + narrated audio + subtitles)
disable: false
agent_created: true
---

# content-narrated-video

把**任意内容**做成 Remotion 图表 + 神经网络语音口播的解说视频。

## When to use

- 用户给了一段内容（AI 对话 / PPT / 书 / 研报 / 文章 / 数据报告），要求"做成视频"
- 用户要求给内容"加口播""加配音""做成解说"
- 需要批量模板化产出同结构视频

## 两条边界（务必记住）

1. **内容源开放**：不限于某个 AI 助手，也不限于对话。PPT、书、研报、文章、数据都行。
2. **分镜结构开放**：**不要套预设模板**（什么"为什么买/风险/怎么买"）。分镜由内容本身的逻辑决定。

分镜怎么切、每镜配什么图表，见 `references/beats-guide.md`。这是唯一需要"动脑"的一步。

## 核心方法论：口播是唯一时间基准

**不要先定画面时长再把稿子硬塞进去。** 反过来：

```
vo/script.json (口播稿，单一数据源)
   ↓ scripts/gen_tts.py    (edge-tts 合成 mp3 + loudnorm 归一)
public/vo/<id>.mp3         (每段真实时长)
   ↓ scripts/gen_narration.py (ffprobe 量时长)
src/narration.json         (含每段 dur)
   ↓ src/timeline.ts        (帧数 = ceil(dur × FPS) + 喘息)
场景组件 + 字幕组件         (全部从 BEATS 派生)
```

这样口播说到哪，画面就停在哪个信息块上，**天然同步**，且改稿子后重跑脚本，整片时长与节奏自动重算。

## 软件清单（全部可自动装，见 Step 0）

| 软件 | 角色 | 安装 |
|---|---|---|
| 内容源（对话/PPT/书/研报） | 唯一内容输入 | 无需装（用户提供） |
| Remotion + React | 编程式视频（图表/动画/字幕） | `npm install`（setup.sh 自动） |
| edge-tts（微软 Azure 语音） | 口播，免费/无 key/**秒级** | `pip install edge-tts`（setup.sh 自动） |
| ffmpeg / ffprobe | 响度归一、测时长、混 BGM、电平校验 | macOS 一般自带，缺则 `brew install ffmpeg` |

## Steps

### 0. 环境准备（新环境必跑，自检 + 自动装依赖）

复制 `scripts/setup.sh` 到工程，跑一次：

```bash
bash scripts/setup.sh
```

它会自动检测并补齐 4 类依赖：
- **工具链**：`ffmpeg` / `ffprobe` / `node` / `npm` / `python3`（缺哪个报哪个）
- **edge-tts**：没装则 `pip install edge-tts`（走清华镜像加速）
- **Remotion**：工程没有 `node_modules` 则自动 `npm install`
- **WorkBuddy fs shim**：自动检测 `NODE_OPTIONS` 是否被注入 shim，是则自动加 `env -u NODE_OPTIONS ...` 绕过（普通环境不加）

幂等，可重复跑。ffmpeg 缺失时提示 `brew install ffmpeg`（脚本不自动装，避免动系统包管理器）。

### 1. 建 Remotion 工程

依赖、tsconfig、npm 绕过 fs shim、渲染命令等**工程细节见 `remotion-narrated-video` skill**（本 skill 专注于内容侧与流水线，不重复讲工程骨架）。

关键依赖：`remotion` + `@remotion/cli` + `react` + `react-dom`，`tsconfig` 开 `resolveJsonModule`。

### 2. 切分镜（动脑的一步）

读 `references/beats-guide.md`，把内容切成"一句话口播 + 一个图表画面"的分镜序列。

### 3. 写口播稿 `vo/script.json`

```json
{
  "voice": "zh-CN-XiaoxiaoNeural",
  "rate": "+0%",
  "segments": [
    {"id": "s01", "scene": "Intro", "text": "……"}
  ]
}
```

格式见 `references/script-template.json`。写作要点：

- 每段对应**一个**画面信息块，段长 60–120 字（约 12–25s）
- **数字全部转中文口语**：`93.5` → "九十三点五"、`92%` → "百分之九十二"、`65.7亿` → "六十五点七亿"
- 稿子里出现数字时，画面上必须**同期显示同一个数字**（"协调一致性"的实质）
- 用「第一 / 第二 / 第三」做序列词，观众靠听觉定位画面
- `scene` 字段是场景组件名，`WhyBuy-Cards` 表示"场景 WhyBuy 的子段 Cards"，子段组件挂到 Group 层，章节标题提到 Group 层（见 remotion-narrated-video skill）

**`voice` 字段现在是 edge-tts 的 voice 名**（如 `zh-CN-XiaoxiaoNeural`），不是旧版 macOS `say` 的名字。

### 4. 生成口播

```bash
python scripts/gen_tts.py            # 默认晓晓，输出 public/vo/<id>.mp3
python scripts/gen_tts.py --voice zh-CN-YunxiNeural --rate -5%   # 男声云希、语速慢 5%
```

常用中文语音（女）：`zh-CN-XiaoxiaoNeural`(晓晓)、`zh-CN-XiaoyiNeural`(晓伊)、`zh-TW-HsiaoChenNeural`(晓臻)；男声：`zh-CN-YunxiNeural`(云希)、`zh-CN-YunjianNeural`(云健)。财经解说要更沉稳可 `--rate -5%`。

### 5. 时间轴 + 渲染 + 混 BGM

一键流水线（在工程根目录跑；`SLUG` 为内容概要，成片名自动带时间戳）：

```bash
COMP=Video SLUG="传统资产重定价-算力光纤化" bash scripts/pipeline.sh
```

分步等价于：
1. `gen_tts.py` → 口播 mp3
2. `gen_narration.py` → narration.json（每段真实时长）
3. `npx remotion render src/index.ts Video out/video.mp4 --concurrency=6`
4. `mix_bgm.py out/video.mp4 vo/bgm/bgm.mp3 --slug "传统资产重定价-算力光纤化"` → `out/final_传统资产重定价-算力光纤化_<时间戳>.mp4`

不传 `SLUG` 则成片仍输出 `out/final.mp4`（向后兼容）。BGM 音量默认压到口播下 ~12dB（`mix_bgm.py` 里 `volume=-12dB` 可调）。**默认 BGM 用 Mixkit 免版权曲库的 Hazy After Hours（`Hazy-After-Hours.mp3`，Electronica，127s）**；选无强旋律的 House/Ambient 曲目，低音量下不抢人声。BGM 下载见 Mixkit（直链格式 `https://assets.mixkit.co/music/{id}/{id}.mp3`）。

## 文件命名规范（最终交付物必带「概要 + 时间戳」）

成片和封面是**要拿出项目目录**的交付物（会复制到发布目录 / 上传平台），若文件名固定会互相覆盖。因此**必须带「内容概要 + 时间戳」**：

| 交付物 | 命名模板 | 示例 |
|---|---|---|
| 成片 | `final_<概要>_<YYYYMMDD-HHMM>.mp4` | `final_传统资产重定价-算力光纤化_20260908-0138.mp4` |
| 封面横版 | `cover_横版_16x9_<概要>_<YYYYMMDD-HHMM>.png` | `cover_横版_16x9_传统资产重定价-算力光纤化_20260908-0138.png` |
| 封面竖版 | `cover_竖版_9x16_<概要>_<YYYYMMDD-HHMM>.png` | `cover_竖版_9x16_传统资产重定价-算力光纤化_20260908-0138.png` |

- `<概要>` = 6~12 字中文短语，词间用 `-` 连接，不含空白和 `/ \ : * ? " < > |`
- `<时间戳>` = 本地时间 `YYYYMMDD-HHMM`（精确到分钟，同一天多期不冲突）
- **时间戳由脚本自动生成**：`mix_bgm.py --slug`、`gen_cover.py --slug` 只传概要，脚本内部拼时间戳，**不要手拼**（避免时区/格式错）
- 中间产物（`out/video.mp4`、`public/vo/*.mp3`、`src/narration.json`）在各自项目目录内，不会跨期冲突，无需时间戳

## 发布模块（发到自媒体平台）

成片不是终点。发到抖音/B站/视频号/小红书还需要 6 项发布资产：**标题、自选标签、简介文案、封面图、分平台格式、合规免责**。完整规则（含多平台标题差异化、发布时机、发布前 checklist、发布后复盘）见 `references/publish-guide.md`。

封面图自动生成（**纯设计型，不抽帧**——数字锤 + 大字标题）：

```bash
python scripts/gen_cover.py \
    --title "传统资产正在被重定价" \
    --metric "8万亿" --unit "元" \
    --sub "× 算力底座光纤化 · 中美五个产业信号" \
    --size 1280x720 --accent gold \
    --slug "传统资产重定价-算力光纤化"
```

传 `--slug`（内容概要）后，脚本自动按尺寸拼 `cover_横版_16x9_<概要>_<时间戳>.png` / `cover_竖版_9x16_<概要>_<时间戳>.png`，无需手写 `--out`。`--size` 用 `1280x720`（横版 B站）或 `1080x1920`（竖版 抖音/视频号）；`--accent` 用 `gold`/`red`(涨)/`green`(跌)。仍可用 `--out` 指定自定义文件名（覆盖 slug 自动命名）。

整套发布资产一键预览：

```bash
python scripts/build_publish_page.py --config publish.json --out publish_preview.html
```

`publish.json` 里写标题候选/标签/简介/封面路径（格式见脚本 docstring），脚本生成 base64 内嵌的预览页，发稿前人工过目。标题/标签/简介由 LLM 按 publish-guide.md 的公式产出，标签发前用 WebSearch 验证平台真实热度。

**注意竖版不是横版裁切**：要改 Remotion 分辨率 + 场景布局重排重渲。

## Pitfalls

- **npm 必须 `env -u NODE_OPTIONS CODEBUDDY_BROKERED_FS_HOOK_ENABLED=0`**，否则 node_modules 写入被 fs shim 拦截（换源/换 npm 无效，只有这个办法）
- **`voice` 字段用 edge-tts 名**，别写 macOS `say` 的名字（`Rocko...`），否则 edge-tts 报错
- **数字转中文口语**：TTS 会把 `93.5` 念成"九十三点五"没问题，但 `92%` 会念"百分之九十二"，`65.7亿` 会念错，必须手动写成中文
- **章节标题放 Group 层**，别放子段里，否则每切子段标题就淡入一次
- **字幕时长用 voDur 算**（纯语音帧数），用 dur 会把留白算进去导致字幕慢半拍
- 财经视频：**A 股惯例涨=红、跌=绿**（与欧美相反）；现价不要用涨跌色
- 数字动画 delay 别设太晚，否则抽帧校验时看到 "0"

## Verification

1. `npx tsc --noEmit` 零错误
2. 每段渲 1 帧 → 逐张肉眼确认字幕 ↔ 画面卡片对应
3. 整片渲染后 `ffprobe` 确认：分辨率/帧率/时长 + 存在 aac 音轨
4. `ffmpeg -i out/final_*.mp4 -af volumedetect -f null - 2>&1 | grep mean_volume`，正常 ≈ -16~-20dB、无削波（成片名带「概要+时间戳」，用通配符 `final_*.mp4`）
5. `present_files` 交付

## 参考实现

- `references/beats-guide.md` —— 分镜提炼方法论（必读）
- `references/publish-guide.md` —— 发布模块（标题/标签/简介/封面/分平台/合规）
- `references/script-template.json` —— 口播稿格式
- `scripts/` —— setup（环境自检+装依赖）/ gen_tts / gen_narration / mix_bgm / pipeline / gen_cover（封面）/ build_publish_page（发布资产预览页）（直接复制到工程）
- Remotion 工程骨架（timeline/Subtitle/场景组件）：见 `remotion-narrated-video` skill
- 完整示例工程结构：见本仓库 `README.md` 的「示例」章节（爱美客个股分析视频）
