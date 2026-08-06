// 表格助手入口（大表哥 L2）：这张卡只有在 excel-ai-analyst 技能对本会话可用时才出现。
// 没装技能的用户看到的仍是原来的三张卡 —— 不允许出现点了没反应的死入口。
import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { SessionIntro } from "./SessionIntro";

type Row = { name: string; description: string; scope: string; enabled: boolean };

function stubFetch(opts: { skills: Row[]; roots: { path: string; primary?: boolean }[] }) {
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: string) => {
      const json = async () => {
        // 会话级技能菜单先于全局 /v1/skills 匹配：URL 里两者都含 "/skills"。
        if (url.includes("/skills")) return { skills: opts.skills };
        if (url.includes("/roots")) return { roots: opts.roots };
        if (url.includes("/connections")) return { connected: [] };
        if (url.includes("/connectors")) return [];
        return {};
      };
      return { ok: true, json } as unknown as Response;
    }),
  );
}

const props = (onPrefill = vi.fn()) => ({
  sessionId: "s1",
  onOpenSessionSettings: vi.fn(),
  onPrefill,
});

const SHEET_SKILL: Row = {
  name: "excel-ai-analyst",
  description: "把含公式的业务 Excel 当作没有文档的遗留代码来逆向工程",
  scope: "global",
  enabled: true,
};

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe("SessionIntro — 表格助手入口", () => {
  it("技能没装时不渲染这张卡（保持原有三张卡）", async () => {
    stubFetch({ skills: [], roots: [{ path: "/w", primary: true }] });
    render(<SessionIntro {...props()} />);
    // 等原有的卡片渲染完，确保不是「还没加载」造成的假阴性
    await screen.findByTestId("intro-task-folder");
    await waitFor(() => expect(screen.queryByTestId("intro-task-sheets")).toBeNull());
  });

  it("技能被本会话静音时也不渲染", async () => {
    stubFetch({
      skills: [{ ...SHEET_SKILL, enabled: false }],
      roots: [{ path: "/w", primary: true }],
    });
    render(<SessionIntro {...props()} />);
    await screen.findByTestId("intro-task-folder");
    await waitFor(() => expect(screen.queryByTestId("intro-task-sheets")).toBeNull());
  });

  it("技能可用但没有共享目录时，卡片是 gated 且引导去选文件夹", async () => {
    const onPrefill = vi.fn();
    stubFetch({ skills: [SHEET_SKILL], roots: [{ path: "/w", primary: true }] });
    render(<SessionIntro {...props(onPrefill)} />);
    const card = await screen.findByTestId("intro-task-sheets");
    expect(card.className).toContain("gated");
    expect(card.textContent).toContain("选择文件夹");
    fireEvent.click(card);
    // 没目录就不该直接开跑，而是先让用户把表格所在目录共享进来
    expect(onPrefill).not.toHaveBeenCalled();
  });

  it("技能可用且有共享目录时，点击预填五步法提示词", async () => {
    const onPrefill = vi.fn();
    stubFetch({
      skills: [SHEET_SKILL],
      roots: [
        { path: "/w", primary: true },
        { path: "/data/报表", primary: false },
      ],
    });
    render(<SessionIntro {...props(onPrefill)} />);
    const card = await screen.findByTestId("intro-task-sheets");
    await waitFor(() => expect(card.className).not.toContain("gated"));
    fireEvent.click(card);
    expect(onPrefill).toHaveBeenCalledTimes(1);
    const text = onPrefill.mock.calls[0][0] as string;
    // 提示词必须点名技能，模型才好从技能目录里认出该 load_skill 哪一个
    expect(text).toContain("excel-ai-analyst");
    expect(text).toContain("五步法");
    // 斜杠前缀是 Composer 的内部状态约定，预填里不能出现，否则会被原样发出去
    expect(text.startsWith("/")).toBe(false);
  });
});
