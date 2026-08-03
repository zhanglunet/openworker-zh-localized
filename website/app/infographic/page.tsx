const architectureNodes = [
  {
    label: "入口层",
    title: "React 工作台",
    text: "会话、Inbox、审批、自动化和产物都在桌面工作台中呈现。",
    tone: "orange",
  },
  {
    label: "桌面壳",
    title: "Tauri 2",
    text: "Rust 进程监管 Python sidecar，并注入地址、端口与启动令牌。",
    tone: "lime",
  },
  {
    label: "本地服务",
    title: "FastAPI + WebSocket",
    text: "SessionManager 协调会话、连接器、计划任务、审计和持久化。",
    tone: "paper",
  },
  {
    label: "Agent Runtime",
    title: "TurnEngine",
    text: "驱动模型和工具的多轮循环：低风险读取并发，写入与 Shell 串行。",
    tone: "ink",
  },
  {
    label: "执行边界",
    title: "PermissionEngine",
    text: "按风险、模式、root、命令规则和批准策略决定是否执行。",
    tone: "orange",
  },
  {
    label: "外部与本机",
    title: "Tools · MCP · Models · Store",
    text: "连接本地文件、Git、Shell、MCP、模型路由、SQLite、JSONL 与 SecretStore。",
    tone: "lime",
  },
];

const loopSteps = [
  ["01", "目标进入会话", "附加上下文、文件、AGENTS.md、skills 与 memory。"],
  ["02", "ProviderRouter 请求模型", "按 provider:model 前缀路由到 OpenAI、Anthropic、Gemini、Ollama 等。"],
  ["03", "模型提出工具调用", "文本、reasoning、tool_calls 被事件流推送到工作台。"],
  ["04", "权限先判定", "PermissionEngine 判断风险等级，必要时进入批准或 Inbox。"],
  ["05", "执行已批准工具", "读取可并发；写入、Shell 和未知工具严格串行。"],
  ["06", "结果回灌或交付", "工具结果写入历史与审计；若还有调用继续循环，否则输出最终产物。"],
];

const safetyRows = [
  ["READ", "读取 / 搜索", "默认低风险，可直接运行。", "直接执行"],
  ["WRITE_LOCAL", "文件写入 / patch", "必须落在可写 root 内。", "按模式批准"],
  ["EXEC", "Shell 命令", "复杂命令不会自动命中白名单。", "重点确认"],
  ["EXTERNAL", "发送或修改外部系统", "可绑定精确目标规则。", "目标级授权"],
];

const metrics = [
  ["main@3766805", "最早信息图快照"],
  ["35", "连接器条目"],
  ["881", "后端测试函数"],
  ["59", "GUI E2E spec"],
];

export default function InfographicPage() {
  return (
    <main className="infographic-page">
      <header className="site-header">
        <a className="brand" href="/" aria-label="返回 OpenWorker 中文站首页">
          <span className="brand-mark" aria-hidden="true">O</span>
          <span>OpenWorker</span>
          <span className="brand-tag">信息图</span>
        </a>
        <nav aria-label="信息图导航">
          <a href="#architecture">系统架构</a>
          <a href="#loop">Agent 循环</a>
          <a href="#safety">安全边界</a>
          <a href="/">返回首页</a>
        </nav>
        <a className="nav-cta" href="https://github.com/andrewyng/openworker" target="_blank" rel="noreferrer">
          上游源码 <span aria-hidden="true">↗</span>
        </a>
      </header>

      <section className="infographic-hero section-shell">
        <div>
          <p className="eyebrow"><span className="signal-dot" /> 仓库分析信息图</p>
          <h1>OpenWorker<br /><em>运行架构地图</em></h1>
          <p>
            这页来自本次对话最早对 <a href="https://github.com/andrewyng/openworker" target="_blank" rel="noreferrer">andrewyng/openworker</a> 的仓库分析，
            将原来的“系统架构 / Agent 循环 / 安全边界”三张图整理成可直接发布的中文网页。
          </p>
        </div>
        <aside className="infographic-snapshot" aria-label="信息图快照">
          {metrics.map(([value, label]) => (
            <div key={label}>
              <strong>{value}</strong>
              <span>{label}</span>
            </div>
          ))}
        </aside>
      </section>

      <section className="infographic-band">
        <div className="section-shell infographic-band-inner">
          <span>核心判断</span>
          <p>OpenWorker 不是桌面壳里直接调用模型，而是一套本地优先的 Agent 运行平台：桌面界面、本地 Python 服务、权限系统、模型路由、连接器和审计持久化共同构成产品壁垒。</p>
        </div>
      </section>

      <section className="section-shell infographic-section" id="architecture">
        <div className="infographic-heading">
          <p className="eyebrow">View 01</p>
          <h2>系统架构</h2>
          <p>用户入口经过 React 与 Tauri 桌面壳进入 Python sidecar，再由会话管理器和 TurnEngine 协调模型、权限、工具与本地状态。</p>
        </div>

        <div className="architecture-infographic" aria-label="OpenWorker 系统架构信息图">
          {architectureNodes.map((node, index) => (
            <article className={`arch-node tone-${node.tone}`} key={node.title}>
              <span>{node.label}</span>
              <h3>{node.title}</h3>
              <p>{node.text}</p>
              {index < architectureNodes.length - 1 && <i aria-hidden="true">→</i>}
            </article>
          ))}
        </div>
      </section>

      <section className="loop-panel" id="loop">
        <div className="section-shell">
          <div className="infographic-heading light-heading">
            <p className="eyebrow">View 02</p>
            <h2>Agent 循环</h2>
            <p>一次用户回合可能经历多次 model ↔ tool 迭代。OpenWorker 的价值在于把每一步变成可观察、可批准、可恢复的执行过程。</p>
          </div>

          <div className="loop-timeline">
            {loopSteps.map(([number, title, text]) => (
              <article className="loop-step" key={number}>
                <span>{number}</span>
                <h3>{title}</h3>
                <p>{text}</p>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section className="section-shell infographic-section" id="safety">
        <div className="infographic-heading">
          <p className="eyebrow">View 03</p>
          <h2>安全边界</h2>
          <p>“本地优先”是一条重要边界，但不是“数据永不出机”。状态和密钥主要留在本机，模型和连接器仍会接收完成任务所需的数据。</p>
        </div>

        <div className="safety-matrix" aria-label="OpenWorker 权限风险矩阵">
          {safetyRows.map(([risk, action, rule, decision]) => (
            <article className="safety-card" key={risk}>
              <span className="risk-code">{risk}</span>
              <h3>{action}</h3>
              <p>{rule}</p>
              <em>{decision}</em>
            </article>
          ))}
        </div>

        <div className="boundary-note">
          <strong>边界结论</strong>
          <p>Discuss / Plan 强制只读；Interactive 默认拦截后果性调用；Auto / Custom 可以提高自主程度，但本地写入仍受 writable root 约束，外部副作用仍依赖目标级规则、审批和审计。</p>
        </div>
      </section>

      <section className="section-shell infographic-footer-cta">
        <a className="button button-primary" href="/">返回中文站首页</a>
        <a className="text-link" href="https://github.com/zhanglunet/openworker-zh-localized" target="_blank" rel="noreferrer">查看本站源码</a>
      </section>
    </main>
  );
}
