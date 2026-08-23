<div align="center">
  <h1>Publication Figure Design</h1>
  <p><strong>面向学术级科学图表生成Skill，可自动完成从数据解读到顶刊格式图表生成的全流程。</strong></p>
  <p>
    问题驱动 · 参考优先 Orchestrator · 29 种图型 · 证据化 QA · 矢量 PDF 交付 · 统计报告
  </p>
  <p>
    <a href="LICENSE"><img alt="License" src="https://img.shields.io/badge/license-Apache--2.0-2ea44f"></a>
    <a href="#安装与使用"><img alt="Install" src="https://img.shields.io/badge/install-Claude%20Code%20%7C%20Codex%20%7C%20Cursor%20%7C%20Copilot-111827"></a>
    <a href="#图表类型全览"><img alt="Figure Types" src="https://img.shields.io/badge/figures-29-0ea5e9"></a>
    <a href="#质量评估与测试"><img alt="QA" src="https://img.shields.io/badge/QA-L0--L3%20layered-success"></a>
    <a href="README_EN.md"><img alt="Language" src="https://img.shields.io/badge/语言-English%20%7C%20中文-1f6feb"></a>
  </p>
  <p>
    <a href="#项目介绍">项目介绍</a>
    · <a href="#安装与使用">安装与使用</a>
    · <a href="#图表类型全览">图表类型</a>
    · <a href="#系统工作流">工作流</a>
    · <a href="#项目结构">项目结构</a>
    · <a href="#质量评估与测试">质量评估</a>
    · <a href="#贡献指南">贡献指南</a>
    · <a href="README_EN.md">English</a>
  </p>
</div>

---

**Publication Figure Design** 以"问题驱动、参考优先而非模板驱动"为核心原则——每一张图都经过可持久化的 `Route → Intake → Reference Retrieval → Reference Inspection → Design Spec → Binding → Render → Compare → Critique → Repair → QA → Export` 状态机，输出可直接投稿的矢量 PDF 主文件 + 300dpi PNG 预览 + 统计报告。更多详情，请关注微信公众号：**科研绘图酱**。

### 当前运行入口

```text
pfd run <task-spec.json>
pfd reference ingest <image> <figure-type>
pfd reference analyze <reference-id>
pfd reference review <reference-id> <review.json>
pfd index build
pfd eval quick|full|visual|release  # release 与 CI 完全一致
```

## Scientific Figure Design Compiler

当前生产链保留 12 阶段状态机，并将参考图编译为可验证合同：

`ScientificContract → ReferenceDNA → StyleCapsule + JournalProfile → DesignPacket → DesignPatch → RenderTrace → L0/L1/L2/L3 QA`

图片、SVG、PDF 和 plotting code 使用不同 analyzer；raster 只输出字体类别和相对层级，
不猜精确字体。索引使用透明的 metadata + semantic + structure + StyleDNA 混合检索，
当前规模直接使用 NumPy 全量搜索，可选 SigLIP2/DINO adapter 不进入 core 依赖。

具体参考图必须先打开并测量，再选择实现材料；结构、风格、组件和注释参考独立检索，最终 raster/vector 必须重新与参考图比较。`SKILL.md` 是薄入口，机器契约、状态机和 QA 规则分别位于 `references/`、`src/` 和 `manifest.yaml`。

---

## 效果预览

<p align="center">
  <img src="assets/figure-atlas/preview.png" width="100%" alt="Publication Figure Design 多面板效果预览">
</p>

<details>
<summary>点击展开更多示例图表</summary>
<p align="center">
  <img src="assets/figure-atlas/data-figure.png" width="100%" alt="示例图表2">
</p>
</details>

---

## 项目介绍

Publication Figure Design 是一个面向 AI 编程助手（Claude Code、Codex 等）的 Skill 包。其工作方式是：将 Nature / Cell / Science 系列期刊的图表制作规范（字体 Arial/Helvetica、栏宽 89mm/183mm、PDF 矢量导出、300dpi 栅格预览）和 29 种常见图型的视觉参数编码为 `SKILL.md` 及其路由的参考/运行时集合。当用户提供数据和科学问题后，Skill 引导 LLM 执行可持久化的 Route → Intake → Reference Retrieval → Reference Inspection → Design Spec → Binding → Render → Compare → Critique → Repair → QA → Export 生命周期；每一步都有机器可读 artifact 和 gate。

该 Skill 不替代 Python 或 R 的绘图能力，而是提供一套结构化的约束条件（constraints）和先验知识（priors），使 LLM 在生成绘图代码时遵循 CNS 期刊的视觉标准，减少人工调整排版、配色和导出参数的工作量。在多面板合成场景中，Skill 支持 Python 脚本和 R 脚本的混合编排——R 面板通过 Cairo 设备渲染为位图，Python 的 `compose.py` 排版引擎按物理尺寸拼合多面板。

### 设计原则

| 原则 | 说明 |
|------|------|
| **一幅图一个核心信息** | 审稿人 3 秒扫读即懂；移除网格线、边框和无用图例 |
| **克制配色 > 丰富配色** | 2-4 个语义主色 + 1 个强调色；禁用 matplotlib/ggplot 默认色板 |
| **面向印刷设计** | 期刊固定栏宽（单栏 89mm / 双栏 183mm），创建时即设定尺寸，不再缩放 |
| **矢量优先** | 线图/散点/柱状 → PDF/SVG；只有真正的栅格内容（热图色块/显微图）才用 ≥300dpi TIFF/PNG |

---

## 核心能力

| 能力 | 说明 |
|------|------|
| **原型分类** | 四类范式：`quantitative_grid`（定量网格）、`schematic-led`（示意引导）、`image plate + quant`（图像-定量融合）、`asymmetric_mixed`（非对称复合）——自动驱动布局与英雄面板策略 |
| **29 种图型** | 热图 / 火山图 / 柱状图 / 散点图 / 箱线图 / PCA / RDA / 雷达图 / 桑基图 / AUROC / 山脊图 / 小提琴图 / 边际密度 / 核密度 / Mantel 相关 / UpSet / 森林图 / 混淆矩阵 / 流形 / 堆叠柱散 / 配对箱线 / 标记基因点图 / 趋势线 / 3D 热图 / 频率热图 / 密度热图 / 相关矩阵 / 分组相关矩阵 / 分组小提琴——每种均有配套生产脚本（`.py` + `.R`）与预览 PNG |
| **参考优先编译** | 先从 `assets/visual-references/` 按 structure/style/palette/component 分角色检索，再把 Reference DNA 编译成 DesignPacket；已有生产资产只在 asset-adaptation 路由显式复用 |
| **跨类型参数继承** | 无生产脚本时，从相近图型借用 Class A（硬参数：颜色/透明度/线宽）、Class B（比例参数：字号/尺寸）、Class C（逻辑参数：图例开关/网格开关）三类视觉参数 |
| **混合语言组合** | R 面板原生运行 → 输出 spec-correct PNG，Python 排版引擎按精确物理尺寸拼合多面板 |
| **英雄面板自动识别** | 承载核心结论的面板自动获得更大的视觉权重，支撑面板居次排列 |
| **分层 QA** | L0 Hard Technical → L1 Scientific → L2 Structural Visual → L3 Perceptual/Aesthetic；四层结果分别落盘，任一硬门禁失败都不能导出 production-ready 资产 |
| **数据校验门禁** | 逐面板预检——火山图需 ≥10 个显著差异基因、AUROC 曲线分离需 ≥0.15、热图须有跨行方差——不通过则拒绝渲染 |
| **统计与可复现报告** | 每张图强制附带：n 定义、中心统计量（均值/中位数）、散布度量（SD/SEM/95%CI）、检验名称、多重比较校正、source-data 溯源 |
| **期刊配色系统** | Nature 偏冷蓝、Cell 偏暖、Science 偏保守灰；色盲友好，避免红绿独对区分 |
| **审稿人模拟模式** | 从五个维度审视成品——科学清晰度、视觉层次、配色可访问性、排版可读性、整体完成度——给出 must-fix vs. suggestion 分级反馈 |

---

## 私有资产图表类型全览

> 图鉴中展示的示例图表基于项目私有数据资产生成，仅作为风格参考。用户请求生成同类型图表时，脚本在保留示例所确立的视觉语言（配色、字体、布局逻辑、图元层级）的前提下，依据实际数据完成适配性重构。私有资产持续更新中。更多详情，请关注微信公众号：科研绘图酱

| 图表名称 | 预览 | 图形特征 | 典型应用场景 |
|---------|------|---------|-------------|
| 3D 热图 | <img src="assets/figure-atlas/3Dheatmap.png" width="100"> | 立体柱面矩阵数值，高度+颜色双重编码 | 多因子交互效应、基因型×环境矩阵、三维强度分布 |
| AUROC 曲线图 | <img src="assets/figure-atlas/auroc.png" width="100"> | TPR-FPR 曲线，含对角参考线与 AUC 标注 | 分类模型评估、多模型 ROC 对比、阈值敏感性分析 |
| 柱状图 | <img src="assets/figure-atlas/bar.png" width="100"> | 单变量条形高度编码，支持误差棒 | 组间均值比较、单指标排序、计数统计 |
| 相关性密度图 | <img src="assets/figure-atlas/CorrelationDensity.png" width="100"> | 散点叠加二维核密度等高线 | 两变量关系强弱、密集区识别、异常点检测 |
| 相关性矩阵图 | <img src="assets/figure-atlas/Correlationmatrix.png" width="100"> | 方形网格，色阶+数值双重展示成对相关系数 | 多变量相关性总览、特征筛选前共线性检查 |
| 密度热图 | <img src="assets/figure-atlas/density_heatmap.png" width="100"> | 连续二维核密度颜色梯度铺满网格 | 大样本点云密度分布、替代过度重叠散点图 |
| 频率 3D 热图 | <img src="assets/figure-atlas/Frequency_3DHeatmap.png" width="100"> | 立体柱面展示分箱频次 | 等位基因频率分布、双因子计数交叉展示 |
| 分组相关性矩阵图 | <img src="assets/figure-atlas/GroupCorrelationmatrix.png" width="100"> | 按分组拆分的多个相关矩阵并列呈现 | 不同处理/环境下相关结构差异比较 |
| 分组柱状图 | <img src="assets/figure-atlas/GroupedBarChart.png" width="100"> | 同一类别下并列多个子组条形 | 多处理×多指标对比、重复实验组间差异 |
| Mantel 相关性检验图 | <img src="assets/figure-atlas/MantelCorrelation.png" width="100"> | 相关矩阵热图叠加连线标注 r 值与显著性 | 环境因子与群落/基因型矩阵关联、距离矩阵分析 |
| PCA 主成分分析图 | <img src="assets/figure-atlas/PCA.png" width="100"> | 样本投影至 PC 平面，附椭圆置信区间 | 群体结构分析、样本聚类趋势、降维可视化 |
| 雷达图 | <img src="assets/figure-atlas/radar.png" width="100"> | 多轴放射排列，闭合多边形综合表现 | 多指标品种/模型综合评估、性状剖面对比 |
| 山脊图 | <img src="assets/figure-atlas/RidgePlot.png" width="100"> | 多组密度曲线纵向错落叠放 | 多组/多时间点分布形态对比、性状分布趋势 |
| 桑基图 | <img src="assets/figure-atlas/sankey.png" width="100"> | 节点间流量宽度编码，多阶段流转 | 通路/流程转化路径、类别间流动归因分解 |
| 堆叠柱状散点复合图 | <img src="assets/figure-atlas/StackedBarScatter.png" width="100"> | 堆叠柱体+叠加散点标注个体数值 | 组成结构展示同时保留原始样本点 |
| 趋势图 | <img src="assets/figure-atlas/trend.png" width="100"> | 折线随连续变量走势，可含置信带 | 性状随环境梯度变化、时间序列走势 |
| 小提琴图 | <img src="assets/figure-atlas/violin_chart.png" width="100"> | 镜像密度轮廓呈现分布形状 | 组间分布形态与离散程度比较、非正态数据展示 |

---

## 单张参考图入库

你只需要把图片交给 agent，并说明“存进参考图库”。Skill 会打开原图、判断主图型和视觉语法、记录标签与来源边界、复制图片生成 sidecar 元数据，并要求 agent 用合成数据写一份视觉语法复现代码和 `reconstruction.png` 预览，再制作等尺寸原图/复现图对照并记录差异，最后重建索引并返回 reference ID。原始数据或原始论文代码不需要；没有复现代码或一致性审查的记录只能保持 `pending`，不能进入 reviewed 推荐池。默认按 `private_reference` 处理，只有明确给出可再分发许可时才进入公开素材范围。详见 `SKILL.md` 的 **Single-image reference intake** 和 [visual-reference-library.md](references/visual-reference-library.md)。

## 系统工作流

```text
┌─────────────────────────────────────────────────────────────┐
│  User Intent Parsing / 用户意图解析                           │
└─────────────────────────────────────────────────────────────┘
  Route → Intake → Reference Retrieval → Reference Inspection
      → Design Spec → Binding → Render → Compare → Critique
      → Repair → QA → Export

Reference DNA → StyleCapsule + JournalProfile → DesignPacket
      → CandidateSet → DesignPatch → RenderTrace → layered QA
```

**核心原则**：科学契约先于视觉参考；参考图只提供可测量的视觉语法。候选图必须消费同一份
`TypographySpec`、`PaletteSpec`、`LayoutSpec`、`ComponentSpec`，并经过结构化 critique/repair 与四层 QA。

---

## 安装与使用

`publication-figure-design` 是一个以 `SKILL.md` 为薄入口、以 `src/publication_figure_design/` 为当前运行时的 Skill 包。完整安装需保留 `references/`、`scripts/`、`assets/`、`profiles/`、`indexes/`、`schemas/` 和 `install/`；维护脚本只是 thin CLI wrappers，生产生命周期由 orchestrator 统一驱动。

所有仓库 Python 命令统一使用本机 `piepaper` 环境的解释器：

```powershell
& "D:\Anaconda\envs\piepaper\python.exe" <script-or-module>
```
详见 `references/runtime-environment.md`；禁止静默回退到 Conda `base` 或系统 Python。

在仓库根目录把当前运行时安装到同一环境后，`pfd` CLI 即可直接使用：

```powershell
& "D:\Anaconda\envs\piepaper\python.exe" -m pip install -e .
```

### Claude Code

如果尚未安装 Claude Code：

```bash
npm install -g @anthropic-ai/claude-code
claude
```

克隆仓库到稳定路径并安装 Skill：

```bash
mkdir -p ~/ai-skills
cd ~/ai-skills
git clone https://github.com/future3317/publication-figure-design.git publication-figure-design
cp -r publication-figure-design ~/.claude/skills/
```

安装后在 Claude Code 会话中直接描述需求即可自动触发：

```text
请使用 publication-figure-design 分析项目文件中的multip-traits.csv数据，并进行可视化分析。
```

```text
用publication-figure-design将data.csv数据绘制为一个 Nature 风格的差异表达火山图。
```

如需更新：

```bash
cd ~/ai-skills/publication-figure-design
git pull
cp -r . ~/.claude/skills/publication-figure-design/
```

### Codex

Codex 支持通过 `install/codex/` 中的 `manifest.yaml` + `instructions.md` 加载 Skill。将以下目录复制到 `~/.codex/skills/publication-figure-design/`：

```bash
git clone https://github.com/future3317/publication-figure-design.git publication-figure-design
cd publication-figure-design
mkdir -p ~/.codex/skills/publication-figure-design
cp -r SKILL.md references/ scripts/ assets/ install/codex/* ~/.codex/skills/publication-figure-design/
```

安装后在 Codex 会话中自然描述需求，Skill 会根据 `manifest.yaml` 中的触发规则自动激活。

也可以让 Codex 代为安装：

```text
从 https://github.com/future3317/publication-figure-design.git 安装 Codex skill。
克隆后将目录命名为 publication-figure-design，再将 SKILL.md、references/、scripts/、assets/ 和 install/codex/ 复制到 ~/.codex/skills/publication-figure-design/。
保持完整目录结构，不要只复制 SKILL.md。
```

### Cursor

将 Skill 规则文件复制到项目根目录，Cursor 在生成代码时会自动遵循其中的规范：

```bash
git clone https://github.com/future3317/publication-figure-design.git publication-figure-design
cp publication-figure-design/install/cursor/.cursorrules <your-project>/.cursorrules
```

`.cursorrules` 包含了配色方案、排版基线、导出规格等核心规则。如需更新规则，重新执行上述复制命令即可。

### GitHub Copilot

将 Skill 指令文件复制到项目的 `.github/` 目录，Copilot 在生成代码时会加载这些上下文：

```bash
git clone https://github.com/future3317/publication-figure-design.git publication-figure-design
mkdir -p <your-project>/.github
cp publication-figure-design/install/copilot/copilot-instructions.md <your-project>/.github/
```

如果已有 `.github/copilot-instructions.md`，建议将本 Skill 的内容追加到文件末尾。

### 其他 Agent

对于其他 AI 编程助手：

1. 保持仓库的稳定克隆副本
2. 创建一个轻量级的 subagent、slash command 或自定义 prompt wrapper，指向 `SKILL.md`
3. 确保 `references/`、`scripts/`、`assets/` 等目录与 `SKILL.md` 保持在同一相对路径下
4. 如果 Agent 有特殊的格式要求，可基于 `SKILL.md` 调整 frontmatter 和 body 结构

---

## 项目结构

```text
	publication-figure-design/                     ← 核心 Skill 包（本目录）
    ├── README.md                      ← 项目说明文档（本文件）
    ├── LICENSE                        ← Apache 2.0 许可证
    ├── SKILL.md                       ← 薄技能入口：Orchestrator、优先级与 Gate
    ├── references/                    ← 16 份共享知识文档
    │   ├── figure-contract.md         ← 图表合同：核心结论 + 证据链 + 审稿风险
    │   ├── color-palettes.md          ← 配色系统：分类/发散/连续 + 色盲友好
    │   ├── typography.md              ← 字体规范：Arial/Helvetica, ≥5pt 底限
    │   ├── journal-specs.md           ← 期刊尺寸：单栏 89mm / 双栏 183mm
    │   ├── export-specs.md            ← 导出规格：PDF/SVG 矢量 + 300dpi PNG
    │   ├── multipanel-layout.md       ← 多面板排版：反冗余 + 英雄面板 + 叙事顺序
    │   ├── directory-map.md           ← 图型目录映射：中英文关键词 → 资产路径
    │   ├── checklist.md               ← 完整 QA 检查清单
    │   ├── common-pitfalls.md         ← 常见陷阱与解决方案
    │   ├── revision-cases.md          ← 审稿修改案例库
    │   ├── journal-intel.md           ← 各期刊特有情报
    │   ├── figure-deconstruction.md   ← 图表解构：构图灵感参考
    │   ├── matplotlib.md              ← Python/matplotlib/seaborn 指南
    │   ├── complexheatmap.md          ← R ComplexHeatmap 指南
    │   ├── r-rendering.md             ← R PNG 渲染规范（cairo 设备）
    │   └── compose.R                  ← R 排版参考实现
    ├── src/publication_figure_design/ ← 当前生产编译器核心
    │   ├── contracts/                 ← ScientificContract、ReferenceDNA、DesignPacket 等
    │   ├── reference_intelligence/    ← 源类型 analyzer、DNA、hybrid retrieval
    │   ├── style/                     ← JournalProfile、StyleCapsule、StyleSpec compiler
    │   ├── design/                    ← 候选生成和 DesignPatch
    │   ├── layout/                    ← mm/pt primitives 和约束布局
    │   ├── renderers/                 ← SVG/vector assembler
    │   └── qa/                        ← L0/L1/L2/L3 分层 QA、RenderTrace、anti-copy
    ├── profiles/                      ← journal profiles + style capsules
    ├── evals/                         ← activation train/validation/holdout 数据
    ├── scripts/                       ← thin CLI wrappers、维护和 release gate
    ├── assets/
    │   ├── figures/                   ← 29+ 种图型生产脚本与预览
    │   │   ├── 3DHeatmap/             ← 3D 热图（R/ComplexHeatmap）
    │   │   ├── AUROC/                 ← AUROC 曲线
    │   │   ├── BarAblation/           ← 消融实验柱状图
    │   │   ├── BarCategorical/        ← 分类柱状图
    │   │   ├── BarComparison/         ← 模型对比柱状图
    │   │   ├── BarComposition/        ← 组成柱状图
    │   │   ├── BarDistribution/       ← 分布柱状图
    │   │   ├── ConfusionMatrix/       ← 混淆矩阵
    │   │   ├── CorrelationMatrix/     ← 相关性矩阵（ggpairs）
    │   │   ├── DensityHeatmap/        ← 密度热图
    │   │   ├── Frequency_3DHeatmap/   ← 频率 3D 热图
    │   │   ├── GroupedBarChart/       ← 分组柱状图
    │   │   ├── GroupedCorrelationMatrix/ ← 分组相关矩阵
    │   │   ├── GroupedViolin/         ← 分组小提琴图
    │   │   ├── KernelDensity/         ← 核密度估计
    │   │   ├── LineTrend/             ← 趋势折线图
    │   │   ├── Manifold/              ← 流形可视化
    │   │   ├── MantelCorrelation/     ← Mantel 相关性检验
    │   │   ├── MarginalDensity/       ← 边际密度图
    │   │   ├── MarkerGeneDotPlot/     ← 标记基因点图
    │   │   ├── PCA/                   ← PCA 主成分分析
    │   │   ├── PairedBoxScatter/      ← 配对箱线散点图
    │   │   ├── Radar/                 ← 雷达图
    │   │   ├── RidgePlot/             ← 山脊密度图
    │   │   ├── SankeyDiagram/         ← 桑基流图
    │   │   ├── StackedBarScatter/     ← 堆叠柱状散点复合图
    │   │   ├── Violin/                ← 小提琴图
    │   │   ├── heatmap/               ← 聚类热图
    │   │   ├── volcano/               ← 火山图
    │   │   ├── basic-plots/           ← 基础图型
    │   │   ├── multipanel/            ← 多面板模板
    │   │   └── other/                 ← 长尾图型
    │   └── figure-atlas/              ← 图鉴预览 PNG 合集
    └── install/                       ← 跨平台适配
        ├── claude-code/               ← Claude Code（原生支持，开箱即用）
        ├── cursor/                    ← Cursor IDE 适配
        ├── copilot/                   ← GitHub Copilot 适配
        └── codex/                     ← Codex CLI 适配
```

---

## 质量评估与测试

### 分层 QA 协议

| 层级 | 名称 | 责任 |
|------|------|------|
| L0 | Hard Technical | clipping、重叠、尺寸/DPI、字体嵌入、向量文本、颜色空间 |
| L1 | Scientific | 数据映射、统计变换、坐标/单位、不确定性和 provenance |
| L2 | Structural Visual | panel topology、比例、留白、对齐、legend、annotation |
| L3 | Perceptual/Aesthetic | 层次、平衡、风格适配、专业完成度、参考亲和度 |

### 运行评估

```bash
# 快速检查
pfd eval quick

# 完整开发评估
pfd eval full

# 视觉 benchmark / holdout
pfd eval visual

# 与 CI 完全相同的 release gate
pfd eval release

# 提交/PR 强制门禁（contract → unit → orchestrator → reference → fidelity → benchmark → adapters → canary）
& "D:\Anaconda\envs\piepaper\python.exe" scripts/ci_gate.py
```

CI 对每次 push 和 pull request 自动执行同一门禁。检索阈值为 Recall@1 ≥ 0.90、
Recall@3 ≥ 0.97、NDCG@3 ≥ 0.95；生成质量按结构、构图、留白、字体、角色配色、
线/标记、标注、密度和 overall style 分维度设 floor，且要求科学正确性和 export
contract 100%、champion regression 为 0。参考图入库遵循 `raw → analyzed → reviewed →
benchmarked → production`，不会因“有代码”自动进入推荐池。

---

## 贡献指南

Publication Figure Design 采用 Skill 插件架构，新增参考图或图型时沿当前路由维护：

1. 用户提供参考图时使用 `pfd reference ingest` 开始 `raw` 入库，再按 `reference_intake` 路由运行 analyze → DNA → reproduction/fidelity → review/benchmark
2. 需要维护生产资产时才在 `assets/figures/<FigureType>/` 增加脚本、预览和 sidecar metadata，并通过 `asset-adaptation` 路由接入
3. 新图型在 `references/directory-map.md` 中添加关键词映射，并补齐对应 benchmark/canary
4. 运行 `& "D:\Anaconda\envs\piepaper\python.exe" -m publication_figure_design.cli eval release` 验证通过

---

## 许可证

[Apache 2.0](LICENSE) © 2025 Publication Figure Design Contributors
