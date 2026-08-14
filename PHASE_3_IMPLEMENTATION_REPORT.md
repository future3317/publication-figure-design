# Phase 3 Implementation Report

> academic-figure-skill 第三轮优化：Palette / Style Integration
> 日期：2026-08-11

---

## 1. 本轮目标

让现有 palette manager 真正进入绘图工作流，同时保持 Production Asset 的原始视觉不被默认色板破坏。

- 新增真实 E2E smoke test：reference 检索 → 读取参考图 → 风格应用 → 出图 → Visual Source Report。
- 为 new generated code / VISUAL ADAPT / PARAM INHERIT 路径提供统一的 palette 解析入口。
- 明确 palette 优先级：explicit colors > explicit palette > reference original palette > skill default。
- `preserve` 默认保持资产原配色；`adaptable` 允许通过 `palette_manager` 调整。
- 不批量修改现有 55 个 production scripts，不大规模重构 style system。

---

## 2. E2E Smoke Test

文件：`scripts/e2e_smoke_test.py`

流程：
1. 创建临时 skill root。
2. Ingest 2 个临时 Visual Reference：
   - `GroupedViolin` + `summer_beach` + `palette_policy=preserve`
   - `GroupedViolin` + `sweet_macaron` + `palette_policy=adaptable`
3. Query `figure_type=GroupedViolin`, tags=`[pastel]`, `journal_style=Nature`, `n_groups=3`。
4. 选中 `preserve` reference。
5. 使用 `palette_manager.get_palette()` 得到 3 个颜色。
6. 生成真实 matplotlib grouped violin 图并保存 PNG。
7. 输出 Visual Source Report。
8. 验证 `adaptable` reference 可被检索到。
9. 删除所有临时资产。

运行结果：

```
E2E smoke test PASSED
Visual Source Report:
  production_asset: GroupedViolin/plot_GroupedViolin.py
  visual_reference: 9bac05e13ad33ecb
  palette: summer_beach
  palette_policy: preserve
  output_png: C:\Users\LRH\AppData\Local\Temp\afs_phase3_smoke_...\smoke_output.png
  colors: ['#FC757B', '#F97F5F', '#FAA26F']
```

---

## 3. Palette Manager 进入工作流

### 3.1 新增 `resolve_visual_style()`

位置：`scripts/reference_library.py`

统一入口：

```python
from scripts.reference_library import ReferenceLibrary

style = ReferenceLibrary().resolve_visual_style(
    figure_type="GroupedViolin",
    reference_id=refs[0].id if refs else None,
    user_colors=None,
    user_palette=None,
    n=3,
)
# style["colors"]
# style["palette"]
# style["palette_policy"]
# style["source"]  # user_colors | user_palette | reference | default
```

优先级：
1. `user_colors` → 原样返回
2. `user_palette` → 通过 palette manager 解析
3. Visual Reference palette：
   - `preserve` → 使用 reference 原 palette
   - `adaptable` → 通过 `palette_manager` 解析（可扩展/调整）
4. Skill default palette

### 3.2 SKILL.md 更新

- **Step 4.5 Visual Reference Retrieval**：加入 `resolve_visual_style()` 调用示例和 palette 优先级。
- **Step 5 Generate Code**：新增 "Palette integration for param inherit / cross-type inherit / new drawing functions" 小节，明确：
  - native-run production asset 保持原 hard-coded 颜色（视觉快照）。
  - new drawing / VISUAL ADAPT / PARAM INHERIT 使用 `resolve_visual_style()`。
  - VISUAL ADAPT 保留 production asset 的 layout、annotation、export 参数；仅当 `palette_policy=adaptable` 时可替换颜色列表。
- **Step 7 Deliver**：继续输出 Visual Source Report。

### 3.3 `compose.py` 安全接入 palette manager

`get_palette()` 新增可选参数 `palette`：

```python
compose.get_palette(3, role="categorical", palette="summer_beach")
```

- 未提供 `palette` 时行为完全不变（journal-safe default）。
- 提供 `palette` 且 `role="categorical"` 时，安全委托给 `palette_manager.get_palette()`。
- `sequential` / `diverging` 不受 `palette` 参数影响，避免把 categorical palette 强行塞进连续/发散色板。

### 3.4 哪些没有改

- 现有 55 个 production scripts 的 hard-coded colors 保持不动。
- 没有新建 theme manager 或 YAML config 系统。
- 没有给 production assets 批量加 metadata。

---

## 4. Style 规范冲突检查

审计报告指出的三处冲突在 Phase 0.1 wrapup 中已统一。本轮复查：

| 规则 | 权威来源 | 状态 |
|---|---|---|
| 字号 | `references/typography.md` COPY VERBATIM 块 | 已统一为 8 pt |
| Spine 线宽 | `references/journal-specs.md` | 已统一为 0.5-0.6 pt |
| Archetype 默认 | `SKILL.md` Step 0a | 已统一为 `asymmetric_mixed` |

本轮未引入新的 style 冲突。

---

## 5. 测试

### 5.1 新增 / 更新测试

- `scripts/e2e_smoke_test.py`：真实 E2E smoke test（preserve + adaptable）。
- `scripts/test_workflow_integration.py`：新增 9 个测试，覆盖：
  - `resolve_visual_style` 优先级（user colors > user palette > reference > default）
  - `preserve` 使用 reference 原 palette
  - `adaptable` 通过 palette manager 解析
  - 无 reference fallback
  - deterministic colors
  - `compose.get_palette(palette=...)` 安全接入 palette manager
  - `compose.get_palette(role="sequential")` 不受 palette 参数影响

### 5.2 全部测试结果

| 测试 | 数量 | 结果 |
|---|---|---|
| `python -m py_compile scripts/*.py` | 23 文件 | OK |
| `scripts/test_palette_manager.py` | 23 | OK |
| `scripts/test_reference_library.py` | 27 | OK |
| `scripts/test_workflow_integration.py` | 28 | OK |
| `scripts/e2e_smoke_test.py` | - | PASSED |
| `scripts/check_references.py` | - | HEALTHY |
| `scripts/run_ab_tests.py` | 21 checks | 100% |
| `scripts/eval_runner.py` | 29 types | 19 pass，10 种 R 脚本环境缺失 WARN |
| `scripts/qa_coverage.py` | 26 cases | 目标检查无漏报 |
| `scripts/trigger_benchmark.py` | 40 prompts | 100% |

---

## 6. 文件变更清单

```
SKILL.md                                    # Step 4.5 / Step 5 / Step 7 接入 palette
references/visual-reference-library.md      # 已在 Phase 2 创建，本轮未改
scripts/reference_library.py                # 新增 resolve_visual_style()
scripts/compose.py                          # get_palette 可选 palette 参数
scripts/__init__.py                         # 导出 resolve_visual_style
scripts/e2e_smoke_test.py                   # 新增真实 E2E smoke test
scripts/test_workflow_integration.py        # 新增 palette 优先级与集成测试
```

---

## 7. 推荐下一步

1. 在真实 create 任务中试用 `resolve_visual_style()`，记录 Visual Source Report。
2. 当生成新图或做 VISUAL ADAPT 时，观察 `preserve` vs `adaptable` 的实际效果。
3. 等积累足够多 reference 后，评估是否需要把 `resolve_visual_style()` 封装成 CLI 工具供非 Python agent 调用。
4. 考虑把 palette manager 接入更多新 production scripts（逐个进行，不批量）。
