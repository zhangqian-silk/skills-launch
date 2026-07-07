# skills-launch

个人推荐的 agent skill 列表集合。

这个仓库的目标很简单：把它交给 agent 后，agent 可以按清单安装这里推荐的 skills。安装时优先从原始 GitHub 地址获取最新版；如果原地址不可用，再使用本仓库 `skills/` 里的副本。

其中大多数条目是标准 `SKILL.md` 目录；`code-simplifier` 和 `code-review` 保留了上游 Claude plugin 结构，安装时请放到目标 agent 支持的 plugin 目录，或让 agent 按 `skills.json` 的 `package_type` 处理。

## 快速使用

安装某个 skill 或 plugin-style capability：

```bash
python3 scripts/skills_launch.py install frontend-design
```

安装清单里的全部条目：

```bash
python3 scripts/skills_launch.py install-all
```

指定安装目录：

```bash
python3 scripts/skills_launch.py install frontend-design --target-dir "$HOME/.codex/skills"
```

批量安装时分别指定 skill 和 plugin 目录：

```bash
python3 scripts/skills_launch.py install-all --skills-dir "$HOME/.codex/skills" --plugins-dir "$HOME/.codex/plugins"
```

如果目标目录里已经有同名 skill，并且你确认要替换：

```bash
python3 scripts/skills_launch.py install frontend-design --force
```

也可以把仓库根目录的 `SKILL.md` 直接交给 agent，让它按 `skills.json` 里的清单安装。

## 推荐清单

| Skill | 原地址 |
| --- | --- |
| `frontend-design` | <https://github.com/anthropics/skills/blob/main/skills/frontend-design/SKILL.md> |
| `doc-coauthoring` | <https://github.com/anthropics/skills/blob/main/skills/doc-coauthoring/SKILL.md> |
| `fullstack-developer` | <https://github.com/Shubhamsaboo/awesome-llm-apps/tree/main/awesome_agent_skills/fullstack-developer> |
| `code-reviewer` | <https://github.com/google-gemini/gemini-cli/blob/main/.gemini/skills/code-reviewer/SKILL.md> |
| `webapp-testing` | <https://github.com/anthropics/skills/tree/main/skills/webapp-testing> |
| `agent-browser` | <https://github.com/vercel-labs/agent-browser/tree/main/skills/agent-browser> |
| `find-skills` (`vercel-labs-skills`) | <https://github.com/vercel-labs/skills/tree/main/skills/find-skills> |
| `test-driven-development` | <https://github.com/obra/superpowers/tree/main/skills/test-driven-development> |
| `ui-ux-pro-max` | <https://github.com/nextlevelbuilder/ui-ux-pro-max-skill> |
| `taste-skill` | <https://github.com/leonxlnx/taste-skill/tree/main/skills/taste-skill> |
| `code-simplifier` | <https://github.com/anthropics/claude-plugins-official/tree/main/plugins/code-simplifier> |
| `code-review` | <https://github.com/anthropics/claude-plugins-official/tree/main/plugins/code-review> |
| `brainstorming` | <https://github.com/obra/superpowers/tree/main/skills/brainstorming> |

## 维护副本

同步所有上游内容到本仓库副本：

```bash
python3 scripts/skills_launch.py sync
```

只同步部分：

```bash
python3 scripts/skills_launch.py sync frontend-design code-review
```

`skills.json` 是机器可读清单；新增 skill 时，请同时补充原地址、仓库副本路径和简短说明。

提交前校验清单和 fallback 副本：

```bash
python3 scripts/skills_launch.py validate
```
