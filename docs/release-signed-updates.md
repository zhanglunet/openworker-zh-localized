# OpenWorker 中文版签名、公证与自动更新发布指南

本仓库的中文版 macOS App 使用 Tauri updater。一个可以安全自动升级的正式包必须同时满足三件事：

1. macOS `.app` 与 `.dmg` 使用 Apple Developer ID Application 证书签名。
2. `.dmg` 通过 Apple notary service 公证并 staple。
3. Tauri 更新产物 `.app.tar.gz` 使用与 `surfaces/gui/src-tauri/tauri.conf.json` 中 `plugins.updater.pubkey` 匹配的私钥签名，并生成 `latest-zh.json`。

缺少任意一项，都不应作为正式自动更新发布。

当前暂缓申请 Apple Developer 和签名材料；后续继续办理时，先看 [正式签名、公证与自动更新材料暂缓申请记录](release-signing-deferred-plan.md)。

## GitHub Actions Secrets

在 `zhanglunet/openworker-zh-localized` 仓库的 Settings → Secrets and variables → Actions 中配置：

| Secret | 用途 |
| --- | --- |
| `APPLE_CERTIFICATE` | Developer ID Application 证书和私钥导出的 `.p12`，base64 后的内容 |
| `APPLE_CERTIFICATE_PASSWORD` | `.p12` 导出密码 |
| `APPLE_SIGNING_IDENTITY` | 代码签名身份，例如 `Developer ID Application: Name (TEAMID)` |
| `APPLE_API_KEY_CONTENT` | App Store Connect API `.p8` 文件，base64 后的内容 |
| `APPLE_API_KEY` | App Store Connect API Key ID |
| `APPLE_API_ISSUER` | App Store Connect Issuer ID |
| `TAURI_SIGNING_PRIVATE_KEY` | Tauri updater 私钥，必须与 App 内置 pubkey 匹配 |
| `TAURI_SIGNING_PRIVATE_KEY_PASSWORD` | Tauri updater 私钥密码；如果私钥无密码可留空 |

当前已安装的 `OpenWorker 中文版 0.1.7` 内置的更新 pubkey 是：

```text
dW50cnVzdGVkIGNvbW1lbnQ6IG1pbmlzaWduIHB1YmxpYyBrZXk6IDVCNzEzRjY5OTkzNUNBNjkKUldScHlqV1phVDl4VzBvTnFLLytzaDkzNVd3WWNuUm8yNE95WTBFNnBtcGF1RENxeTRuNVhQeloK
```

如果找不到与它匹配的 `TAURI_SIGNING_PRIVATE_KEY`，则不能让 0.1.7 直接自动升级到下一版。更换 updater key 会导致旧客户端无法验证新更新包，只能通过重新下载安装包迁移一次。

## 本地准备 Secrets 的常用命令

```bash
# .p12 转 base64
base64 -i DeveloperIDApplication.p12 | pbcopy
gh secret set APPLE_CERTIFICATE --repo zhanglunet/openworker-zh-localized

gh secret set APPLE_CERTIFICATE_PASSWORD --repo zhanglunet/openworker-zh-localized
gh secret set APPLE_SIGNING_IDENTITY --repo zhanglunet/openworker-zh-localized

# App Store Connect AuthKey_XXXX.p8 转 base64
base64 -i AuthKey_XXXX.p8 | pbcopy
gh secret set APPLE_API_KEY_CONTENT --repo zhanglunet/openworker-zh-localized

gh secret set APPLE_API_KEY --repo zhanglunet/openworker-zh-localized
gh secret set APPLE_API_ISSUER --repo zhanglunet/openworker-zh-localized

gh secret set TAURI_SIGNING_PRIVATE_KEY --repo zhanglunet/openworker-zh-localized
gh secret set TAURI_SIGNING_PRIVATE_KEY_PASSWORD --repo zhanglunet/openworker-zh-localized
```

## 发布流程

1. 更新 `surfaces/gui/src-tauri/tauri.conf.json` 中的版本号，例如 `0.1.8`。
2. 提交并推送主分支。
3. 创建并推送 tag，推荐中文版 tag 使用 `v0.1.8-zh`：

```bash
git tag v0.1.8-zh
git push origin v0.1.8-zh
```

4. GitHub Actions 的 Release workflow 会：
   - 在 macOS arm64、macOS x64、Windows 构建安装包；
   - tag 发布时强制检查签名、公证和 updater Secrets；
   - 生成稳定命名的 `OpenWorker-CN-*` 下载资产；
   - 生成 `latest-zh.json`；
   - 发布 GitHub Release；
   - 将 `latest-zh.json` 回写到 `main` 分支的 `releases/latest-zh.json`，兼容已经安装的中文版客户端。

## 验证清单

正式发布完成后至少验证：

```bash
gh release view v0.1.8-zh --repo zhanglunet/openworker-zh-localized --json assets,url
curl -fsSL https://raw.githubusercontent.com/zhanglunet/openworker-zh-localized/main/releases/latest-zh.json
spctl -a -t open --context context:primary-signature OpenWorker-CN-macos-arm64.dmg
xcrun stapler validate OpenWorker-CN-macos-arm64.dmg
```

`latest-zh.json` 中对应平台必须包含 `signature` 和 `url`。如果 `platforms` 为空，说明这不是可自动升级的正式发布。
