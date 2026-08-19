# Phase 2 Implementation Report

> academic-figure-skill 第二轮优化：Visual Reference Library 接入 SKILL.md 工作流
> 日期：2026-08-11

---

## 1. 本轮目标

让 agent 在绘图时能够主动利用已积累的 visual references，同时保持 production assets 的核心地位。

- 在 `SKILL.md` 中以最小侵入方式增加 task dispatch 和 reference retrieval。
- 明确 Production Asset 与 Visual Reference 的职责边界。
- 支持 natural-language reference 任务，不重新实现第二套系统。
- 不批量修改现有 55 个 production scripts，不大规模重构 references 或目录。

---

## 2. SKILL.md 改动

### 2.1 新增 Task Dispatch

在 `Design Principles` 之前插入 `## Task Dispatch`，将用户请求分为 5 种模式：

| 模式 | 触发语 | 工作流 |
|---|---|---|
| **create** | 新图/从数据画图 | 完整 pipeline Step -1 → 7 |
| **revise** | 改图/改颜色字号 | 只跳到相关步骤 |
| **review** | 审稿评价 | Reviewer Simulation Mode |
| **export** | 导出/转格式/改尺寸 | 加载已有代码/图，改导出参数，QA |
| **reference** | 存图/找参考 | 直接调用 `scripts/reference_library.py` |

`reference` 模式明确映射到现有 API：
- "把这张图存起来" / "这张我喜欢，收进参考库" → `ingest(...)` / `archive_generated_figure(...)`
- "找几个好看的 grouped violin" → `query(figure_type="GroupedViolin", ...)`
- "有没有 pastel 风格的 PCA 参考" → `query(figure_type="PCA", tags=["pastel"], ...)`

### 2.2 新增 Step 4.5: Visual Reference Retrieval

在 `Step 4: Production Asset Scan` 与 `Step 5: Generate Code` 之间插入新步骤。

触发条件（create 模式且 figure type 已确定）：
- 用户提到风格词：pastel / minimal / bold / Nature style 等
- 用户指定 palette 或 layout
- 需要相似数据密度、组数、annotation 的参考

查询方式：

```python
from scripts.reference_library import ReferenceLibrary

refs = ReferenceLibrary().query(
    figure_type="GroupedViolin",
    tags=["pastel", "minimal"],
    journal_style="Nature",
    min_aesthetic_rating=3,
    limit=3,
)
```

默认限制：**最多 3 个 reference**。

### 2.3 职责与优先级

**Production Asset** 决定：
- 图型语义
- 数据结构
- 统计实现
- 可执行性

**Visual Reference** 决定：
- palette
- layout
- annotation
- legend / spacing
- highlight
- data density 表现

使用优先级：
1. 用户明确要求
2. 科学语义和数据结构
3. Production Asset 实现
4. 匹配的 Visual Reference
5. Skill 默认视觉规范

Palette 优先级：
1. 用户 explicit colors
2. 用户 explicit palette
3. Production / reference 原始 palette
4. Skill default palette

`palette_policy`：
- `preserve`：默认保留 reference 的视觉配色逻辑
- `adaptable`：可结合用户要求或 palette manager 调整

### 2.4 Step 7 Deliver 增加 Visual Source Report

交付物新增：

```
Visual Source Report
- Production asset: GroupedViolin/plot_GroupedViolin.py
- Visual reference: vr_44933a30fd0c3c58
- Palette: summer_beach
- Palette policy: preserve
```

未使用 visual reference 时明确写 `None`。

### 2.5 References 表更新

在 `On-Demand` references 中增加：
- `references/visual-reference-library.md` → Step 4.5 使用规则与 API

---

## 3. 新增 reference 文档

文件：`references/visual-reference-library.md`

内容：
- 何时查询 visual references
- Production Asset 与 Visual Reference 的职责 split
- 查询 API 示例
- 应用优先级
- 视觉来源记录格式
- reference 任务的自然语言映射

不重复完整 metadata schema 或 CLI 文档，指向 `scripts/reference_library.py` 获取细节。

---

## 4. 新增测试

文件：`scripts/test_workflow_integration.py`（19 个测试）

覆盖：
- `SKILL.md` 包含 Task Dispatch 五种模式
- `SKILL.md` 包含 Step 4.5 章节
- 默认 reference limit = 3
- 科学语义优先级高于 visual reference
- palette 优先级顺序正确
- `palette_policy` preserve / adaptable 行为
- create workflow 能查询 reference
- 无 reference 时正常 fallback
- query 最多返回 limit 个候选
- figure_type 过滤正确
- n_groups 过滤正确
- reference 任务能 archive generated figure

---

## 5. 测试结果

| 测试 | 数量 | 结果 |
|---|---|---|
| `python -m py_compile scripts/*.py` | 23 文件 | OK |
| `scripts/test_palette_manager.py` | 23 | OK |
| `scripts/test_reference_library.py` | 27 | OK |
| `scripts/test_workflow_integration.py` | 19 | OK |
| `scripts/check_references.py` | - | HEALTHY（SKILL.md refs 从 16 增至 18） |
| `scripts/run_ab_tests.py` | 21 checks | 100% |
| `scripts/eval_runner.py` | 29 types | 19 pass，10 种 R 脚本因环境缺失 WARN |
| `scripts/qa_coverage.py` | 26 cases | 目标检查无漏报 |
| `scripts/trigger_benchmark.py` | 40 prompts | 100% |

---

## 6. 本轮未做的事

- 未引入 embedding / CLIP / vector database
- 未给 production assets 全量加 metadata
- 未大规模重构目录结构
- 未重写 COPY-FIRST
- 未批量修改 55 个 production scripts
- 未把 palette manager 强制接入所有 production scripts

---

## 7. 文件变更清单

```
SKILL.md                                    # 增加 task dispatch、Step 4.5、交付物 visual source report
references/visual-reference-library.md      # 新增
scripts/test_workflow_integration.py        # 新增 19 个集成测试
```

---

## 8. 推荐下一步

1. **在真实 create 任务中试用**：当用户提到风格词时，执行 Step 4.5 查询并记录 visual source。
2. **积累 generated-archive 样本**：当用户说“这张图不错，存起来”时，用 `archive_generated_figure` 归档。
3. **逐步接入 palette manager**：选择 1-2 个新 production script，在 `palette_policy = adaptable` 的 reference 影响下试用 `resolve_palette()`。
4. **观察 reference 是否过载**：如果 3 个 reference 过多或过少，根据实际使用调整 limit。
