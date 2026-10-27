# PRD-268/T1：Agent-Reach 式中文公开源能力层设计

- 日期：2026-10-28
- 来源：2026-10-27 趋势日报 openworker-zh-localized 第 2 条，用户当日拍板采纳
- trend issue：[zhanglunet/trend#1340](https://github.com/zhanglunet/trend/issues/1340)
- 中央 PRD：`trend/adopted/PRD-268-owzh-agent-reach-zh-sources.md`
- 状态：T1 设计稿，待评审；实现类任务（T2–T4）只开 PR 不合并

## 1. 目标与非目标

**目标**：中文公开源（Bilibili 公开视频页、小红书公开笔记页、通用中文 RSS）之上建**接入与健康层**：每源声明 ToS 与限流、配置主备、故障自动切换留审计、`doctor` 显示健康/限流/故障态。

**非目标**：
- 不做内容分析与产出——栏目归 PRD-184（build-in-public），图解指南归 PRD-211；本条只管"源可达吗、挂了怎么办"；
- **不绕登录墙**：只接无需登录即可访问的公开页面/公开接口；不模拟登录态、不携带任何个人 cookie；
- 不做爬虫规避（反反爬）：遵守 robots 与限流，429 退避，被明确拒绝的来源标记 `disallowed` 停用而非对抗。

## 2. 与既有能力的划界

| 既有能力 | 关系 |
|---|---|
| PRD-184 中文 build-in-public 栏目 | 184 是栏目（内容与叙事）；268 是其引用的公开源的接入健康层，184 不自建连接 |
| PRD-211 图解指南 | 211 是指南产出；无关 |
| PRD-259（brain27 同型） | 模式同源；本仓特色=中文平台源（B 站/小红书公开面）与中文平台 ToS 特殊性（对自动化访问普遍严格→更保守默认限流） |

## 3. 方案设计

### 3.1 中文公开源注册表（`zh-source-v1`）

```json
{
  "schema": "zh-source-v1",
  "source_id": "bili-public-example",
  "kind": "public-page|rss",
  "platform": "bilibili|xiaohongshu|generic-rss",
  "primary": { "url": "https://www.example.com/<公开页路径>", "tos_url": "<平台用户协议/robots 指针>", "rate_limit": { "requests_per_min": 2, "burst": 1, "note": "中文平台默认保守值" } },
  "standbys": [],
  "auth": "none",
  "data_class": "public",
  "robots_respected": true,
  "enabled": true
}
```

- `auth` 只允许 `none`；`data_class` 只允许 `public`；`tos_url` 与 `robots_respected: true` 必填；
- 中文平台默认限流保守值（2 req/min，burst 1）——**宁慢勿冲**；
- 平台字段 `platform` 封闭枚举，便于平台级限流策略（同平台多源共享预算）。

### 3.2 健康与主备切换（T3）

- 状态机沿用同型设计：healthy → degraded → failed；429 标 throttled；
- failed 自动切备源（若有）+ 审计事件 `zh_source_failover`；恢复探测切回留痕；
- **平台级限流预算**：同平台全部源共享 requests_per_min 预算（平台维度限流器），避免多源叠加冲击单平台；
- robots/ToS 变更检测：`disallowed` 状态（人工确认后停用），不对抗。

### 3.3 doctor（T2）

人读表格 + `--json`：source_id/platform/状态/限流用量/last_error/tos——中文界面文案（本仓中文优先），JSON 字段名保持英文（机读纪律）。

### 3.4 与 PRD-184/211 边界（T4）

- 184 栏目引用公开视频/笔记时向 268 要 `(source_handle, health_meta)`；184 不自建请求；
- 211 图解指南引用截图类素材的合规要求不变（素材来源仍是人工采集审核，268 不自动下载图片）；
- 边界一句话：**268 管"中文公开源活着吗"，184/211 管"拿它做什么"**。

## 4. 安全红线

1. 只接公开源：auth=none + data_class=public + robots_respected 必填；不绕登录墙、不带个人态、不做验证码对抗；
2. 平台级限流预算 + 保守默认值；429 退避；被拒来源 `disallowed` 停用不对抗；
3. 切换与停用全留审计；doctor/审计零密钥零内网主机名；
4. 拉取数据只含公开页面元数据，不落用户个人数据；
5. 示例源全占位（example.com / <公开页路径>）。

## 5. T2–T5 任务拆分（按 PRD）

| 任务 | 内容 | 验收标准（PRD 原文口径） |
|---|---|---|
| T2 | 来源注册与 doctor 最小实现 | 健康态可显示 |
| T3 | 主备切换与审计 | 切换有测试 |
| T4 | 与 PRD-184/211 边界文档 | 边界齐全 |
| T5 | 验收试运行：模拟故障切换 | 不绕登录墙；无密钥 |

## 6. T5 验收标准

1. 注入故障场景 doctor 四态正确（中文界面 + 英文 JSON 字段）；
2. failed 自动切备 + `zh_source_failover` 审计；恢复切回留痕；
3. 加载器拒绝 auth≠none / 缺 tos_url / robots_respected≠true 条目；
4. 平台级限流预算生效（同平台双源叠加不超预算的测试）；
5. 全程零密钥、无登录墙绕过（代码路径断言 + 扫描）。

## 7. 借鉴划界

- [Panniantong/Agent-Reach](https://github.com/Panniantong/Agent-Reach)：License API 实测 **MIT**。仅借鉴"公开源能力层+doctor+主备"形态，不复制代码与文案；中文平台源注册表、平台级限流预算、disallowed 停用语义为本仓原创。
- 与日报原文的差异修正：无。
