# ACADEMIC FIGURE SKILL — 架构审计报告

> 面向后续架构设计的技术报告，基于本地仓库 `C:/Users/LRH/.agents/skills/academic-figure-skill` 的真实状态。
> 审计日期：2026-08-11。本次审计为只读分析，未修改任何代码、配置、文档或资产。
> 上游来源：`https://github.com/TingxiYu/academic-figure-skill`（本地无 `.git`，为去版本化的二次开发副本）。

---

## 一、Repository Snapshot

### 结构概览

```
academic-figure-skill/
├── SKILL.md                  # skill 入口：YAML frontmatter + 8 步工作流（525 行, 29 KB）
├── README.md / README_EN.md  # 中/英项目介绍（面向人类用户，含图集展示）
├── LICENSE                   # Apache-2.0
├── references/               # 16 个规范文件（15 .md + compose.R），2542 行
├── scripts/                  # 20 个 .py + .eval_results.json（Python 包，含 __init__.py）
├── assets/
│   ├── figures/              # 32 个图型目录：55 个生产脚本 + 96 个预览（70 MB）
│   └── figure-atlas/         # 19 个展示 PNG（14 MB，仅 README 使用）
└── install/                  # claude-code / codex / copilot / cursor 四个平台适配（自动生成）
```

### 一级目录职责矩阵

| 目录/文件 | 职责 | 读者 | runtime 依赖 | 分类 |
|---|---|---|---|---|
| `SKILL.md` | skill 触发定义 + 主工作流编排 | agent（dispatcher + 执行时） | 是（入口） | instruction |
| `README*.md` | 项目介绍、安装、图集展示 | 人类用户 | 否 | documentation |
| `references/` | 规范/协议/映射表（QA、期刊、配色、排版、图型路由） | agent 执行时按需加载 | 是（workflow 步骤引用） | instruction + configuration |
| `scripts/` | QA 校验、组合引擎、评测、色板管理、适配器生成 | agent CLI 调用 / 少数作为 library import | 部分（compose、palette_manager、qa_validator） | executable code + QA/testing |
| `assets/figures/` | 每图型的生产脚本 + 渲染预览 | agent（COPY-FIRST 复制源） | 是（Step 4/5 核心依赖） | production asset |
| `assets/figure-atlas/` | 展示图集 | 人类（仅 README 引用） | 否 | visual reference（事实上的） |
| `install/` | 平台安装适配 | 人类安装时 | 否 | configuration（generated） |

### 文件统计（实测）

- 文件总数：**228**
- Python：**55**（scripts/ 20 + assets/figures/ 35）
- R：**21**（references/compose.R 1 + assets/figures/ 20）
- Markdown：**26**
- PNG：**108**（figures/ 89 + figure-atlas/ 19）；PDF：**7**；JPG/SVG：**0**
- 其他：yaml 1、json 1、.cursorrules 1、LICENSE 1、pyc 7
- `assets/figures/` 图型目录：**32**（其中 29 个含实际脚本；`basic-plots/`、`multipanel/`、`other/` 为仅有占位 README 的空目录）
- 每图型平均：**1.90 个 script**（55/29），**3.0 个 preview**（96/32）

---

## 二、Git / Local Modification Summary

### Git 状态

```
git status     → fatal: not a git repository
git remote -v  → （无）
git log        → （无）
```

**本地目录不是 git 仓库**（`.git` 已在二次开发前被移除或从未带入）。无法做 `git diff upstream/main...HEAD`。

### 上游基线识别

通过 GitHub API 对比上游仓库 `TingxiYu/academic-figure-skill` 的 `scripts/` 与 `references/` 文件清单（2026-08-11 查询），可确定本地差异：

### 本地新增（相对 upstream）

| 文件 | 意图与影响 |
|---|---|
| `scripts/palettes.py`（3.5 KB） | 7 套内置命名 categorical palette 的纯数据模块（每套 8 hex，含 `name_zh`/`tags`/`type`/`source` 元数据 + 中文别名映射）。上游无此文件。 |
| `scripts/palette_manager.py`（12.5 KB） | 统一色板管理 API（查询/默认色板/确定性扩展/预览/校验）。上游无此文件。 |
| `scripts/test_palette_manager.py`（6.0 KB） | palette manager 的 23 条 unittest。上游无此文件。 |
| `scripts/__init__.py`（514 B） | 使 scripts/ 成为 Python 包并 re-export palette API。上游无此文件（上游 scripts/ 为扁平脚本集）。 |

### 本地修改（相对 upstream）

| 文件 | 意图与影响 |
|---|---|
| `references/color-palettes.md` | 上游版本 85 行、不含 `palette_manager` 字样；本地 152 行，末尾追加「Optional: Unified Categorical Palette Manager」一节，原有 CNS 基线常量块未动。非破坏性追加。 |

### 本地删除

- 未发现（上游 scripts/ 的 17 个 .py 与 references/ 的 16 个文件在本地全部存在）。
- 注意：本地删除了 `.git` 本身，导致未来与 upstream 同步/再分叉的成本升高。

---

## 三、Skill Entry Point Analysis（SKILL.md）

**规模**：525 行 / 29 KB / 约 8–9k token（中英混合，估算值）。

### 1. Trigger / scope

frontmatter `description` 定义为：manuscript submission 场景的科研图创建/润色/审查/导出（Nature/Cell/Science 导向）。明确 DO-NOT-trigger：交互式 dashboard、无发表意图的探索性分析、数学函数图、**pie/3D charts**、PPT、Illustrator/Figma-first。SKIP：统计检验、数据清洗、文献调研、代码调试。

### 2. 主工作流步骤

共 **9 个编号步骤（Step -1 到 Step 7）+ 1 个插入步骤（5.5）**：

| Step | 内容 | 必须? | 依赖 references | 依赖 assets/figures | 依赖 scripts | 用户确认 gate |
|---|---|---|---|---|---|---|
| -1 | 理解任务（DISPATCH FIRST） | 是 | — | — | — | **硬 STOP**：有数据无问题必须问 |
| 0 | 分类 & 数据解析（0a 构图原型 / 0b 数据结构） | 是（DATA INTEGRITY 不可协商） | — | — | compose(archetype=) | 数据形状不符必须告知并等待 |
| 1 | 推荐 & 论证（固定 Visualization Plan 表） | 是 | — | — | — | **显式确认**，反馈后重述 |
| 2 | 运行时环境检测 | 是 | — | — | — | 不允许静默降级，用户决定 |
| 3 | 样式基线注入（ALWAYS FIRST） | 是 | typography / color-palettes / export-specs / journal-specs（COPY VERBATIM） | — | — | 无 |
| 4 | 生产资产扫描（每面板） | 是 | directory-map.md | **是（核心）** | — | VISUAL ADAPT 的列映射需用户确认 |
| 5 | 生成（COPY-FIRST 规则） | 是 | r-rendering.md（R 时） | **是（核心）** | — | 降级必须记录/告知 |
| 5.5 | 数据验证 | 是 | （阈值复制自 checklist VV-5） | — | — | 无 |
| 6 | QA 协议 | 是 | checklist.md（AP/CL/VI/VV 全套） | — | qa_validator（间接） | 无运行时则跳过 Pass 3 并警告 |
| 7 | 交付（含统计报告） | 是 | export-specs.md | — | — | 无 |

### 3. 对 agent 的潜在问题

- **重复读取**：Style baseline（Step 3）、QA（Step 6）、Anti-Pattern 三处都指向相同的规则集合（typography/color/export/pitfalls），agent 在单次任务中可能多次加载同一 reference。
- **token 消耗**：SKILL.md 本体 ~9k token 每次触发必载；加上 Always Load 的 typography/color-palettes/export-specs/journal-specs/figure-contract/journal-specs，单次任务固定开销约 15–20k token（估算）。
- **指令冲突**：见第四节末尾的冲突清单（字体 7 vs 8、archetype 默认值矛盾等）——agent 照单全收时无法同时满足。
- **workflow 死板**：小任务（"把这张图导出成 300 dpi PDF"）也必须走 Step -1→7 全管道，9 步中 6 步带用户确认 gate，轻量任务交互成本过高。没有"快速通道"。
- **Step 5.5 阈值表**是 checklist.md VV-5 的近乎逐字子集——同一规则两处维护。

### 4. 内容归属判断

- **应留在 SKILL.md 的核心原则**：问题驱动（question-driven）、数据完整性规则、COPY-FIRST 契约、用户确认 gate 的存在性、降级必须透明。
- **应抽离的内容**：Design Principles 四条（与 references 重复）、Step 5.5 阈值表（checklist 已有）、Anti-Pattern Recognition（common-pitfalls + checklist Pass 0 已有）、Class A/B/C 参数分类法（可入 asset 开发规范）、eval 脚本清单（可入 scripts/README）。

### 5. 分类判定：**B — 中等编排层（偏重）**

不是精简 router：内含完整的 5 分支 dispatch 决策树、7 步 VISUAL ADAPT 子协议、borrowing 表、强制脚本结构规范、禁用模式列表。但也不是 monolithic：样式数值、QA 检查项、期刊细节、案例库都真实委托给了 references/。约 1/3 内容（Design Principles、5.5 表、Anti-Pattern 节）是可移除的重复 reference 材料，移除后是更健康的 B。

---

## 四、Reference System Analysis

16 个文件，2542 行 / ~127 KB。

| file | purpose | referenced by | importance | overlap | recommendation |
|---|---|---|---|---|---|
| `checklist.md`（470 行） | 四轮 QA 协议（AP-0..7/CL-1..7/VI-1..7/VV-1..5） | SKILL.md Step 6；qa_validator.py 的代码蓝本 | 核心 | VV-5 阈值与 SKILL.md Step 5.5 重复；AP/VI 与 common-pitfalls 重复 | 保留；修复乱码；作为 QA 唯一权威源 |
| `typography.md`（90 行） | 字体/字号 COPY VERBATIM 基线 | SKILL.md Step 3 + Always Load | 核心 | 与 matplotlib.md、compose.R、checklist AP-0 字号冲突（7 vs 8）；**同文件内两个 theme_cns 定义（base_size 8 和 7）** | 保留但需消除内部矛盾，成为唯一样式权威 |
| `color-palettes.md`（152 行） | CNS 配色基线（COPY VERBATIM）+ 本地新增的 palette manager 可选 API | SKILL.md Step 3；common-pitfalls/complexheatmap/matplotlib 交叉引用 | 核心 | diverging `#2166AC/#F7F7F7/#B2182B` 出现在 4 个文件 | 保留；基线 hex 应收敛为机器可读单一源 |
| `export-specs.md`（110 行） | 导出基线（矢量/300dpi/fonttype42） | SKILL.md Step 3/7；checklist AP-5/CL-3/CL-4 | 核心 | 与 matplotlib/complexheatmap/r-rendering/typography 重复 | 保留为导出唯一权威，其他文件改为引用 |
| `journal-specs.md`（63 行） | 89/183 mm 尺寸、spine/tick 硬规范 | SKILL.md Step 3 + Always Load | 核心 | spine 线宽与 checklist CL-5 不一致（0.5–0.6 vs 0.5–0.8） | 保留 |
| `journal-intel.md`（89 行） | 各期刊未成文编辑偏好 | SKILL.md On-Demand | 中 | 无 | 保留 |
| `directory-map.md`（44 行） | 关键词→图型目录路由表（35 行条目） | SKILL.md Step 4；check_references.py 校验 | 核心 | 无 | 保留；未来应升级为机器可读 registry（见八节） |
| `figure-contract.md`（93 行） | 五点图契约（结论先行） | SKILL.md Always Load | 中 | §3 archetype 默认值与 SKILL.md Step 0a **直接矛盾** | 保留但修正矛盾；步骤编号引用已过时 |
| `figure-deconstruction.md`（141 行） | 5 个 CNS 已发表图逆向解构 | SKILL.md On-Demand | 中 | 无 | 保留——这是 visual reference 理念的雏形 |
| `multipanel-layout.md`（74 行） | 多面板反冗余、hero panel、叙事顺序 | SKILL.md On-Demand | 中 | 步骤编号引用过时 | 保留 |
| `common-pitfalls.md`（106 行） | 跨图型常见错误 ❌/✅ | SKILL.md On-Demand | 中 | 与 checklist AP 系列、journal-specs 大量重复 | 考虑合并入 checklist 或明确分工（pitfalls=案例，checklist=协议） |
| `revision-cases.md`（194 行） | 10 个审稿拒稿案例 | SKILL.md On-Demand；checklist VI-7 | 中 | 个别规则与 journal-specs 重复 | 保留（独特价值） |
| `matplotlib.md`（65 行） | matplotlib/seaborn 发表级规范（中文） | SKILL.md On-Demand | 中 | rcParams 与 typography.md 冲突（font.size 7 vs 8） | 保留为运行时特化，删除与 typography 重复的基线块 |
| `complexheatmap.md`（88 行） | R ComplexHeatmap 规范（中文） | SKILL.md On-Demand | 低-中 | diverging 色板与 color-palettes 重复 | 保留为运行时特化 |
| `r-rendering.md`（46 行） | R PNG 渲染三规则 | SKILL.md Step 5（两处引用） | 中 | 无 | 保留 |
| `compose.R`（192 行） | R 端组合引擎（theme_cns/compose_figure） | **仅文件自身头部提及；SKILL.md 的 References 表未列出** | 高（R 路径必需） | theme_cns 与 typography.md 两处定义不同 | 保留；应登记进 SKILL.md references 表；常量与 compose.py 需单一源 |

### 关键发现

1. **重复**：字体基线 4 处（typography ×2、matplotlib、compose.R）、diverging 色板 4 处、导出规则 5 处、spine/tick 规则 4 处、"n<10 显示散点" 5 处。
2. **SKILL.md 复制 references**：Design Principles、Step 5.5、Anti-Pattern 三处（见三节）。
3. **直接冲突**（agent 无法同时满足）：
   - 字号：`typography.md` verbatim 块 `font.size: 8` vs `checklist.md` AP-0 要求 7 vs `matplotlib.md` 用 7。
   - archetype 默认：SKILL.md Step 0a "不确定默认 `asymmetric_mixed`" vs `figure-contract.md` §3 "不确定默认 quantitative grid"。
   - spine 线宽：journal-specs 0.5–0.6pt vs checklist CL-5 0.5–0.8pt。
   - 触发器排除 "3D charts"，但资产库含 `3DHeatmap/`、`Frequency_3DHeatmap/` 且 directory-map 有对应条目。
4. **过时引用**：checklist.md 称 QA 为 "Hub workflow Step 5"（现 Step 6）；figure-contract 引用不存在的 "Hub Step 1/2"；multipanel-layout 引用 "Step 4 生成布局"（Step 4 是资产扫描）。
5. **编码损坏**：`checklist.md` 存在大面积乱码（"鈥?"、"脳"、"鈫?" 等），VV-5 部分阈值不可读。这是 QA 核心文件，损坏影响实际使用。
6. **应转机器可读的**：directory-map（路由表）、style 基线常量（typography/color/export 的 COPY VERBATIM 块）——目前以"供 LLM 抄写的 markdown 代码块"形式存在，同时被 compose.py 硬编码、eval_runner 校验，三处手工同步。

---

## 五、Figure Asset Architecture

### 图型资产清单（32 目录全量）

| directory | .py | .R | PNG | PDF | README/meta | script↔preview 对应 |
|---|---|---|---|---|---|---|
| 3DHeatmap | 0 | 1 | 4 | 0 | 无 | 1 script → `_1`–`_4` |
| AUROC | 3 | 0 | 3 | 0 | 无 | 不一致（`AUROC1_1.png` vs `AUROC2.png`） |
| BarAblation | 3 | 0 | 6 | 0 | 无 | 弱（preview 名与 script 名不对应） |
| BarCategorical | 2 | 0 | 2 | 0 | 无 | 清晰 |
| BarComparison | 3* | 0 | 2 | 0 | 无 | *含 1 个数据 helper（`raw_data.py`） |
| BarComposition | 2 | 0 | 2 | 0 | 无 | 清晰 |
| BarDistribution | 1 | 0 | 1 | 0 | 无 | 清晰 1:1 |
| ConfusionMatrix | 1 | 0 | 1 | 0 | 无 | 清晰 1:1 |
| CorrelationMatrix | 0 | 3 | 3 | 0 | 无 | 清晰 |
| DensityHeatmap | 0 | 1 | 7 | 0 | 无 | `_2`–`_8`（无 `_1`） |
| Frequency_3DHeatmap | 0 | 1 | 6 | 0 | 无 | `_1`–`_6` |
| GroupedBarChart | 4 | 0 | 2 | 0 | 无 | **v2–v4 无 preview** |
| GroupedCorrelationMatrix | 0 | 1 | 5 | 4 | 无 | `_1`–`_5` |
| GroupedViolin | 1 | 0 | 1 | 0 | 无 | 清晰 1:1 |
| KernelDensity | 0 | 3 | 6 | 0 | 无 | 主图 + `_detail` 变体 |
| LineTrend | 3 | 0 | 3 | 0 | 无 | 仅语义对应 |
| Manifold | 3 | 0 | 3 | 0 | 无 | 清晰 |
| MantelCorrelation | 0 | 3(.r) | 3 | 0 | 无 | 清晰；扩展名大小写不一致 |
| MarginalDensity | 1 | 0 | 6 | 0 | 无 | `_1`–`_6` |
| MarkerGeneDotPlot | 1 | 0 | 1 | 0 | 无 | 清晰 1:1 |
| PCA | 0 | 2 | 2 | 0 | 无 | `plot_PCAa.R` 无明确 preview |
| PairedBoxScatter | 0 | 3 | 6 | 0 | 无 | 主图 + `_detail` |
| Radar | 1 | 0 | 1 | 0 | 0 | 清晰 1:1 |
| RidgePlot | 0 | 2 | 4 | 0 | 无 | 主图 + `_detail` |
| SankeyDiagram | 1 | 0 | 3 | 0 | 无 | `_1`–`_3` |
| StackedBarScatter | 1 | 0 | 2 | 3 | 无 | 清晰（PDF 为主输出） |
| Violin | 1 | 0 | 1 | 0 | 无 | 清晰 1:1 |
| basic-plots | 0 | 0 | 0 | 0 | `_README.md` | 占位（规范待定资产） |
| heatmap | 2 | 0 | 2 | 0 | `_README.md` | 仅语义对应 |
| multipanel | 0 | 0 | 0 | 0 | `_README.md` | 占位 |
| other | 0 | 0 | 0 | 0 | `_README.md` | 占位（长尾 fallback） |
| volcano | 1 | 0 | 1 | 0 | `_README.md` | 清晰 1:1 |

**全局特征**：
- 命名主约定 `plot_<Name>.<ext>` + `plot_<Name>.png`，但仅约半数目录严格满足 1:1；多 preview 用 `_N` 后缀，编号有缺号、有不一致。
- **全库无任何 yaml/json 元数据**；仅 5 个 `_README.md`（其中 3 个是"未来资产规范"占位）。
- **全库不附带任何数据文件**：脚本分两派——(a) 内置硬编码 demo 数据可直接运行；(b) 读外部 CSV/TSV 路径，原地执行必然失败。
- 机器可检索性：仅靠目录名 + directory-map 关键词；人可浏览性：有 preview PNG 但无 gallery 索引（README 的表格只覆盖部分图型）。

### 5 个代表图型深入分析

**GroupedViolin**（`plot_GroupedViolin.py`，173 行）
- 数据入口：模块底部 `pd.read_csv("Violin-data.csv")`——**CSV 不随库分发**。
- 视觉参数：函数参数带默认值；demo 调用处硬编码 hex list；fallback tab20。
- 核心函数 `plot_violin_significance()` 是干净的参数化可复用函数（df 传参、可换检验函数）。
- 换数据：需 wide-format CSV + 编辑 `groups`/`pairs` 列表，中等成本，函数本体不易破。
- 判定：**reusable component + executable example**（5 个中最健康）。

**PCA**（`plot_PCA.R` 254 行 + `plot_PCAa.R` 179 行）
- 数据入口：3 个 TSV 路径（`./Data/smetana_...tsv`）——文件不随库分发。
- 颜色走外部 color_file TSV（分离良好）；但 `theme(size=15/16)`、`"royalblue"` 等硬编码。
- **含领域硬编码逻辑**：正则 `"M_(.+)_e"` 提取化合物 ID、`met_category` 聚合——特定于某代谢组数据集。
- 换数据：ID 格式不同必须改函数内部，不只是参数。
- 判定：**reference implementation**（真实论文分析代码，需改造才能复用）。

**heatmap**（`plot_composition.py` 81 行 + `plot_comparison.py` 228 行）
- composition：模块级 `DATA` dict 全硬编码；rcParams 硬编码（usetex、helvetica、16pt）；数据与绘图完全混合。判定：**executable example**。
- comparison：~40 行硬编码 benchmark 数组 + 13 色 hex 硬编码，全部在 `__main__` 块，连函数都没有。判定：**reference implementation / 归档脚本**，复用需重写。
- 两者依赖 `text.usetex=True`——未声明的 LaTeX 运行时依赖。

**MarginalDensity**（`plot_VariableCorrelation.py`，320 行）
- 数据入口：`pd.read_csv('./data.csv')`——不随库分发。
- 视觉参数：**集中式 CONFIG dict**（列名、组顺序、硬编码 hex、轴限、inset 位置）——5 个中最接近可配置模板。
- 但混有领域语义（`is_drep95` 质量列）、依赖第三方 `statannotations`、写 Excel/HTML/LaTeX 副作用重。
- 判定：**template**。

**StackedBarScatter**（`plot_StackedBarScatter.py`，326 行）
- 数据入口：硬编码 DataFrame 字面量（18 值 × 3 组）+ 派生 demo。
- 视觉参数：~40 个带文档 kwargs（docstring 含中文参数手册）；默认 3 色 hex 硬编码 + tab10 扩展。
- 风格与数据通过 kwargs 解耦；换数据容易（传自己的 wide DataFrame）。
- 判定：**reusable component**（附带 executable example）。

### Copy-First 模式判定

**优点（真实存在）**：
- 脚本来自真实发表场景，视觉质量基线高；复制-改数据路径对 agent 是低出错操作（比从零生成可控得多）。
- preview PNG 提供了"语义匹配检查"的锚点（VISUAL ADAPT 的硬 STOP 依据）。

**缺点（真实存在）**：
- 资产质量两极分化：少数 reusable component/template，多数是 executable example 甚至归档脚本（领域正则、"ours" benchmark 行、数据集专属列语义）。
- (b) 派脚本原地不可运行（无数据文件），COPY-FIRST 的"复制→只改数据路径→执行"对 (a) 派又无数据路径可改——契约与资产现状存在结构性错位。
- 无元数据导致 agent 无法预知一个脚本属于哪一派、有哪些隐藏依赖（LaTeX、statannotations），只能读了才知道。
- 全部脚本颜色硬编码，与本地新增的 palette manager 零集成（见七节）。

---

## 六、Figure Discovery / Routing

### 当前管道（以"给我画一个分组小提琴图"为例）

```
user request "分组小提琴图"
│
├─[1] figure semantic classification（agent 判断）
│     输入: 用户自然语言  输出: 匹配 directory-map.md Keywords 列
│     deterministic: 否（LLM 语义匹配）
│     failure mode: 关键词不在 35 行表内 → 无匹配
│     fallback: "ls figures/"（注：directory-map 原文路径少 assets/ 前缀，与 SKILL.md 不一致）
│
├─[2] directory map lookup（确定性查表）
│     输入: 匹配行  输出: 目录名 GroupedViolin
│     deterministic: 是（静态 3 列 markdown 表）
│     failure mode: 一行多目录（cross-type 行如 "RDA via PCA"）→ 需二次判断
│
├─[3] asset directory scan（确定性）
│     输入: assets/figures/GroupedViolin/  输出: plot_GroupedViolin.py + plot_GroupedViolin.png
│     deterministic: 是（ls）；check_references.py 保证表↔目录双向覆盖
│     failure mode: 目录内多脚本（如 GroupedBarChart v1–v4）→ 无元数据指导选哪个
│
├─[4] script matching / runtime selection（半确定）
│     输入: 脚本集 + Step 2 的运行时检测结果  输出: 选定脚本
│     deterministic: 运行时检测是；脚本选择否（无变体元数据，v1–v4 靠 agent 读代码判断）
│     failure mode: 选到无 preview 的变体（v2–v4）→ 语义匹配检查无锚点
│
├─[5] data adaptation（agent 判断，COPY-FIRST / VISUAL ADAPT / PARAM INHERIT / CROSS-TYPE INHERIT 决策树）
│     输入: 用户数据结构 vs 脚本预期  输出: 适配后的 <panel>_production.<ext>
│     deterministic: 决策树分支条件是，兼容性是判断否
│     failure mode: 结构不兼容逐级降级；每次降级要求记录并告知用户
│
└─[6] render + QA（确定性机制 + agent 执行的清单协议）
      输入: 适配脚本  输出: PNG/PDF + QA 报告
      failure mode: 无运行时 → Pass 3 跳过并警告
```

### 当前系统本质

**A（directory lookup）+ C（example retrieval）的混合**：用静态关键词表做目录级路由（A），然后取目录内的脚本作为"最近邻示例"进行复制改造（C）。**不是** template retrieval（脚本不是参数化模板，无 slot/schema），**完全没有** visual retrieval（无任何按视觉特征检索的机制；preview PNG 仅在选定目录后用于语义校验）。

### 500–5000 张示例时的可扩展性

**当前架构不能工作**，原因：

1. directory-map 是单一扁平表，35 行已是人工维护极限；500+ 条目时关键词冲突不可避免（"bar" 已对应 6 个 Bar* 目录）。
2. 无二级分类（图型 → 子类型 → 变体），无法表达"同一个 grouped violin 的 10 种视觉方案"。
3. 无元数据 → 无法按 palette/layout/journal style/density 过滤。
4. 无机器可读 registry → 检索完全依赖 LLM 逐行读 markdown，token 成本随条目线性增长。
5. script↔preview 命名约定不统一，程序无法稳定地从脚本找到预览图。

---

## 七、Palette Manager Audit

### 涉及文件（全部为本地新增/修改，见二节）

- `scripts/palettes.py`（3.5 KB）— 纯数据：7 套 palette × 8 hex，元数据 schema `{id, name_zh, colors, tags, type: "categorical", source: "custom"}`，`ZH_TO_ID` 中文别名映射。
- `scripts/palette_manager.py`（12.5 KB）— API 层。
- `scripts/test_palette_manager.py`（6.0 KB）— 23 条 unittest。
- `scripts/__init__.py` — 包化 + re-export。
- `references/color-palettes.md` — 末尾追加「Optional: Unified Categorical Palette Manager」文档节。

### 完整 API

| API | 行为 |
|---|---|
| `list_palettes()` | 返回全部 palette 的 id / name_zh / tags |
| `get_palette(name, n=None)` | 按英文 id 或中文别名取色；n ≤ 8 返回**确定性前 n 色**（不随机） |
| `get_palette_info(name)` | 返回完整元数据 dict |
| `resolve_palette(name=None, n=None)` | 绘图函数统一入口；`name=None` 用默认 palette |
| `resolve_colors(colors=None, palette=None, n=None)` | 优先级：**显式 colors > 显式 palette > 默认 palette** |
| `set_default_palette(name)` / 默认 `pastel_girl` | 模块级默认切换，非法名报错 |
| `extend_palette(name, n)` | n > 8 时：**原始 8 色完整保留在列表前端**，补充色为 HSL 空间均匀插值的确定性生成色，不循环重复 |
| `preview_palettes(..., font=None)` | matplotlib 色块预览图（font 参数解决中文缺字形） |
| `validate_palettes()` | QA 校验（数量、hex 合法性等） |

### 测试执行结果（实测）

```
$ cd scripts && python test_palette_manager.py
Ran 23 tests in 0.001s — OK
```

23/23 通过。覆盖：全部 palette 可获取、每套恰好 8 个合法 hex、中/英名解析、n 参数、非法名错误信息、默认切换、显式颜色不被覆盖、扩展确定性、原始 8 色保留。

### 评估

- **API 设计合理**：单一数据模块 + 单一管理模块 + 包级 re-export；确定性行为（子集不随机、扩展不循环、原始色前置）符合科学绘图复现要求；显式颜色优先级正确。
- **与现有 style baseline 的关系**：**并存但不同源**。CNS 基线 hex（`CATEGORICAL`/`DIVERGING`/`SEQUENTIAL`）仍硬编码在 `compose.py` 并以 COPY VERBATIM 块存于 `color-palettes.md` 前 85 行；palette manager 的 7 套色板是独立的"命名主题"体系，两者无映射、无冲突检测。eval_runner 的 `color:consistency` 检查只维护 compose.py ↔ color-palettes.md 旧基线的一致，不涉及新模块。
- **是否被生产脚本使用**：**没有**。对 `assets/figures/` 全库 grep `palette_manager|palettes` 零命中；55 个生产脚本全部硬编码 hex 或用 matplotlib/ggplot2 默认色。
- **定位判定：B — 基础设施完成但未接入绘图层**。

### 渐进接入路径建议（避免大规模重写）

1. **不动存量 55 个脚本**——它们是"已发表视觉"的快照，硬编码 hex 即其历史真实性的一部分。
2. 接入点放在**生成侧**而非资产侧：SKILL.md Step 3（Style Baseline Injection）和 Step 5（COPY-FIRST 后的 VISUAL ADAPT / PARAM INHERIT 分支）是 agent 写新代码的地方——在这两处指示 agent 用 `resolve_colors()` 取色，即可覆盖所有新生成代码，无需改任何资产文件。
3. `compose.py` 的硬编码 `CATEGORICAL` 可改为从 palette manager 取默认（或注册 CNS 基线为第 8 套 palette，`source: "cns-baseline"`），一处改动消除三处同步。
4. 新增资产规范（未来的 `_README.md` 标准）中要求新脚本"颜色经由 palette manager 或显式 CONFIG"，自然过渡。

---

## 八、Visual Example / Reference Library Readiness

### 现状：两个概念已混在同一目录树下，但只有一个半机制

- **A. Production Assets**（可执行/可改造代码）：`assets/figures/` 的 55 个脚本。定位明确（COPY-FIRST 的复制源）。
- **B. Visual References**（视觉灵感，无代码）：`assets/figure-atlas/` 的 19 张 PNG——但它是为 README 营销手工组装的，**SKILL.md 和 references 从不引用它**，agent 工作流中不存在。另外 `references/figure-deconstruction.md`（5 个 CNS 图的文字解构）是 B 的"文字化"雏形，`assets/figures/` 里的 96 张 preview 事实上也兼作 B（VISUAL ADAPT 的语义匹配锚点）。

即：**A 有机制（directory-map + COPY-FIRST），B 无机制（无目录、无元数据、无检索路径、无 agent 引用）**。

### 当前 assets/figures 不适合承担 visual reference 职责的原因

1. 目录即图型，一个图型一个目录——无法容纳"同图型 10 种视觉方案"而不污染生产资产池。
2. 入库门槛隐含为"有可执行脚本"，image-only 参考无处可放（figure-atlas 无元数据、无引用，是死资产）。
3. 无质量分层：reusable component 与归档脚本混居，agent 无法区分。
4. 命名/组织围绕"代码"设计（`plot_X.py`），不围绕"视觉案例"设计。

### 建议的分离架构（仅建议，不实现）

```
assets/
├── figures/              # Production Assets（现状保留，逐步加 metadata）
│   └── <FigureType>/
│       ├── plot_X.py
│       ├── plot_X.png
│       └── asset.yaml    # 新增：每个资产的元数据
├── visual-references/    # Visual References（新建）
│   └── <FigureType>/
│       ├── ref_<id>.png
│       └── ref_<id>.yaml
└── figure-atlas/         # 保留为 README 展示，或迁入 visual-references/showcase/
```

### 元数据 schema 建议（每个 example 一文件，或汇总为 registry.jsonl）

用户提议的字段基本合理，建议补充/调整：

```json
{
  "id": "gv_nature_2024_001",
  "kind": "production | visual_reference",
  "figure_type": "GroupedViolin",
  "subtype": "with_stripplot_significance",
  "source": "paper_doi | github_url | self_generated | upstream",
  "tags": ["pastel", "minimal", "horizontal"],
  "palette": "sweet_macaron",
  "layout": "single_column_89mm",
  "journal_style": "nature",
  "n_groups": 4,
  "data_density": "medium",
  "has_code": true,
  "code_path": "assets/figures/GroupedViolin/plot_GroupedViolin.py",
  "image_path": "assets/figures/GroupedViolin/plot_GroupedViolin.png",
  "quality": "production_ready | reviewed | draft",
  "runtime": ["python", "matplotlib", "statannotations"],
  "notes": "..."
}
```

关键新增字段理由：`kind`（区分 A/B）、`quality`（支撑质量分层与晋升）、`runtime`（隐藏依赖显性化，解决五节发现的 LaTeX/statannotations 问题）、`n_groups`/`data_density`（支撑结构化查询）。

### 未来查询支持

- **结构化过滤**（metadata 即可，无需 embedding）：figure_type、palette、journal_style、n_groups、layout、quality、has_code。覆盖用户列举的 "grouped violin / pastel / Nature style / 4 groups / horizontal / publication / dense data"。
- **自由文本/语义**（"highlight one category"、"清新感"）：tags + notes 的文本匹配可起步；规模化后需要 embedding。
- **视觉语义检索（CLIP 等）**：**在示例达到数百张且结构化过滤不够用时才值得引入**。当前 96 张 preview 的规模下，metadata 过滤 + LLM 看几张候选 PNG 的"视觉核验"（agent 本身能读图）已足够。不建议现在实现 embedding 系统——维护成本高于收益，且 agent 的多模态读图能力已构成穷人的 visual retrieval。

### 规模演化判断

- ~100 张：目录 + metadata 文件足够。
- ~500 张：需要 registry.jsonl 汇总索引（单次扫描目录 I/O 开始浪费 token）。
- ~1000+ 张：才需要考虑 embedding/向量索引；届时 registry 中的 image_path 可直接喂 CLIP。

---

## 九、Example Ingestion Workflow（未来工作流草案 vs 现状缺口）

目标：看到好看的图 → 放入 skill → 写极少信息 → 自动注册 → 未来可检索/参考/晋升。

### 现状缺口总览

| 缺口 | 现状 |
|---|---|
| 存放位置 | 无 visual-references 目录；figure-atlas 是死资产 |
| 元数据格式 | 不存在任何资产元数据 |
| 注册机制 | 无 registry；directory-map 只覆盖生产图型且手工维护 |
| 校验工具 | check_references.py 只校验 directory-map ↔ figures 双向覆盖，不校验资产内部一致性 |
| 晋升路径 | 无"参考 → 生产"的状态概念 |

### 分场景差距分析

**Image only（只有截图）**
- 需要：`visual-references/` 目录 + 最小元数据（id/figure_type/tags/source/image_path，其余可空）。
- 缺口：全部。当前唯一可做的是丢进 figure-atlas，但那等于丢弃（无检索路径）。
- 轻量方案：一张图 + 一个同名 `.yaml`（5 个必填字段），ingest 脚本校验 hex/路径存在性并追加 registry 行。

**Image + source code**
- 需要：上述 + `has_code`/`code_path`/`runtime` 字段；代码放入 `visual-references/<type>/` 而非 `figures/`（未达生产标准前不污染生产池）。
- 缺口：无"待评审代码"的中间态目录；无 runtime 依赖声明习惯。

**Generated figure（skill 自产、用户满意的成品）**
- 这是最顺滑的潜在来源：QA Pass 后用户说"这张存起来"→ 已有脚本 + 预览 + 完整上下文（palette/journal/图型都知道，元数据可自动生成，用户零填写）。
- 缺口：SKILL.md Step 7（Deliver）无"归档"分支；无归档脚本。这是**性价比最高的 ingest 入口**，建议优先做。

**Production-ready template（确认高质量，正式进入 Copy-First 池）**
- 需要：质量门（脚本可运行、preview 存在、命名符合 `plot_X` 约定、颜色来源声明）+ 注册到 directory-map（或未来 registry）。
- 缺口：无质量门工具（eval_runner 只查存量）；directory-map 手工编辑；无"晋升"操作定义。
- 轻量方案：`quality: reviewed → production_ready` 状态翻转 + 一个 `promote` 脚本做校验 + 目录迁移 + registry 更新。

---

## 十、Script / Utility Architecture

### 功能分类（scripts/ 全 20 个 .py）

| 类别 | 文件 | 形态 |
|---|---|---|
| 组合引擎 | `compose.py`（21.7 KB） | library（也有 CLI 倾向） |
| palette | `palettes.py`、`palette_manager.py`、`__init__.py` | **library（包）** |
| QA 静态校验（套 1） | `qa_validator.py`（13 KB，~20 项检查） | library + CLI |
| QA 静态校验（套 2） | `check_colors.py`、`check_fontsize.py`、`check_dimensions.py`、`check_export.py` + 编排器 `check_figure.py` | CLI 工具组 |
| 仓库自检 | `check_references.py` | CLI |
| 生成器 | `generate_atlas.py`（64.8 KB，最大文件）、`generate_adapters.py` | 一次性 utility |
| 评测/测试 | `ab_test.py`、`e2e_runner.py`、`run_ab_tests.py`、`eval_runner.py`、`trigger_benchmark.py`、`qa_coverage.py` | test / CLI |
| 单元测试 | `test_palette_manager.py` | test（唯一标准 unittest） |

### 真实问题（不为工程化而工程化）

1. **`run_ab_tests.py` 整体损坏**：第 14 行 `s1_academic-figure-skill_passes = []`——变量名含连字符，语法错误，ast.parse 失败，完全不可运行。疑为 skill 改名时批量替换事故。
2. **路径假设错误**：`eval_runner`、`check_references`、`ab_test`、`trigger_benchmark` 等用 `Path(__file__).resolve().parents[2]` 再拼 `academic-figure-skill/`，假设外层仓库布局 `<repo>/academic-figure-skill/scripts/`。当前安装在 `~/.agents/skills/academic-figure-skill/scripts/` 时 `parents[2]` = `~/.agents`，拼接结果不存在——**这些脚本在当前安装形态下会路径解析失败**（静态推断，未实跑验证）。
3. **QA 两套并行**：`check_*` 四件套（check_figure 编排）与 `qa_validator.py` 功能大量重叠（默认色板、jet/rainbow、默认字体、低分辨率导出各查一遍，正则各自维护）。应合并为一套。
4. **配色三处**：`compose.py` 硬编码 CATEGORICAL hex；`color-palettes.md` COPY VERBATIM 块；新 palette manager。eval_runner 专门写检查维持前两处 17 个 hex 一致——这是"应收敛为单一源"的直接证据。
5. **场景定义两处半**：`ab_test.py` 与 `e2e_runner.py` 各自重复定义 SCENARIOS（e2e 自称 "against ab_test criteria" 但并不 import）；`run_ab_tests.py` 第三处（已损坏）。
6. **包架构半吊子**：`__init__.py` 存在（palette 模块相对导入），但其余 CLI 脚本走 `sys.path.insert` + 平级导入，两种风格混用。由于这些脚本是 agent 以 `python scripts/xxx.py` 方式调用的 CLI，**不建议**为统一而强制包化——现状可接受，只需注意 palette 模块的相对导入 + fallback 已正确处理两种调用方式。
7. **`generate_atlas.py` 输出路径过时**：写死 `assets/chart-atlas/`，实际目录是 `assets/figure-atlas/`——重跑会新建错误目录。
8. **不需要进一步拆 package**。20 个脚本、清晰的单文件职责，拆分只会增加 agent 的查找成本。

---

## 十一、Testing / QA / Benchmark

### 能力矩阵

| 能力 | 覆盖情况 | 设施 |
|---|---|---|
| A. 代码正确性 | **部分** | palette manager 23 条 unittest（全绿）；qa_coverage.py 测 qa_validator 本身的回归；其余工具脚本零测试 |
| B. 数据/引用完整性 | **有** | check_references.py（directory-map ↔ assets 双向覆盖、SKILL.md 引用文件存在性） |
| C. 出图成功 | **仅语法级** | eval_runner 只做 ast.parse/语法编译，**不真正执行渲染**；R 脚本上次评测 `"r": null`（环境无 R） |
| D. journal spec 合规 | **有（静态）** | qa_validator（AP/CL ~20 项）+ check_* 四件套（重复实现）；只查生成脚本文本，不查渲染产物 |
| E. 图像视觉质量 | **无自动化** | checklist Pass 2/3（VI/VV 系列）是"LLM 执行"的协议文本，无代码实现 |
| F. retrieval quality | **无** | 无检索系统可测；trigger_benchmark 测的是 skill 触发准确率（相邻问题） |
| G. aesthetic quality | **无** | — |

### 评测资产现状

- `scripts/.eval_results.json`：eval_runner 上次结果（2026-08-10），R 环境缺失。
- A/B 测试链（skill vs 裸 Claude，5 场景 6 维评分）定义完整但 `run_ab_tests.py` 损坏，实际未运行。

### 未来"示例越来越多但不变乱"的机制建议

核心是**入库时校验 + 分层质量状态**，而非事后审查：

1. ingest 时机器校验：preview 存在、命名合规、metadata schema 完整、hex 合法（palette_manager 的 `validate_palettes` 模式可推广为 `validate_asset`）。
2. `quality: draft → reviewed → production_ready` 单向状态机，检索默认只返回 reviewed 以上。
3. production 池额外门槛：脚本语法可运行（eval_runner 已有）+ preview 与脚本同名（现有约定形式化）。
4. 定期（非每次）跑 eval_runner 全量，结果入 `.eval_results.json` 追踪退化。
5. 视觉质量（E/G）保持"人眼入库"原则——用户觉得好看才 ingest，机器只做完整性兜底，不试图自动评美。

---

## 十二、Architecture Problems（按优先级）

### P0 — 严重

**P0-1 仓库失去版本控制与 upstream 连接**
- Why：无法追踪本地修改、无法合并 upstream 更新、无法回滚；二次开发成果（palette manager）随时可能因误操作丢失。
- Evidence：`git status` → not a git repository；本地新增 4 文件 + 修改 1 文件无任何版本记录。
- Direction：`git init` + 提交当前状态为基线；添加 upstream remote 指向 TingxiYu/academic-figure-skill。

**P0-2 QA 核心文件 checklist.md 编码损坏**
- Why：SKILL.md Step 6 强制加载的 QA 协议文件大面积乱码，VV-5 部分阈值不可读——agent 每次 QA 都在读一份残缺的协议。
- Evidence：文件中 "鈥?"、"脳"、"鈫?"、"卤3mm" 等 mojibake。
- Direction：从 upstream 恢复干净副本（上游同文件存在）。

**P0-3 多个工具脚本在当前安装形态下路径解析失败**
- Why：`parents[2]` 假设外层仓库布局，在 `~/.agents/skills/` 安装下拼出不存在的路径；eval/自检基础设施在用户实际使用位置是坏的。
- Evidence：eval_runner、check_references、ab_test、trigger_benchmark 的 PROJECT_ROOT 计算（静态推断，实跑行为 NOT VERIFIED）。
- Direction：改为 `Path(__file__).resolve().parents[1]`（脚本所在包的根）并以资产目录存在性做断言。

### P1 — 重要

**P1-1 规范冲突使 agent 无法同时满足所有指令**
- Why：字体 7 vs 8（三处）、archetype 默认值（SKILL.md vs figure-contract 直接相反）、spine 线宽、Hub 步骤编号过时——agent 每次执行都在随机消解矛盾，行为不可复现。
- Evidence：四节冲突清单（含文件与行内容）。
- Direction：确立"每类规则唯一权威文件"，其余改为引用；修一轮交叉引用。

**P1-2 Visual reference 机制缺失（最阻碍用户核心目标）**
- Why：用户最重要的未来需求是积累视觉示例库，但当前 B 类资产无目录、无元数据、无检索路径；figure-atlas 是死资产。
- Evidence：figure-atlas 仅 README 引用；全库零元数据文件；directory-map 只路由生产图型。
- Direction：见八节——分离 visual-references/ + 元数据 schema + registry。

**P1-3 生产资产无元数据，质量与依赖不可预知**
- Why：COPY-FIRST 决策树要求 agent 判断"脚本是否适配"，但无元数据意味着必须读完整脚本才能知道它是 reusable component 还是归档脚本、是否依赖 LaTeX/statannotations、原地能否运行。
- Evidence：五节深潜——两派脚本（自包含 vs 缺数据文件）并存、未声明依赖、v2–v4 无 preview。
- Direction：每资产 asset.yaml（最小字段集），ingest 时强制。

**P1-4 palette manager 未接入绘图层**
- Why：基础设施完成（23 测试全绿）但 55 个生产脚本零使用；新增代码仍将从 compose.py 的第三处硬编码取色。
- Evidence：`assets/figures/` grep palette_manager 零命中；配色三处维护。
- Direction：接入生成侧（SKILL.md Step 3/5 + compose.py），不动存量资产（七节路径）。

**P1-5 QA/测试设施重复且部分损坏**
- Why：两套静态 QA 实现各自维护正则，规则漂移只是时间问题；run_ab_tests.py 语法损坏；场景定义两处半。
- Evidence：十节问题 1/3/5。
- Direction：合并为 qa_validator 一套；修复或删除 run_ab_tests.py；场景定义单一源。

### P2 — 可优化

**P2-1 SKILL.md 约 1/3 内容可从 references 去重**
- Why：每次触发 ~9k token，其中 Design Principles、Step 5.5、Anti-Pattern 是重复内容；小任务无快速通道。
- Direction：删重复、保留判定逻辑；考虑为导出/微调类小任务定义 shortcut。

**P2-2 script↔preview 命名约定不统一**
- Why：程序无法稳定配对（`_N` 缺号、`AUROC1_1` vs `AUROC2`、v2–v4 无 preview），阻碍 registry 自动化。
- Direction：命名规范写入资产标准，存量逐步对齐（不强制）。

**P2-3 generate_atlas.py 输出路径过时（chart-atlas vs figure-atlas）**
- Direction：改一行路径或删除该生成器（figure-atlas 实为手工组装）。

---

## 十三、Things That Are Already Good

值得保留、不应在重构中丢掉的设计：

1. **Question-driven workflow（Step -1 硬 STOP）**："有数据无问题必须问"是科研绘图 agent 最正确的一条规则，防止生成技术上正确但科学上无意义的图。**高价值**。
2. **COPY-FIRST + 逐级降级契约**：复制真实发表级脚本 → VISUAL ADAPT → PARAM INHERIT → CROSS-TYPE，每级降级强制透明记录。比从零生成可控得多，"Asset Confirmation Table 必须是生成代码首行"是可机器审计的巧设计。**高价值**。
3. **Directory map 双语关键词路由**：44 行静态表解决 80% 的路由问题，check_references.py 保证表与资产双向同步不漂移。简单、确定、够用。**高价值**（在当前规模下）。
4. **VISUAL ADAPT 的 preview 语义锚点**：改列前先对照 companion PNG 做 1D/2D 硬 STOP——利用了 agent 的多模态能力，是低成本高保障的校验。**高价值**。
5. **四轮 QA 协议（AP/CL/VI/VV 分层）**：从反模式→编码→视觉→数据验证的分层是专业的；qa_validator 把文本协议翻译成可执行断言的方向正确。**价值高**（尽管 checklist.md 文件本身需修复）。
6. **期刊物理尺寸优先（89/183 mm）**：从打印尺寸反推 figsize 而非像素思维，是多数绘图 agent 缺失的专业意识。**高价值**。
7. **运行时检测 + 不静默降级**（Step 2）：环境不确定时把选择权交还用户，避免无声的质量妥协。**高价值**。
8. **Palette manager（本地新增）**：数据/API/测试三件套干净完整；确定性语义（子集不随机、扩展不循环、原始色前置、显式颜色优先）设计正确；中文别名实用。**高价值，待接入**。
9. **Asset atlas 理念**：figure-atlas 方向对（视觉展示），只是没接进工作流。
10. **跨平台 adapter 自动生成**（generate_adapters.py → install/）：单一源（SKILL.md）派生多平台配置，避免手工同步。**设计正确**。

---

## 十四、Recommended Evolution Direction

### Option A — Minimal cleanup

只做：恢复 git、修 checklist.md 乱码、修路径假设、消除规范冲突、修 run_ab_tests.py。

- 优点：成本极低（1–2 天工作量），立即恢复基础设施可信度；不动任何架构。
- 缺点：用户的核心目标（视觉示例库）零进展；资产规模增长后路由问题依旧。
- 改动成本：**低**。长期扩展性：**无提升**。

### Option B — Modular evolution（推荐）

保留现有核心（workflow、COPY-FIRST、directory-map、QA），逐步拆出六个关注点：

- **router**（SKILL.md 瘦身：trigger + workflow 骨架 + gate）
- **style system**（typography/color/export 单一机器可读源；palette manager 接入生成侧；compose.py 从同一源取色）
- **asset registry**（资产元数据 schema + registry.jsonl + check/promote 工具）
- **reference library**（新建 visual-references/，与 figures/ 生产池并列）
- **render engine**（compose.py / compose.R 保持，常量外置）
- **QA**（合并两套静态校验；eval_runner 修路径后继续作为回归）

- 优点：每一步独立可交付、可回退；直接支撑视觉示例库目标；SKILL.md 停止膨胀；不要求一次性重写。
- 缺点：需要设计元数据 schema 并保持纪律；中期存在"新旧两套并存"的过渡态。
- 改动成本：**中**（可分 4–6 个独立阶段）。长期扩展性：**好**——到 ~500 示例无压力。

### Option C — Retrieval-first architecture

重构为：scientific intent → figure type → **visual reference retrieval** → **production template retrieval** → adaptation → rendering → QA。引入统一 registry、结构化过滤、最终 CLIP 视觉语义检索。

- 优点：是数千示例规模的终态；检索质量成为一等公民；production 与 reference 完全分层。
- 缺点：现在做是过度工程——96 张 preview 的规模配不上 embedding 基础设施；一次性重写 SKILL.md 工作流风险高，会打破已被验证的 COPY-FIRST 契约；维护成本（索引更新、embedding 模型依赖）重。
- 改动成本：**高**。长期扩展性：**最好**（但提前兑现的代价大）。

### 推荐：**Option B，并把 Option C 作为 registry 设计的兼容目标**

理由：用户的核心未来需求（示例库持续增长、可检索、可晋升）被 B 完整覆盖；B 的 asset registry（`kind`/`quality`/`tags`/`image_path` 字段）天然是 C 的检索索引前身——未来示例到 500+ 时，在 registry 上加向量索引即可平滑升级 C，不需要再次重构。A 的修复项全部并入 B 的第一阶段。

---

## 十五、Suggested Future Target Architecture（proposal，未实施）

```
academic-figure-skill/
├── SKILL.md                      # 瘦身：trigger + workflow 骨架 + gates（目标 ≤300 行）
├── README.md / README_EN.md
├── LICENSE
│
├── instructions/                 # 从 SKILL.md 抽出的稳定协议（agent 按需加载）
│   ├── copy-first-contract.md    # COPY-FIRST / VISUAL ADAPT / 降级规则
│   ├── qa-protocol.md            # 现 checklist.md（修复乱码后）
│   └── reviewer-simulation.md
│
├── config/                       # 机器可读单一源（COPY VERBATIM 块的归宿）
│   ├── style-baseline.yaml       # 字体/字号/spine/导出参数（唯一权威）
│   ├── journals.yaml             # 期刊尺寸/DPI/偏好
│   └── palettes.yaml             # 调色板注册表（含 CNS 基线 + 7 套命名色板）
│
├── references/                   # 保留为人类/agent 可读知识（不装常量）
│   ├── directory-map.md          # 过渡期保留，长期由 registry 生成
│   ├── figure-contract.md / journal-intel.md / revision-cases.md
│   ├── figure-deconstruction.md / multipanel-layout.md / common-pitfalls.md
│   ├── matplotlib.md / complexheatmap.md / r-rendering.md
│   └── compose.R
│
├── scripts/                      # 工具层（现状保留 + 修复 + 合并）
│   ├── palettes.py / palette_manager.py / __init__.py
│   ├── compose.py                # 常量改从 config/ 读
│   ├── qa_validator.py           # 吸收 check_* 四件套后成为唯一静态 QA
│   ├── eval_runner.py / qa_coverage.py / trigger_benchmark.py / e2e_runner.py
│   ├── check_references.py       # 扩展为 registry 校验
│   ├── registry.py               # 新增：ingest / promote / query
│   └── tests/                    # test_palette_manager.py 等集中
│
├── assets/
│   ├── figures/                  # Production Assets（Copy-First 池，quality=production_ready）
│   │   └── <FigureType>/
│   │       ├── plot_X.py  /  plot_X.png  /  asset.yaml
│   ├── visual-references/        # Visual References（灵感库，可无代码）
│   │   └── <FigureType>/
│   │       ├── ref_<id>.png  /  ref_<id>.yaml
│   ├── registry.jsonl            # 全部资产（两类）的统一索引，脚本维护
│   └── figure-atlas/             # README 展示（可选迁入 visual-references/showcase/）
│
└── install/                      # 保持自动生成
```

设计要点对应：

1. **instruction / implementation 分离**：SKILL.md 只剩路由与 gate；协议入 instructions/；常量入 config/；代码留 scripts/。
2. **production / visual reference 分离**：`assets/figures/`（有代码、可执行、quality 门槛）与 `assets/visual-references/`（可无代码、低门槛入库）并列，`registry.jsonl` 统一索引。
3. **palette / theme 管理**：`config/palettes.yaml` 为唯一注册表；`config/style-baseline.yaml` 消除字体 7/8 三处冲突；compose.py 与生成侧统一从 config 取色。
4. **元数据 registry**：每资产一 yaml（八节 schema），ingest/promote/query 三个脚本操作 registry；directory-map 可从中生成，不再手工维护。
5. **示例可持续增加**：image-only 入库成本 = 1 张图 + 5 字段 yaml；自产图归档零填写（上下文自动生成元数据）。
6. **SKILL.md 不膨胀**：新增能力（新图型、新 reference、新 palette）全部落在 assets/config/references，入口文件稳定。

---

## 十六、Quick Facts for Next AI

## Quick Facts

**Repository purpose:**
AI-agent skill（Claude Code / Codex / Copilot / Cursor）用于生成发表级科研图（Nature/Cell/Science 导向）。上游 `github.com/TingxiYu/academic-figure-skill`；本地为去 git 化的二次开发副本，新增统一 palette 管理模块。

**Core entry point:**
`SKILL.md`（525 行，~9k token）= trigger 描述 + 9 步工作流（Step -1 到 7）。分类：中等编排层偏重，约 1/3 内容与 references/ 重复。

**Main workflow:**
理解问题（硬 STOP）→ 分类/数据解析 → 推荐确认 → 运行时检测 → 样式基线注入 → **资产扫描（directory-map）** → **COPY-FIRST 生成**（→VISUAL ADAPT→PARAM INHERIT 降级链）→ 数据验证 → 四轮 QA（checklist.md）→ 交付。

**Current figure types:**
32 个目录（29 个有实际脚本），55 个脚本（35 py + 20 R），96 个 preview（89 PNG + 7 PDF）。平均 1.9 脚本 / 3.0 preview 每图型。全库无数据文件、无元数据。

**Production asset location:**
`assets/figures/<FigureType>/plot_X.{py,R}` + 同名 preview PNG。由 `references/directory-map.md`（35 行双语关键词表）路由。质量不均：少数 reusable component（GroupedViolin、StackedBarScatter），多数 executable example / 归档脚本。

**Visual reference mechanism:**
**不存在有效机制**。`assets/figure-atlas/`（19 PNG）仅 README 引用，agent 工作流不触及；`references/figure-deconstruction.md` 是文字化解构雏形。production 与 visual reference 两类资产当前混居且无 B 类检索路径。

**Palette system:**
本地新增：`scripts/palettes.py`（7 套 × 8 hex，中/英名，tags，type=categorical）+ `scripts/palette_manager.py`（list/get/resolve/set_default/extend/preview/validate；显式颜色 > 显式 palette > 默认 pastel_girl；n>8 确定性 HSL 扩展、原始 8 色前置不循环）+ 23 条 unittest 全绿。**状态：基础设施完成，未接入绘图层**（生产脚本零使用；compose.py 与 color-palettes.md 的旧 CNS 基线三处硬编码并存）。接入路径：改生成侧（SKILL.md Step 3/5 + compose.py），不动存量资产。

**Current local modifications（vs upstream，经 GitHub API 确认）:**
新增 `scripts/palettes.py`、`scripts/palette_manager.py`、`scripts/test_palette_manager.py`、`scripts/__init__.py`；修改 `references/color-palettes.md`（追加 palette manager 文档节，85→152 行）。无删除（除 `.git` 本身）。

**Main architectural strengths:**
question-driven 硬 STOP；COPY-FIRST 契约 + 透明降级链；directory-map 简单确定性路由 + 双向一致性校验；preview PNG 作为视觉语义锚点；分层 QA 协议；期刊物理尺寸优先；palette manager 工程质量好。

**Main architectural weaknesses:**
无 git/失连 upstream；checklist.md 乱码（QA 核心文件）；多脚本路径假设在当前安装形态下失效；规范冲突（字号 7/8、archetype 默认相反）；visual reference 机制缺失；资产无元数据（质量/依赖不可预知）；QA 两套并行 + run_ab_tests.py 损坏；palette manager 未接入。

**Most important future requirement:**
"可以长期积累好看的科研绘图示例，并在后续生成图片时方便检索、参考和升级为 production asset。"

**Recommended next step:**
采用 Option B（modular evolution），第一阶段做四件事：
1. `git init` + 提交基线 + 接 upstream remote（P0-1）。
2. 从 upstream 恢复 `references/checklist.md` 干净副本（P0-2）。
3. 设计资产元数据 schema（`kind`/`quality`/`figure_type`/`tags`/`palette`/`image_path`/`code_path`/`runtime`），新建 `assets/visual-references/`（P1-2/P1-3）。
4. 写最小 `ingest` 路径：先生成图归档场景（skill 自产图，元数据可从上下文自动生成，用户零填写）（九节）。

---

## 附：NOT VERIFIED 事项清单

- 各工具脚本（eval_runner/check_references/ab_test/trigger_benchmark）在当前安装路径下的实跑行为（路径问题为静态推断）。
- R 脚本是否可运行（本机未验证 R 环境；`.eval_results.json` 显示上次评测 R 缺失）。
- figure-atlas 19 张 PNG 与 figures/ 下 preview 是否字节级重复（文件名不同，未做内容哈希对比）。
- `plot_PCA_coactivity.png` 的产出脚本归属（推断为 plot_PCA.R，未实跑确认）。
- 上游仓库在 references/ 与 scripts/ 之外是否有本地未同步的新提交（本次仅对比了两个目录的文件清单与 color-palettes.md 内容）。
- SKILL.md token 估算（8–9k）为近似值。
