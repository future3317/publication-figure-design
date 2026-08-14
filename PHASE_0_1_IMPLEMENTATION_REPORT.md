# Phase 0.1 Implementation Report

> academic-figure-skill 第一轮优化：基础修复 + Visual Reference Library 最小闭环
> 日期：2026-08-11

---

## 1. 本轮目标

1. 先实际运行现有检查和测试，再决定修改什么；只修复已确认的基础问题。
2. 为本地二次开发版本建立 git 版本控制，并把上游 `TingxiYu/academic-figure-skill` 添加为 upstream（仅比较/同步，不 push）。
3. 建立轻量 Visual Reference Library，区分 Production Assets（`assets/figures/`）和 Visual References（`assets/visual-references/`）。
4. 新增 registry 工具与单元测试，不全面重构、不批量修改现有 55 个 production scripts。

---

## 2. 基础修复：实际验证与结论

### 2.1 运行结果（实测）

| 检查/测试 | 命令 | 结果 |
|---|---|---|
| Python 编译 | `python -m py_compile scripts/*.py` | OK |
| Palette Manager 测试 | `python scripts/test_palette_manager.py` | 23/23 OK |
| Reference Library 测试 | `python -m unittest scripts.test_reference_library` | 27/27 OK |
| Reference Integrity | `python scripts/check_references.py` | HEALTHY |
| A/B Test Runner | `python scripts/run_ab_tests.py` | 100% (21/21) |
| Eval Runner | `python scripts/eval_runner.py` | 19/29 pass，10 种图型因本地无 R 环境报 WARN |
| QA Coverage | `python scripts/qa_coverage.py` | 26/26 目标检查通过 |
| Trigger Benchmark | `python scripts/trigger_benchmark.py` | 40/40 正确分类 |

> 说明：`eval_runner.py` 的 10 个 WARN 全部来自 R 脚本（如 PCA、RidgePlot、CorrelationMatrix 等），原因是当前环境未安装 R，不是代码或路径错误。

### 2.2 审计报告中提到的问题：实测状态

| 审计问题 | 实测结论 | 本轮动作 |
|---|---|---|
| `references/checklist.md` 编码乱码 | **已修复**。文件为 UTF-8，无 replacement chars，无 GBK 乱码模式。 | 无修改；保留现状。 |
| `scripts/run_ab_tests.py` 语法损坏 | **已修复**。`python scripts/run_ab_tests.py` 可正常运行。 | 本轮进一步修复了其中 2 个字符串匹配 bug（见 2.4）。 |
| 评测脚本路径假设在 `~/.agents/skills/` 下失效 | **已修复**。脚本使用 `SKILL_ROOT` helper（基于 `SKILL.md` 存在性解析），不再硬编码 `parents[2] / "academic-figure-skill"`。 | 无修改。 |
| `scripts/ab_test.py` S2-S5 `name` 缺失 | **已修复**。`python scripts/ab_test.py` 可直接打印 5 个 scenario。 | 无修改。 |

> 说明：编码/路径/语法类修复在本次会话开始前的本地状态中已完成。本轮通过实际运行确认了它们的真实有效性，并补充修复了 A/B 测试内部 bug。

### 2.3 明确规范冲突的解决

审计报告指出的三处直接冲突已按“一类规则一个权威来源”原则解决：

| 规则 | 权威来源 | 修改 |
|---|---|---|
| Python 基础字号 | `references/typography.md` COPY VERBATIM 块 | `font.size: 8` 保持不变 |
| R 基础字号 | `references/typography.md` COPY VERBATIM 块 | 将 R 段落后重复的 `theme_cns` 从 `base_size = 7` 改为 `8`，与 COPY VERBATIM 块一致 |
| 清单对字号的检查 | `references/checklist.md` 引用 typography.md | AP-0 改为检查 `font.size: 8`，并标注权威来源 |
| matplotlib 规范 | `references/matplotlib.md` 引用 typography.md | `font.size` 从 `7` 改为 `8` |
| Spine 线宽 | `references/journal-specs.md` Spines and Axes | 保持 `0.5-0.6 pt` 不变 |
| 清单对 spine 的检查 | `references/checklist.md` 引用 journal-specs.md | CL-5 pass 条件从 `0.5-0.8 pt` 改为 `0.5-0.6 pt`，并标注权威来源 |
| 默认 archetype | `SKILL.md` Step 0a | `asymmetric_mixed` 保持不变 |
| 合同对 archetype 的默认 | `references/figure-contract.md` 引用 SKILL.md | 从 `quantitative grid` 改为 `asymmetric_mixed`，并标注权威来源 |

没有修改现有 production scripts 的视觉实现；只统一了规则描述。

### 2.4 A/B 测试 2 项失败的原因与修复

`run_ab_tests.py` 原本 S4、S5 各有一项实际未通过，但报告输出把所有检查都显示为 `[PASS]`（显示逻辑 bug）。

**S4 失败原因：** 测试查找 `Long-Tail`（大写 T）或 `general practitioner`，而 `SKILL.md` 实际写的是 `Long-tail fallback`（小写 t）。大小写不匹配导致该检查实际为 False。

**S5 失败原因：** 测试查找 `do NOT auto-generate` 或 `no template`，而 `SKILL.md` 实际写的是 `not from a template`。子串不匹配导致该检查实际为 False。

**修复内容：**
- S4 改为大小写不敏感匹配 `long-tail`。
- S5 改为同时匹配 `do not auto-generate`、`not from a template`、`not by a template`。
- 统一输出格式：每个检查根据实际布尔值显示 `[PASS]` / `[FAIL]`，不再对学术侧全部显示 `[PASS]`。

修复后 A/B 测试从 90% (19/21) 提升到 100% (21/21)。这一提升来自修复真实 bug，而非降低测试标准。

### 2.5 Git 版本控制

- 初始化本地仓库：
  ```bash
  git init
  git remote add upstream https://github.com/TingxiYu/academic-figure-skill.git
  ```
- Baseline commit：`56c914f baseline: current local state before Phase 0.1 optimization`
- Phase 0.1 commit：`6570533 feat(visual-references): add ReferenceLibrary, registry, tests and .gitignore`
- Report commit：`8643fe1 docs: add Phase 0.1 implementation report`
- 上游 remote 仅用于以后比较/同步，**不会向上游 push**。

---

## 3. Visual Reference Library

### 3.1 目录结构

```
assets/
├── figures/                    # Production Assets（COPY-FIRST），未改动
├── figure-atlas/               # README showcase，未改动
├── registry.jsonl              # 自动生成的索引（可删除并 rebuild）
└── visual-references/
    ├── .staging/               # 临时文件，gitignored
    ├── references/             # 外部参考图：论文截图、GitHub 示例、灵感图
    └── generated-archive/      # skill 自己生成并被用户认可的图
        └── <id>/
            ├── image.png
            ├── code.py         # 可选
            └── metadata.json   # 唯一真源
```

### 3.2 Metadata Schema（sidecar `metadata.json`）

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | string | SHA-256 前 16 字节 hex，稳定且去重 |
| `scope` | string | `references` / `generated-archive` |
| `figure_type` | string | 图型类型，如 `GroupedViolin` |
| `subtype` | string? | 子类型 |
| `tags` | list[string] | 人工标签 |
| `palette` | string? | 使用的 palette id 或中文别名 |
| `palette_policy` | string | `preserve`（默认）/ `adaptable` |
| `layout` | string? | 布局，如 `1x1`、`2x2` |
| `journal_style` | string? | 目标期刊风格 |
| `source` | string | `unknown` / `paper` / `github` / `self-generated` 等 |
| `source_url` | string? | 来源 URL |
| `license` | string | 默认 `unknown` |
| `usage_scope` | string | `private_reference`（默认）/ `internal_reference` / `redistributable`；**仅表示使用/版权范围** |
| `image_path` | string | 相对 skill root 的图片路径 |
| `code_path` | string? | 相对 skill root 的代码路径 |
| `review_status` | string | `pending` / `reviewed` / `rejected` / `promoted` |
| `aesthetic_rating` | number? | 0-5，人工视觉质量评分 |
| `production_ready` | bool | 是否达到未来 COPY-FIRST 标准 |
| `n_groups` | int? | 分组数 |
| `data_density` | string? | `low` / `medium` / `high` |
| `notes` | string? | 备注 |
| `created_at` | string | UTC 时间戳 |
| `sha256` | string | 完整 SHA-256（用于校验与去重） |

关键设计：
- `aesthetic_rating` 与 `production_ready` **分离**，不合并为单个 quality 字段。
- `usage_scope` **只表示版权/使用范围**；模板成熟度由 `review_status` 与 `production_ready` 表达。
- 外部图片来源默认 `usage_scope = private_reference`，不假定可重新分发。
- 所有路径相对 skill root，禁止写入本地绝对路径。

### 3.3 Registry 工具

文件：`scripts/reference_library.py`

核心 API：

```python
from scripts.reference_library import ReferenceLibrary

lib = ReferenceLibrary()

# 1. 用户给一张外部图片
ref = lib.ingest(
    image_path="path/to/incoming.png",
    figure_type="GroupedViolin",
    metadata_override={
        "tags": ["pastel", "minimal"],
        "aesthetic_rating": 4,
        "journal_style": "Nature",
        "palette": "summer_beach",
        "palette_policy": "preserve",
    },
)

# 2. skill 自己生成了一张满意的图
ref = lib.archive_generated_figure(
    image_path="tmp/my_figure.png",
    figure_type="StackedBarScatter",
    code_path="tmp/my_figure.py",
    metadata_override={
        "palette": "fresh_holiday",
        "aesthetic_rating": 5,
    },
)

# 3. 查询
results = lib.query(
    figure_type="GroupedViolin",
    tags=["pastel", "minimal"],
    min_aesthetic_rating=3,
    limit=5,
)

# 4. 验证所有 sidecar
ok, problems = lib.validate()

# 5. 重建 registry.jsonl
lib.rebuild_registry()
```

CLI 用法：

```bash
# 外部图片入库
python scripts/reference_library.py ingest image.png GroupedViolin \
  -m '{"tags":["pastel","minimal"],"aesthetic_rating":4,"palette":"summer_beach"}'

# 归档 skill 自己生成的图
python scripts/reference_library.py archive output.png StackedBarScatter \
  --code output.py -m '{"palette":"fresh_holiday","aesthetic_rating":5}'

# 查询
python scripts/reference_library.py query --tags pastel --min-aesthetic-rating 3 --limit 5

# 列出、获取、验证、重建
python scripts/reference_library.py list --scope references
python scripts/reference_library.py get <id>
python scripts/reference_library.py validate
python scripts/reference_library.py rebuild
```

### 3.4 关键行为

- **确定性 ID**：相同图片字节永远得到相同 id，避免重复入库。
- **单一资产记录**：同一图片（相同 SHA-256）只能注册一次；重新 ingest 会抛出 `already exists` 错误。
- **registry.jsonl 是缓存**：完全由 sidecar metadata 自动生成，可删除后 `rebuild` 恢复。
- **无 embedding / vector DB**：查询为纯 metadata 过滤 + 排序。
- **palette_policy**：默认 `preserve`，为后续“显式颜色 > 显式 palette > 原资产配色 > skill 默认 palette” 预留接口。

---

## 4. 测试

新增文件：`scripts/test_reference_library.py`（27 个测试）

覆盖：
- SHA-256 / short id 确定性
- 相对路径转换与绝对路径拦截
- metadata validation（必填、枚举、palette 别名、评分范围、非法路径）
- ingest / 重复检测 / 重复注册必失败
- `archive_generated_figure` 带 code 归档
- get / list / query / min aesthetic rating / 排序
- validate / 损坏 metadata 检测
- registry rebuild / load_registry
- 包级导出符号

运行方式：

```bash
# 推荐
python -m unittest scripts.test_reference_library

# 也可直接运行
python scripts/test_reference_library.py
```

实测结果：`Ran 27 tests in 0.262s OK`

---

## 5. 合并测试结果

| 测试 | 数量 | 结果 |
|---|---|---|
| `python -m py_compile scripts/*.py` | 22 文件 | OK |
| `scripts/test_palette_manager.py` | 23 | OK |
| `scripts/test_reference_library.py` | 27 | OK |
| `scripts/check_references.py` | - | HEALTHY |
| `scripts/run_ab_tests.py` | 21 checks | 100% |
| `scripts/eval_runner.py` | 29 types | 19 pass，10 种 R 脚本因环境缺失 WARN |
| `scripts/qa_coverage.py` | 26 cases | 目标检查无漏报 |
| `scripts/trigger_benchmark.py` | 40 prompts | 100% Accuracy/Precision/Recall/F1 |

---

## 6. 本轮未触碰的内容

- 未修改 `SKILL.md`。
- 未批量修改 `assets/figures/` 下 55 个 production scripts 的视觉实现。
- 未把 `assets/figure-atlas/` 自动导入 reference library。
- 未给现有 production assets 批量加 metadata。
- 未引入 embedding / CLIP / FAISS / vector DB。
- 未新建 `instructions/` 目录。
- 未重构所有 QA 工具。

---

## 7. 仍留到下一阶段的问题

1. **Palette Manager 接入绘图层**：当前 palette manager 仍是基础设施；后续需要逐步在 production scripts 中替换硬编码颜色，优先在新 script 中接入 `resolve_palette()`。
2. **Reference Library 与 SKILL.md 集成**：当前 agent 还无法通过自然语言直接检索 visual references；后续需要在 SKILL.md 中增加可选步骤或 helper，让 agent 在“找参考”时调用 `query`。
3. **metadata schema 实战打磨**：`n_groups`、`data_density` 等字段需要更多真实案例后才能确定是否足够。
4. **production_ready 晋升工作流**：目前仅是一个布尔字段；后续需要定义从 `generated-archive` 到 `assets/figures/` production asset 的评审与复制流程。
5. **R 脚本环境**：`eval_runner.py` 对 R 脚本的检查因本地无 R 环境而 WARN，这不是代码问题，而是运行环境缺失。

---

## 8. 文件变更清单

```
.gitignore                                  # 新增
references/checklist.md                     # 统一字号与 spine 线宽规范
references/figure-contract.md               # 统一 archetype 默认值
references/matplotlib.md                    # 统一字号
references/typography.md                    # 统一 R theme_cns base_size
scripts/__init__.py                         # 导出 ReferenceLibrary 等符号
scripts/reference_library.py                # 新增（registry 核心实现）
scripts/run_ab_tests.py                     # 修复字符串匹配与输出显示 bug
scripts/test_reference_library.py           # 新增（27 个单元测试）
assets/visual-references/                   # 新增目录结构
assets/registry.jsonl                       # 由工具自动生成，当前为空
```

---

## 9. 验证过的审计断言

- `checklist.md` 编码损坏：已验证为干净，无需再修。
- `run_ab_tests.py` 语法损坏：已验证可运行；本轮进一步修复了 2 处字符串匹配 bug 和 1 处显示 bug。
- 评测脚本路径假设：已验证使用 SKILL_ROOT helper。
- typography / spine / archetype 冲突：已按“一个权威来源”原则统一。
- palette manager 23 项测试：通过。
- reference library 27 项测试：通过。
- reference integrity：HEALTHY。
- qa coverage / trigger benchmark：达到各自目标（qa 无漏报，trigger 40/40）。
- eval_runner：19/29 图型通过；未通过项全部因本地无 R 环境，已在报告中明确标注。

---

## 10. 推荐下一步

1. 在真实绘图任务中试用 `archive_generated_figure()`，积累第一批 `generated-archive` 样本。
2. 选择 1-2 个最常用图型（如 `GroupedViolin`、`StackedBarScatter`），在新脚本中试点接入 palette manager。
3. 等样本积累到 10-20 个后，评估 metadata schema 是否足够，再决定是否增加字段或目录层级。
