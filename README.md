# skills-launch

维护上游 Skill 原版与当前使用的精简 Skill。

## 目录

- `originals/`：从上游仓库拉取的完整原版。
- `skills/`：经过选择、合并和精简后实际维护的 Skill。
- `skills.json`：上游来源及 original → Skill 的映射。
- `ADAPTATIONS.md`：来源、合并关系和适配决策。

仓库不提供安装器，也不会自动把上游变更复制到 `skills/`。

## 使用或安装当前 Skill

agent 使用或安装本仓库的 Skill 时，只以 `skills/` 当前存在的目录为准：

1. 在 `skills/` 中选择用户指定或与任务匹配的 Skill。
2. 阅读所选目录的 `SKILL.md`，并按其中引用加载同目录资源。
3. 安装前检查目标环境中实际存在的常见 Skill 目录，例如项目目录或用户目录下的 `.agents/skills/`、`.codex/skills/` 和 `.claude/skills/`。
4. 若发现名称不同但功能相近的 Skill，向用户列出名称、路径和主要重叠点，由用户选择全部保留或只保留部分；得到选择前不要覆盖、删除或合并。
5. 确认后，按照目标 agent 的约定复制完整的 `skills/<name>/` 目录。

本地检查只用于发现已安装 Skill 的功能冲突，不把它们作为本次安装的内容来源。安装候选仍只来自本仓库当前的 `skills/`；不要读取 `originals/`、`skills.json` 或 `ADAPTATIONS.md` 来补充安装内容，也不要从上游仓库获取内容。请求的 Skill 不在 `skills/` 中时，直接说明当前仓库未提供，不以 original 或外部 Skill 替代。

## 更新上游原版

更新指定 original：

```bash
python3 scripts/update_originals.py browser-use
```

更新全部 original：

```bash
python3 scripts/update_originals.py
```

脚本只更新 `originals/`，并输出：

- 新增、修改和删除的文件；
- 可能受影响的 `skills/` 条目；
- 用于审查原版差异的 `git diff` 命令。

现有 original 有未提交修改时，脚本会拒绝覆盖。下载或替换失败时，已有 original 保持不变。

## 决定是否更新 Skill

上游更新后：

1. 查看脚本输出和 `git diff -- originals/<name>`。
2. 阅读受影响的现有 `skills/<name>/SKILL.md` 及运行资源。
3. 判断上游变化是否改善当前工作流，是否与其他来源重复，是否引入平台假设或不必要复杂度。
4. 只把有明确收益的部分手动应用到 `skills/`；不要整目录覆盖。
5. 若能力被合并、拆分、保留或省略，更新 `ADAPTATIONS.md`。
6. 运行相关 Skill 的实际检查和仓库测试后再提交。

## 当前 Skill

| Skill | 能力 |
| --- | --- |
| `frontend-design` | 前端设计、UI/UX、设计系统搜索与实现检查 |
| `browser-workflows` | Browser Use 操作和本地 Web 应用测试 |
| `engineering-quality` | 方案设计与范围控制、风险与复杂度预算、实现决策、代码审查及行为保持的简化 |
| `doc-coauthoring` | 结构化文档协作、可靠性设计准入和读者验证 |
| `test-driven-development` | 面向已承诺行为的风险分级测试与小改动快速验证 |
| `find-skills` | 外部 Skill 发现、评估和授权安装 |

## 验证

```bash
python3 -m unittest discover -s tests -v
```
