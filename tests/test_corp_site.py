"""企业站模板（enterprise/site → Cloudflare Workers）。

这个站有两条不能破的红线，测试基本都围着它们转：

1. **不能覆盖汉化站。** 汉化站 oaosf.cn 的 Worker 叫 openworker-cn-site。企业仓是从汉化仓
   镜像来的，website/wrangler.jsonc 里那个名字一直在树里——抄一次配置就够把线上站顶掉，
   而且 wrangler 不会问你一句。
2. **不能把内部信息发到公网。** 企业站是公网可访问的，public/ 里出现内网域名、私网 IP
   或凭据，发出去就已经被抓取了，撤回也晚了。

模板本身也要是对的：占位符不能漏替换（漏了就是页面上明晃晃的 __CORP_NAME__），
downloads.json 的 key 必须和页面里的 PLATFORMS 对得上（对不上就是三个「即将开放」，
而且没人会发现是配置写错了）。
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "docs" / "enterprise" / "templates" / "site"
PUBLIC = SITE / "public"
WRANGLER = SITE / "wrangler.jsonc"
WORKFLOW = ROOT / "docs" / "enterprise" / "templates" / "deploy-corp-site.yml"

LOCALIZED_WORKER = "openworker-cn-site"

# 模板里允许出现的占位符。init 脚本负责替换，替换表漏一个就会印在页面上。
PLACEHOLDERS = {
    "__CORP_ID__",
    "__CORP_NAME__",
    "__CORP_PRODUCT__",
    "__CORP_SUPPORT__",
    "__CORP_ACCENT__",
    "__CORP_ACCENT_DARK__",
}


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _strip_jsonc(text: str) -> str:
    """wrangler.jsonc 带 // 注释，json 模块吃不下。"""
    return re.sub(r"^\s*//.*$", "", text, flags=re.MULTILINE)


# -- 红线 1：不能覆盖汉化站 -------------------------------------------------------
def test_wrangler_worker_name_is_not_the_localized_site():
    """把 name 改成 openworker-cn-site，这条必须变红。"""
    conf = json.loads(_strip_jsonc(_read(WRANGLER)))
    assert conf["name"] != LOCALIZED_WORKER, (
        "企业站 Worker 名和汉化站 oaosf.cn 撞了。同账号下同名部署会直接覆盖线上汉化站。"
    )


def test_deploy_workflow_refuses_the_localized_worker_name():
    """守卫得真的在工作流里，而不是只写在注释里。"""
    text = _read(WORKFLOW)
    assert f'"{LOCALIZED_WORKER}"' in text or LOCALIZED_WORKER in text
    guard = re.search(
        r'if \[ "\$worker" = "openworker-cn-site" \]; then.*?exit 1', text, re.S
    )
    assert guard, "工作流里没有「解析出的 Worker 名等于汉化站就 exit 1」这条守卫"


def test_deploy_workflow_also_checks_the_config_file():
    """光判变量不够：有人把 website/wrangler.jsonc 整个抄过来时，
    CORP_ID 是对的、配置文件里的名字是错的，只判变量就放行了。"""
    text = _read(WORKFLOW)
    assert "enterprise/site/wrangler.jsonc" in text
    assert "grep -q 'openworker-cn-site'" in text


def _config_guard_trips(config_text: str) -> bool:
    """复刻工作流里那条守卫：只看 "name" 字段行，不是整文件 grep。"""
    for line in config_text.splitlines():
        if re.match(r'^\s*"name"\s*:', line) and "openworker-cn-site" in line:
            return True
    return False


def test_config_guard_does_not_trip_on_its_own_warning_comment():
    """wrangler.jsonc 的注释里就写着「不能是 openworker-cn-site」。

    第一版守卫是整文件 grep，被这条注释绊倒 —— 每次部署都会失败，而且报的是
    「配置里有汉化站名」，看起来还挺像真的。守卫必须只认 name 字段。
    """
    assert _config_guard_trips(_read(WRANGLER)) is False, (
        "守卫被模板自己的告警注释绊倒了"
    )


def test_config_guard_still_catches_a_real_localized_name():
    """守卫不能为了绕开注释就变成摆设。"""
    assert _config_guard_trips('{\n  "name": "openworker-cn-site",\n}') is True


def test_worker_name_is_derived_from_corp_id():
    text = _read(WORKFLOW)
    assert 'worker="openworker-${corp_id}-site"' in text
    assert "--name \"${{ steps.name.outputs.worker }}\"" in text


# -- 红线 2：不能把内部信息发到公网 -------------------------------------------------
_INTERNAL = re.compile(
    r"\.internal\b|\.corp\b|10\.\d+\.\d+\.\d+|192\.168\.\d+\.\d+"
    r"|172\.(1[6-9]|2\d|3[01])\.\d+\.\d+",
    re.I,
)


@pytest.mark.parametrize(
    "path", sorted(p for p in PUBLIC.rglob("*") if p.is_file()), ids=lambda p: p.name
)
def test_shipped_site_files_carry_no_internal_markers(path):
    """模板自己先得干净——它是给人照抄的。"""
    hit = _INTERNAL.search(_read(path))
    assert hit is None, f"{path.name} 里出现内网标记：{hit.group(0) if hit else ''}"


def test_deploy_workflow_scans_public_before_deploying():
    text = _read(WORKFLOW)
    assert "拒绝把内部信息发到公网" in text
    assert "enterprise/site/public" in text
    # 扫描必须排在部署之前，否则拦截毫无意义
    assert text.index("拒绝把内部信息发到公网") < text.index("部署到 Cloudflare Workers")


def test_site_does_not_publish_repository_commit_log():
    """汉化站会把仓库最近提交发布到页面上（generate-site-reports.mjs）。
    在企业仓里那等于公开企业的开发动态——企业站不能继承这个行为。"""
    html = _read(PUBLIC / "index.html")
    for marker in ("git log", "recentCommits", "generate:reports", "source-analysis"):
        assert marker not in html, f"企业站页面里出现了 {marker}"


# -- 模板本身要是对的 --------------------------------------------------------------
def test_every_placeholder_is_a_known_one():
    """写了个 __CORP_FOO__ 但 init 脚本没有对应替换 = 页面上直接印出来。"""
    found = set()
    for path in SITE.rglob("*"):
        if path.is_file():
            found |= set(re.findall(r"__[A-Z0-9_]+__", _read(path)))
    unknown = found - PLACEHOLDERS
    assert not unknown, f"未知占位符（init 脚本不会替换它们）：{sorted(unknown)}"


def test_placeholders_are_actually_used():
    """替换表里有、模板里没用到的占位符，说明表和模板脱节了。"""
    blob = "".join(_read(p) for p in SITE.rglob("*") if p.is_file())
    unused = {p for p in PLACEHOLDERS if p not in blob}
    assert not unused, f"声明了却没用到的占位符：{sorted(unused)}"


def test_downloads_keys_match_the_page():
    """downloads.json 的 key 和页面里的 PLATFORMS 对不上，
    结果是三个「即将开放」，而且没人会想到是 key 写错了。"""
    data = json.loads(_read(PUBLIC / "downloads.json"))
    html = _read(PUBLIC / "index.html")
    page_keys = set(re.findall(r'key:\s*"([a-z0-9-]+)"', html))
    assert page_keys, "页面里没解析到 PLATFORMS 的 key"
    assert set(data["files"]) == page_keys, (
        f"downloads.json 的 key {sorted(data['files'])} 与页面 {sorted(page_keys)} 不一致"
    )


def test_downloads_ships_empty_so_the_page_degrades():
    """模板不该带假链接。空 url → 页面显示「即将开放」，不是 404。"""
    data = json.loads(_read(PUBLIC / "downloads.json"))
    for key, entry in data["files"].items():
        assert entry.get("url") == "", f"{key} 的模板里带了 url，应该留空"
    html = _read(PUBLIC / "index.html")
    assert "即将开放" in html


def test_wrangler_is_assets_only():
    """没有 main = assets-only 静态部署。加了 main 就得有构建产物，
    而这个站故意不引入构建步骤。"""
    conf = json.loads(_strip_jsonc(_read(WRANGLER)))
    assert "main" not in conf
    assert conf["assets"]["directory"] == "./public"


def test_page_has_no_external_requests():
    """内网/弱网环境下外链字体和 CDN 就是白屏。站点必须自包含。"""
    html = _read(PUBLIC / "index.html")
    for m in re.finditer(r'(?:src|href)="([^"]+)"', html):
        url = m.group(1)
        assert not url.startswith(("http://", "https://", "//")), f"外部资源：{url}"


def test_page_declares_charset_and_viewport():
    html = _read(PUBLIC / "index.html")
    assert 'charset="utf-8"' in html
    assert "width=device-width" in html


def test_styles_cover_light_and_dark():
    css = _read(PUBLIC / "styles.css")
    assert "prefers-color-scheme: dark" in css


# -- 与汉化站的隔离 ----------------------------------------------------------------
def test_workflow_paths_do_not_overlap_the_localized_site():
    """企业站流水线不能被 website/ 的改动触发，否则两条链路会互相打架。"""
    text = _read(WORKFLOW)
    trigger = text[text.index("on:") : text.index("permissions:")]
    assert "enterprise/site/**" in trigger
    assert "website/" not in trigger
    assert "docs/**" not in trigger


def test_workflow_skips_instead_of_failing_without_credentials():
    """没配 token 就报红，会让人习惯性无视这条流水线的红灯。"""
    text = _read(WORKFLOW)
    assert 'echo "ready=false"' in text
    assert "::notice::" in text


# -- 免责声明：本站带着企业品牌名与配色，不澄清就会被读成官方发布 ----------------
def test_disclaimer_is_present_and_says_the_three_things():
    """三件事缺一不可：个人作品、非官方发布、无隶属/背书关系。

    只写"个人作品"不够——读者会理解成"公司内部某个人做的官方工具"。
    """
    html = _read(PUBLIC / "index.html")
    for phrase in ("免责声明", "个人作品", "官方发布", "无隶属"):
        assert phrase in html, f"免责声明缺少「{phrase}」"


def test_disclaimer_comes_before_the_hero():
    """澄清得越晚越无效。它必须排在带品牌名的 hero 之前，不能塞进页脚了事。"""
    html = _read(PUBLIC / "index.html")
    assert html.index('class="disclaimer"') < html.index('class="hero"')


def test_disclaimer_is_also_in_the_footer():
    """长页面滚到底的人不会回头看顶部。"""
    html = _read(PUBLIC / "index.html")
    foot = html[html.index("<footer"):html.index("</footer>")]
    assert "非 __CORP_NAME__ 官方发布" in foot or "官方发布" in foot


def test_disclaimer_survives_placeholder_substitution():
    """免责声明里用的是 __CORP_NAME__，必须在已知占位符表里，否则会原样印在页面上。"""
    html = _read(PUBLIC / "index.html")
    block = html[html.index('class="disclaimer"'):html.index("</header>")]
    for ph in re.findall(r"__[A-Z0-9_]+__", block):
        assert ph in PLACEHOLDERS, f"免责声明里的 {ph} 不在替换表里"


def test_hero_does_not_claim_official_or_corporate_endorsement():
    """措辞层面也要守住：别写成公司 IT 部门发的东西。

    注意禁的是「声称官方」，不是「官方」这两个字本身——hero 里的
    「个人作品 · 非官方」恰恰是我们要的表述。第一版把「官方」整个拉黑，
    被自己的澄清文案命中了。
    """
    html = _read(PUBLIC / "index.html")
    hero = html[html.index('class="hero"'):html.index("</header>")]
    # 公司口径的表述：把它写成"公司发给员工的东西"
    for claim in ("内部发布", "企业边界", "员工的 AI 助手客户端", "官方发布的", "官方出品"):
        assert claim not in hero, f"hero 里出现了会被读成官方口径的表述：「{claim}」"
    # 「官方」只允许以否定形式出现
    for m in re.finditer("官方", hero):
        before = hero[max(0, m.start() - 3):m.start()]
        assert "非" in before, f"hero 里的「官方」不是否定形式：…{hero[max(0,m.start()-12):m.end()+8]}…"


def test_hero_states_it_is_a_personal_project():
    """光是"不声称官方"还不够，要主动说明身份。"""
    html = _read(PUBLIC / "index.html")
    hero = html[html.index('class="hero"'):html.index("</header>")]
    assert "个人作品" in hero and "非官方" in hero


def test_disclaimer_is_styled_to_stand_out_from_the_brand():
    """用品牌色会让它看起来像页面的一部分，而它的作用恰恰是从品牌里跳出来。"""
    css = _read(PUBLIC / "styles.css")
    assert ".disclaimer" in css
    block = css[css.index(".disclaimer"):]
    assert "var(--accent)" not in block.split("}")[0], "免责声明条不该用品牌主色"
