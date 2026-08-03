import { repoReport } from "./generated";

export default function UpdatesPage() {
  const weekly = repoReport.weeklyCommits.length > 0 ? repoReport.weeklyCommits : repoReport.recentCommits.slice(0, 6);

  return (
    <main className="updates-page">
      <header className="site-header">
        <a className="brand" href="/" aria-label="返回 OpenWorker 中文站首页">
          <span className="brand-mark" aria-hidden="true">O</span>
          <span>OpenWorker</span>
          <span className="brand-tag">日志</span>
        </a>
        <nav aria-label="日志导航">
          <a href="#changelog">更新日志</a>
          <a href="#weekly">周报</a>
          <a href="/source-analysis">源码分析</a>
          <a href="/">返回首页</a>
        </nav>
        <a className="nav-cta" href="https://github.com/zhanglunet/openworker-zh-localized" target="_blank" rel="noreferrer">
          GitHub <span aria-hidden="true">↗</span>
        </a>
      </header>

      <section className="updates-hero section-shell">
        <div>
          <p className="eyebrow"><span className="signal-dot" /> Release Journal</p>
          <h1>更新日志<br /><em>与每周周报</em></h1>
          <p>
            这里把仓库 Git 历史转成面向用户的更新流。每次构建会刷新当前日志；每周的自动任务会重新生成报告并在有变化时提交。
          </p>
        </div>
        <aside className="updates-summary">
          <div><strong>{repoReport.recentCommits.length}</strong><span>近期提交</span></div>
          <div><strong>{weekly.length}</strong><span>本周条目</span></div>
          <div><strong>{repoReport.shortHead}</strong><span>当前版本</span></div>
        </aside>
      </section>

      <section className="section-shell updates-section" id="changelog">
        <div className="deep-heading">
          <p className="eyebrow">01 · Changelog</p>
          <h2>最近更新</h2>
          <p>按 Git 提交时间倒序展示。原始 Markdown 同步保存在 <code>docs/updates/CHANGELOG.md</code>。</p>
        </div>
        <div className="timeline-list">
          {repoReport.recentCommits.map((commit) => (
            <article key={commit.hash}>
              <time>{commit.date}</time>
              <code>{commit.hash}</code>
              <h3>{commit.subject}</h3>
            </article>
          ))}
        </div>
      </section>

      <section className="dark-section updates-weekly" id="weekly">
        <div className="section-shell">
          <div className="deep-heading light-heading">
            <p className="eyebrow">02 · Weekly Report</p>
            <h2>本周周报</h2>
            <p>周报从最近 7 天提交生成，适合快速判断本周网站、下载包、文档和本地化工作的进展。</p>
          </div>
          <div className="weekly-grid">
            <article>
              <span>本周主线</span>
              <h3>中文站与下载链路持续完善</h3>
              <p>本周重点围绕中文版 App 下载、正式域名、README 展示、网站信息图和源码分析页面展开。</p>
            </article>
            <article>
              <span>维护提醒</span>
              <h3>发布前保持三项同步</h3>
              <p>DMG、README、网站下载入口需要一起更新；源码分析和日志页由构建脚本自动再生成。</p>
            </article>
          </div>
          <div className="weekly-commits">
            {weekly.map((commit) => (
              <div key={commit.hash}>
                <time>{commit.date}</time>
                <code>{commit.hash}</code>
                <p>{commit.subject}</p>
              </div>
            ))}
          </div>
        </div>
      </section>
    </main>
  );
}
