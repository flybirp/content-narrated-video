# content-narrated-video

把**任意结构化内容**做成 Remotion 图表动画 + 神经网络语音口播 + 字幕 + 背景乐的解说视频。

> 内容源完全开放：AI 对话记录（元宝 / ChatGPT / Claude / DeepSeek…）、PPT、一本书、研报、文章、数据报告——都可以。分镜结构也完全开放，由内容本身的内在逻辑决定，不套预设模板。

一句话概括核心方法论：**口播是唯一时间基准，画面从口播时长派生**——先说稿、再让画面跟着声音走，旁白和画面天然严格同步。

---

## 目录

- [它解决什么问题](#它解决什么问题)
- [核心方法论](#核心方法论)
- [两条边界](#两条边界)
- [软件依赖](#软件依赖)
- [目录结构](#目录结构)
- [快速开始](#快速开始)
- [分镜怎么切](#分镜怎么切)
- [发布模块](#发布模块)
- [示例：爱美客个股分析](#示例爱美客个股分析)
- [常见坑](#常见坑)
- [安装为 WorkBuddy Skill](#安装为-workbuddy-skill)
- [License](#license)
- [免责声明](#免责声明)

---

## 它解决什么问题

「把一段内容讲成视频」这件事，最费时间的不是写稿，而是**让画面和声音对得上**。

传统做法是先定画面时长、再把稿子硬塞进去，结果经常口播讲 A、画面还停在 B。这个 skill 反过来：

1. 先写口播稿（唯一数据源）
2. edge-tts 秒级合成每段语音，量出**真实时长**
3. 画面帧数 = `ceil(时长 × 帧率) + 喘息`，由脚本自动算好
4. 改稿后重跑脚本，整片时长与节奏自动重排

整条流水线几分钟跑完，不用等音色克隆、不用逐帧对时间轴。

## 核心方法论

```
vo/script.json（口播稿，单一数据源）
   ↓ scripts/gen_tts.py        edge-tts 合成 mp3 + loudnorm 归一
public/vo/<id>.mp3             （每段真实时长）
   ↓ scripts/gen_narration.py  ffprobe 量时长
src/narration.json             （含每段 dur）
   ↓ src/timeline.ts           帧数 = ceil(dur × FPS) + 喘息
场景组件 + 字幕组件             （全部从分镜派生）
```

口播说到哪，画面就停在哪个信息块上，**天然同步**。

## 两条边界

这是本 skill 最重要的两个设计约束：

1. **内容源开放** — 不限于某个 AI 助手，也不限于对话。PPT、书、研报、文章、数据都行。
2. **分镜结构开放** — 不套「为什么买/风险/怎么买」这类预设模板。分镜由内容本身的逻辑决定。

> 举例：`定调 → 为什么买 → 风险 → 怎么买 → 预期收益 → 信号 → 收尾` 只是「个股分析」这个内容形态自然长出的**一个例子**，不是模板。一本书的一章可能是「观点 → 论证1 → 论证2 → 反例 → 结论」，一份数据报告可能是「背景 → 三个发现 → 归因 → 建议」。详见 [`references/beats-guide.md`](references/beats-guide.md)。

## 软件依赖

| 软件 | 角色 | 安装 |
|---|---|---|
| Remotion + React | 编程式视频（图表/动画/字幕） | `npm install`（setup.sh 自动） |
| edge-tts（微软 Azure 语音） | 口播，免费 / 无 key / **秒级** | `pip install edge-tts`（setup.sh 自动） |
| ffmpeg / ffprobe | 响度归一、测时长、混 BGM、电平校验 | macOS 一般自带，缺则 `brew install ffmpeg` |

> `scripts/setup.sh` 会自动检测并补齐以上依赖（幂等，可重复跑）。唯一不自动装的是 ffmpeg（避免动系统包管理器）。

## 目录结构

```
content-narrated-video/
├── SKILL.md                     # skill 入口（给 Agent 读的完整工作流）
├── README.md                    # 本文档
├── references/
│   ├── beats-guide.md           # 分镜提炼方法论（必读，唯一需要"动脑"的一步）
│   ├── publish-guide.md         # 发布模块（标题/标签/简介/封面/分平台/合规）
│   └── script-template.json     # 口播稿格式模板
└── scripts/                     # 直接复制到工程使用
    ├── setup.sh                 # 环境自检 + 自动装依赖
    ├── gen_tts.py               # edge-tts 合成口播 + loudnorm
    ├── gen_narration.py         # ffprobe 测时长 → narration.json
    ├── mix_bgm.py               # BGM 混音（压到口播下 ~10dB）
    ├── pipeline.sh              # 一键流水线
    ├── gen_cover.py             # 纯设计型封面（数字锤 + 大字标题）
    └── build_publish_page.py    # 从 publish.json 生成发布资产预览页
```

## 快速开始

### 0. 环境准备（新环境必跑）

```bash
bash scripts/setup.sh
```

自动检测并补齐工具链（ffmpeg/ffprobe/node/npm/python3）、edge-tts、Remotion 依赖。

### 1. 建 Remotion 工程

关键依赖：`remotion` + `@remotion/cli` + `react` + `react-dom`，`tsconfig` 开 `resolveJsonModule`。

工程骨架（`src/index.ts`、`src/timeline.ts`、`Subtitle` 组件、场景组件）需要另搭。本仓库只含「内容 → 分镜 → 口播 → 时间轴 → 渲染 → BGM」的流水线脚本与内容侧方法论；Remotion 工程骨架（timeline 帧数计算、字幕组件、场景组件写法）见配套的 `remotion-narrated-video` skill。

### 2. 切分镜（唯一需要"动脑"的一步）

读 [`references/beats-guide.md`](references/beats-guide.md)，把内容切成「一句话口播 + 一个图表画面」的分镜序列。

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

写作要点：

- 每段对应**一个**画面信息块，段长 60–120 字（约 12–25s）
- **数字全部转中文口语**：`93.5` → 「九十三点五」、`92%` → 「百分之九十二」、`65.7亿` → 「六十五点七亿」
- 稿子里出现数字时，画面必须**同期显示同一个数字**
- 用「第一 / 第二 / 第三」做序列词，观众靠听觉定位画面
- `voice` 字段用 edge-tts 名（如 `zh-CN-XiaoxiaoNeural`），不是 macOS `say` 的名字

### 4. 生成口播

```bash
python scripts/gen_tts.py                          # 默认晓晓
python scripts/gen_tts.py --voice zh-CN-YunxiNeural --rate -5%   # 男声云希、慢 5%
```

常用语音：女声 `zh-CN-XiaoxiaoNeural`（晓晓）、`zh-CN-XiaoyiNeural`（晓伊）、`zh-TW-HsiaoChenNeural`（晓臻）；男声 `zh-CN-YunxiNeural`（云希）、`zh-CN-YunjianNeural`（云健）。

### 5. 时间轴 + 渲染 + 混 BGM

```bash
COMP=Video bash scripts/pipeline.sh
```

分步等价于：`gen_tts.py` → `gen_narration.py` → `npx remotion render` → `mix_bgm.py`。

BGM 默认压到口播下 ~10dB，选无强旋律的 House/Ambient 曲目。

## 分镜怎么切

一个分镜 = **一个信息块** = 一句话口播 + 一个图表画面。三条判断标准（都要满足）：

1. **一句话能说清** → 对应一句口播
2. **一个画面能表达** → 对应一个图表/动画
3. **和前后镜有逻辑递进** → 顺着内容往下走，不是硬凑

图表选型由信息形态决定：横向对比→柱状图、随时间→折线、构成→饼图、单数字→大数字滚动、层级→堆叠卡片、状态→胶囊、推演→概率树。完整表见 [`references/beats-guide.md`](references/beats-guide.md)。

## 发布模块

成片不是终点。发到抖音/B站/视频号/小红书还需要 6 项发布资产：

| # | 资产 | 产出方式 |
|---|---|---|
| 1 | 标题 | LLM 写（钩子 + 多平台差异化） |
| 2 | 自选标签 | LLM 选（查平台真实话题，不自创） |
| 3 | 简介文案 | LLM 写（钩子 + 摘要 + 互动 + 免责） |
| 4 | 封面图 | `gen_cover.py` 纯设计型 |
| 5 | 分平台格式 | 改渲染参数（竖版 9:16 / 横版 16:9） |
| 6 | 合规免责 | 固定模板（财经必加） |

```bash
# 封面（纯设计型：数字锤 + 大字标题）
python scripts/gen_cover.py \
    --title "爱美客能抄底吗？" --metric "93" --unit "元" \
    --sub "从199跌到93 · 跌幅70% · 市盈率25.8倍" \
    --size 1280x720 --accent gold --out cover.png

# 整套发布资产一键预览
python scripts/build_publish_page.py --config publish.json --out publish_preview.html
```

完整规则（多平台标题差异化、黄金时段、发布前 checklist、发布后复盘、合规禁词清单）见 [`references/publish-guide.md`](references/publish-guide.md)。

## 示例：爱美客个股分析

一个完整的示例是「爱美客从 199 跌到 93，能不能抄底」的 4 分钟解说视频。它的工程结构长这样（任何内容都适用同样的结构）：

```
aimeike-video/
├── vo/
│   ├── script.json           # 口播稿（唯一数据源）
│   └── bgm/bgm.mp3           # 背景音乐
├── src/
│   ├── index.ts              # registerRoot
│   ├── timeline.ts           # 帧数 = ceil(dur×FPS)+喘息，从 narration.json 派生
│   ├── narration.json        # gen_narration.py 生成（每段真实时长）
│   ├── beats.ts              # 分镜定义（scene/字幕/图表）
│   ├── Subtitle.tsx          # 字幕组件
│   └── scenes/               # 场景组件（卡片/大数字/柱状图/概率树…）
├── public/vo/<id>.mp3        # gen_tts.py 生成的口播
├── out/
│   ├── video.mp4             # Remotion 渲染的纯画面
│   └── final.mp4             # mix_bgm.py 混完 BGM 的成片
└── publish/
    ├── publish.json          # 发布资产配置（标题/标签/简介/封面）
    ├── cover_横版_16x9.png    # gen_cover.py 生成
    ├── cover_竖版_9x16.png    # gen_cover.py 生成
    └── publish_preview.html  # build_publish_page.py 生成
```

## 常见坑

- **npm 必须带 `env -u NODE_OPTIONS CODEBUDDY_BROKERED_FS_HOOK_ENABLED=0`**，否则 node_modules 写入被 WorkBuddy fs shim 拦截（换源/换 npm 无效，只有这个办法）。
- **`voice` 字段用 edge-tts 名**，别写 macOS `say` 的名字，否则 edge-tts 报错。
- **数字转中文口语**：`92%` 会念「百分之九十二」没问题，但 `65.7亿` 必须手动写成「六十五点七亿」，否则 TTS 念错。
- **章节标题放 Group 层**，别放子段里，否则每切子段标题就淡入一次。
- **字幕时长用 voDur 算**（纯语音帧数），用 dur 会把留白算进去导致字幕慢半拍。
- 财经视频：**A 股惯例涨=红、跌=绿**（与欧美相反）；现价不要用涨跌色。
- 数字动画 delay 别设太晚，否则抽帧校验时看到 "0"。

## 安装为 WorkBuddy Skill

把这个仓库克隆到 WorkBuddy 的用户级 skill 目录即可被识别：

```bash
git clone https://github.com/flybirp/content-narrated-video.git \
    ~/.workbuddy/skills/content-narrated-video
```

之后在 WorkBuddy 里说「帮我把这段内容做成解说视频」，它就会加载本 skill 并按上面的工作流执行。

## License

[MIT](LICENSE)

## 免责声明

本工具用于内容创作与数据可视化，生成内容中的任何观点、数据、情景推演仅供演示与学习，**不构成投资建议**。财经类视频发布时请遵守各平台规范（画面、简介、评论区三处均需注明「不构成投资建议」）。
