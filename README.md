# skills-launch

为 Claude 和 Codex 维护的 Skill 源码与优化发行仓库。

## 目录模型

- `originals/`：完整上游内容，只用于同步和重新适配。
- `distributions/claude/skills/`：可直接安装给 Claude 的标准 Skill。
- `distributions/codex/skills/`：面向 Codex 精简、合并后的标准 Skill。
- `ADAPTATIONS.md`：集中记录来源、合并关系和平台适配规则，不随 Skill 安装。

安装完全使用仓库中已经检验的发行版，不访问上游网络，也不会安装 `originals/`。

## 安装

安装给 Codex：

```bash
python3 scripts/skills_launch.py install frontend-design --agent codex
```

安装给 Claude：

```bash
python3 scripts/skills_launch.py install frontend-design --agent claude
```

安装目标 Agent 的全部 Skill：

```bash
python3 scripts/skills_launch.py install-all --agent codex
python3 scripts/skills_launch.py install-all --agent claude
```

使用 `--target-dir <path>` 指定目录，使用 `--force` 替换已有安装。默认情况下，Codex 使用 `$CODEX_HOME/skills` 或 `$HOME/.agents/skills`，Claude 使用 `$CLAUDE_HOME/skills` 或 `$HOME/.claude/skills`；`AGENT_SKILLS_DIR` 可统一覆盖默认值。

## Codex 发行版

| Skill | 能力 |
| --- | --- |
| `frontend-design` | 前端设计、UI/UX、设计系统搜索与实现检查 |
| `browser-workflows` | Browser Use 操作和本地 Web 应用测试 |
| `code-quality` | 代码审查与行为保持的简化 |
| `doc-coauthoring` | 结构化文档协作与读者验证 |
| `test-driven-development` | 风险分级的 TDD 与小改动快速验证 |
| `find-skills` | 外部 Skill 发现、评估和授权安装 |

Codex 安装时可继续使用原名称作为别名，例如 `ui-ux-pro-max` 会安装合并后的 `frontend-design`，`browser-use` 会安装 `browser-workflows`。

## Claude 发行版

Claude 保留 11 个标准 Skill：`frontend-design`、`doc-coauthoring`、`fullstack-developer`、`code-reviewer`、`webapp-testing`、`browser-use`、`find-skills`、`ui-ux-pro-max`、`taste-skill`、`code-simplifier` 和 `test-driven-development`。

## Browser Use CLI

安装浏览器 Skill 不会自动修改 Python 环境。缺少 `browser-use` 命令时运行：

```bash
uv tool install --python 3.12 --upgrade --force browser-use
browser-use --doctor
```

## 维护

同步一个或全部完整原版：

```bash
python3 scripts/skills_launch.py sync browser-use
python3 scripts/skills_launch.py sync
```

同步只更新 `originals/`，不会覆盖任何发行版。适配前阅读 `ADAPTATIONS.md`。

完成修改前运行：

```bash
python3 scripts/skills_launch.py validate
python3 -m unittest discover -s tests -v
```
