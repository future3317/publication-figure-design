# Publication Figure Design

面向不同研究领域和发表场景的科研绘图 Skill。它帮助 Codex 从科学问题与数据出发，选择合适的图形结构，参考真实视觉样例，修改或生成可复现的绘图源文件，并检查最终渲染图。

参考图只提供视觉语言，不得改变数据、统计变换、不确定性、标签或科学结论。

## 使用方式

在 Codex 中调用 `publication-figure-design` Skill，并直接说明要画什么、数据/源文件在哪里、期望的输出和可用参考图。日常绘图由 Agent 直接检查、编辑、渲染和修图；不需要先填写 TaskSpec 或运行 `pfd run`。该 CLI 只管理可恢复的任务会话和 QA 元数据，本身不负责绘图。

默认视觉语言：柔和分区、简短标题、清晰文字层级、结构化留白、低饱和语义色、克制图例与注释；文字和关键图形必须保持足够对比度。真实科学关系和明确用户要求优先于风格偏好。

## 仓库结构

- [`SKILL.md`](SKILL.md)：Agent 使用的简明工作约定。
- [`references/`](references/)：只在具体任务需要时读取的参考重建、编码、不确定性和 TeX 指南。
- [`assets/visual-references/`](assets/visual-references/)：参考图及其分析和复现素材。
- [`rules/`](rules/)：可供程序化 QA 使用的机器规则。
- [`src/publication_figure_design/`](src/publication_figure_design/)：合同、设计包、可选 session runner 和 QA 组件。
- [`scripts/`](scripts/) 与 [`evals/`](evals/)：参考库维护、测试、评测和发布检查。

## 可选命令

需要可恢复任务会话或使用参考库维护、评测功能时，使用专用 `piepaper` 环境：

```powershell
& "D:\Anaconda\envs\piepaper\python.exe" -m publication_figure_design.cli run <task-spec.json>
& "D:\Anaconda\envs\piepaper\python.exe" -m publication_figure_design.cli reference ingest <image> <figure-type>
& "D:\Anaconda\envs\piepaper\python.exe" -m publication_figure_design.cli index build
& "D:\Anaconda\envs\piepaper\python.exe" scripts/ci_gate.py
```

`pfd run` 不生成图，也不替代对实际 PNG/PDF 的检查。TeX/TikZ/PGFPlots 任务请先读 [`references/tex-rendering.md`](references/tex-rendering.md)。参考库、视觉评测和维护流程见 [`docs/maintenance/runtime-and-evaluation.md`](docs/maintenance/runtime-and-evaluation.md)。

## 维护

项目专用解释器路径和环境约定见 [`references/runtime-environment.md`](references/runtime-environment.md)。不得在参考图入库时执行其中附带的 `code.py`。修改仓库前阅读 [`AGENTS.md`](AGENTS.md) 和 [`CONTRIBUTING.md`](CONTRIBUTING.md)。
