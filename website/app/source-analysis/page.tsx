import { repoReport } from "./generated";

const repoUrl = "https://github.com/zhanglunet/openworker-zh-localized";
const upstreamUrl = "https://github.com/andrewyng/openworker";

export default function SourceAnalysisPage() {
  return (
    <main className="analysis-detail-page">
      <header className="site-header">
        <a className="brand" href="/" aria-label="返回 OpenWorker 中文站首页">
          <span className="brand-mark" aria-hidden="true">O</span>
          <span>OpenWorker</span>
          <span className="brand-tag">源码分析</span>
        </a>
        <nav aria-label="源码分析导航">
          <a href="#map">目录地图</a>
          <a href="#runtime">运行流程</a>
          <a href="#api">接口 / MCP</a>
          <a href="#enterprise">企业定制</a>
          <a href="/updates">日志周报</a>
        </nav>
        <a className="nav-cta" href={repoUrl} target="_blank" rel="noreferrer">
          中文仓库 <span aria-hidden="true">↗</span>
        </a>
      </header>

      <section className="analysis-detail-hero section-shell">
        <div>
          <p className="eyebrow"><span className="signal-dot" /> Repository Deep Dive</p>
          <h1>OpenWorker 中文版<br /><em>源码全景分析</em></h1>
          <p>
            这页分析 <a href={repoUrl} target="_blank" rel="noreferrer">zhanglunet/openworker-zh-localized</a> 的真实仓库结构、
            运行流程、功能边界、接口、MCP、打包产物和中文站维护方式，并把同一份分析持久化到
            <code> docs/analysis/openworker-zh-localized-source-analysis.md</code>。
          </p>
          <div className="source-actions">
            <a className="button button-primary" href="/infographic">查看信息图</a>
            <a className="text-link" href={upstreamUrl} target="_blank" rel="noreferrer">上游 openworker</a>
          </div>
        </div>
        <aside className="deep-snapshot" aria-label="源码分析快照">
          <div><strong>{repoReport.totalFiles}</strong><span>Git 跟踪文件</span></div>
          <div><strong>{repoReport.shortHead}</strong><span>当前提交</span></div>
          <div><strong>{repoReport.byExt[0]?.count ?? 0}</strong><span>{repoReport.byExt[0]?.name} 文件最多</span></div>
          <div><strong>{repoReport.generatedAt.slice(0, 10)}</strong><span>分析生成日期</span></div>
        </aside>
      </section>

      <section className="section-shell deep-section" id="map">
        <div className="deep-heading">
          <p className="eyebrow">01 · 目录地图</p>
          <h2>不是一个单页应用，<br />而是一套本地 Agent 平台。</h2>
          <p>仓库按桌面壳、前端工作台、Python sidecar、Agent 核心、连接器、打包发布和中文站拆分。下面的统计来自当前 Git 跟踪文件。</p>
        </div>

        <div className="directory-grid">
          {repoReport.byTopDir.map((item) => (
            <article key={item.name}>
              <span>{item.name}</span>
              <strong>{item.count}</strong>
              <p>{directoryDescription(item.name)}</p>
            </article>
          ))}
        </div>

        <div className="ext-wall" aria-label="文件类型统计">
          {repoReport.byExt.map((item) => (
            <span key={item.name}>{item.name} · {item.count}</span>
          ))}
        </div>
      </section>

      <section className="dark-section deep-dark" id="runtime">
        <div className="section-shell">
          <div className="deep-heading light-heading">
            <p className="eyebrow">02 · 运行流程</p>
            <h2>从双击 App 到完成任务，<br />中间有九个关键动作。</h2>
            <p>OpenWorker 的核心不是“一次 API 请求”，而是 GUI、sidecar、模型、工具、权限和审计之间的循环。</p>
          </div>
          <div className="runtime-steps">
            {repoReport.runtimeFlow.map((step, index) => (
              <article key={step}>
                <span>{String(index + 1).padStart(2, "0")}</span>
                <p>{step}</p>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section className="section-shell deep-section">
        <div className="deep-heading">
          <p className="eyebrow">03 · 模块拆解</p>
          <h2>六组核心模块，<br />决定它能不能真的做事。</h2>
        </div>
        <div className="module-grid">
          {repoReport.highlights.map((item) => (
            <article key={item.title}>
              <h3>{item.title}</h3>
              <p>{item.summary}</p>
              <ul>
                {item.files.map((file) => <li key={file}>{file}</li>)}
              </ul>
            </article>
          ))}
        </div>
      </section>

      <section className="section-shell deep-section" id="api">
        <div className="deep-heading">
          <p className="eyebrow">04 · 接口、MCP 与能力面</p>
          <h2>接口层把桌面体验<br />接到本地 Agent Runtime。</h2>
          <p>前端通过 REST 与 WebSocket 连接 sidecar；MCP 让第三方工具以标准协议接入；连接器把 Gmail、Slack、GitHub、日历等工作系统纳入执行边界。</p>
        </div>
        <div className="api-grid">
          {repoReport.apiGroups.map((group) => (
            <article key={group.name}>
              <h3>{group.name}</h3>
              {group.examples.map((example) => <code key={example}>{example}</code>)}
            </article>
          ))}
        </div>
      </section>

      <section className="section-shell deep-section">
        <div className="deep-heading">
          <p className="eyebrow">05 · 架构流程图</p>
          <h2>数据与控制流<br />从目标走向交付物。</h2>
        </div>
        <div className="flow-ribbon">
          {repoReport.architectureFlow.map((node, index) => (
            <div key={node}>
              <span>{String(index + 1).padStart(2, "0")}</span>
              <b>{node}</b>
            </div>
          ))}
        </div>
      </section>

      <section className="section-shell deep-section" id="enterprise">
        <div className="deep-heading">
          <p className="eyebrow">06 · 企业定制扩展点</p>
          <h2>不重写核心，<br />八个层次做出企业版。</h2>
          <p>
            私有模型、企业技能包、知识库、企业 CLI、大表哥表格助手、品牌换肤、三仓同步与多平台发布——
            大部分是配置级或资产级定制。完整 PRD、开发计划、同步与部署方案见仓库
            <code> docs/enterprise/</code>。
          </p>
        </div>
        <div className="module-grid">
          {repoReport.enterpriseLayers.map((item) => (
            <article key={item.layer}>
              <h3>{item.layer} <small>（{item.grade}）</small></h3>
              <p>{item.summary}</p>
              <ul>
                {item.files.map((file) => <li key={file}>{file}</li>)}
              </ul>
            </article>
          ))}
        </div>
      </section>

      <section className="section-shell deep-section">
        <div className="deep-heading">
          <p className="eyebrow">07 · 持续维护</p>
          <h2>分析不是一次性页面，<br />它会随版本再生成。</h2>
          <p>构建前会运行报告生成脚本，刷新源码分析、更新日志和周报数据。最近提交如下：</p>
        </div>
        <div className="commit-list">
          {repoReport.recentCommits.slice(0, 8).map((commit) => (
            <div key={commit.hash}>
              <span>{commit.date}</span>
              <code>{commit.hash}</code>
              <p>{commit.subject}</p>
            </div>
          ))}
        </div>
      </section>
    </main>
  );
}

function directoryDescription(name: string) {
  const descriptions: Record<string, string> = {
    coworker: "Python Agent 服务、权限、模型、工具、连接器和持久化。",
    surfaces: "React GUI 与 Tauri 桌面壳。",
    website: "中文站、信息图、源码分析和日志页面。",
    docs: "分析文档、更新记录、截图素材。",
    releases: "已构建的安装包下载产物。",
    packaging: "PyInstaller、Tauri、DMG/Windows 打包脚本。",
    tests: "后端、权限、连接器、自动化等测试资产。",
    stt: "语音输入与转写 sidecar。",
    ".github": "CI、构建和计划任务工作流。",
  };
  return descriptions[name] ?? "辅助源码、配置或项目资产。";
}
