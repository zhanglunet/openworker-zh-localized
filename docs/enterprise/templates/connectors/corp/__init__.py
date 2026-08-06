"""企业内部系统连接器 —— 原生描述符模板。

这是接内部系统的第二条路（第一条是 corp-api 的 stdio 桥，见
docs/enterprise/CONNECTOR_GUIDE.md）。选它的理由只有一个：**你要那张 GUI 卡片**——
连接器页面上一个「连接内部 ERP」的入口，员工自己点、自己授权、自己看到"已连接为
张三"，而不是让 IT 挨台机器往 .env 里塞一个全公司共用的 token。

它比 stdio 桥多给三样东西，也多要一样东西：

多给：
1. 设置向导 + 凭据校验：`validate` 真的打一次内网接口，连不上就当场说清楚，
   而不是等模型第一次调用时回一个 401。
2. **逐工具审批**：读工具永不打扰，写工具永远拦一道。stdio 桥的 requires_approval
   是 server 级的（coworker/mcp/config.py），只能靠"读写各起一个 server"来近似；
   走这条路是 coworker/server/manager.py 的 prepare_mcp_tools 按下面 CORP_TOOLS 的
   read/write 分类逐个设 requires_approval，粒度真到工具。
3. 工具白名单被描述符钉死：`include_tools` 由 CORP_TOOLS 生成，内网 MCP 端点哪天
   多冒出来几个工具也进不来——漂移只能让能力变小，不能变大。

多要：一个**内网自托管的 HTTP MCP 端点**，且要支持 OAuth 2.1 + 动态客户端注册（DCR）。
没有这个就别选这条路——把 MCP_URL 留空，descriptor 会退化成"只有卡片没有工具"，
那还不如直接用 stdio 桥。

—— 挂载点（唯一需要动上游文件的地方，5 行）——
在 coworker/connectors/descriptors.py 末尾、experimental 那一段旁边加：

    try:
        from .corp import register as _register_corp
    except ImportError:
        pass
    else:
        _register_corp()

选这个位置是因为上游极少动它，冲突时一眼能看懂该留什么。
（同步纪律见 docs/enterprise/UPSTREAM_SYNC.md 的"挂载点"一节。）

—— 改哪里 ——
下面 CONFIG 里的每一项都要按你们的内网改。改完跑：

    python3 -m pytest tests/test_corp_connector_template.py -q
"""

from __future__ import annotations

import os
from typing import Any

from coworker.connectors.descriptors import (
    ConnectorDescriptor,
    Field,
    ValidationResult,
    register_descriptor,
)
from coworker.connectors.tool_defs import ConnectorToolDef

# ==============================================================================
# 改这里
# ==============================================================================
CONFIG: dict[str, Any] = {
    # 连接器 id。会成为工具名前缀 mcp__<name>__<tool>，也是 config.toml 里
    # allowed_connectors / denied_connectors 认的那个名字。只用小写字母和连字符。
    "name": "corp-erp",
    "title": "内部 ERP",
    "icon": "🏭",
    "blurb": "查询订单、库存与客户资料；关单等写操作每次都会请你确认。",
    "brand_color": "#1f6feb",
    # 内网 HTTP MCP 端点。留空 = 不提供一键连接（只剩卡片，没有工具）。
    # 支持用环境变量覆盖，方便测试环境和生产环境用同一个包。
    "mcp_url": os.environ.get("COWORKER_CORP_MCP_URL", ""),
    # 凭据校验用的内网接口：GET <api_base><whoami_path>，2xx 且能取出身份即通过。
    "api_base": os.environ.get("COWORKER_CORP_API_BASE", ""),
    "whoami_path": "/me",
    # whoami 响应里哪个字段是"人"。按你们接口改。
    "identity_fields": ("display_name", "name", "username", "email"),
}

# 工具清单：内网 MCP 端点暴露的工具，逐个声明读还是写。
#
# 这张表就是审批策略本身 —— kind="read" 的永不弹框，kind="write" 的每次都弹。
# 少写一个工具，它就永远进不来（include_tools 由这里生成）；把写的标成读，
# 就等于把关单操作变成了静默执行。所以这张表要和内网接口的 owner 一起过一遍。
CORP_TOOLS: tuple[tuple[str, str, str, str], ...] = (
    # (工具名（不含 mcp__<name>__ 前缀), 中文标签, "read"|"write", 说明)
    ("order_get", "查订单", "read", "按订单号查询订单详情。"),
    ("order_search", "搜订单", "read", "按客户与状态搜索订单清单。"),
    ("stock_get", "查库存", "read", "查询某物料在指定仓库的可用库存。"),
    ("customer_get", "查客户", "read", "按客户编码查询客户档案。"),
    ("order_close", "关闭订单", "write", "关闭一张订单，需要给出原因。不可逆。"),
)
# ==============================================================================


def _validate(creds: dict) -> ValidationResult:
    """真打一次内网接口。连不上/无权就当场说清楚，别留到模型第一次调用时才炸。"""
    base = (creds.get("api_base") or CONFIG["api_base"] or "").rstrip("/")
    token = creds.get("api_token") or ""
    if not base:
        return ValidationResult(False, error="没有配置内部系统地址（api_base）")
    if not token:
        return ValidationResult(False, error="请填写访问令牌")

    import httpx

    try:
        resp = httpx.get(
            base + CONFIG["whoami_path"],
            headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
            timeout=15,
            # 内网系统的 302 通常是 SSO 登录页：跟过去只会把令牌送给它，
            # 还拿回一坨 HTML 然后报"响应格式不对"。不如直说。
            follow_redirects=False,
        )
    except Exception as exc:  # 网络层错误照原样说，运维要靠它排查
        return ValidationResult(False, error=f"连不上内部系统：{exc}")

    if 300 <= resp.status_code < 400:
        return ValidationResult(
            False, error="内部系统把请求重定向了（多半是 SSO 登录页）：令牌可能已过期"
        )
    if resp.status_code in (401, 403):
        return ValidationResult(False, error="令牌无效或该账号无权访问内部系统")
    if resp.status_code >= 400:
        return ValidationResult(False, error=f"内部系统返回 HTTP {resp.status_code}")
    try:
        data = resp.json()
    except Exception:
        return ValidationResult(False, error="内部系统返回的不是 JSON")
    for key in CONFIG["identity_fields"]:
        value = data.get(key) if isinstance(data, dict) else None
        if value:
            return ValidationResult(True, identity=str(value))
    return ValidationResult(False, error="内部系统没返回可识别的身份字段")


def build_descriptor() -> ConnectorDescriptor:
    return ConnectorDescriptor(
        name=CONFIG["name"],
        title=CONFIG["title"],
        icon=CONFIG["icon"],
        blurb=CONFIG["blurb"],
        auth="api_token",
        two_way=False,
        brand_color=CONFIG["brand_color"],
        mcp_url=CONFIG["mcp_url"],
        fields=[
            Field(
                "api_token",
                "访问令牌",
                secret=True,
                help="在内部系统「个人设置 → API 令牌」里生成，只需只读权限即可完成校验。",
            ),
            Field(
                "api_base",
                "系统地址（高级）",
                required=False,
                help="留空则用企业预置的默认地址。测试环境才需要填。",
                placeholder="https://erp.corp.example.com/api/v2",
            ),
        ],
        instructions=[
            "打开内部 ERP → 个人设置 → API 令牌。",
            "新建一个令牌，权限选「只读 + 订单写入」（关单需要写入权限）。",
            "把令牌粘贴到下面并点连接——会立刻校验一次，连不上会直接告诉你原因。",
        ],
        validate=_validate,
    )


def build_tool_defs() -> list[ConnectorToolDef]:
    """CORP_TOOLS → ConnectorToolDef。名字必须是 `mcp__<connector>__<tool>`：

    prepare_mcp_tools 靠这个前缀把内网端点报上来的工具名对回这张表，对不上的
    (a) 进不了 include_tools，(b) 就算硬进来了也拿不到 read 分类，默认按需审批。
    两道都是失败关闭。
    """
    name = CONFIG["name"]
    return [
        ConnectorToolDef(
            connector=name,
            name=f"mcp__{name}__{tool}",
            label=label,
            kind=kind,
            description=description,
        )
        for tool, label, kind, description in CORP_TOOLS
    ]


def register() -> ConnectorDescriptor:
    """注册描述符 + 工具定义。幂等：重复调用不会把连接器注册成两个。

    （上游有过这个 bug —— 一个新描述符和一份没删干净的占位符同名共存，连接器页面上
    出现两张卡片、工具名互相顶掉。tests/test_connectors.py 的
    test_registry_has_no_duplicate_names 就是那次留下的守卫，这里也不能破它。）
    """
    from coworker.connectors import tool_defs as td
    from coworker.connectors.descriptors import list_descriptors

    descriptor = build_descriptor()
    if CONFIG["name"] not in {d.name for d in list_descriptors()}:
        register_descriptor(descriptor)

    defs = [d for d in build_tool_defs() if d.name not in td.TOOL_TO_CONNECTOR]
    # TOOL_DEFS 是元组，但下面这几张表才是运行时真正被读的地方
    # （_KIND_BY_NAME 决定审批、TOOLS_BY_CONNECTOR 决定 include_tools 与开关）。
    # 一起更新，别让它们对不上——对不上的那一刻就是"以为关了其实还开着"。
    td.TOOL_DEFS = tuple(td.TOOL_DEFS) + tuple(defs)
    for d in defs:
        td.TOOL_TO_CONNECTOR[d.name] = d.connector
        td.TOOLS_BY_CONNECTOR.setdefault(d.connector, []).append(d)
        td._KIND_BY_NAME[d.name] = d.kind
        if d.target_arg:
            td.TARGET_ARGS[d.name] = d.target_arg
    return descriptor


__all__ = [
    "CONFIG",
    "CORP_TOOLS",
    "build_descriptor",
    "build_tool_defs",
    "register",
]
