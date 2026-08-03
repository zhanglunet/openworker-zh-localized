const providers = [
  "OpenAI",
  "Anthropic",
  "Gemini",
  "GLM",
  "DeepSeek",
  "Kimi",
  "Qwen",
  "MiniMax",
  "Mistral",
  "Ollama",
];

const connectors = [
  "Slack",
  "Gmail",
  "Outlook",
  "Google Calendar",
  "Notion",
  "GitHub",
  "HubSpot",
  "Jira",
  "Linear",
  "Google Drive",
  "Box",
  "MCP",
];

const outcomes = [
  {
    number: "01",
    title: "整理客户会前简报",
    text: "读取 CRM、邮件和日历，把分散信息整理成可直接使用的会前材料。",
    tools: "HubSpot · Email · Calendar",
  },
  {
    number: "02",
    title: "排查线上故障",
    text: "串联告警、代码提交和运行手册，生成事件时间线与建议动作。",
    tools: "Slack · GitHub · 本地文件",
  },
  {
    number: "03",
    title: "完成周期性报告",
    text: "按计划拉取数据、更新报告，并把需要确认的动作留在 Inbox。",
    tools: "Automations · Connectors · Inbox",
  },
];

const architecture = [
  {
    index: "1",
    label: "桌面入口",
    title: "React + Tauri 2",
    text: "桌面壳负责窗口、托盘和进程生命周期；React 工作台展示会话、审批、产物和连接状态。",
  },
  {
    index: "2",
    label: "本地服务",
    title: "FastAPI + WebSocket",
    text: "Python sidecar 暴露本地 API 和事件流；SessionManager 协调会话、Inbox、自动化、审计与持久化。",
  },
  {
    index: "3",
    label: "Agent 核心",
    title: "TurnEngine",
    text: "驱动模型与工具的多轮循环。低风险读取可以并发，写入和 Shell 保持严格顺序。",
  },
  {
    index: "4",
    label: "执行边界",
    title: "权限、工具与模型",
    text: "PermissionEngine 把风险、模式、目录范围和批准规则组合起来，再连接本地工具、MCP 与模型路由。",
  },
];

const faqs = [
  {
    q: "它和普通 AI 聊天工具有什么不同？",
    a: "普通聊天工具主要返回答案；OpenWorker 的目标是把任务推进到交付状态，例如生成文件、整理报告、发送经过批准的消息，或更新外部工具中的记录。",
  },
  {
    q: "数据是否完全不会离开电脑？",
    a: "不是绝对意义上的离线。会话、记忆、密钥和主要运行状态保存在本机，但你选择的模型服务和连接器会接收完成任务所需的数据。完全本地运行可选择 Ollama，并避免启用外部连接器。",
  },
  {
    q: "它会不会未经允许执行操作？",
    a: "默认交互模式会拦截有后果的操作并请求批准。只读、计划、交互、自定义和自动模式提供不同自主程度；本地文件写入仍受可写目录范围约束。",
  },
  {
    q: "现在适合直接用于生产工作吗？",
    a: "项目已具备完整产品形态和较丰富的测试资产，但官方仍标注为 Open Beta。建议先在低风险工作流中试用，并逐项检查连接器权限、审批模式和模型数据政策。",
  },
];

export default function Home() {
  return (
    <main>
      <header className="site-header">
        <a className="brand" href="#top" aria-label="OpenWorker 中文站首页">
          <span className="brand-mark" aria-hidden="true">O</span>
          <span>OpenWorker</span>
          <span className="brand-tag">中文站</span>
        </a>
        <nav aria-label="主导航">
          <a href="#capabilities">能力</a>
          <a href="#workflow">工作方式</a>
          <a href="#architecture">源码分析</a>
          <a href="#safety">安全边界</a>
        </nav>
        <a className="nav-cta" href="https://github.com/andrewyng/openworker" target="_blank" rel="noreferrer">
          查看源码 <span aria-hidden="true">↗</span>
        </a>
      </header>

      <section className="hero section-shell" id="top">
        <div className="hero-copy">
          <p className="eyebrow"><span className="signal-dot" /> 开源 · 本地优先 · Open Beta</p>
          <h1>把结果交给 AI，<br /><em>不只得到回答。</em></h1>
          <p className="hero-lede">
            OpenWorker 是运行在桌面的开源 AI coworker。它能读取文件、连接日常工具、分解任务、请求批准，并把工作推进成真正可用的交付物。
          </p>
          <div className="hero-actions">
            <a className="button button-primary" href="https://download.openworker.com" target="_blank" rel="noreferrer">
              下载 macOS 版 <span aria-hidden="true">→</span>
            </a>
            <a className="button button-secondary" href="#architecture">先看源码分析</a>
          </div>
          <div className="trust-row" aria-label="产品特点">
            <span>MIT 开源</span>
            <span>自带模型密钥</span>
            <span>支持 Ollama</span>
          </div>
        </div>

        <div className="product-stage" aria-label="OpenWorker 工作界面示意">
          <div className="ambient ambient-one" />
          <div className="ambient ambient-two" />
          <div className="app-window">
            <div className="window-bar">
              <div className="traffic"><i /><i /><i /></div>
              <span>客户续约准备</span>
              <span className="window-status">本机运行</span>
            </div>
            <div className="app-body">
              <aside className="app-sidebar">
                <div className="mini-brand">OW</div>
                <div className="sidebar-icon active">✦</div>
                <div className="sidebar-icon">⌁</div>
                <div className="sidebar-icon">✓</div>
                <div className="sidebar-icon bottom">⚙</div>
              </aside>
              <div className="conversation">
                <div className="message user-message">帮我准备明天和 Northwind 的续约会议。</div>
                <div className="progress-line"><span className="spinner" /> 正在读取已授权的信息源</div>
                <div className="task-list">
                  <div><span className="task-check">✓</span> 查看 CRM 历史记录</div>
                  <div><span className="task-check">✓</span> 汇总最近邮件与会议纪要</div>
                  <div><span className="task-live" /> 生成会前简报</div>
                </div>
                <div className="message assistant-message">
                  <span className="assistant-label">交付完成</span>
                  <strong>续约势头良好，建议从使用增长切入。</strong>
                  <p>Q2 使用量翻倍，两个支持问题均已关闭。分析功能扩展是最明确的续约机会。</p>
                  <div className="artifact"><span>▤</span><div><b>Northwind 续约简报</b><small>northwind-renewal-brief.html</small></div><span>打开 ↗</span></div>
                </div>
                <div className="approval">
                  <div><span>即将离开本机</span><strong>把跟进邮件发送给客户？</strong></div>
                  <div className="approval-actions"><button>暂不</button><button>批准</button></div>
                </div>
              </div>
            </div>
          </div>
          <div className="floating-note note-model"><span>模型</span><b>任选提供商</b></div>
          <div className="floating-note note-local"><span>状态</span><b>保存在本机</b></div>
        </div>
      </section>

      <section className="ticker" aria-label="支持的模型和工具">
        <div className="ticker-track">
          {[...providers, ...providers].map((item, index) => <span key={`${item}-${index}`}>{item}</span>)}
        </div>
      </section>

      <section className="section-shell section-block" id="capabilities">
        <div className="section-heading split-heading">
          <div>
            <p className="eyebrow">从问题到成品</p>
            <h2>让 AI 接手流程，<br />而不是只写一段回复。</h2>
          </div>
          <p>它会在你授权的文件与工具间工作，保存完整过程，并在发送消息、修改日历或运行命令前停下来请你确认。</p>
        </div>
        <div className="outcome-grid">
          {outcomes.map((item) => (
            <article className="outcome-card" key={item.number}>
              <span className="card-number">{item.number}</span>
              <div className="card-orbit" aria-hidden="true"><i /><i /><i /></div>
              <h3>{item.title}</h3>
              <p>{item.text}</p>
              <div className="tool-line">{item.tools}</div>
            </article>
          ))}
        </div>
      </section>

      <section className="dark-section" id="workflow">
        <div className="section-shell">
          <div className="section-heading dark-heading">
            <p className="eyebrow">工作方式</p>
            <h2>你说目标，它完成中间步骤。</h2>
            <p>每次任务都是一个可观察、可中断、可批准的执行循环。</p>
          </div>
          <div className="workflow-line">
            <div className="workflow-node">
              <span>01</span><b>提出结果</b><p>简报、报告、回复、更新或调查</p>
            </div>
            <div className="workflow-arrow" aria-hidden="true">→</div>
            <div className="workflow-node active-node">
              <span>02</span><b>本机执行</b><p>模型推理、工具调用、权限检查</p>
            </div>
            <div className="workflow-arrow" aria-hidden="true">→</div>
            <div className="workflow-node">
              <span>03</span><b>返回成品</b><p>聊天回复、文件或外部系统变更</p>
            </div>
          </div>
          <div className="connector-wall">
            <div className="connector-intro"><span>连接你实际使用的工具</span><b>官方目录 + 通用 MCP</b></div>
            <div className="connector-list">
              {connectors.map((item) => <span key={item}>{item}</span>)}
            </div>
          </div>
        </div>
      </section>

      <section className="section-shell section-block analysis-section" id="architecture">
        <div className="analysis-title">
          <div>
            <p className="eyebrow">源码分析 · 2026-08-03</p>
            <h2>真正的核心，<br />藏在桌面界面之下。</h2>
          </div>
          <div className="analysis-verdict">
            <span>总体判断</span>
            <p>这不是“套壳聊天应用”，而是一套本地 Agent 运行平台。产品壁垒主要来自工具循环、权限系统、连接器和持久化，而不是单一模型。</p>
          </div>
        </div>

        <div className="architecture-map">
          {architecture.map((item, index) => (
            <div className="architecture-row" key={item.index}>
              <div className="architecture-index">{item.index}</div>
              <div className="architecture-meta"><span>{item.label}</span><b>{item.title}</b></div>
              <p>{item.text}</p>
              {index < architecture.length - 1 && <span className="architecture-connector" aria-hidden="true" />}
            </div>
          ))}
        </div>

        <div className="repo-metrics" aria-label="仓库分析快照">
          <div><strong>221</strong><span>Python 文件</span></div>
          <div><strong>165</strong><span>TypeScript / TSX 文件</span></div>
          <div><strong>40</strong><span>连接器描述项</span></div>
          <div><strong>1,044</strong><span>后端测试函数</span></div>
          <div><strong>65</strong><span>GUI E2E spec</span></div>
        </div>

        <div className="analysis-grid">
          <article className="analysis-card strength-card">
            <span className="analysis-kicker">值得关注的设计</span>
            <h3>并发读取，串行写入</h3>
            <p>TurnEngine 会先逐个授权工具调用，再并发执行明确标记为低风险的读取；写入、Shell 和未标注工具保持顺序，降低竞态与意外副作用。</p>
          </article>
          <article className="analysis-card">
            <span className="analysis-kicker">工程热点</span>
            <h3>中心模块正在变重</h3>
            <p><code>server/manager.py</code> 已超过 4,000 行，连接器执行层接近 5,000 行。功能闭环很完整，但后续维护会需要继续拆分边界。</p>
          </article>
          <article className="analysis-card">
            <span className="analysis-kicker">成熟度判断</span>
            <h3>产品完整，仍在快速演进</h3>
            <p>仓库包含大量后端与端到端测试，安装、更新和跨平台打包链路齐全；但官方仍明确标注 Open Beta，应以受控权限逐步导入真实工作。</p>
          </article>
        </div>
        <p className="snapshot-note">统计来自 <a href="https://github.com/andrewyng/openworker/commit/01b6f83b3927e02912dda84bb392942c13ca70d1" target="_blank" rel="noreferrer">main@01b6f83</a>；测试数字代表代码资产数量，不代表本站运行了原项目测试。</p>
      </section>

      <section className="safety-section" id="safety">
        <div className="section-shell safety-grid">
          <div className="safety-copy">
            <p className="eyebrow">安全与隐私</p>
            <h2>“本地优先”是一条边界，<br />不是一句绝对承诺。</h2>
            <p>主要状态、会话、记忆和密钥留在设备上；当你选择云端模型或外部连接器时，完成任务所需的数据仍会发送到相应服务。</p>
            <a href="https://github.com/andrewyng/openworker/blob/main/coworker/permissions.py" target="_blank" rel="noreferrer">查看权限实现 <span aria-hidden="true">↗</span></a>
          </div>
          <div className="risk-stack">
            <div className="risk-row"><span className="risk-dot read" /><div><b>READ</b><p>读取与搜索，默认低风险运行</p></div><em>直接执行</em></div>
            <div className="risk-row"><span className="risk-dot write" /><div><b>WRITE_LOCAL</b><p>本地文件写入，受可写目录约束</p></div><em>按模式批准</em></div>
            <div className="risk-row"><span className="risk-dot exec" /><div><b>EXEC</b><p>运行命令，复杂 Shell 不能自动命中白名单</p></div><em>重点确认</em></div>
            <div className="risk-row"><span className="risk-dot external" /><div><b>EXTERNAL</b><p>发送消息或修改外部系统</p></div><em>目标级授权</em></div>
          </div>
        </div>
      </section>

      <section className="section-shell section-block source-section" id="source">
        <div className="source-copy">
          <p className="eyebrow">从源码运行</p>
          <h2>想研究 Agent 架构？<br />它也是一份可运行的参考实现。</h2>
          <p>后端基于 Python 3.10+，前端需要 Node 20+；完整桌面壳还需要 Rust 工具链。</p>
          <div className="source-actions">
            <a className="button button-primary" href="https://github.com/andrewyng/openworker" target="_blank" rel="noreferrer">打开 GitHub <span aria-hidden="true">↗</span></a>
            <a className="text-link" href="https://github.com/andrewyng/openworker/issues" target="_blank" rel="noreferrer">查看 Issues</a>
          </div>
        </div>
        <div className="code-panel" aria-label="从源码启动命令">
          <div className="code-bar"><span>快速启动</span><span>bash</span></div>
          <pre><code><span className="code-muted"># 克隆与初始化</span>{"\n"}git clone https://github.com/andrewyng/openworker{"\n"}cd openworker{"\n"}bash packaging/setup_dev_env.sh{"\n\n"}<span className="code-muted"># 启动本地 Agent Server</span>{"\n"}.venv/bin/openworker-server --cwd ~/project --port 8765{"\n\n"}<span className="code-muted"># 另一个终端启动界面</span>{"\n"}cd surfaces/gui && npm install && npm run dev</code></pre>
        </div>
      </section>

      <section className="faq-section section-shell">
        <div className="section-heading faq-heading">
          <p className="eyebrow">常见问题</p>
          <h2>先把边界讲清楚。</h2>
        </div>
        <div className="faq-list">
          {faqs.map((item, index) => (
            <details key={item.q} open={index === 0}>
              <summary><span>{item.q}</span><i aria-hidden="true">＋</i></summary>
              <p>{item.a}</p>
            </details>
          ))}
        </div>
      </section>

      <section className="final-cta">
        <div className="section-shell final-cta-inner">
          <p className="eyebrow">准备好交付第一件工作了吗？</p>
          <h2>让 AI 从“会回答”<br />走到“能完成”。</h2>
          <div className="hero-actions centered-actions">
            <a className="button button-light" href="https://download.openworker.com" target="_blank" rel="noreferrer">下载 OpenWorker <span aria-hidden="true">→</span></a>
            <a className="button button-outline-light" href="https://github.com/andrewyng/openworker" target="_blank" rel="noreferrer">查看源代码</a>
          </div>
        </div>
      </section>

      <footer className="site-footer section-shell">
        <div className="brand footer-brand"><span className="brand-mark">O</span><span>OpenWorker</span><span className="brand-tag">中文站</span></div>
        <p>非官方中文介绍站 · 内容基于公开代码与文档整理</p>
        <div><a href="https://openworker.com" target="_blank" rel="noreferrer">官方网站</a><a href="https://github.com/andrewyng/openworker" target="_blank" rel="noreferrer">GitHub</a></div>
      </footer>
    </main>
  );
}
