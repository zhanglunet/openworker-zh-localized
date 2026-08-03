# 正式签名、公证与自动更新材料暂缓申请记录

记录日期：2026-08-04

状态：暂缓申请。当前不注册 Apple Developer Program，不创建 Developer ID 证书，不创建 App Store Connect API Key，不写入 GitHub Actions Secrets，不发布新的正式签名包。

## 背景

OpenWorker 中文版已经具备正式发布流水线：

- GitHub Actions 可在 tag 发布时构建 macOS / Windows 安装包；
- macOS 发布链路已支持 Developer ID 签名、Apple 公证、staple 和 Gatekeeper 校验；
- Tauri updater 可生成 `.app.tar.gz` 更新包和 `.sig` 签名；
- Release workflow 会生成 `latest-zh.json`，并回写到 `main` 分支的 `releases/latest-zh.json`；
- 中文客户端更新源已经切到 `zhanglunet/openworker-zh-localized`，避免再次更新成官方英文版。

但正式签名、公证和安全自动升级仍依赖账号与私钥材料。这些材料不能提交到仓库，也不应通过聊天明文传递。

## 暂缓原因

目前用户决定暂时不申请 Apple Developer Program 和相关证书，后续需要公开稳定分发时再办理。

## 未来需要申请或准备的材料

### 1. Apple Developer Program

用途：获得创建 Developer ID 证书和使用 Apple 公证服务的资格。

办理入口：

- https://developer.apple.com/programs/

备注：

- 个人账号可以发布 Developer ID 应用；
- 若希望发布者显示公司或组织名称，需要组织账号，通常需要额外的组织身份材料。

### 2. Developer ID Application 证书

用途：签名 macOS `.app` 和 `.dmg`。

未来产物：

- `Developer ID Application` 证书；
- 从钥匙串导出的 `.p12` 文件；
- `.p12` 导出密码；
- 签名身份字符串，例如 `Developer ID Application: Name (TEAMID)`。

对应 GitHub Actions Secrets：

```text
APPLE_CERTIFICATE
APPLE_CERTIFICATE_PASSWORD
APPLE_SIGNING_IDENTITY
```

### 3. App Store Connect API Key

用途：让 GitHub Actions 调用 Apple notary service 完成公证。

未来产物：

- `AuthKey_XXXX.p8`；
- API Key ID；
- Issuer ID。

对应 GitHub Actions Secrets：

```text
APPLE_API_KEY_CONTENT
APPLE_API_KEY
APPLE_API_ISSUER
```

### 4. Tauri updater 私钥

用途：签名自动更新包，客户端用内置 pubkey 验证更新包。

对应 GitHub Actions Secrets：

```text
TAURI_SIGNING_PRIVATE_KEY
TAURI_SIGNING_PRIVATE_KEY_PASSWORD
```

当前 `OpenWorker 中文版 0.1.7` 内置 updater pubkey：

```text
dW50cnVzdGVkIGNvbW1lbnQ6IG1pbmlzaWduIHB1YmxpYyBrZXk6IDVCNzEzRjY5OTkzNUNBNjkKUldScHlqV1phVDl4VzBvTnFLLytzaDkzNVd3WWNuUm8yNE95WTBFNnBtcGF1RENxeTRuNVhQeloK
```

重要限制：

- 如果能找到与该 pubkey 匹配的私钥，当前 0.1.7 客户端可直接通过自动更新升级；
- 如果找不到匹配私钥，需要生成新的 updater key，并发布一个用户手动安装的桥接版本；
- 从桥接版本之后，才可以使用新的 updater key 继续自动升级。

## 未来继续办理时的执行清单

1. 用户在 Apple 侧完成 Developer Program、Developer ID 证书、App Store Connect API Key。
2. 用户把 `.p12`、`.p8`、Tauri updater 私钥放在本机安全目录，不提交仓库，不粘贴到聊天。
3. 使用 `gh secret set` 写入 `zhanglunet/openworker-zh-localized` 的 GitHub Actions Secrets。
4. 检查 `gh secret list --repo zhanglunet/openworker-zh-localized` 是否列出所需 Secret 名称。
5. 更新 `surfaces/gui/src-tauri/tauri.conf.json` 版本号。
6. 创建并推送 tag，例如：

```bash
git tag v0.1.8-zh
git push origin v0.1.8-zh
```

7. 等待 GitHub Actions Release workflow 完成。
8. 验证 GitHub Release、DMG 公证、`latest-zh.json`、客户端自动更新。

## 当前明确不做

- 不申请 Apple Developer Program；
- 不创建证书；
- 不生成或替换 Tauri updater key；
- 不写入任何 GitHub Secrets；
- 不发布新的 tag；
- 不替换当前 `v0.1.7-zh` 下载包。

## 相关文件

- [正式签名、公证与自动更新发布指南](release-signed-updates.md)
- [Release workflow](../.github/workflows/release.yml)
- [Tauri 配置](../surfaces/gui/src-tauri/tauri.conf.json)
- [中文更新 manifest](../releases/latest-zh.json)
