import { execFileSync } from "node:child_process";
import { mkdirSync, writeFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const siteRoot = resolve(here, "..");
const repoRoot = resolve(siteRoot, "..");

function git(args) {
  return execFileSync("git", args, { cwd: repoRoot, encoding: "utf8" }).trim();
}

function safeGit(args, fallback = "") {
  try {
    return git(args);
  } catch {
    return fallback;
  }
}

function trackedFiles() {
  return git(["ls-files"]).split("\n").filter(Boolean);
}

function extname(file) {
  const base = file.split("/").pop() ?? file;
  const index = base.lastIndexOf(".");
  return index > 0 ? base.slice(index + 1).toLowerCase() : "[none]";
}

function countBy(items, mapper) {
  const map = new Map();
  for (const item of items) {
    const key = mapper(item);
    map.set(key, (map.get(key) ?? 0) + 1);
  }
  return [...map.entries()].sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]));
}

function commits(args = []) {
  const out = safeGit(["log", "--date=short", "--pretty=format:%h%x09%ad%x09%s", ...args]);
  return out
    ? out.split("\n").map((line) => {
        const [hash, date, ...subject] = line.split("\t");
        return { hash, date, subject: subject.join("\t") };
      })
    : [];
}

const files = trackedFiles();
const byExt = countBy(files, extname);
const byTopDir = countBy(files, (file) => file.split("/")[0] ?? file);
const head = git(["rev-parse", "HEAD"]);
const shortHead = git(["rev-parse", "--short", "HEAD"]);
const branch = safeGit(["branch", "--show-current"], "main");
const generatedAt =
  process.env.REPORT_GENERATED_AT ||
  safeGit(["log", "-1", "--date=iso-strict", "--format=%cd"], new Date().toISOString());
const recentCommits = commits(["-n", "12"]);
const weeklyCommits = commits(["--since=7 days ago"]);

const highlights = [
  {
    title: "桌面壳",
    files: ["surfaces/gui/src-tauri/src/lib.rs", "surfaces/gui/src-tauri/tauri.conf.json"],
    summary: "Tauri 负责启动窗口、托盘、原生权限、语音输入、更新检查和 Python sidecar 生命周期。",
  },
  {
    title: "前端工作台",
    files: ["surfaces/gui/src/App.tsx", "surfaces/gui/src/api.ts", "surfaces/gui/src/components"],
    summary: "React 工作台承载会话、审批、收件箱、连接器、模型配置、产物和实时事件流。",
  },
  {
    title: "本地服务",
    files: ["coworker/server/app.py", "coworker/server/manager.py"],
    summary: "FastAPI sidecar 暴露 REST 与 WebSocket，集中协调会话、任务、审计、自动化和持久化。",
  },
  {
    title: "Agent 运行核心",
    files: ["coworker/engine.py", "coworker/permissions.py", "coworker/tools", "coworker/providers"],
    summary: "TurnEngine、PermissionEngine、工具注册表和 ProviderRouter 组成 model-tool 循环。",
  },
  {
    title: "连接器与 MCP",
    files: ["coworker/connectors", "coworker/mcp", "surfaces/gui/src/connectors"],
    summary: "内置连接器、MCP server 管理和 OAuth/账户视图把外部系统接入本地运行时。",
  },
  {
    title: "中文站与发布物",
    files: ["website", "docs", "releases"],
    summary: "中文站、架构信息图、源码分析、日志周报和 macOS DMG 下载入口随仓库维护。",
  },
];

const architectureFlow = [
  "用户目标",
  "React/Tauri 工作台",
  "FastAPI sidecar",
  "SessionManager",
  "TurnEngine",
  "ProviderRouter",
  "模型",
  "工具/MCP/连接器",
  "权限与审计",
  "交付物",
];

const runtimeFlow = [
  "下载 DMG 或源码启动",
  "Tauri/浏览器加载 GUI",
  "sidecar 选择端口并生成 token",
  "GUI 通过 REST/WebSocket 连接本地服务",
  "用户发起目标与上下文",
  "模型提出计划与工具调用",
  "权限系统判断风险与批准策略",
  "工具结果写入会话、审计、Inbox 或文件",
  "最终结果返回用户",
];

const apiGroups = [
  { name: "健康与启动", examples: ["/v1/health", "WebSocket /ws/events"] },
  { name: "会话", examples: ["/v1/sessions", "/ws/session/{sessionId}"] },
  { name: "模型提供商", examples: ["/v1/providers", "/v1/providers/models"] },
  { name: "连接器", examples: ["/v1/connectors/*", "OAuth 状态轮询"] },
  { name: "MCP", examples: ["/v1/mcp/*", "stdio / streamable-http server"] },
  { name: "自动化与 Inbox", examples: ["/v1/automations/*", "/v1/inbox/*"] },
  { name: "本地文件与产物", examples: ["文件工具", "目录授权", "产物预览"] },
];

const weeklySummary =
  weeklyCommits.length > 0
    ? weeklyCommits
        .slice(0, 8)
        .map((commit) => `- ${commit.date} ${commit.hash} ${commit.subject}`)
        .join("\n")
    : "- 最近 7 天没有新的 Git 提交。";

const analysisMarkdown = `# OpenWorker 中文本地化仓库源码分析

更新时间：${generatedAt}

仓库：zhanglunet/openworker-zh-localized

当前分支：${branch}

当前提交：${head}

## 1. 总体判断

本仓库是在 OpenWorker 原始项目基础上的中文本地化与中文站扩展版本。它不是单纯的静态翻译包，而是包含桌面 App、Python 本地 Agent 服务、React 工作台、连接器/MCP、打包脚本、中文网站、下载产物和持续文档化页面的一体化仓库。

## 2. 代码规模快照

- 跟踪文件总数：${files.length}
- 当前提交：${shortHead}
- 主要文件类型：
${byExt
  .slice(0, 16)
  .map(([ext, count]) => `  - ${ext}: ${count}`)
  .join("\n")}

## 3. 目录结构

${byTopDir.map(([dir, count]) => `- ${dir}: ${count} 个文件`).join("\n")}

## 4. 核心模块

${highlights
  .map(
    (item) => `### ${item.title}

${item.summary}

关键路径：
${item.files.map((file) => `- \`${file}\``).join("\n")}`,
  )
  .join("\n\n")}

## 5. 运行链路

${runtimeFlow.map((item, index) => `${index + 1}. ${item}`).join("\n")}

## 6. 架构流程图

\`\`\`mermaid
flowchart LR
${architectureFlow.map((item, index) => `  N${index}["${item}"]`).join("\n")}
${architectureFlow
  .slice(0, -1)
  .map((_, index) => `  N${index} --> N${index + 1}`)
  .join("\n")}
\`\`\`

## 7. API 与 MCP

${apiGroups.map((group) => `- ${group.name}: ${group.examples.join("、")}`).join("\n")}

## 8. 最近更新

${recentCommits.map((commit) => `- ${commit.date} ${commit.hash} ${commit.subject}`).join("\n")}
`;

const changelogMarkdown = `# OpenWorker 中文站更新日志

更新时间：${generatedAt}

## 最近提交

${recentCommits.map((commit) => `- ${commit.date} ${commit.hash} ${commit.subject}`).join("\n")}
`;

const weeklyMarkdown = `# OpenWorker 中文站周报

生成时间：${generatedAt}

## 本周概览

${weeklySummary}

## 维护建议

- 每次发布前运行 \`npm test\`，确保首页、信息图、源码分析和日志页都能渲染。
- DMG 更新后同步校验 README、网站下载入口和 Release 说明。
- 上游同步前保持 PR 范围清晰，避免把中文站部署物和二进制文件混入不适合上游的改动。
`;

const generatedTs = `export const repoReport = ${JSON.stringify(
  {
    generatedAt,
    branch,
    head,
    shortHead,
    totalFiles: files.length,
    byExt: byExt.slice(0, 18).map(([name, count]) => ({ name, count })),
    byTopDir: byTopDir.map(([name, count]) => ({ name, count })),
    highlights,
    architectureFlow,
    runtimeFlow,
    apiGroups,
    recentCommits,
    weeklyCommits,
  },
  null,
  2,
)} as const;
`;

mkdirSync(join(repoRoot, "docs", "analysis"), { recursive: true });
mkdirSync(join(repoRoot, "docs", "updates"), { recursive: true });
mkdirSync(join(siteRoot, "app", "source-analysis"), { recursive: true });
mkdirSync(join(siteRoot, "app", "updates"), { recursive: true });

writeFileSync(join(repoRoot, "docs", "analysis", "openworker-zh-localized-source-analysis.md"), analysisMarkdown);
writeFileSync(join(repoRoot, "docs", "updates", "CHANGELOG.md"), changelogMarkdown);
writeFileSync(join(repoRoot, "docs", "updates", "WEEKLY.md"), weeklyMarkdown);
writeFileSync(join(siteRoot, "app", "source-analysis", "generated.ts"), generatedTs);
writeFileSync(join(siteRoot, "app", "updates", "generated.ts"), generatedTs);

console.log(`generated reports for ${shortHead}: ${files.length} tracked files`);
