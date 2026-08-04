const localizedDownloadUrl =
  "https://github.com/zhanglunet/openworker-zh-localized/raw/main/releases/OpenWorker-CN-0.1.7-aarch64.dmg";

const links = {
  openworker: "https://openworker.com",
  upstream: "https://github.com/andrewyng/openworker",
  localized: "https://github.com/zhanglunet/openworker-zh-localized",
  release: "https://github.com/zhanglunet/openworker-zh-localized/releases/tag/v0.1.7-zh",
  codex: "https://chatgpt.com/codex/",
};

const differences = [
  {
    name: "OpenWorker",
    focus: "个人桌面上的 AI coworker",
    fit: "日常办公、文件、连接器、MCP、本地模型、需要可控权限的个人工作流",
    note: "开源、本地优先、可带自己的模型 API，也可以接 Ollama。",
  },
  {
    name: "WorkBuddy 类办公 AI",
    focus: "企业办公协同与平台化服务",
    fit: "组织内部流程、企业账号体系、统一管理与协同入口",
    note: "通常更像产品化平台；OpenWorker 更适合自己掌控本地运行与工具链。",
  },
  {
    name: "Codex",
    focus: "软件工程和代码任务",
    fit: "写代码、修 bug、重构、跑测试、提 PR、代码审查",
    note: "Codex 是很强的开发者工具；OpenWorker 的目标更横向，面向日常任务交付。",
  },
];

export default function RecommendationPage() {
  return (
    <main className="recommend-page">
      <header className="site-header">
        <a className="brand" href="/" aria-label="返回 OpenWorker 中文站首页">
          <span className="brand-mark" aria-hidden="true">O</span>
          <span>OpenWorker</span>
          <span className="brand-tag">推荐</span>
        </a>
        <nav aria-label="文章导航">
          <a href="#why">为什么推荐</a>
          <a href="#compare">差别</a>
          <a href="#download">下载</a>
          <a href="/source-analysis">源码分析</a>
          <a href="/">首页</a>
        </nav>
        <a className="nav-cta" href={links.localized} target="_blank" rel="noreferrer">
          中文仓库 <span aria-hidden="true">↗</span>
        </a>
      </header>

      <article>
        <section className="recommend-hero section-shell">
          <div>
            <p className="eyebrow"><span className="signal-dot" /> 推荐阅读</p>
            <h1>OpenWorker：<br /><em>让 AI 从聊天走向交付。</em></h1>
            <p>
              如果你已经用过很多 AI 聊天工具，会发现一个微妙的瓶颈：它们很会回答，
              但真正把材料整理好、文件生成好、工具连接好、关键动作交给你确认，这中间还差一段路。
              OpenWorker 想补上的，正是这段路。
            </p>
            <div className="hero-actions">
              <a className="button button-primary" href={localizedDownloadUrl} target="_blank" rel="noreferrer">
                下载中文版 <span aria-hidden="true">→</span>
              </a>
              <a className="button button-secondary" href={links.upstream} target="_blank" rel="noreferrer">
                查看上游开源项目
              </a>
            </div>
          </div>
          <aside className="recommend-card" aria-label="文章摘要">
            <span>一句话推荐</span>
            <strong>OpenWorker 更像一个住在你电脑里的 AI coworker，而不是一个只会回复的聊天窗口。</strong>
            <p>它开源、本地优先、支持多模型和本地模型，并在重要操作前保留人工批准。</p>
          </aside>
        </section>

        <section className="article-section section-shell" id="why">
          <div className="article-kicker">01 · 为什么值得看</div>
          <div className="article-body">
            <p>
              OpenWorker 是由 Andrew Ng（吴恩达）账号发布的开源桌面 AI coworker 项目。
              官方介绍里，它强调的不是“再做一个聊天框”，而是让 AI 在你的电脑和日常工具里推进任务，
              最后交付一份文档、一条待确认的消息、一个整理好的日程或一个可直接使用的文件。
            </p>
            <p>
              我喜欢它的地方，是它把几个关键词放在了一起：开源、本地优先、可接多种模型、可连接工具、
              有权限审批。这个组合很重要。因为真正进入工作流的 AI，不只是要聪明，还要可控、可追踪，
              以及尽量不把所有东西都锁在某个单一平台里。
            </p>
            <blockquote>
              它最吸引我的，不是“AI 能不能回答问题”，而是“AI 能不能把一件工作推到完成”。
            </blockquote>
          </div>
        </section>

        <section className="article-section section-shell">
          <div className="article-kicker">02 · 中文版做了什么</div>
          <div className="article-body">
            <p>
              我整理的中文版把桌面端和主要 GUI 文案都做了中文本地化，并单独准备了中文介绍站、源码分析、
              架构信息图、更新日志和 macOS Apple Silicon 下载包。对于只是想先体验的人，可以直接下载安装；
              对想研究 Agent 架构的人，也可以从源码、流程和 MCP 接入方式开始看。
            </p>
            <p>
              当前中文版仍是 beta 体验版，公开 DMG 尚未做 Apple Developer 正式签名和公证；
              首次打开可能需要右键选择“打开”。如果你只是想尝鲜、研究、搭自己的工作流，它已经足够好玩。
            </p>
          </div>
        </section>

        <section className="article-section section-shell" id="compare">
          <div className="article-kicker">03 · 和 WorkBuddy、Codex 的差别</div>
          <div className="comparison-table" role="table" aria-label="OpenWorker、WorkBuddy 类产品和 Codex 的差别">
            <div className="comparison-row comparison-head" role="row">
              <span>工具</span>
              <span>核心定位</span>
              <span>更适合</span>
              <span>我的理解</span>
            </div>
            {differences.map((item) => (
              <div className="comparison-row" role="row" key={item.name}>
                <strong>{item.name}</strong>
                <span>{item.focus}</span>
                <span>{item.fit}</span>
                <span>{item.note}</span>
              </div>
            ))}
          </div>
          <div className="article-body article-body-narrow">
            <p>
              简单说：WorkBuddy 类产品更像组织里的办公 AI 平台；Codex 更像工程师的代码同事；
              OpenWorker 则更像个人电脑里的通用 AI coworker。它不一定替代谁，反而适合和它们并存：
              代码交给 Codex，企业流程交给企业平台，自己的桌面文件、个人工具和可控实验交给 OpenWorker。
            </p>
          </div>
        </section>

        <section className="article-section section-shell">
          <div className="article-kicker">04 · 适合谁下载</div>
          <div className="article-grid">
            <div>
              <h2>适合</h2>
              <ul>
                <li>想体验本地优先 AI Agent 的人；</li>
                <li>希望自己选择模型 API 或本地模型的人；</li>
                <li>想研究桌面 Agent、权限审批、MCP 和连接器的人；</li>
                <li>愿意接受 beta 阶段小粗糙、但喜欢折腾新工具的人。</li>
              </ul>
            </div>
            <div>
              <h2>暂不适合</h2>
              <ul>
                <li>要求企业级统一管控和正式 SLA 的团队；</li>
                <li>完全不想处理模型 API、权限和本地配置的人；</li>
                <li>必须使用已签名、公证正式安装包的保守环境。</li>
              </ul>
            </div>
          </div>
        </section>

        <section className="recommend-download section-shell" id="download">
          <div>
            <p className="eyebrow">下载与源码</p>
            <h2>推荐先从中文版开始。</h2>
            <p>
              先把 App 装起来，跑一个低风险任务，例如整理本地资料、生成一份摘要、
              或者连接一个你愿意授权的工具。理解它的权限边界后，再逐步扩大使用范围。
            </p>
          </div>
          <div className="recommend-actions">
            <a className="button button-light" href={localizedDownloadUrl} target="_blank" rel="noreferrer">
              下载 macOS 中文版
            </a>
            <a className="button button-outline-light" href={links.release} target="_blank" rel="noreferrer">
              GitHub Release
            </a>
            <a className="button button-outline-light" href={links.openworker} target="_blank" rel="noreferrer">
              OpenWorker 官网
            </a>
          </div>
        </section>

        <section className="article-section section-shell">
          <div className="article-kicker">资料来源</div>
          <div className="source-list">
            <a href={links.upstream} target="_blank" rel="noreferrer">andrewyng/openworker GitHub 仓库</a>
            <a href={links.openworker} target="_blank" rel="noreferrer">OpenWorker 官方网站</a>
            <a href={links.codex} target="_blank" rel="noreferrer">OpenAI Codex 介绍页</a>
            <a href={links.localized} target="_blank" rel="noreferrer">OpenWorker 中文本地化仓库</a>
          </div>
        </section>
      </article>
    </main>
  );
}
