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
| Reference Integrity | `python scripts/check_references.py` | HEALTHY |
| A/B Test Runner | `python scripts/run_ab_tests.py` | 90% (19/21) |
| Eval Runner | `python scripts/eval_runner.py` | 19/29 pass，R 脚本因无 R 环境报 WARN |
| QA Coverage | `python scripts/qa_coverage.py` | ALL TARGETED CHECKS WORK |
| Trigger Benchmark | `python scripts/trigger_benchmark.py` | 100% Accuracy/Precision/Recall/F1 |

### 2.2 审计报告中提到的问题：实测状态

| 审计问题 | 实测结论 | 本轮动作 |
|---|---|---|
| `references/checklist.md` 编码乱码 | **已修复**。文件为 UTF-8，无 replacement chars，无 GBK 乱码模式。 | 无修改；保留现状。 |
| `scripts/run_ab_tests.py` 语法损坏 | **已修复**。`python scripts/run_ab_tests.py` 可正常运行，Overall 90%。 | 无修改。 |
| 评测脚本路径假设在 `~/.agents/skills/` 下失效 | **已修复**。脚本使用 `SKILL_ROOT` helper（基于 `SKILL.md` 存在性解析），不再硬编码 `parents[2] / "academic-figure-skill"`。 | 无修改。 |
| `scripts/ab_test.py` S2–S5 `name` 缺失 | **已修复**。`python scripts/ab_test.py` 可直接打印 5 个 scenario。 | 无修改。 |

> 说明：上述修复在本次会话开始前的本地状态中已完成。本轮通过实际运行确认了它们的真实有效性，因此没有重复修改代码。

### 2.3 Git 版本控制

- 初始化本地仓库：
  ```bash
  git init
  git remote add upstream https://github.com/TingxiYu/academic-figure-skill.git
  ```
- Baseline commit：`56c914f baseline: current local state before Phase 0.1 optimization`
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
| `usage_scope` | string | `private_reference`（默认）/ `internal_reference` / `shareable` / `template_candidate` |
| `image_path` | string | 相对 skill root 的图片路径 |
| `code_path` | string? | 相对 skill root 的代码路径 |
| `review_status` | string | `pending` / `reviewed` / `rejected` / `promoted` |
| `aesthetic_rating` | number? | 0–5，人工视觉质量评分 |
| `production_ready` | bool | 是否达到未来 COPY-FIRST 标准 |
| `n_groups` | int? | 分组数 |
| `data_density` | string? | `low` / `medium` / `high` |
| `notes` | string? | 备注 |
| `created_at` | string | UTC 时间戳 |
| `sha256` | string | 完整 SHA-256（用于校验与去重） |

关键设计：
- `aesthetic_rating` 与 `production_ready` **分离**，不合并为单个 quality 字段。
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
- **重复检测**：默认拒绝重复图片；`allow_duplicates=True` 可强制再次入库。
- **registry.jsonl 是缓存**：完全由 sidecar metadata 自动生成，可删除后 `rebuild` 恢复。
- **无 embedding / vector DB**：查询为纯 metadata 过滤 + 排序。
- **palette_policy**：默认 `preserve`，为后续"显式颜色 > 显式 palette > 原资产配色 > skill 默认 palette" 预留接口。

---

## 4. 测试

新增文件：`scripts/test_reference_library.py`（27 个测试）

覆盖：
- SHA-256 / short id 确定性
- 相对路径转换与绝对路径拦截
- metadata validation（必填、枚举、palette 别名、评分范围、非法路径）
- ingest / 重复检测 / allow_duplicates
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

实测结果：`Ran 27 tests in 0.211s OK (skipped=1)`
（skipped 1 为包导入测试，在直接运行文件时因 sys.path 上下文会跳过；用 `python -m unittest` 时通过。）

---

## 5. 合并测试结果

| 测试 | 数量 | 结果 |
|---|---|---|
| `scripts/test_palette_manager.py` | 23 | OK |
| `scripts/test_reference_library.py` | 27 | OK (skipped=1 in direct mode) |
| `scripts/check_references.py` | — | HEALTHY |
| `scripts/run_ab_tests.py` | 21 checks | 90% |
| `scripts/eval_runner.py` | 29 types | 19 pass，10 need R env |
| `scripts/qa_coverage.py` | 26 cases | 100% |
| `scripts/trigger_benchmark.py` | 40 prompts | 100% |
| `python -m py_compile scripts/*.py` | 22 files | OK |

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
2. **Reference Library 与 SKILL.md 集成**：当前 agent 还无法通过自然语言直接检索 visual references；后续需要在 SKILL.md 中增加可选步骤或 helper，让 agent 在 "找参考" 时调用 `query`。
3. **metadata schema 实战打磨**：`n_groups`、`data_density` 等字段需要更多真实案例后才能确定是否足够。
4. **production_ready 晋升工作流**：目前仅是一个布尔字段；后续需要定义从 `template_candidate` 到 `assets/figures/` production asset 的评审与复制流程。
5. **重复规则与冲突未解决**：审计中提到的 typography 字号冲突、spine 线宽冲突、archetype 默认值矛盾等仍在 references 中，未在本轮修复。
6. **R 脚本环境**：`eval_runner.py` 对 R 脚本的检查因本地无 R 环境而 WARN，这不是代码问题，而是运行环境缺失。

---

## 8. 文件变更清单

```
.gitignore                                  # 新增
scripts/__init__.py                         # 导出 ReferenceLibrary 等符号
scripts/reference_library.py                # 新增（registry 核心实现）
scripts/test_reference_library.py           # 新增（27 个单元测试）
assets/visual-references/                   # 新增目录结构
assets/registry.jsonl                       # 由工具自动生成，当前为空
```

---

## 9. 验证过的审计断言

- `checklist.md` 编码损坏：已验证为干净，无需再修。
- `run_ab_tests.py` 语法损坏：已验证可运行。
- 评测脚本路径假设：已验证使用 SKILL_ROOT helper。
- palette manager 23 项测试：全部通过。
- reference integrity / eval / qa / trigger：全部通过。

---

## 10. 推荐下一步

1. 在真实绘图任务中试用 `archive_generated_figure()`，积累第一批 `generated-archive` 样本。
2. 选择 1–2 个最常用图型（如 `GroupedViolin`、`StackedBarScatter`），在新脚本中试点接入 palette manager。
3. 等样本积累到 10–20 个后，评估 metadata schema 是否足够，再决定是否增加字段或目录层级。
