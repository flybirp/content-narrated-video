/**
 * vertical-template.tsx —— 竖版 9:16 独立模板（参考实现，需按工程适配）
 *
 * 这是「每日双源产业解读」视频号竖版的实战代码，抽成可复用模板。
 * 关键点：竖版是「专用 1080×1920 组合」重渲，不是横版缩放/模糊背景兜底。
 * 图表与横版分镜同源——直接复用工程的 data.ts，保证数字协调一致。
 *
 * 依赖（你工程里要已有，路径按需改）：
 *   import {C, FONT, FONT_NUM, FPS} from '../theme';
 *   import {BEATS, TOTAL} from '../timeline';
 *   import {Avatar, Backdrop} from '../components/ui';   // Avatar 已改用 staticFile('avatar.png')
 *   import {rise, countTo, fmt} from '../anim';
 *   import {TITLE, DATE, DISCLAIMER} from '../data';
 *   import {QUALCOMM, CORNING, GOOGLE, TRADE, PRICES, FISCAL, SYNTHESIS, COMPARE} from '../data';
 *
 * 注册第二个 Composition（src/index.ts 或 Root.tsx）：
 *   <Composition id="Video9x16" component={VerticalMain}
 *     durationInFrames={TOTAL} fps={FPS} width={1080} height={1920} />
 *
 * 渲染：COMP=Video9x16 bash scripts/pipeline.sh
 */
import React from 'react';
import {AbsoluteFill, Sequence, useCurrentFrame, Audio, staticFile, interpolate} from 'remotion';
import {C, FONT, FONT_NUM, FPS} from '../theme';
import {BEATS, TOTAL} from '../timeline';
import {Avatar, Backdrop} from '../components/ui';
import {rise, countTo, fmt} from '../anim';
import {TITLE, DATE, DISCLAIMER} from '../data';
// ↓↓↓ 这些是你工程 data.ts 里的图表数据源，竖版与横版共用，数字天然一致
import {
  QUALCOMM, CORNING, GOOGLE, TRADE, PRICES, FISCAL, SYNTHESIS, COMPARE,
} from '../data';

const PAD = 64;
const CLAMP = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;

/** 每段 kicker（场景→标签）。换主题时改这张表即可。 */
const SCENE_KICKER: Record<string, string> = {
  Intro: '信号速览',
  Qualcomm: '高通 × 亚马逊',
  Corning: '康宁 × Verizon',
  Google: '谷歌 × Fortum',
  Synthesis: '核心研判',
  Outro: '关注 · 跟踪',
  Domestic: '国内双源',
  Overseas: '海外长单',
  Trade: '服务贸易',
  Prices: '价格信号',
  Fiscal: '财政金融',
  Compare: '中美映射',
};
const kickerOf = (scene: string) =>
  SCENE_KICKER[scene] ?? '';

const colOf = (d: any) =>
  d.color === 'gold' ? C.gold
    : d.color === 'cyan' ? C.cyan
      : d.color === 'violet' ? C.violet
        : d.tone === 'up' ? C.up
          : d.tone === 'down' ? C.down
            : C.gold;

/* ---- 指标 tile（带数字滚动动画） ---- */
const MetricTile: React.FC<{d: any; delay: number; full?: boolean}> = ({d, delay, full}) => {
  const f = useCurrentFrame();
  const col = colOf(d);
  const a = rise(f, delay, 18, 30);
  const num = countTo(f, d.value ?? 0, delay + 4, 26, 0);
  return (
    <div style={{
      width: '100%', maxWidth: full ? 900 : 760, padding: '24px 30px',
      background: C.panel, border: `1px solid ${C.border}`, borderTop: `3px solid ${col}`,
      borderRadius: 18, opacity: a.opacity, transform: `translateY(${a.y}px)`,
    }}>
      <div style={{fontFamily: FONT, fontSize: 23, color: C.faint, letterSpacing: 2}}>{d.label}</div>
      <div style={{display: 'flex', alignItems: 'baseline', gap: 8, marginTop: 8}}>
        <span style={{fontFamily: FONT_NUM, fontSize: 68, fontWeight: 800, color: col, fontVariantNumeric: 'tabular-nums', lineHeight: 1}}>
          {fmt(num, d.dec ?? 0)}
        </span>
        {d.unit ? <span style={{fontFamily: FONT, fontSize: 28, color: C.dim, fontWeight: 600}}>{d.unit}</span> : null}
      </div>
      {d.note ? <div style={{fontFamily: FONT, fontSize: 19, color: C.dim, marginTop: 8}}>{d.note}</div> : null}
    </div>
  );
};

/* ---- 单个超大数字（HeroFigure 式） ---- */
const HeroFigure: React.FC<{d: any; delay: number}> = ({d, delay}) => {
  const f = useCurrentFrame();
  const a = rise(f, delay, 18, 30);
  const num = countTo(f, d.value, delay + 4, 30, 0);
  return (
    <div style={{opacity: a.opacity, transform: `translateY(${a.y}px)`, textAlign: 'center'}}>
      <div style={{display: 'flex', alignItems: 'baseline', gap: 14, justifyContent: 'center'}}>
        <span style={{fontFamily: FONT_NUM, fontSize: 132, fontWeight: 900, color: C.cyan, fontVariantNumeric: 'tabular-nums', lineHeight: 1}}>
          {fmt(num, d.dec ?? 0)}
        </span>
        <span style={{fontFamily: FONT, fontSize: 46, color: C.dim, fontWeight: 700}}>{d.unit}</span>
      </div>
      {d.note ? <div style={{fontFamily: FONT, fontSize: 22, color: C.faint, marginTop: 8, letterSpacing: 1}}>{d.note}</div> : null}
    </div>
  );
};

/* ---- 三判断列表（Synthesis 式） ---- */
const SynthesisList: React.FC<{delay: number}> = ({delay}) => (
  <div style={{display: 'flex', flexDirection: 'column', gap: 18, width: '100%', maxWidth: 900}}>
    {SYNTHESIS.map((s, i) => {
      const f = useCurrentFrame();
      const a = rise(f, delay + i * 10, 18, 28);
      return (
        <div key={i} style={{display: 'flex', gap: 16, alignItems: 'flex-start', opacity: a.opacity, transform: `translateY(${a.y}px)`}}>
          <div style={{flex: 'none', fontFamily: FONT_NUM, fontSize: 26, fontWeight: 800, color: C.gold, minWidth: 70}}>{s.n}：</div>
          <div style={{fontFamily: FONT, fontSize: 29, color: C.text, lineHeight: 1.5}}>{s.text}</div>
        </div>
      );
    })}
  </div>
);

/* ---- 中美双栏（Compare 式） ---- */
const ComparePanel: React.FC<{delay: number}> = ({delay}) => {
  const f = useCurrentFrame();
  const a = rise(f, delay, 18, 30);
  return (
    <div style={{display: 'flex', gap: 18, width: '100%', maxWidth: 940, opacity: a.opacity, transform: `translateY(${a.y}px)`}}>
      {[COMPARE.cn, COMPARE.us].map((c, i) => {
        const col = c.color === 'gold' ? C.gold : C.cyan;
        return (
          <div key={i} style={{flex: 1, padding: '22px 24px', background: C.panel, border: `1px solid ${C.border}`, borderTop: `3px solid ${col}`, borderRadius: 18}}>
            <div style={{fontFamily: FONT, fontSize: 27, fontWeight: 800, color: col}}>{c.title}</div>
            <div style={{fontFamily: FONT, fontSize: 23, color: C.text, marginTop: 10, lineHeight: 1.5}}>{c.point}</div>
            <div style={{fontFamily: FONT, fontSize: 18, color: C.dim, marginTop: 8}}>{c.sub}</div>
          </div>
        );
      })}
    </div>
  );
};

/* ---- 财政（from→to 与 value 混合） ---- */
const FiscalTile: React.FC<{d: any; delay: number}> = ({d, delay}) => {
  const f = useCurrentFrame();
  const col = colOf(d);
  const a = rise(f, delay, 18, 30);
  return (
    <div style={{width: '100%', maxWidth: 760, padding: '22px 28px', background: C.panel, border: `1px solid ${C.border}`, borderTop: `3px solid ${col}`, borderRadius: 18, opacity: a.opacity, transform: `translateY(${a.y}px)`}}>
      <div style={{fontFamily: FONT, fontSize: 22, color: C.faint, letterSpacing: 1}}>{d.label}</div>
      <div style={{display: 'flex', alignItems: 'baseline', gap: 8, marginTop: 8}}>
        {typeof d.value === 'number' ? (
          <>
            <span style={{fontFamily: FONT_NUM, fontSize: 60, fontWeight: 800, color: col}}>{fmt(d.value, d.dec ?? 0)}</span>
            {d.unit ? <span style={{fontFamily: FONT, fontSize: 26, color: C.dim}}>{d.unit}</span> : null}
          </>
        ) : (
          <>
            <span style={{fontFamily: FONT_NUM, fontSize: 46, fontWeight: 800, color: col}}>{d.from}</span>
            <span style={{fontFamily: FONT, fontSize: 28, color: C.dim}}>→</span>
            <span style={{fontFamily: FONT_NUM, fontSize: 46, fontWeight: 800, color: col}}>{d.to}</span>
            {d.unit ? <span style={{fontFamily: FONT, fontSize: 24, color: C.dim}}>{d.unit}</span> : null}
          </>
        )}
      </div>
      {d.note ? <div style={{fontFamily: FONT, fontSize: 18, color: C.dim, marginTop: 6}}>{d.note}</div> : null}
    </div>
  );
};

/**
 * 每段对应的图表面板 —— 与横版分镜同源（复用 data.ts），数字天然一致。
 * 无数据的段（纯口播段）返回 null，只放文字卡。这是「竖版不能丢图表」的实现核心。
 */
const BeatFigures: React.FC<{scene: string}> = ({scene}) => {
  switch (scene) {
    case 'Qualcomm':
    case 'Google':
    case 'Trade':
    case 'Prices':
      return (
        <div style={{display: 'flex', flexDirection: 'column', gap: 16, width: '100%', alignItems: 'center'}}>
          {(scene === 'Qualcomm' ? QUALCOMM : scene === 'Google' ? GOOGLE : scene === 'Trade' ? TRADE : PRICES)
            .map((d, i) => <MetricTile key={i} d={d} delay={4 + i * 10} />)}
        </div>
      );
    case 'Fiscal':
      return (
        <div style={{display: 'flex', flexDirection: 'column', gap: 16, width: '100%', alignItems: 'center'}}>
          {FISCAL.map((d, i) => <FiscalTile key={i} d={d} delay={4 + i * 10} />)}
        </div>
      );
    case 'Corning':
      return <div style={{display: 'flex', justifyContent: 'center', width: '100%'}}><HeroFigure d={CORNING} delay={4} /></div>;
    case 'Synthesis':
      return <div style={{display: 'flex', justifyContent: 'center', width: '100%'}}><SynthesisList delay={4} /></div>;
    case 'Compare':
      return <div style={{display: 'flex', justifyContent: 'center', width: '100%'}}><ComparePanel delay={4} /></div>;
    default:
      return null;
  }
};

const BeatCard: React.FC<{b: (typeof BEATS)[number]; index: number}> = ({b, index}) => {
  const f = useCurrentFrame();
  const kicker = kickerOf(b.scene);
  const figs = BeatFigures({scene: b.scene});
  const hasFig = !!figs;
  const inA = interpolate(f, [2, 16], [0, 1], CLAMP);
  const outA = interpolate(f, [b.dur - 12, b.dur], [1, 0], CLAMP);
  const y = interpolate(f, [2, 18], [42, 0], { ...CLAMP, easing: (t) => 1 - Math.pow(1 - t, 3) });
  const len = b.text.length;
  const capSize = hasFig ? 36 : len > 60 ? 44 : len > 40 ? 52 : 60;

  return (
    <AbsoluteFill style={{justifyContent: 'center', alignItems: 'center', padding: `0 ${PAD}px`}}>
      <div style={{position: 'absolute', top: 250, right: 54, fontFamily: FONT_NUM, fontSize: 380, fontWeight: 800, color: 'rgba(255,255,255,0.045)', lineHeight: 1, userSelect: 'none'}}>
        {String(index + 1).padStart(2, '0')}
      </div>
      <div style={{position: 'relative', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: hasFig ? 24 : 30, maxWidth: 940, opacity: inA * outA, transform: `translateY(${y}px)`}}>
        {kicker ? (
          <div style={{fontFamily: FONT, fontSize: 28, fontWeight: 700, color: C.gold, letterSpacing: 4, padding: '9px 24px', borderRadius: 999, border: `1px solid rgba(232,176,75,0.5)`, background: 'rgba(232,176,75,0.08)'}}>
            {kicker}
          </div>
        ) : null}
        {figs}
        <div style={{fontFamily: FONT, fontSize: capSize, fontWeight: 700, color: C.text, lineHeight: 1.5, textAlign: 'center', letterSpacing: 1, padding: hasFig ? '22px 30px' : '40px 44px', borderRadius: 28, border: `1px solid ${C.border}`, background: 'rgba(255,255,255,0.035)', boxShadow: '0 30px 80px rgba(0,0,0,0.4), inset 0 0 60px rgba(232,176,75,0.04)'}}>
          {b.text}
        </div>
        <div style={{width: 120, height: 5, borderRadius: 3, background: `linear-gradient(90deg, ${C.gold}, ${C.cyan})`}} />
      </div>
    </AbsoluteFill>
  );
};

/** 竖版 9:16 模板：手机竖屏专用重排（非横版缩放）；图表与横版同源。 */
export const VerticalMain: React.FC = () => {
  const f = useCurrentFrame();
  const progress = Math.max(0, Math.min(1, f / TOTAL));

  return (
    <AbsoluteFill style={{fontFamily: FONT, background: C.bg0}}>
      <Backdrop />

      {BEATS.map((b, i) => (
        <Sequence key={b.id} from={b.from} durationInFrames={b.dur}>
          <BeatCard b={b} index={i} />
          <Audio src={staticFile(`vo/${b.id}.mp3`)} />
        </Sequence>
      ))}

      {/* 顶栏：真人头像 + 频道 + 双源标签 */}
      <div style={{position: 'absolute', top: 0, left: 0, right: 0, height: 150, display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: `0 ${PAD}px`, borderBottom: `1px solid ${C.borderSoft}`, background: 'linear-gradient(180deg, rgba(6,10,18,0.92), rgba(6,10,18,0))'}}>
        <div style={{display: 'flex', alignItems: 'center', gap: 18}}>
          <Avatar size={84} />
          <div style={{display: 'flex', flexDirection: 'column'}}>
            <span style={{fontFamily: FONT, fontSize: 38, fontWeight: 800, color: C.text}}>{TITLE}</span>
            <span style={{fontFamily: FONT_NUM, fontSize: 20, color: C.faint, letterSpacing: 1}}>{DATE} · 每日更新</span>
          </div>
        </div>
        <span style={{fontFamily: FONT_NUM, fontSize: 20, fontWeight: 700, color: C.gold, letterSpacing: 2}}>新闻联播 · WSJ 双源</span>
      </div>

      {/* 底栏：交叉验证来源 + 进度 + 免责 */}
      <div style={{position: 'absolute', left: 0, right: 0, bottom: 0, padding: `0 ${PAD}px 40px`, display: 'flex', flexDirection: 'column', gap: 18, background: 'linear-gradient(0deg, rgba(6,10,18,0.92), rgba(6,10,18,0))'}}>
        <div style={{fontFamily: FONT, fontSize: 22, color: C.dim, letterSpacing: 1}}>新闻联播 × 华尔街日报 · 交叉验证信号</div>
        <div style={{height: 6, width: '100%', borderRadius: 3, background: 'rgba(255,255,255,0.08)', overflow: 'hidden'}}>
          <div style={{height: '100%', width: `${progress * 100}%`, background: `linear-gradient(90deg, ${C.gold}, ${C.cyan})`}} />
        </div>
        <div style={{fontFamily: FONT, fontSize: 18, color: C.faint}}>{DISCLAIMER}</div>
      </div>
    </AbsoluteFill>
  );
};
