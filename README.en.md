# OpenWorker — Fully Localized Chinese Edition (Chinese GUI + macOS Desktop Client)

<p align="center"><a href="./README.md">中文</a> | <a href="./README.en.md">English</a></p>

<p align="center"><strong>An English AI desktop assistant, opened the Chinese way.</strong></p>

<p align="center"><sub>8 UI module groups fully localized · 2 layers (web GUI + desktop shell) · 3 ways to run · 1 DMG, ready to use</sub></p>

## What this is

This repository is a full Chinese localization of [OpenWorker](https://github.com/andrewyng/openworker), the open-source AI desktop assistant. It keeps feature parity with upstream — only the interface language changes: the web GUI and the macOS desktop shell are translated into Chinese, end to end. It builds on [Lenovo202409/openworker-zh](https://github.com/Lenovo202409/openworker-zh) and follows the upstream MIT license, for learning and personal local use.

## How it differs

| Item | Upstream | Lenovo202409/openworker-zh | This repo |
|------|----------|------------------------------|-----------|
| Language | English | Frontend localized | Frontend + desktop shell localized |
| Custom API | No | Yes | Yes |
| StepFun | No | Yes | Yes |
| Source-run guide | Brief | None | Detailed |
| Environment setup guide | None | None | Detailed |
| Launcher scripts | None | None | Yes |

## Three ways to run

1. **Browser GUI** — the quickest way to try it.
2. **Tauri desktop client (dev mode)** — a real desktop app with system tray, shortcuts, and voice input.
3. **macOS DMG** — a ready-made Apple Silicon build for direct download.

## Download

- Chinese site: [https://oaosf.cn](https://oaosf.cn)
- macOS Apple Silicon DMG: [OpenWorker-CN-0.1.7-aarch64.dmg](https://github.com/zhanglunet/openworker-zh-localized/raw/main/releases/OpenWorker-CN-0.1.7-aarch64.dmg)
- GitHub Release: [v0.1.7-zh](https://github.com/zhanglunet/openworker-zh-localized/releases/tag/v0.1.7-zh)

> The current public DMG is an unsigned local build, intended for personal trial use. The signed, notarized release flow with Tauri auto-update is documented in the Chinese README.

## What is localized

- **Web GUI** — every user-visible string across 8 module groups: onboarding, settings, sidebar, chat, approvals & inbox, automations, connectors, and provider configuration.
- **Desktop shell** — Tauri menus (open / settings / quit), voice-input error prompts, update prompts, and macOS permission dialogs (microphone, desktop, documents, downloads, photo library).

> The complete guide — environment setup, running from source, FAQ, and repository tour — is maintained in the [Chinese README](./README.md).

## License

MIT (same as upstream OpenWorker).
