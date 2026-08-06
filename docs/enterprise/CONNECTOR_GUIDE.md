# 内部系统接入指南（Connector）

> 对应 PRD 的 F11「企业 CLI / 内部系统接入」与 DEV_PLAN M3。
> 配套模板：`templates/mcp/corp-api/`（路线 A）、`templates/connectors/corp/`（路线 B）。
> 配套测试：`tests/test_corp_api_server.py`（59 项）、`tests/test_corp_connector_template.py`（25 项）。

企业接的第一个内部系统，十有八九是一套 HTTP/REST 接口：ERP、工单、HR、审批流。
接它有两条路。**先花两分钟选对路，比写代码重要得多**——选错了要么白做一个内网 OAuth 端点，
要么给自己留一个每次同步上游都要手动解的冲突。

---

## 0. 先做选择题

| 你的情况 | 走哪条 |
|---|---|
| 只想让 Agent 能查内部数据，凭据由 IT 统一下发 | **A**（stdio 桥） |
| 内网没有、也不打算做 OAuth 端点 | **A** |
| 想两周内上线第一个内部系统 | **A** |
| 要在「连接器」页面上有一张卡片，员工各自授权、各自看到自己的身份 | **B** |
| 读工具不能弹框、写工具必须每次弹框（同一个系统里混着） | **B** |
| 内网已经有 OAuth 2.1 + DCR 的网关 | **B** |

拿不准就选 A。A 随时能升级成 B（描述符是叠加的，spec 不用改）；反过来把 B 退回 A 要拆挂载点。

两条路的硬差别只有三条：

| | A：stdio 桥 | B：原生描述符 + 内网 HTTP MCP |
|---|---|---|
| GUI 连接器卡片 | 没有（在 MCP 页面里） | 有，含设置向导与凭据校验 |
| 审批粒度 | **server 级**（`coworker/mcp/config.py` 的 `requires_approval`） | **工具级**（`prepare_mcp_tools` 按 read/write 逐个设） |
| 要动上游文件 | **0 个** | 1 个挂载点，5 行 |
| 内网前置条件 | 无 | 一个支持 OAuth 2.1 + DCR 的 HTTP MCP 端点 |
| 凭据存放 | `<state-dir>/.env`（预置脚本已覆盖） | OAuth 令牌，存 SecretStore |

> 审批粒度那一格是选 B 的**唯一**硬理由。A 不是不能做到"读不弹、写弹"——把读工具和写工具
> 拆成两个 MCP server 条目就行，下面第 1.3 节讲怎么拆。真正的差别是 A 的粒度上限是"一组"，
> B 是"一个"。

---

## 1. 路线 A：corp-api stdio 桥

用一份 `api.json` 声明「哪些接口、各自什么参数、返回哪些字段」，桥自己生成 MCP 工具。
换一个内网系统只改 JSON，不写 Python。

### 1.1 五步接入

**第 1 步：拷模板**（建仓脚本已自动放到 `enterprise/mcp/corp-api/`）

```bash
cp -r docs/enterprise/templates/mcp/corp-api /opt/corp/openworker/
```

**第 2 步：照着 `erp-read.example.json` 写你们的 spec**

字段参考见 1.4。写完先校验，**不要直接上线**：

```bash
python3 /opt/corp/openworker/corp-api/server.py \
    --spec /opt/corp/openworker/corp-api/erp-read.json --check
```

`--check` 会列出每个工具是读还是写、必填参数、有没有字段白名单，并在发现写工具时
提醒你把它挂到需审批的 server 上。spec 有问题会直接退出码 2，不会带着半个配置跑起来。

**第 3 步：放凭据**

凭据只从环境变量取，写进 spec 会被拒绝加载（这份 spec 会进版本库）。
写到 `<state-dir>/.env`——企业预置（`coworker/provisioning.py`）已经会在首启时铺这个文件：

```
CORP_API_TOKEN=……
```

**第 4 步：注册进 `<state-dir>/mcp.json`**

```json
{
  "mcpServers": {
    "corp-erp": {
      "command": "python3",
      "args": ["/opt/corp/openworker/corp-api/server.py",
               "--spec", "/opt/corp/openworker/corp-api/erp-read.json",
               "--name", "corp-erp"],
      "env": {"CORP_API_TOKEN": "${CORP_API_TOKEN}"},
      "requires_approval": false
    },
    "corp-erp-write": {
      "command": "python3",
      "args": ["/opt/corp/openworker/corp-api/server.py",
               "--spec", "/opt/corp/openworker/corp-api/erp-write.json",
               "--name", "corp-erp-write"],
      "env": {"CORP_API_TOKEN": "${CORP_API_TOKEN}"},
      "requires_approval": true
    }
  }
}
```

`${CORP_API_TOKEN}` 在加载时由 SecretStore 从「进程环境 + `<state-dir>/.env`」解析
（`coworker/secrets.py`）。MCP SDK 会把它并进子进程环境，`PATH` 之类不会丢。

**第 5 步：开一个新会话验证**

工具名会是 `mcp__corp-erp__corp_order_get`。查一条订单，确认不弹框；关一张测试订单，
确认弹框。

### 1.2 这个桥替你守住的边界

每一条都有测试钉着，且都做过变异测试（把守卫删掉，对应用例必须变红）：

| 守卫 | 拦的是什么 |
|---|---|
| 路径参数逐段百分号转义 | `{order_no}` 传 `../../admin/users` → 打不到别的接口 |
| 拼完的 URL 归一化后必须仍在 `base_url` 之下 | 纵深防御。**注意是归一化后比**——纯字符串前缀比对在这里是假守卫，`https://host/api/v2` + `/../../admin` 前缀完全匹配却解析成 `/admin`（第一版就是这么写的，被测试打红了） |
| 不跟随重定向 | 内网系统一个 302 就能把 `Authorization` 头送到别的 host |
| 响应按 `fields` 白名单裁剪 | 内网记录里的身份证号、薪资、手机号不整包进模型上下文 |
| 非 GET/HEAD 必须显式 `"write": true` | 哪些工具会改数据，是配置里看得见的事实，不是读代码猜的 |
| spec 里出现 `Authorization`/`Cookie` → 拒绝加载 | 这份 spec 会进版本库 |
| 缺凭据环境变量 → 启动即失败 | 好过每次调用回 401，让模型以为是"这条记录没权限" |
| 不允许 `verify: false` | 自签证书配 `ca_bundle`，别关校验 |
| 未声明的参数拒绝，不是忽略 | 静默忽略会让调用方以为参数生效了 |
| 超时 / 输出截断 / 输出脱敏 | 一次 CLI 输出不该撑爆模型上下文 |

### 1.3 读写为什么必须拆成两个 server

`requires_approval` 是 **server 级**的，不是工具级（`coworker/mcp/config.py:38`）。
混在一个 server 里只有两种结局：

- 打开审批 → 查个订单也弹框 → 用户弹到开始无脑点「同意」 → 关单那次也被无脑同意了
- 关掉审批 → 连关单、改单一起放行

拆开之后，读的那半永不打扰，写的那半永远拦一道。这也是为什么模板给了
`erp-read.example.json` 和 `erp-write.example.json` 两份，而不是一份——
测试里有两条断言专门盯着这个拆分不被合回去。

> 只有当 server 名对应一个带 `mcp_url` 的描述符时（路线 B），审批才会降到工具级：
> `coworker/server/manager.py` 的 `prepare_mcp_tools` 会按 `tool_defs` 的 read/write
> 分类逐个设 `requires_approval`，未分类的一律按需审批——失败关闭。

### 1.4 spec 字段参考

顶层：

| 字段 | 必填 | 说明 |
|---|---|---|
| `base_url` | ✅ | `http(s)://` 绝对地址。所有工具的 URL 都必须落在它之下 |
| `auth` | | `{"type": "bearer"\|"header"\|"basic"\|"none", "token_env": …}`。凭据只从环境变量取 |
| `defaults.timeout` | | 秒，默认 30 |
| `defaults.max_output` | | 字符，默认 20000 |
| `defaults.ca_bundle` | | 企业内网根证书路径。文件不存在 → 加载失败 |
| `defaults.headers` | | 非凭据类的固定头。写 `Authorization`/`Cookie` 会被拒绝 |
| `defaults.redact` | | 正则数组，命中的部分在输出里替换为 `«已脱敏»` |
| `tools` | ✅ | 非空数组 |

每个工具：

| 字段 | 必填 | 说明 |
|---|---|---|
| `name` | ✅ | `[A-Za-z0-9_-]{1,64}` |
| `description` | ✅ | 模型靠它决定要不要调用，写清楚"什么时候用" |
| `method` | | 默认 `GET` |
| `path` | ✅ | 以 `/` 开头，`{param}` 占位符必须与声明的路径参数**完全一致**（打错一个字会在加载时报错，而不是运行时 404） |
| `params[].in` | | `path` / `query` / `body`，默认 `query`。路径参数必须 `required` |
| `params[].type` | | `string` / `integer` / `number` / `boolean` |
| `params[].enum` | | 非空数组，逐值校验 |
| `write` | | 非 GET/HEAD 时必填 `true` |
| `fields` | | 响应字段白名单，支持 `customer.name` 点号路径，列表逐元素套用 |

### 1.5 `fields` 白名单怎么写

假设接口返回：

```json
{"total": 2, "results": [{"order_no": "SO1", "status": "open", "cost": 1}]}
```

写 `["total", "results.order_no", "results.status"]`，模型只会看到

```json
{"total": 2, "results": [{"order_no": "SO1", "status": "open"}]}
```

不写 `fields` 就是不裁剪。**模板里每个示例工具都写了 fields，这是有意的示范**——
内网响应默认不该整包回流，测试里有一条断言专门盯着模板不许退化。

### 1.6 常见坑

- **接口返回 302** → 桥不跟随，会告诉你重定向目标的 host。多半是 SSO 登录页，说明令牌过期了；
  如果那是正常行为，把 `base_url` 直接指向最终地址。
- **加载时报"占位符与声明的路径参数不一致"** → `path` 里写了 `{orderno}`、参数声明成 `order_no`，
  或者反过来声明了路径参数但模板里没用上。
- **模型反复调同一个工具** → `description` 太含糊。写清楚"什么时候用它、返回什么"，比调模型有用。
- **输出被截断** → 调大该工具的 `max_output`，或者收紧 `fields`。优先收紧 `fields`。

---

## 2. 路线 B：原生描述符 + 内网 HTTP MCP 端点

模板：`templates/connectors/corp/__init__.py`。

### 2.1 前置条件（先确认，再开工）

- 内网有一个 **HTTP MCP 端点**，支持 **OAuth 2.1 + 动态客户端注册（DCR）**。
  `coworker/mcp/oauth.py` 走的就是这套；令牌落在本机 SecretStore，不经过任何中间人。
- 没有这个就别选 B。把 `MCP_URL` 留空只会得到"有卡片、没工具"，还不如 A。

### 2.2 改哪里

模板顶部的 `CONFIG` 和 `CORP_TOOLS` 两块，其余不用动。

`CORP_TOOLS` **就是审批策略本身**：

```python
CORP_TOOLS = (
    ("order_get",    "查订单",   "read",  "按订单号查询订单详情。"),
    ("order_close",  "关闭订单", "write", "关闭一张订单，需要给出原因。不可逆。"),
)
```

- 少写一个工具，它就永远进不来（`include_tools` 由这张表生成）
- 把写的标成读 = 关单操作变成静默执行，没人会收到弹框、也没人会发现

第二条没有任何运行时机制能替你兜住——所以模板的测试里有一条
`test_mutating_tool_names_must_be_declared_write`：工具名里带 `create/update/delete/close/…`
之类动词的，`kind` 必须是 `write`。真有例外（比如 `set_filter` 其实只影响查询）就在那张
动词表里显式豁免并写清理由。**这张表要和内网接口的 owner 一起过一遍，不要一个人拍板。**

### 2.3 挂载点（唯一要动的上游文件，5 行）

在 `coworker/connectors/descriptors.py` 末尾、experimental 那一段旁边加：

```python
try:
    from .corp import register as _register_corp
except ImportError:
    pass
else:
    _register_corp()
```

选这个位置的理由：上游极少动它，而且旁边就有一段形状一模一样的 experimental 加载代码，
冲突时一眼能看懂该留什么。同步纪律见 [UPSTREAM_SYNC.md](UPSTREAM_SYNC.md) 的「挂载点」一节，
`templates/test_enterprise_customization.py` 的挂载点形状断言会在每次同步 PR 上验证它还在。

`register()` 是幂等的——挂载点被 import 两次不会出现两张卡片。
（上游踩过这个坑：一个新描述符和没删干净的占位符同名共存，连接器页面出现两张卡片、
工具名互相顶掉。`tests/test_connectors.py::test_registry_has_no_duplicate_names` 是那次留下的守卫。）

### 2.4 一键连接时实际发生了什么

`coworker/server/manager.py::mcp_connect_connector`：

1. 按描述符的 `mcp_url` 写一条全局 MCP server 配置，`include_tools` 钉死为 `CORP_TOOLS`
   —— 内网端点哪天多冒出来几个工具也进不来，**漂移只能让能力变小，不能变大**
2. `requires_approval: false`（server 级关掉），改由 `prepare_mcp_tools` 按 read/write 逐工具设
3. 跑浏览器 OAuth 流程
4. 成功 → 连接器 profile 标 `mode: "mcp", enabled: True`
5. **失败 → 把刚写的那条配置删掉**。上游 2026-07-20 踩过：一个失败的一键连接留下了
   enabled 但没令牌的 oauth 条目，每次开会话都重新触发流程，把所有新会话冻住

### 2.5 凭据校验（`validate`）

模板的 `_validate` 真的会打一次内网接口，而不是只做格式检查。它区分四种失败：

- 连不上 → 网络错误原样返回，运维要靠它排查
- 302 → "多半是 SSO 登录页，令牌可能已过期"（并且**不跟随**，跟过去只会把令牌送给它）
- 401/403 → "令牌无效或该账号无权访问"，明说不是服务故障
- 200 但没有身份字段 → 说明 `identity_fields` 配错了

错误信息里**绝不回显令牌**——它会进日志、进对话、进用户截图。

---

## 3. 两条路都要过的检查

### 3.1 连上之后默认是开的

`coworker/connections.py::effective` 的规则是：**已连接、且没有任何人对它表过态 → 继承为开**。
企业连接器不在任何 persona 的 manifest 里，所以它一连上，所有 persona 都能用。

这通常正是你要的。如果某个 persona 不该看到内部系统，去它的默认连接里显式关掉——
别指望"没写就是关"。

### 3.2 企业策略照样管得住它

`config.toml`（**全局**，不是 workspace 的）：

```toml
allowed_connectors = ["corp-erp", "github"]
denied_connectors  = ["gmail", "slack"]
```

自研连接器不是策略之外的特例，`catalog_policy` 对它一样生效，且**拒绝优先于允许**。
两个模板的测试里都有对应断言。

### 3.3 审计

内部系统的每次调用都会进审计库；配了 `audit_forward_url` 就会异步外发到企业 SIEM
（`coworker/audit_forward.py`，失败开放、丢最旧、不阻塞主流程）。上线内部系统之前
把这条打通——"Agent 到底动过哪张单"这个问题，事后是补不出来的。

### 3.4 上线前自检

- [ ] `--check`（路线 A）/ `pytest tests/test_corp_connector_template.py`（路线 B）全绿
- [ ] 写工具确实会弹框，读工具确实不弹（**手工各验一次，别只看配置**）
- [ ] 字段白名单过了一遍：身份证号、手机号、薪资、成本价有没有漏出去
- [ ] 令牌只在 `.env` / SecretStore 里，`git grep` 一遍 spec 目录确认没写死
- [ ] 内网证书走 `ca_bundle`，没有任何地方关了 TLS 校验
- [ ] 审计外发通了，能在 SIEM 里查到一条测试调用
- [ ] （路线 B）挂载点那 5 行进了 `test_enterprise_customization.py` 的形状断言

---

## 4. 同步上游时的影响面

| | 冲突面 |
|---|---|
| 路线 A | **零**。桥、spec、mcp.json 全在企业目录与 state-dir 里，上游动不到 |
| 路线 B | 一个挂载点、5 行。上游动 `descriptors.py` 末尾时会冲突，保留两段 `try/except` 即可 |

`sync-localized.yml` 的定制存活冒烟会在每个同步 PR 上跑一遍，挂载点被同步覆盖会当场报红，
不会等到发版才发现。详见 [UPSTREAM_SYNC.md](UPSTREAM_SYNC.md)。
