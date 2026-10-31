# 中文快速上手图解指南

> PRD-211/T2（trend #1056）：核心路径图解——安装 → 首个任务 → 常用场景

## 第一步：安装

```bash
pip install openworker-zh-localized
```

## 第二步：跑第一个中文任务

```bash
owzh run "帮我写一封示例邮件"
```

## 第三步：查看结果

```bash
owzh status
```

## 常用场景

| 场景 | 命令 |
|------|------|
| 写邮件 | 运行 `owzh run`，任务词写 "帮我写邮件" |
| 做报表 | 运行 `owzh run`，任务词写 "帮我做月度报表" |
| 整理数据 | 运行 `owzh run`，任务词写 "帮我整理这份数据" |

## 下一步

- 详细配置见 `docs/config.example.toml`
- 角色包见 `skills/` 目录

## 开箱叙事（跟做指南）

想按场景跟做一遍？见 `docs/role-packs-onboarding.md`（角色包 10 分钟开箱指南，对接 PRD-121 中文开箱动线）；本手册配套的模板见 `docs/guides/templates.md`。
