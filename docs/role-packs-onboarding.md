# 角色包 10 分钟开箱指南（PRD-183/T4，trend #918）

> 对接 PRD-121 中文开箱动线。三包：`hr`（人事）/ `legal`（法务）/ `sales`
> （销售）；术语表与质量门见 `role-packs/terms.txt` 与 `scripts/quality-gate.py`。

## 你将得到（≈10 分钟）

- 三个中文职业角色包安装进本地 OpenWorker，角色人设与中文话术即刻可用；
- 会验证安装结果并跑一遍中文质量门。

## 步骤（每步 ≈2 分钟）

### 1. 取包（2 分钟）

从本仓库取 `role-packs/<pack>/`（hr / legal / sales 任选或全取）。
整包自包含：`persona.md` + `skills/`。**包根目录只有一个 `.md`**——
这是安装器的硬约束（`install_from_dir` 会严格解析包根全部 `.md`），
不要往包根另加文件。

### 2. 安装（2 分钟）

两步都走本地目录动线（**git URL 安装在本仓不可用**——克隆即扫会撞包根
约束，见步骤 1）：

- **装技能**：把 `role-packs/<pack>/skills/<技能名>/` 整个目录拷入全局技能
  目录（state_dir 下的 `skills/`），或项目 `.coworker/skills/`；也可以把技能
  目录打包成 zip，走设置页技能上传（暂存 → 预览 → 确认）。
- **装角色**：用 OpenWorker 的本地目录安装入口（`install_from_dir`）指向
  `role-packs/<pack>` 目录，核对中文授权摘要后确认启用。
  注意 `install_from_dir` 只装角色本体，不装包内技能——技能须按上一步单独拷入。

### 3. 验证（3 分钟）

- 技能列表出现该包全部成员技能；
- 触发一次角色技能（如 hr 的《岗位说明（JD）》草稿：对角色说
  「帮我写个 JD」），确认中文提示词按 persona 生效；
- 可选：跑 `python3 scripts/release-gate-role-packs.py` 自查
  （质量门自测 + 三包全量术语一致性；发版前为强制门，见 §5。
  注意 `quality-gate.py --root` 只扫 surfaces/docs，不覆盖 role-packs/，
  三包术语自查以发行门为准）。

### 4. 迭代/卸载（1 分钟）

- 改话术：改包内 SKILL.md 后重装；
- 卸载：客户端移除该包，或删除已安装目录。

### 5. 发版前（2 分钟）

维护者发布新版本前跑发行门：
`python3 scripts/release-gate-role-packs.py`
（质量门自测 + 全量术语一致性，任一失败退出码 1 = 不可发行；
豁免须在扫描范围内留痕，详见该脚本 docstring。）

## 红线

- 三包职责边界见 `role-packs/README.md`（hr 管"人"、legal 管"合规"、
  sales 管"转化"），越界需求不接；
- 术语以 `role-packs/terms.txt` + `scripts/quality-gate.py` TERMS 为准；
- 文档与示例全虚构占位，无真实主机名/IP/账号/密钥。
