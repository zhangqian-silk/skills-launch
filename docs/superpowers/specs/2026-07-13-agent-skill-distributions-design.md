# Claude 与 Codex Skill 双发行版设计

## 目标

将仓库从“优先安装上游、失败后使用本地副本”的单层清单，改造成三层 Skill 发行仓库：

1. `originals/` 保存未经平台适配的完整上游内容。
2. `distributions/claude/skills/` 保存可直接安装给 Claude 的发行版。
3. `distributions/codex/skills/` 保存可直接安装给 Codex 的精简发行版。

仓库交给 Codex 后必须支持两个明确场景：

- **维护模式**：Codex 根据完整原版和集中适配规则维护本仓库。
- **安装模式**：Codex 只安装已经验证的目标平台发行版，不在安装过程中临时同步或改写上游内容。

Codex 发行版优先减少上下文成本，可以合并重复 Skill，也可以省略 Codex 已可靠具备、且没有额外程序性价值的通用说明。

## 非目标

- 不记录每次同步所对应的上游 commit。
- 不在发行版目录中保存来源、适配历史、维护说明或参考网页。
- 不在安装时自动重新生成发行版。
- 不保留完整 Superpowers 套件，只保留并正常适配其中的 TDD Skill。
- 不保留 Claude 官方 `code-review` plugin；`code-reviewer` 的有效审查能力将进入对应发行版。
- 不依靠根目录 `SKILL.md` 引导 Agent；该文件将被移除。

## 官方设计依据

Codex 适配以 2026-07-13 读取的以下 OpenAI 官方资料为准：

- [Latest model migration quickstart](https://developers.openai.com/api/docs/guides/latest-model#migration-quickstart)
- [Latest model prompting best practices](https://developers.openai.com/api/docs/guides/latest-model#prompting-best-practices)
- [Codex customization: AGENTS.md and Skills](https://developers.openai.com/codex/concepts/customization)

本设计将这些建议落实为：指令只表达一次；只保留非显然的领域信息和程序性约束；明确成功标准、自治边界和需要确认的情况；不硬编码模型或推理强度；通过 Skill 元数据、正文和按需资源进行渐进披露。

## 顶层结构

```text
skills-launch/
├── AGENTS.md
├── CLAUDE.md
├── README.md
├── ADAPTATIONS.md
├── skills.json
├── originals/
│   ├── browser-use/
│   ├── code-reviewer/
│   ├── code-simplifier/
│   ├── doc-coauthoring/
│   ├── find-skills/
│   ├── frontend-design/
│   ├── fullstack-developer/
│   ├── taste-skill/
│   ├── test-driven-development/
│   ├── ui-ux-pro-max/
│   └── webapp-testing/
├── distributions/
│   ├── claude/
│   │   └── skills/
│   └── codex/
│       └── skills/
├── scripts/
│   └── skills_launch.py
└── tests/
```

## 文件职责

### `AGENTS.md`

Codex 自动读取的仓库级操作入口。文件保持短小，只包含：

- 维护模式与安装模式的识别规则。
- 各模式必须读取和不得读取的目录。
- `originals/` 不允许手工适配、发行版不允许携带维护信息等硬约束。
- 仓库的验证命令和完成标准。
- 请求不明确时不得安装或改写的边界。

### `CLAUDE.md`

Claude 对应的仓库入口，与 `AGENTS.md` 使用相同的目录边界和维护原则，但使用 Claude 可发现的入口文件名。两者不复制完整适配内容，而是按需指向 `ADAPTATIONS.md`。

### `README.md`

面向使用者说明项目目标、目录结构、Claude/Codex 安装命令、清单和外部依赖。README 不承担 Agent 必须遵循的操作约束。

### `ADAPTATIONS.md`

唯一的人类可读适配记录，集中保存：

- 官方参考资料和读取日期。
- Claude 与 Codex 的全局适配原则。
- 原版到发行版的合并、保留和省略映射。
- 每个发行 Skill 保留的能力和删除的冗余。
- Claude、Gemini 或特定工具硬编码的替换策略。
- 新上游内容应如何判断更适合 Claude、Codex 或两者。
- 后续 Agent 的重新适配步骤和质量检查清单。

发行版目录不得复制 `ADAPTATIONS.md` 中的内容。

### `skills.json`

机器可读的唯一目录和映射来源。采用版本 2 schema，分为 `sources` 和 `distributions`：

```json
{
  "version": 2,
  "sources": [
    {
      "name": "frontend-design",
      "source": {
        "kind": "github_file",
        "repo": "anthropics/skills",
        "ref": "main",
        "path": "skills/frontend-design/SKILL.md"
      },
      "original": "originals/frontend-design"
    }
  ],
  "distributions": {
    "codex": [
      {
        "name": "frontend-design",
        "sources": ["frontend-design", "ui-ux-pro-max", "taste-skill"],
        "path": "distributions/codex/skills/frontend-design"
      }
    ],
    "claude": []
  }
}
```

`sources` 供同步和维护使用；`distributions` 供安装和验证使用。来源映射不会被复制到安装目录。

## 两种运行模式

### 维护模式

用户要求同步、更新、适配、合并、删除或校验 Skill 时进入维护模式。

数据流：

```text
upstream GitHub
  -> sync
  -> originals/<source>
  -> Agent reads ADAPTATIONS.md and relevant originals
  -> Agent edits distributions/<agent>/skills
  -> validate and tests
```

`sync` 只更新 `originals/`，永远不覆盖发行版。发行版必须由 Agent 根据集中规则有意识地重写，避免把上游平台硬编码机械复制到另一平台。

### 安装模式

用户要求安装某个 Skill 或全部 Skill 时进入安装模式。

数据流：

```text
skills.json
  -> select distributions.<agent>
  -> copy distributions/<agent>/skills/<name>
  -> target skills directory
```

安装模式不得读取或下载上游内容，不得从 `originals/` 安装，也不得修改仓库。调用方必须显式提供 `--agent codex` 或 `--agent claude`。

## 发行版内容约束

每个发行 Skill 只允许包含完成任务所需的内容：

```text
<skill>/
├── SKILL.md
├── agents/openai.yaml    # 仅 Codex 发行版需要且生成有效元数据时
├── scripts/              # 仅确定性、可复用程序需要
├── references/           # 仅执行任务需要按需读取的知识
└── assets/               # 仅执行或生成结果需要的资源
```

禁止包含：

- README、安装指南、快速参考和 changelog。
- 上游 Skill 名称、GitHub 来源链接或合并历史。
- `ADAPTATION.md`、`source-context.md` 或同类维护文件。
- 目标平台不支持的工具名、模型名和目录假设。
- 与 Codex 基础能力重复的大段通用软件工程知识。

外部 CLI 的运行要求属于 Skill 功能的一部分，可以在 `SKILL.md` 中简洁说明；依赖安装方式放在根 README 和机器清单中，不放进发行 Skill。

## Claude 发行版

Claude 发行版原则上保持一份原版对应一份标准 Skill，保留上游的独特流程和 Claude 可用能力，但统一为可从 `distributions/claude/skills/` 直接安装的结构。Claude plugin 风格的 `code-simplifier` 将规范化为标准 Skill，而不是把整个 plugin 包作为发行单元。

Claude 发行版包含：

- `frontend-design`
- `doc-coauthoring`
- `fullstack-developer`
- `code-reviewer`
- `webapp-testing`
- `browser-use`
- `find-skills`
- `ui-ux-pro-max`
- `taste-skill`
- `code-simplifier`
- `test-driven-development`

## Codex 发行版及合并策略

Codex 发行版只保留六个边界清晰的 Skill。

### `frontend-design`

合并原版 `frontend-design`、`ui-ux-pro-max` 和 `taste-skill`。

保留：明确视觉方向、反通用 AI 美学约束、响应式与无障碍检查、设计系统搜索能力、主要前端栈的关键实现规则。

删除：重复的审美口号、庞大的行内枚举、互相冲突的优先级、硬编码仓库路径。大规模设计数据只有在搜索脚本实际使用时才作为 assets 保留。

### `browser-workflows`

合并原版 `browser-use` 和 `webapp-testing`。

保留：Browser Use CLI 的直接浏览器操作、本地服务器生命周期、页面探索、日志/截图/回归验证、失败诊断。外部 Python CLI 由安装器检查但不静默安装。

删除：重复浏览器操作说明、Claude artifact 假设和固定工作目录。

### `code-quality`

合并原版 `code-reviewer` 和 `code-simplifier`。

正文先根据用户意图区分 review 与 simplify：review 只报告高置信度、可操作的问题；simplify 在保持行为的前提下减少复杂度并验证。删除固定 `npm run preflight`、`model: opus`、`CLAUDE.md` 等项目假设。

### `doc-coauthoring`

保留独立 Skill，将原来的三阶段流程压缩为“收集上下文、结构化草拟、首次读者验证”。删除 Claude、Claude.ai、connectors、`create_file` 和 `str_replace` 等平台/工具硬编码。读者验证优先使用独立上下文；不可用时执行明确的冷读检查。

### `test-driven-development`

仅从 Superpowers 保留此 Skill，并将 Codex 版改写为风险分级的测试纪律，而不是所有改动一律强制严格 TDD。

- 新功能、回归修复、非平凡逻辑、公共接口、状态迁移和高风险重构使用 red-green-refactor：先确认测试因缺失行为而失败，再写最小实现并运行相关回归。
- 文档、注释、提示词、元数据、简单配置和明显的机械修改采用快速路径：直接完成改动，只运行最相关的低成本校验，不为了形式增加低价值测试。
- 看似很小的改动一旦影响可观察行为、扩大修改范围或缺少可靠验证，就切换到严格 TDD。

Codex 版 frontmatter 描述必须同时表达“复杂行为优先 TDD”和“小型低风险改动优先快速交付”，避免仅因 Skill 被触发就把所有任务扩展成完整测试工程。详细测试反模式只有对实际执行有帮助时才放入 reference。Claude 发行版仍保留原版的严格倾向。

### `find-skills`

保留独立 Skill，精简为发现、比较、获得用户授权、安装和验证五步流程。删除特定平台目录假设，将安装目标交给当前 Agent 环境或显式参数决定。

### Codex 不单独发行 `fullstack-developer`

该原版主要重复现代 Codex 已具备的通用 Web 技术知识，且范围过宽，难以可靠触发。独特、可执行的质量要求分别并入相关 Skill；完整原版和 Claude 版继续保留。

## Codex 提示重写标准

每个 Codex `SKILL.md` 必须满足：

1. Frontmatter 仅包含 `name` 和 `description`。
2. `description` 同时描述能力和具体触发场景，正文不再重复“When to use”。
3. 使用祈使式、短句和明确动作，不要求模型“多思考”或指定推理强度。
4. 每条硬约束只出现一次；示例只在能消除真实歧义时保留。
5. 明确成功标准、验证动作和停止条件。
6. 安全的本地读取、分析、编辑和验证可自主执行；外部发布、破坏性操作、昂贵操作和范围扩张需要确认。
7. 不写死 Codex 工具名；只在能力确实依赖某个外部 CLI 时写明命令接口。
8. `SKILL.md` 不超过 250 行；更长的执行知识必须按需下沉到 references。
9. 详细知识移到一层 `references/`；只有正文明确说明何时读取的 reference 才能存在。
10. 不把同一信息同时写在正文和 reference 中。

## CLI 设计

### 安装

```bash
python3 scripts/skills_launch.py install <name> --agent codex
python3 scripts/skills_launch.py install-all --agent claude
```

安装始终来自目标发行版。目标目录优先级：

1. 显式 `--target-dir`。
2. `AGENT_SKILLS_DIR`。
3. Codex 使用已设置的 `CODEX_HOME/skills`，否则使用 `$HOME/.agents/skills`。
4. Claude 使用已设置的 `CLAUDE_HOME/skills`，否则使用 `$HOME/.claude/skills`。

别名只在对应 Agent 的发行清单中解析。目标已存在时必须使用 `--force`。替换采用临时目录和原子移动，失败时保留已有安装。

Browser Use 发行项声明 `browser-use` CLI 依赖。安装器不自动改变 Python 环境；缺失时输出 README 中记录的 `uv tool install --python 3.12 --upgrade --force browser-use` 和 `browser-use --doctor` 引导。

### 同步

```bash
python3 scripts/skills_launch.py sync [source ...]
```

同步通过 `sources` 写入 `originals/`。下载先落入临时目录，成功并验证基本结构后再替换原版；任一来源失败时保留该来源现有副本并汇总错误。

### 校验

```bash
python3 scripts/skills_launch.py validate
```

校验 schema、路径、映射、Skill frontmatter、文件边界、Codex 内容质量和外部依赖声明。任何错误返回非零状态。

## 错误处理

- 未指定或不支持 `--agent`：列出允许值，不推测目标。
- 未知 Skill 或别名：按目标 Agent 列出可用名称。
- 分发路径缺失或逃逸仓库：拒绝安装。
- 目标存在且没有 `--force`：不修改目标。
- 安装复制失败：清理临时内容并保留原目标。
- 同步下载或验证失败：保留现有 original，继续处理其他来源后统一失败。
- Browser Use CLI 缺失：Skill 文件仍可安装，但明确报告依赖未就绪和修复命令。
- 发行映射引用未知 source：`validate` 失败。

## 测试策略

本次迁移涉及清单 schema、安装路由、原子替换和同步隔离，属于非平凡行为变更，因此核心行为遵循测试驱动开发：先写一个能因缺失功能而正确失败的测试，再写最小实现。纯文档搬迁、原版文件移动和机械目录调整使用快速路径，并通过结构校验和全量回归覆盖。

### 清单与目录测试

- schema 版本为 2。
- sources 和各 Agent 发行名唯一。
- source、distribution 路径存在且位于仓库内。
- 所有发行项引用的 source 存在。
- 根 `SKILL.md`、旧 `skills/`、完整 `suites/superpowers/` 和 `code-review` 不存在。

### 安装测试

- `--agent` 必填并正确路由 Claude/Codex 同名 Skill。
- 安装只复制发行版，不访问网络和 originals。
- alias、`--target-dir`、默认目录、冲突和 `--force` 行为正确。
- 安装失败保留已有目标。
- `install-all` 只安装所选 Agent 的目录项。
- Browser Use 依赖缺失时输出可执行引导。

### 同步测试

- sync 只写 originals。
- 单个失败不破坏现有副本。
- 文件和目录类型来源均能写入正确目标。

### Codex Skill 质量测试

- frontmatter 仅有 `name` 和 `description`，目录名与 name 一致。
- 每个 SKILL.md 不超过 250 行。
- 禁止出现 `Claude.ai`、`model: opus`、`create_file`、`str_replace`、固定 `.claude` 路径和旧仓库内硬编码路径。
- 禁止出现上游链接、来源说明、适配历史、README 和 changelog。
- references 必须由 SKILL.md 直接引用，且只允许一层。
- 合并后的触发描述覆盖预期任务，六个 Skill 之间没有明显的通用触发重叠。
- 保留的辅助脚本执行代表性 smoke test。

### 回归命令

```bash
python3 scripts/skills_launch.py validate
python3 -m unittest discover -s tests -v
```

## 迁移顺序

1. 为 schema v2、双 Agent 安装和目录边界编写失败测试。
2. 迁移原版内容到 `originals/`，只提取 Superpowers 的 TDD，删除其余套件和旧 `code-review`。
3. 建立 Claude 标准 Skill 发行版。
4. 重写六个 Codex Skill，并逐个执行结构和内容质量测试。
5. 改造 manifest、安装器、同步器和校验器。
6. 新增 `AGENTS.md`、`CLAUDE.md`、`ADAPTATIONS.md`，重写 README，删除根 `SKILL.md`。
7. 运行代表性脚本 smoke test、全量单元测试和安装隔离测试。

## 验收标准

- 将仓库交给 Codex 时，它能从 `AGENTS.md` 正确区分维护和安装请求。
- Codex 与 Claude 安装必须显式选定 Agent，并且只复制对应发行版。
- 所有完整原版可在 `originals/` 中用于后续重新适配。
- 完整 Superpowers 和 Claude `code-review` 已删除，TDD 以普通原版和两个发行版存在。
- Codex 只暴露六个精简、无平台硬编码、无溯源冗余的 Skill。
- 适配历史和官方参考资料只集中存在于 `ADAPTATIONS.md` 与机器清单。
- 同步失败不会破坏原版，安装失败不会破坏已有目标。
- `validate` 与全量测试通过。
