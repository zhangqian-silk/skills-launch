# skills-launch

个人推荐的 agent skill 列表集合。

这个仓库的目标很简单：把它交给 agent 后，agent 可以按清单安装这里推荐的 skills。安装时优先从原始 GitHub 地址获取最新版；如果原地址不可用，再使用本仓库中的 fallback 副本。

其中大多数条目是标准 `SKILL.md` 目录；`code-simplifier` 保留了上游 Claude plugin 结构。`superpowers` 是完整的跨平台 skill 套件，保留上游仓库结构。安装时请按 `skills.json` 的 `package_type` 将不同类型放到目标 agent 支持的目录。

## 快速使用

安装某个 skill 或 plugin-style capability：

```bash
python3 scripts/skills_launch.py install frontend-design
```

安装完整 Superpowers 套件：

```bash
python3 scripts/skills_launch.py install superpowers
```

安装清单里的全部条目：

```bash
python3 scripts/skills_launch.py install-all
```

指定安装目录：

```bash
python3 scripts/skills_launch.py install frontend-design --target-dir "$HOME/.codex/skills"
```

批量安装时分别指定 skill、plugin 和套件目录：

```bash
python3 scripts/skills_launch.py install-all \
  --skills-dir "$HOME/.codex/skills" \
  --plugins-dir "$HOME/.codex/plugins" \
  --suites-dir "$HOME/.codex/plugins"
```

如果目标目录里已经有同名 skill，并且你确认要替换：

```bash
python3 scripts/skills_launch.py install frontend-design --force
```

### Browser Use CLI 依赖

`browser-use` 的 `SKILL.md` 负责告诉 agent 如何操作浏览器；实际的浏览器控制能力由 Python CLI 提供。通过本仓库安装 skill 后，还需要使用 `uv` 安装或升级 CLI：

```bash
uv tool install --python 3.12 --upgrade --force browser-use
browser-use --doctor
```

如果没有通过本仓库安装 skill，也可以让 Browser Use CLI 将自带的版本匹配 skill 注册到支持的 agent：

```bash
browser-use skill install
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
| `browser-use` | <https://github.com/browser-use/browser-use/tree/main/skills/browser-use> |
| `find-skills` (`vercel-labs-skills`) | <https://github.com/vercel-labs/skills/tree/main/skills/find-skills> |
| `superpowers`（完整套件） | <https://github.com/obra/superpowers> |
| `ui-ux-pro-max` | <https://github.com/nextlevelbuilder/ui-ux-pro-max-skill> |
| `taste-skill` | <https://github.com/leonxlnx/taste-skill/tree/main/skills/taste-skill> |
| `code-simplifier` | <https://github.com/anthropics/claude-plugins-official/tree/main/plugins/code-simplifier> |

## 维护副本

同步所有上游内容到本仓库副本：

```bash
python3 scripts/skills_launch.py sync
```

只同步部分：

```bash
python3 scripts/skills_launch.py sync frontend-design browser-use
```

`skills.json` 是机器可读清单；新增 skill 时，请同时补充原地址、仓库副本路径和简短说明。

提交前校验清单和 fallback 副本：

```bash
python3 scripts/skills_launch.py validate
```
