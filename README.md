# Publication Figure Design

跨研究领域、跨发表 venue 的 reference-first 科研绘图 Skill 与设计编译器。仓库把科学任务、参考图的视觉证据、版式/风格规格、渲染结果和分层 QA 连接为可恢复的工作流。

参考图只提供视觉语法，不能改变源数据、统计变换、不确定性语义、变量角色或科学结论。

## 项目组成

- [`SKILL.md`](SKILL.md)：精简的 agent 工作入口。
- [`manifest.yaml`](manifest.yaml)：唯一的 workflow stage、条件插入、规则源和适配器 runtime 清单。
- [`src/publication_figure_design/`](src/publication_figure_design/)：合同、reference intelligence、风格编译、布局、渲染、orchestrator 和 QA。
- [`rules/`](rules/) 与 [`sources/registry.yaml`](sources/registry.yaml)：机器规则、权威层级和来源。
- [`profiles/`](profiles/) 与 [`indexes/`](indexes/)：journal/domain profiles、StyleCapsule 和检索索引。
- [`assets/`](assets/)：参考图库、ReferenceDNA、复现素材和 anti-pattern atlas。
- [`evals/`](evals/) 与 [`scripts/`](scripts/)：独立的 benchmark、维护和发布门禁。

## 工作流

每个 `WorkflowSession` 持久化自己的 `RoutePlan`、阶段游标、参考选择、规则策略、QA 结果和导出信息。路由由任务类型决定：create/revise 只运行所需阶段；review 与 export 使用短路径；有参考时才加入检索、像素检查和比较；create/revise 的 QA 失败时最多插入一次 critique → repair → render → QA。Critique 会带着具体失败项暂停，等待 Agent 提交 `DesignPatch` 后再用 `--resume` 继续；review/export 的 QA 失败只报告并阻断，不强制进入重画流程。

```text
TaskSpec → RoutePlan → PolicyPacket → stage handlers → QA feedback → Export
```

`manifest.yaml` 是执行图的单一来源。Runtime 将当前任务适用的 global、house、family、route 与 journal 约束编译为紧凑 `PolicyPacket`。验证器执行硬约束，并把具体失败项提供给修复阶段；Agent 无需在每次任务中加载整套规则 YAML。

参考按 `structure`、`style`、`palette`、`component` 和 `annotation` 等角色分开选择。检查像素后，将视觉证据编译为 `ReferenceDNA → StyleCapsule + JournalProfile → DesignPacket`。生产默认生成一个候选；评测工作流可显式请求结构优先、风格优先和平衡三个候选。

全局视觉语言强调柔和分区、短标题层级、结构化留白、低饱和语义色，以及克制的图例和注释；可访问性对比度和科学语义优先。

## TeX 后端

TeX/TikZ/PGFPlots 是一等后端。选用后阅读 [`references/tex-rendering.md`](references/tex-rendering.md)，声明编译引擎和包版本，并将编译日志、字体嵌入、overfull box、页面尺寸与目标物理尺寸 PNG 纳入 QA。TeX 能力缺失时应明确阻断该后端，不静默替换。

## 快速开始

在本机使用专用 `piepaper` 环境：

```powershell
& "D:\Anaconda\envs\piepaper\python.exe" -m pip install -e .
& "D:\Anaconda\envs\piepaper\python.exe" -m publication_figure_design.cli run <task-spec.json>
```

常用维护入口：

```powershell
& "D:\Anaconda\envs\piepaper\python.exe" -m publication_figure_design.cli reference ingest <image> <figure-type>
& "D:\Anaconda\envs\piepaper\python.exe" -m publication_figure_design.cli index build
& "D:\Anaconda\envs\piepaper\python.exe" -m publication_figure_design.cli eval quick
& "D:\Anaconda\envs\piepaper\python.exe" scripts/ci_gate.py
```

不要使用 Conda `base`、裸系统 Python 或无关环境。只在目标 route 需要时，将可选依赖安装到 `piepaper`。

## 参考与质量门

新参考按 `raw → analyzed → reviewed → benchmarked → production` 晋级。正式参考应具有元数据、适用的分析和复现材料、预览、来源记录，并通过相关 canary。入库不会执行参考目录里的 `code.py`。

QA 分层记录技术/导出、科学正确性、结构视觉对齐和感知质量。视觉相似不能覆盖科学或导出失败。参考驱动的 renderer 必须消费 `TypographySpec`、`PaletteSpec`、`LayoutSpec` 和 `ComponentSpec`。

CI、visual sprint、holdout、自动盲评、champion 晋级与 baseline 维护仅供项目维护者使用，集中记录在 [`docs/maintenance/runtime-and-evaluation.md`](docs/maintenance/runtime-and-evaluation.md)。

维护前阅读 [`AGENTS.md`](AGENTS.md) 与 [`CONTRIBUTING.md`](CONTRIBUTING.md)。保持一条当前生产实现，不恢复已删除旧 runner，也不新增普通 `v1/v2/final2` 副本。
