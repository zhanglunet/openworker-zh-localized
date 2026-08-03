import assert from "node:assert/strict";
import test from "node:test";

async function render(path = "/") {
  const workerUrl = new URL("../dist/server/index.js", import.meta.url);
  workerUrl.searchParams.set("test", `${process.pid}-${Date.now()}`);
  const { default: worker } = await import(workerUrl.href);

  return worker.fetch(
    new Request(`http://localhost${path}`, { headers: { accept: "text/html" } }),
    { ASSETS: { fetch: async () => new Response("Not found", { status: 404 }) } },
    { waitUntil() {}, passThroughOnException() {} },
  );
}

test("server-renders the Chinese OpenWorker product page", async () => {
  const response = await render();
  assert.equal(response.status, 200);
  assert.match(response.headers.get("content-type") ?? "", /^text\/html\b/i);

  const html = await response.text();
  assert.match(html, /OpenWorker 中文站/);
  assert.match(html, /把结果交给 AI/);
  assert.match(html, /源码分析/);
  assert.match(html, /安全与隐私/);
  assert.doesNotMatch(html, /codex-preview|Your site is taking shape|react-loading-skeleton/i);
});

test("links both the upstream source and localized repository", async () => {
  const html = await (await render()).text();
  assert.match(html, /https:\/\/github\.com\/andrewyng\/openworker/);
  assert.match(html, /https:\/\/github\.com\/zhanglunet\/openworker-zh-localized/);
  assert.match(html, /项目源码来自/);
  assert.match(html, /中文本地化/);
});

test("server-renders the OpenWorker infographic page", async () => {
  const response = await render("/infographic");
  assert.equal(response.status, 200);

  const html = await response.text();
  assert.match(html, /OpenWorker.*运行架构地图/s);
  assert.match(html, /系统架构/);
  assert.match(html, /Agent 循环/);
  assert.match(html, /安全边界/);
  assert.match(html, /main@3766805/);
});
