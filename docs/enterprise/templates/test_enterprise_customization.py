"""企业定制「存活冒烟测试」——防止上游 / 汉化版同步把企业定制静默覆盖。

放置位置：企业私有仓 ``enterprise/tests/test_enterprise_customization.py``
运行位置：每个同步 PR 的 CI（sync-upstream / sync-localized 工作流触发的 PR 必跑）

为什么需要它
------------
三仓单向同步链 ``andrewyng/openworker`` → ``zhanglunet/openworker-zh-localized``
→ ``<corp>/openworker-enterprise``。企业定制里有一部分是**落在上游文件里的「挂载点」改动**
（tauri.conf.json 的品牌字段、providers/registry.py 的 DESCRIPTORS 条目、
providers/matrix.py 的 MATRIX 条目、GUI 入口对企业主题的 import）。这些位置在合并上游
提交时最容易被「以上游为准」地覆盖掉，而且**不会报错**——构建照样成功，只是装出来的包
变回了社区版皮肤、企业模型掉出能力矩阵、企业技能没被打进去。

本文件把每一处定制变成一条断言，失败信息统一提示「定制可能被同步覆盖，请检查 X」。

设计约束
--------
1. **在汉化仓（无 ``enterprise/`` 目录）里也能跑通**：企业专属断言用 skipif 优雅跳过，
   只有「挂载点形状」和「provider 存活」这类通用断言真正执行。结果只会是 pass / skip，
   不会 error。
2. **零网络**：只做文件读取与对象构建；provider 用假配置构建（OpenAIProvider 的 SDK
   client 是懒加载的，构造函数不发请求，见 coworker/providers/openai_provider.py）。
3. **期望值不硬编码**：企业品牌名 / Bundle ID / 发行方 / 更新域名从
   ``enterprise/config/branding.json`` 或环境变量读取；仓库里只硬编码「**禁止出现**的值」
   （汉化版公钥、非企业域名）——那是必须被替换掉的旧值，写死才有意义。
4. **仓库根用 pathlib 从 ``__file__`` 往上找**（找不到再退回 cwd），不依赖 CI 的工作目录。

环境变量（可选，优先级高于 branding.json）
------------------------------------------
- ``OPENWORKER_ENTERPRISE_DIR``           企业定制目录（默认 ``<repo>/enterprise``）。
  **显式设置了却指向不存在的目录会直接报错**——写错一个字母就让整套企业断言变成 skip、
  CI 全绿，是这类守门测试最危险的失效方式，所以宁可炸掉收集阶段。
- ``OPENWORKER_ENTERPRISE_PRODUCT_NAME``  期望的 tauri ``productName``
- ``OPENWORKER_ENTERPRISE_IDENTIFIER``    期望的 tauri ``identifier``
- ``OPENWORKER_ENTERPRISE_PUBLISHER``     期望的 tauri ``bundle.publisher``
- ``OPENWORKER_ENTERPRISE_UPDATER_HOST``  期望的更新服务域名（子串匹配）
- ``OPENWORKER_ENTERPRISE_PROVIDERS``     企业 provider 名，逗号分隔（默认 ``custom``）
- ``OPENWORKER_ENTERPRISE_MODELS``        企业模型完整路由 id，逗号分隔（如 ``custom:qwen3-72b-corp``）
- ``OPENWORKER_ENTERPRISE_THEME_VARS``    主题必检 CSS 变量，逗号分隔
- ``OPENWORKER_ENTERPRISE_THEME_MOUNT``   企业主题挂载文件（相对仓库根），逗号分隔

``enterprise/config/branding.json`` 期望字段（键名大小写不敏感，支持嵌套，
也接受下划线写法 ``product_name`` / ``bundle_identifier`` / ``publisher``）::

    {
      "productName": "XX企业智能助手",
      "identifier": "com.corp.openworker",
      "publisher": "XX科技股份有限公司",
      "updaterHost": "release.corp.internal",
      "providers": ["custom"],
      "models": ["custom:qwen3-72b-corp"]
    }
"""

from __future__ import annotations

import base64
import json
import os
import re
from pathlib import Path
from typing import Any, Iterable, Optional

import pytest

try:  # Python 3.11+ 自带；3.10 退回 tomli（可选依赖，缺失则相关用例 skip）
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - 仅在 py3.10 上走到
    try:
        import tomli as tomllib  # type: ignore[no-redef]
    except ModuleNotFoundError:  # pragma: no cover
        tomllib = None  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# 定位仓库根与企业定制目录
# ---------------------------------------------------------------------------

def _find_repo_root() -> Optional[Path]:
    """从本文件（企业仓里是 ``<root>/enterprise/tests/``）向上找仓库根。

    判据是两个必然同时存在的标志物：``pyproject.toml`` + ``coworker/`` 包目录。
    找不到就从当前工作目录再找一遍——这样把本文件单独拷到别处运行（例如在汉化仓里
    做冒烟验证）也能定位到正确的仓库。
    """
    starts = [Path(__file__).resolve().parent, Path.cwd().resolve()]
    for start in starts:
        for candidate in (start, *start.parents):
            if (candidate / "pyproject.toml").is_file() and (candidate / "coworker").is_dir():
                return candidate
    # 最后兜底：用已安装的 coworker 包位置反推（可编辑安装时即仓库内）
    try:
        import coworker  # noqa: PLC0415

        pkg_parent = Path(coworker.__file__).resolve().parent.parent
        if (pkg_parent / "pyproject.toml").is_file():
            return pkg_parent
    except Exception:  # pragma: no cover - 没装也不该让收集阶段炸掉
        pass
    # 定位不到仓库根（例如本文件被单独拷到仓库外运行）：返回 None，让依赖仓库的用例
    # 优雅 skip。绝不能瞎猜一个路径——那会让"文件不存在"伪装成"定制被同步覆盖"，
    # 把冒烟测试变成狼来了。
    return None


REPO_ROOT = _find_repo_root()
IN_REPO = REPO_ROOT is not None
# 仓库外运行（本文件被单独拷出来）时的占位根：所有依赖它的用例都会被 requires_repo skip，
# 这个路径只是为了让模块能顺利 import，不会被真正读取。
_NO_REPO = Path("/nonexistent-openworker-repo")
requires_repo = pytest.mark.skipif(
    not IN_REPO,
    reason="未定位到仓库根（pyproject.toml + coworker/）——本用例只在仓库内有意义",
)

_ENTERPRISE_DIR_ENV = (os.environ.get("OPENWORKER_ENTERPRISE_DIR") or "").strip()
ENTERPRISE_DIR = (
    Path(_ENTERPRISE_DIR_ENV).expanduser().resolve()
    if _ENTERPRISE_DIR_ENV
    else ((REPO_ROOT / "enterprise") if IN_REPO else _NO_REPO / "enterprise")
)
if _ENTERPRISE_DIR_ENV and not ENTERPRISE_DIR.is_dir():
    # 不要退化成 skip：显式指定了目录却找不到，只可能是 CI 变量写错或目录被同步删掉，
    # 而这恰恰是本文件要拦的事故。收集阶段直接失败，比 12 条 skip + 全绿安全得多。
    raise RuntimeError(
        f"OPENWORKER_ENTERPRISE_DIR={_ENTERPRISE_DIR_ENV!r} 指向的目录不存在："
        f"{ENTERPRISE_DIR}。请修正该环境变量，或删掉它以使用默认的 <仓库根>/enterprise。"
    )

# 企业定制的各个落点（与 docs/enterprise/DEPLOYMENT.md、BRANDING_PACKAGING.md 一致）
SKILLS_DIR = ENTERPRISE_DIR / "skills"
BRANDING_JSON = ENTERPRISE_DIR / "config" / "branding.json"
CONFIG_DEFAULT_TOML = ENTERPRISE_DIR / "config" / "config.default.toml"
THEME_CSS = ENTERPRISE_DIR / "branding" / "theme.css"
MCP_DIR = ENTERPRISE_DIR / "mcp"

# 上游文件里的「挂载点」——同步时最容易被覆盖的几处
_ROOT = REPO_ROOT if IN_REPO else _NO_REPO  # 仓库外运行时这些路径只是占位，用例已 skip
TAURI_CONF = _ROOT / "surfaces" / "gui" / "src-tauri" / "tauri.conf.json"
SKILL_STORE_PY = _ROOT / "coworker" / "skills" / "store.py"
GUI_ENTRY_CANDIDATES = (
    _ROOT / "surfaces" / "gui" / "src" / "main.tsx",
    _ROOT / "surfaces" / "gui" / "index.html",
    _ROOT / "surfaces" / "gui" / "src" / "styles.css",
)

# 技能名合法性——与 coworker/skills/store.py 的 _NAME_RE 逐字一致（folder-is-truth，
# 技能名即文件夹名，非 ASCII 中文名会被 validate_name 拒绝）
SKILL_NAME_PATTERN = r"^[A-Za-z0-9][A-Za-z0-9._-]*$"
SKILL_NAME_RE = re.compile(SKILL_NAME_PATTERN)
SKILL_NAME_MAX = 64  # store.py 的 _MAX_NAME

# 必须被替换掉的旧值：汉化版 tauri.conf.json 里的 minisign 更新公钥。
# 企业版若仍是这把公钥，说明品牌/签名配置被同步回退了（企业签名私钥将无法通过校验）。
ZH_LOCALIZED_UPDATER_PUBKEY = (
    "dW50cnVzdGVkIGNvbW1lbnQ6IG1pbmlzaWduIHB1YmxpYyBrZXk6IDVCNzEzRjY5OTkzNUNBNjkK"
    "UldScHlqV1phVDl4VzBvTnFLLytzaDkzNVd3WWNuUm8yNE95WTBFNnBtcGF1RENxeTRuNVhQeloK"
)
# 更新源里出现即视为「非企业域」：上游作者、汉化版托管方、GitHub 公共域
FORBIDDEN_UPDATER_MARKERS = (
    "zhanglunet",
    "andrewyng",
    "github.com",
    "githubusercontent.com",
    "openworker.com",
)

# 汉化版的品牌值——企业版里出现任意一个都说明品牌字段被同步覆盖回去了
ZH_LOCALIZED_BRAND = {
    "productName": "OpenWorker 中文版",
    "identifier": "com.openworker.desktop.zh",
}

# config.default.toml 的必要键（对应 coworker/config.py 的 Config 字段）
REQUIRED_CONFIG_KEYS = ("model", "mode", "host", "port")

# 合法的审批模式 —— 必须与 coworker/permissions.py 的 Mode 枚举完全一致，
# 共 5 个值（discuss / plan / interactive / auto / custom）。
# 只写 interactive/auto/custom 会把只读模式 discuss、plan 误判成非法配置，
# 而 enterprise/config/config.default.toml 的模板注释里就列着这两个值。
_FALLBACK_MODES = ("discuss", "plan", "interactive", "auto", "custom")


def _valid_modes() -> tuple[str, ...]:
    """以运行时的 Mode 枚举为准；导不到（依赖未装）才退回硬编码全集。"""
    try:
        from coworker.permissions import Mode  # noqa: PLC0415

        return tuple(m.value for m in Mode)
    except Exception:
        return _FALLBACK_MODES


# init-enterprise-repo.sh 生成模板时留下的占位串。留着没换 = 定制没做完，
# 必须报错而不是拿它去做「期望值」比对（那只会给出一条看不懂的失败信息）。
PLACEHOLDER_MARKERS = ("REPLACE-ME", "REPLACE_ME", "@@CORP")

# 主题必检变量（取自 BRANDING_PACKAGING.md 的企业皮肤示例：只覆盖变量，不动组件）
DEFAULT_THEME_VARS = ("--accent", "--accent-soft", "--solid", "--on-solid")

# 与 coworker/mcp/config.py 的 _HTTP_TYPES 逐字一致
HTTP_TYPES = frozenset(
    {"http", "https", "sse", "streamable-http", "streamable_http"}
)

# 明文密钥特征。用 search 而非 match：真实泄露多半长成 "Bearer sk-…"、
# "token=ghp_…"，锚在行首会全部漏掉。${VAR} 引用不含这些前缀，不会误伤。
SECRET_LOOKALIKE_RE = re.compile(
    r"(sk-[A-Za-z0-9_\-]{12,}"          # OpenAI / 多数兼容厂商
    r"|sk-ant-[A-Za-z0-9_\-]{12,}"      # Anthropic
    r"|ghp_[A-Za-z0-9]{20,}"            # GitHub personal access token
    r"|github_pat_[A-Za-z0-9_]{20,}"    # GitHub fine-grained PAT
    r"|xox[baprs]-[A-Za-z0-9-]{10,}"    # Slack
    r"|AKIA[0-9A-Z]{16}"                # AWS access key id
    r"|AIza[0-9A-Za-z_\-]{30,})"        # Google API key
)


# ---------------------------------------------------------------------------
# 通用小工具
# ---------------------------------------------------------------------------

def _msg(what: str, where: Any, hint: str = "") -> str:
    """统一的失败信息：说清丢了什么 + 去哪儿查。"""
    tail = f"\n提示：{hint}" if hint else ""
    return (
        f"企业定制缺失或被改回上游值：{what}。\n"
        f"定制可能被上游/汉化版同步覆盖，请检查 {where}。{tail}"
    )


def _env_list(name: str) -> list[str]:
    return [v.strip() for v in (os.environ.get(name) or "").split(",") if v.strip()]


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _load_json(path: Path) -> Any:
    return json.loads(_read_text(path))


def _deep_get_str(data: Any, aliases: Iterable[str]) -> Optional[str]:
    """在（可能嵌套的）JSON 里按别名找第一个非空字符串——容忍 branding.json 的不同写法。"""
    if not isinstance(data, dict):
        return None
    lowered = {str(k).lower(): v for k, v in data.items()}
    for alias in aliases:
        value = lowered.get(alias.lower())
        if isinstance(value, str) and value.strip():
            return value.strip()
    for value in data.values():
        if isinstance(value, dict):
            found = _deep_get_str(value, aliases)
            if found:
                return found
    return None


def _deep_get_list(data: Any, aliases: Iterable[str]) -> list[str]:
    if not isinstance(data, dict):
        return []
    lowered = {str(k).lower(): v for k, v in data.items()}
    for alias in aliases:
        value = lowered.get(alias.lower())
        if isinstance(value, list):
            return [str(v).strip() for v in value if str(v).strip()]
        if isinstance(value, str) and value.strip():
            return [value.strip()]
    for value in data.values():
        if isinstance(value, dict):
            found = _deep_get_list(value, aliases)
            if found:
                return found
    return []


def _branding_json() -> dict:
    """读 enterprise/config/branding.json。

    **不存在**才返回空字典（用例随后 skip，这是汉化仓/尚未填期望值时的预期路径）；
    **存在但解析不出对象**一律抛错——静默吞掉 JSONDecodeError 会让所有正向品牌断言
    退化成 skip，一个多余的逗号就能把整道品牌闸门变成绿灯。
    """
    if not BRANDING_JSON.is_file():
        return {}
    try:
        data = _load_json(BRANDING_JSON)
    except (OSError, json.JSONDecodeError) as exc:
        raise AssertionError(
            _msg(
                f"{BRANDING_JSON.name} 存在但不是合法 JSON（{exc}）",
                BRANDING_JSON,
                "品牌期望值读不出来，所有正向品牌断言都会失效，必须先修好这个文件。",
            )
        ) from exc
    if not isinstance(data, dict):
        raise AssertionError(
            _msg(f"{BRANDING_JSON.name} 的顶层必须是 JSON 对象", BRANDING_JSON)
        )
    return data


def _expected(env_name: str, aliases: Iterable[str]) -> Optional[str]:
    """期望值：环境变量优先，其次 branding.json；都没有则返回 None（用例 skip 而非误报）。

    取到的值若仍是 init-enterprise-repo.sh 的占位串（REPLACE-ME… / @@CORP…），直接报错：
    拿占位串去比对只会得到一条难以理解的「不相等」失败，不如直说「模板没填完」。
    """
    from_env = (os.environ.get(env_name) or "").strip()
    value = from_env or _deep_get_str(_branding_json(), aliases)
    if value and any(marker in value for marker in PLACEHOLDER_MARKERS):
        raise AssertionError(
            _msg(
                f"期望值 {value!r} 还是初始化脚本留下的占位串（{env_name} / {list(aliases)}）",
                f"{BRANDING_JSON} 或环境变量 {env_name}",
                "把占位串替换成企业真实的品牌名 / Bundle ID / 发行方 / 更新域名。",
            )
        )
    return value


def _enterprise_provider_names() -> list[str]:
    """企业 provider 名单：环境变量 > branding.json > config.default.toml 的 model 前缀 > custom。"""
    names = _env_list("OPENWORKER_ENTERPRISE_PROVIDERS")
    if names:
        return names
    names = _deep_get_list(_branding_json(), ("providers", "provider", "provider_names"))
    if names:
        return names
    model = _config_default_model()
    if model and ":" in model:
        return [model.split(":", 1)[0]]
    # 汉化仓/上游仓里也成立的缺省：name="custom" 的 OpenAI 兼容自定义端点
    # （coworker/providers/registry.py 的 DESCRIPTORS 中已有该条目）
    return ["custom"]


def _config_default_model() -> Optional[str]:
    """从 enterprise/config/config.default.toml 读 model（读不到返回 None）。"""
    if tomllib is None or not CONFIG_DEFAULT_TOML.is_file():
        return None
    try:
        with open(CONFIG_DEFAULT_TOML, "rb") as fh:
            data = tomllib.load(fh)
    except Exception:
        return None
    model = data.get("model")
    return model.strip() if isinstance(model, str) and model.strip() else None


def _enterprise_model_ids() -> list[str]:
    """企业模型完整路由 id：环境变量 > branding.json > config.default.toml 的 model。"""
    ids = _env_list("OPENWORKER_ENTERPRISE_MODELS")
    if ids:
        return ids
    ids = _deep_get_list(_branding_json(), ("models", "model_ids", "enterprise_models"))
    if ids:
        return ids
    model = _config_default_model()
    return [model] if model else []


def _parse_frontmatter(text: str) -> dict[str, str]:
    """按 coworker/skills/base.py 的 ``_parse_skill`` 同款逐行解析 frontmatter。

    刻意不用 yaml.safe_load 作为主判据：运行时就是这么解析的，测试必须和运行时同构，
    否则会出现「测试通过但 SkillLoader 读不到 name」的假绿灯。
    """
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    out: dict[str, str] = {}
    for line in text[3:end].splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        out[key.strip().lower()] = value.strip()
    return out


_CSS_COMMENT_RE = re.compile(r"/\*.*?\*/", re.S)


def _strip_css_comments(text: str) -> str:
    """删掉 /* … */ 注释后再解析。

    两个真实问题都出在这里：
    1. 被注释掉的 ``/* --accent: #2563eb; */`` 对浏览器完全无效，但字符串搜索照样命中——
       企业把变量注释回去（等于换肤失效），测试却是绿的；
    2. 注释里写 ``.foo { … }`` 这类示例会把花括号配对算歪，块的边界跟着错。
    注释里出现 ``*/`` 字面量的情况在 CSS 里不可能（那就是注释结束），无需额外处理。
    """
    return _CSS_COMMENT_RE.sub("", text)


def _css_block(text: str, selector_re: str) -> Optional[str]:
    """抠出某个选择器的声明块（做花括号配对，容忍块内嵌套）。

    调用方需自行先过 ``_strip_css_comments``。
    """
    match = re.search(selector_re, text)
    if not match:
        return None
    start = text.find("{", match.end() - 1)
    if start == -1:
        return None
    depth = 0
    for index in range(start, len(text)):
        char = text[index]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start + 1 : index]
    return None


def _skill_dirs() -> list[Path]:
    """enterprise/skills 下的技能文件夹（目录不存在时返回空列表，交给专门的用例报错）。"""
    if not SKILLS_DIR.is_dir():
        return []
    return [
        p
        for p in sorted(SKILLS_DIR.iterdir())
        if p.is_dir() and not p.name.startswith(".")
    ]


SKILL_DIRS = _skill_dirs()

# 参数化占位：没有企业技能目录时产出一条 skip，而不是 0 条用例（0 条会被误读为"跑过了"）
_SKILL_PARAMS = SKILL_DIRS or [
    pytest.param(
        None,
        marks=pytest.mark.skip(
            reason=f"未发现企业技能目录 {SKILLS_DIR}（在汉化版/上游仓库中运行属正常）"
        ),
    )
]

requires_enterprise = pytest.mark.skipif(
    not ENTERPRISE_DIR.is_dir(),
    reason=(
        f"未发现企业定制目录 {ENTERPRISE_DIR}——本用例只在企业私有仓生效；"
        "在汉化版/上游仓库中跳过属预期行为。"
    ),
)
requires_tomllib = pytest.mark.skipif(
    tomllib is None, reason="缺少 tomllib/tomli（Python 3.10 需安装 tomli）"
)


# ===========================================================================
# 0. 挂载点形状（企业仓与汉化仓都执行）——上游一旦重构这些位置，企业定制就无处可挂
# ===========================================================================

@requires_repo
def test_mount_point_skill_name_rule_unchanged():
    """技能名规则仍是 ASCII 白名单：企业技能文件夹命名依据它，规则变了要同步复核。"""
    assert SKILL_STORE_PY.is_file(), _msg(
        "技能存储模块 coworker/skills/store.py 不存在", SKILL_STORE_PY
    )
    source = _read_text(SKILL_STORE_PY)
    assert SKILL_NAME_PATTERN in source, _msg(
        f"coworker/skills/store.py 里的技能名正则不再是 {SKILL_NAME_PATTERN}",
        SKILL_STORE_PY,
        "上游改了 validate_name 的约束——请复核 enterprise/skills/ 下所有技能文件夹名是否仍合法。",
    )


@requires_repo
def test_mount_point_tauri_conf_shape():
    """品牌挂载点仍在：productName / identifier / bundle.publisher / updater 端点+公钥。"""
    assert TAURI_CONF.is_file(), _msg(
        "桌面壳配置 surfaces/gui/src-tauri/tauri.conf.json 不存在", TAURI_CONF
    )
    conf = _load_json(TAURI_CONF)
    for key in ("productName", "identifier"):
        assert conf.get(key), _msg(f"tauri.conf.json 顶层缺少 {key}", TAURI_CONF)
    assert isinstance(conf.get("bundle"), dict) and conf["bundle"].get("publisher"), _msg(
        "tauri.conf.json 缺少 bundle.publisher", TAURI_CONF
    )
    updater = (conf.get("plugins") or {}).get("updater") or {}
    assert isinstance(updater.get("endpoints"), list) and updater["endpoints"], _msg(
        "tauri.conf.json 缺少 plugins.updater.endpoints", TAURI_CONF
    )
    assert updater.get("pubkey"), _msg(
        "tauri.conf.json 缺少 plugins.updater.pubkey", TAURI_CONF
    )


def test_mount_point_provider_registry_api():
    """Provider 注册表 API 仍是 DESCRIPTORS / get_descriptor / build_provider_client。"""
    registry = pytest.importorskip(
        "coworker.providers.registry", reason="coworker 依赖未安装，跳过 provider 挂载点检查"
    )
    for attr in ("DESCRIPTORS", "get_descriptor", "build_provider_client", "provider_names"):
        assert hasattr(registry, attr), _msg(
            f"coworker/providers/registry.py 缺少 {attr}",
            registry.__file__,
            "上游重构了 provider 注册方式——企业 provider 条目需要重新挂载。",
        )
    assert registry.DESCRIPTORS, _msg(
        "coworker/providers/registry.py 的 DESCRIPTORS 为空", registry.__file__
    )
    matrix_mod = pytest.importorskip(
        "coworker.providers.matrix", reason="coworker 依赖未安装，跳过能力矩阵挂载点检查"
    )
    assert isinstance(matrix_mod.MATRIX, dict) and matrix_mod.MATRIX, _msg(
        "coworker/providers/matrix.py 的 MATRIX 为空", matrix_mod.__file__
    )


def test_mount_point_connector_registry_api():
    """内部系统连接器（CONNECTOR_GUIDE 路线 B）的挂载面仍在。

    企业的 corp 连接器靠两件事挂上去：descriptors.register_descriptor()，以及 tool_defs
    里那几张**可变**查找表。上游要是把 TOOLS_BY_CONNECTOR / _KIND_BY_NAME 换成不可变结构，
    或改成从 TOOL_DEFS 惰性计算，企业连接器会**静默地只剩一张卡片没有工具**——
    没有弹框、没有报错、没人会发现。所以这条要在同步 PR 上就红。
    """
    ds = pytest.importorskip(
        "coworker.connectors.descriptors", reason="coworker 依赖未安装，跳过连接器挂载点检查"
    )
    for attr in ("ConnectorDescriptor", "Field", "ValidationResult", "register_descriptor",
                 "list_descriptors", "get_descriptor"):
        assert hasattr(ds, attr), _msg(
            f"coworker/connectors/descriptors.py 缺少 {attr}",
            ds.__file__,
            "上游重构了连接器注册方式——企业连接器需要重新挂载（见 docs/enterprise/CONNECTOR_GUIDE.md §2.3）。",
        )
    td = pytest.importorskip(
        "coworker.connectors.tool_defs", reason="coworker 依赖未安装，跳过工具注册表挂载点检查"
    )
    # 这四张表是 register() 真正写入的地方；只要有一张变成不可变或消失，工具就挂不上去
    for name, kind in (
        ("TOOL_TO_CONNECTOR", dict),
        ("TOOLS_BY_CONNECTOR", dict),
        ("_KIND_BY_NAME", dict),
        ("TARGET_ARGS", dict),
    ):
        assert isinstance(getattr(td, name, None), kind), _msg(
            f"coworker/connectors/tool_defs.py 的 {name} 不再是可写的 {kind.__name__}",
            td.__file__,
            "企业连接器的工具注册依赖直接写入这张表——上游换了结构就得改 corp/__init__.py 的 register()。",
        )
    for attr in ("ConnectorToolDef", "approval_for_tool", "mcp_pinned_tools", "mcp_tool_defs"):
        assert hasattr(td, attr), _msg(
            f"coworker/connectors/tool_defs.py 缺少 {attr}", td.__file__
        )
    # 逐工具审批的判据仍是 read/write：分类语义变了，CORP_TOOLS 那张表就要重新过一遍
    assert td.approval_for_tool("github_search") is False, _msg(
        "连接器 read 工具不再免审批（§36 的『reads never gate』变了）", td.__file__
    )


# ===========================================================================
# 1. 企业技能包存活
# ===========================================================================

@requires_enterprise
def test_enterprise_skills_present():
    """enterprise/skills/ 存在且至少有一个技能。"""
    assert SKILLS_DIR.is_dir(), _msg("企业技能目录 enterprise/skills/ 不存在", SKILLS_DIR)
    assert SKILL_DIRS, _msg(
        "企业技能目录 enterprise/skills/ 下没有任何技能文件夹",
        SKILLS_DIR,
        "同步合并可能删掉了技能资产；技能包是首启拷贝到 state_dir()/skills 的唯一来源。",
    )


@pytest.mark.parametrize("skill_dir", _SKILL_PARAMS, ids=lambda p: getattr(p, "name", str(p)))
def test_enterprise_skill_folder_name_is_ascii_safe(skill_dir: Path):
    """技能文件夹名必须过 validate_name（^[A-Za-z0-9][A-Za-z0-9._-]*$，≤64 字符）。"""
    name = skill_dir.name
    assert len(name) <= SKILL_NAME_MAX, _msg(
        f"技能文件夹名过长（>{SKILL_NAME_MAX}）：{name}", skill_dir
    )
    assert SKILL_NAME_RE.match(name), _msg(
        f"技能文件夹名 {name!r} 不符合 coworker/skills/store.py 的 validate_name 约束 "
        f"{SKILL_NAME_PATTERN}（不允许中文/空格/斜杠）",
        skill_dir,
        "非法名的技能无法被 SkillStore 管理，GUI 里会消失。",
    )
    # 真实约束以运行时代码为准：能 import 到就用真的 validate_name 再校一遍
    try:
        from coworker.skills.store import validate_name  # noqa: PLC0415
    except Exception:
        return
    validate_name(name)  # 抛 ValueError 即用例失败，异常信息本身已说明问题


@pytest.mark.parametrize("skill_dir", _SKILL_PARAMS, ids=lambda p: getattr(p, "name", str(p)))
def test_enterprise_skill_has_valid_skill_md(skill_dir: Path):
    """每个技能有 SKILL.md，且 frontmatter 含非空 name / description。"""
    md = skill_dir / "SKILL.md"
    assert md.is_file(), _msg(
        f"技能 {skill_dir.name} 缺少 SKILL.md", md, "没有 SKILL.md 的文件夹会被加载器直接忽略。"
    )
    text = _read_text(md)
    assert text.startswith("---"), _msg(
        f"技能 {skill_dir.name} 的 SKILL.md 没有 YAML frontmatter（首行必须是 ---）", md
    )
    front = _parse_frontmatter(text)
    assert front.get("name"), _msg(f"技能 {skill_dir.name} 的 SKILL.md frontmatter 缺少 name", md)
    assert front.get("description"), _msg(
        f"技能 {skill_dir.name} 的 SKILL.md frontmatter 缺少 description",
        md,
        "description 就是会话启动时注入的技能目录条目，缺了模型不知道何时用它。",
    )
    assert SKILL_NAME_RE.match(front["name"]), _msg(
        f"技能 {skill_dir.name} 的 frontmatter name={front['name']!r} 不符合 {SKILL_NAME_PATTERN}",
        md,
    )
    body = text[text.find("\n---", 3) + 4 :].strip()
    assert body, _msg(f"技能 {skill_dir.name} 的 SKILL.md 正文为空", md)
    # frontmatter 的 name 覆盖文件夹名（见 base.py::_parse_skill），不一致会让 SkillStore
    # 按文件夹找不到、按名字又能列出来——直接在这里拦掉
    assert front["name"] == skill_dir.name, _msg(
        f"技能 {skill_dir.name} 的 frontmatter name={front['name']!r} 与文件夹名不一致",
        md,
        "SkillLoader 以 frontmatter name 为准、SkillStore 以文件夹名为准，二者必须相同。",
    )


@requires_enterprise
def test_skill_loader_discovers_enterprise_skills():
    """用真实的 SkillLoader 指向 enterprise/skills，确认每个技能都能被发现。"""
    try:
        from coworker.skills.base import SkillLoader  # noqa: PLC0415
    except Exception as exc:  # aisuite 等运行时依赖未安装的最小环境
        pytest.skip(f"无法导入 coworker.skills.base（{exc.__class__.__name__}: {exc}）")
    assert SKILL_DIRS, _msg("企业技能目录下没有技能", SKILLS_DIR)
    loader = SkillLoader([SKILLS_DIR])
    discovered = set(loader.names())
    expected = {p.name for p in SKILL_DIRS}
    missing = sorted(expected - discovered)
    assert not missing, _msg(
        f"SkillLoader 未能发现这些企业技能：{missing}",
        SKILLS_DIR,
        "检查对应文件夹的 SKILL.md 是否存在、frontmatter name 是否与文件夹名一致。",
    )
    catalog = {entry["name"]: entry["description"] for entry in loader.catalog()}
    empty = sorted(n for n in expected if not catalog.get(n))
    assert not empty, _msg(
        f"这些企业技能的 description 为空（技能目录条目会是空行）：{empty}", SKILLS_DIR
    )


# ===========================================================================
# 2. 企业 Provider 与能力矩阵存活
# ===========================================================================

@pytest.mark.parametrize("provider_name", _enterprise_provider_names())
def test_enterprise_provider_descriptor_alive(provider_name: str):
    """企业 provider 条目仍在 DESCRIPTORS 里（按名字 get_descriptor 查得到）。"""
    registry = pytest.importorskip(
        "coworker.providers.registry", reason="coworker 依赖未安装，跳过 provider 存活检查"
    )
    descriptor = registry.get_descriptor(provider_name)
    assert descriptor is not None, _msg(
        f"provider {provider_name!r} 已不在 DESCRIPTORS 中",
        f"{registry.__file__} 的 DESCRIPTORS 列表",
        "合并上游时最容易被整段覆盖；注意 build_provider_client 对未知 provider 会静默回退到 openai。",
    )
    assert descriptor.name == provider_name
    field_keys = {f.key for f in descriptor.fields}
    if provider_name == "custom":
        # OpenAI 兼容自定义端点的三个字段是企业内网网关接入的全部依赖
        for key in ("base_url", "api_key", "model"):
            assert key in field_keys, _msg(
                f"provider custom 缺少配置字段 {key}",
                f"{registry.__file__} 的 name=\"custom\" 描述符",
            )


@pytest.mark.parametrize("provider_name", _enterprise_provider_names())
def test_enterprise_provider_builds_with_fake_profile(provider_name: str):
    """用假配置构建企业 provider 客户端——纯本地，绝不发网络请求。

    OpenAI SDK 的 client 是懒加载的（见 openai_provider.py::_ensure_client），
    构造阶段既不校验 key 也不连网，所以这条断言在离线 CI 上完全可靠。
    """
    registry = pytest.importorskip(
        "coworker.providers.registry", reason="coworker 依赖未安装，跳过 provider 构建检查"
    )
    base_mod = pytest.importorskip("coworker.providers.base")
    descriptor = registry.get_descriptor(provider_name)
    assert descriptor is not None, _msg(
        f"provider {provider_name!r} 已不在 DESCRIPTORS 中", registry.__file__
    )
    fake_profile = {
        # .invalid 是 RFC 2606 保留后缀，永远解析不出来——即便哪天变成真请求也不会打到外网
        "base_url": "https://llm.enterprise.invalid/v1",
        "api_key": "sk-fake-not-a-real-key",
        "model": "enterprise-smoke-test-model",
        "region": "us-east-1",
        "project": "enterprise-smoke-test",
        "location": "global",
    }
    # 走描述符自身的 build。
    client = descriptor.build(fake_profile, None)
    assert isinstance(client, base_mod.ProviderClient), _msg(
        f"provider {provider_name!r} 的 build() 未返回 ProviderClient",
        registry.__file__,
    )
    # 再走一遍工厂。注意 build_provider_client 对未知名字会**静默回退到 openai**
    # （`_BY_NAME.get(name) or _BY_NAME["openai"]`），回退结果同样是个合法的
    # ProviderClient，所以光断言 isinstance 证明不了任何事——必须另外确认名字仍在
    # 公开名单里，否则「企业条目被删」这件事会被回退路径完全掩盖。
    assert provider_name in registry.provider_names(), _msg(
        f"provider {provider_name!r} 不在 registry.provider_names() 里，"
        "build_provider_client 会静默回退到 openai",
        f"{registry.__file__} 的 DESCRIPTORS",
        "回退不会报错，只是请求全部打到 api.openai.com。",
    )
    routed = registry.build_provider_client(provider_name, fake_profile, None)
    assert isinstance(routed, base_mod.ProviderClient), _msg(
        f"build_provider_client({provider_name!r}) 未返回 ProviderClient", registry.__file__
    )
    # OpenAI 兼容实现会把 base_url 收进 _base_url；据此确认用的是企业配置而不是内置默认端点
    if hasattr(routed, "_base_url"):
        assert routed._base_url == fake_profile["base_url"], _msg(
            f"provider {provider_name!r} 忽略了配置里的 base_url（拿到 {routed._base_url!r}）",
            registry.__file__,
            "企业内网网关地址不生效，请求会打到厂商公网端点。",
        )


def _declared_in_repo() -> dict:
    """仓库里那份模型声明（enterprise/config/models.json），用**运行时同一套解析器**读。

    为什么不直接 json.load：model_overlay 会丢弃类型不对的字段（布尔写成字符串、
    context_window 写成 "128k"）并只打一条 warning。naive 解析看着好好的，
    运行时却少一半能力——测试必须和运行时同构。
    """
    path = ENTERPRISE_DIR / "config" / "models.json"
    if not path.is_file():
        return {}
    overlay = pytest.importorskip(
        "coworker.providers.model_overlay", reason="coworker 依赖未安装"
    )
    import shutil
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        shutil.copyfile(path, Path(tmp) / "models.json")
        old_dir = os.environ.get("COWORKER_STATE_DIR")
        os.environ["COWORKER_STATE_DIR"] = tmp
        try:
            overlay.invalidate()
            return dict(overlay.declared())
        finally:
            if old_dir is None:
                os.environ.pop("COWORKER_STATE_DIR", None)
            else:
                os.environ["COWORKER_STATE_DIR"] = old_dir
            overlay.invalidate()


@requires_enterprise
def test_model_declaration_types_survive_the_runtime_parser():
    """models.json 里写下的值，必须和运行时真正用到的值一致。

    model_overlay._parse_entry 遇到类型不对（布尔写成 "true"、context_window 写成 "128k"）
    只打一条 warning 然后**回落到默认值**。于是：
      "parallel_tool_calls": "true"   → 实际生效 False → Agent 永远串行，慢一倍
      "vision": "false"               → 实际生效 False → 恰好一致，看不出问题
    第一种是把实测出来的能力静默关掉，而 JSON 本身完全合法、naive 校验也查不出来。
    这条比对「文件里写的」与「解析器给出的」，不一致即失败。
    """
    path = ENTERPRISE_DIR / "config" / "models.json"
    if not path.is_file():
        pytest.skip("没有 enterprise/config/models.json（走的是改 matrix.py 那条路）")
    raw = _load_json(path)
    parsed = _declared_in_repo()
    for model_id, row in (raw.get("models") or {}).items():
        entry = parsed.get(model_id)
        assert entry is not None, _msg(
            f"{model_id} 写在 models.json 里，运行时解析器却没收下它", path
        )
        for flag in ("tools", "streaming", "vision", "pdf", "parallel_tool_calls"):
            if flag not in row:
                continue
            written = row[flag]
            assert isinstance(written, bool), _msg(
                f"{model_id}.{flag} 写成了 {type(written).__name__}（{written!r}），必须是 true/false",
                path,
                "解析器会丢弃它并回落到默认值——JSON 合法、构建照过，能力却静默变了。",
            )
            assert getattr(entry.caps, flag) is written, _msg(
                f"{model_id}.{flag} 写的是 {written}，运行时实际是 {getattr(entry.caps, flag)}",
                path,
            )
        if "context_window" in row:
            assert isinstance(row["context_window"], int) and row["context_window"] > 0, _msg(
                f"{model_id}.context_window 必须是正整数，收到 {row['context_window']!r}", path
            )
            assert entry.context_window == row["context_window"], _msg(
                f"{model_id}.context_window 写的是 {row['context_window']}，"
                f"运行时实际是 {entry.context_window}",
                path,
            )


@requires_enterprise
def test_enterprise_models_registered_in_matrix():
    """企业模型可被解析到 —— 内置 MATRIX 或 enterprise/config/models.json 声明，两条都算。

    早先这里只看 matrix_mod.MATRIX 这个原字典，那是错的：运行时读的是 _effective()，
    它把 <state-dir>/models.json 的声明合进**一个新字典**、不写回 MATRIX。
    于是一个正确用声明覆盖层配好的部署（零上游改动，正是我们推荐的做法），
    冒烟测试照样红 —— 假警报。而 CI 里又没有 state-dir，所以也不能去读运行时那份，
    要校验的是**仓库里**那份声明。
    """
    matrix_mod = pytest.importorskip(
        "coworker.providers.matrix", reason="coworker 依赖未安装，跳过能力矩阵检查"
    )
    matrix = dict(matrix_mod.MATRIX)
    for mid, row in _declared_in_repo().items():
        matrix[mid] = matrix_mod.ModelEntry(row.label, row.caps, row.context_window)
    # 前缀不能写死成 "custom:" —— 企业换用 ollama / 某个 OpenAI 兼容厂商时，
    # 写死会让这条断言永远失败，且失败信息指向一个根本不相关的 provider。
    prefixes = tuple(f"{name}:" for name in _enterprise_provider_names())
    enterprise_keys = [k for k in matrix if k.startswith(prefixes)]
    assert enterprise_keys, _msg(
        f"没有任何 {list(prefixes)} 前缀的企业模型条目",
        f"{matrix_mod.__file__} 的 MATRIX，或 enterprise/config/models.json",
        "未登记的模型会落到 capabilities.py 的保守启发式：并行工具调用/视觉默认关、"
        "GUI 上下文水位条消失，Agent 效果被动降级。",
    )
    expected_ids = _enterprise_model_ids()
    if not expected_ids:
        pytest.skip(
            "未声明企业模型 id（可设 OPENWORKER_ENTERPRISE_MODELS 或在 "
            "enterprise/config/branding.json 里写 models，或在 config.default.toml 配 model）"
        )
    for model_id in expected_ids:
        entry = matrix.get(model_id)
        assert entry is not None, _msg(
            f"企业模型 {model_id!r} 既不在 MATRIX 里，也没有在 enterprise/config/models.json 里声明",
            f"{matrix_mod.__file__} 的 MATRIX 或 enterprise/config/models.json"
            "（键必须是完整路由 id，含 provider 前缀）",
            "推荐用 models.json 声明：不动上游文件，同步时零冲突。"
            "能力值请用 verify-private-model.py 实测得出，不要照抄上游同名模型。",
        )
        assert getattr(entry.caps, "tools", False), _msg(
            f"企业模型 {model_id!r} 的 MATRIX 条目 tools=False",
            matrix_mod.__file__,
            "不支持工具调用的模型无法驱动 Agent 循环。",
        )
        assert entry.label.strip(), _msg(
            f"企业模型 {model_id!r} 的 MATRIX 条目 label 为空", matrix_mod.__file__
        )


# ===========================================================================
# 3. 桌面品牌字段存活（tauri.conf.json）
# ===========================================================================

def _tauri_conf() -> dict:
    assert TAURI_CONF.is_file(), _msg("tauri.conf.json 不存在", TAURI_CONF)
    return _load_json(TAURI_CONF)


@requires_enterprise
def test_brand_fields_are_enterprise_values():
    """productName / identifier / bundle.publisher 是企业值，不是上游或汉化版的值。"""
    conf = _tauri_conf()
    actual = {
        "productName": conf.get("productName", ""),
        "identifier": conf.get("identifier", ""),
        "publisher": (conf.get("bundle") or {}).get("publisher", ""),
    }
    # 先做「不许等于旧值」的负向断言——不依赖任何期望值配置，永远能跑
    for key, stale in ZH_LOCALIZED_BRAND.items():
        assert actual[key] != stale, _msg(
            f"tauri.conf.json 的 {key} 又变回汉化版的 {stale!r}",
            TAURI_CONF,
            "改回上游值意味着安装包名/Bundle ID 回退（Bundle ID 变化还会导致状态目录不互通）。",
        )
    expectations = {
        "productName": _expected(
            "OPENWORKER_ENTERPRISE_PRODUCT_NAME", ("productName", "product_name", "app_name")
        ),
        "identifier": _expected(
            "OPENWORKER_ENTERPRISE_IDENTIFIER",
            ("identifier", "bundle_identifier", "bundleId", "bundle_id"),
        ),
        "publisher": _expected(
            "OPENWORKER_ENTERPRISE_PUBLISHER", ("publisher", "bundle_publisher", "company")
        ),
    }
    declared = {k: v for k, v in expectations.items() if v}
    if not declared:
        pytest.skip(
            f"未声明品牌期望值：请提供 {BRANDING_JSON} 或 OPENWORKER_ENTERPRISE_PRODUCT_NAME "
            "/ _IDENTIFIER / _PUBLISHER 环境变量"
        )
    for key, want in declared.items():
        assert actual[key] == want, _msg(
            f"tauri.conf.json 的 {key} 是 {actual[key]!r}，期望 {want!r}",
            f"{TAURI_CONF}（期望值来源：{BRANDING_JSON} 或环境变量）",
        )


@requires_enterprise
def test_updater_endpoints_point_at_enterprise_host():
    """更新源不得指向 zhanglunet / andrewyng / github.com 等非企业域。"""
    conf = _tauri_conf()
    updater = (conf.get("plugins") or {}).get("updater") or {}
    endpoints = updater.get("endpoints") or []
    assert endpoints, _msg(
        "tauri.conf.json 的 plugins.updater.endpoints 为空", TAURI_CONF
    )
    for url in endpoints:
        lowered = str(url).lower()
        hit = [m for m in FORBIDDEN_UPDATER_MARKERS if m in lowered]
        assert not hit, _msg(
            f"更新源 {url} 仍指向非企业域 {hit}",
            TAURI_CONF,
            "企业版会从社区仓库拉到未签名/非企业构建，必须改为企业托管地址。",
        )
    host = _expected("OPENWORKER_ENTERPRISE_UPDATER_HOST", ("updaterHost", "updater_host", "update_domain"))
    if host:
        for url in endpoints:
            assert host.lower() in str(url).lower(), _msg(
                f"更新源 {url} 不包含企业更新域名 {host!r}",
                f"{TAURI_CONF}（期望值来源：{BRANDING_JSON} 或 OPENWORKER_ENTERPRISE_UPDATER_HOST）",
            )


@requires_enterprise
def test_updater_pubkey_is_not_the_localized_key():
    """更新公钥必须换成企业自己的 minisign 公钥。"""
    conf = _tauri_conf()
    updater = (conf.get("plugins") or {}).get("updater") or {}
    pubkey = str(updater.get("pubkey") or "").strip()
    assert pubkey, _msg("tauri.conf.json 的 plugins.updater.pubkey 为空", TAURI_CONF)
    forbidden = {ZH_LOCALIZED_UPDATER_PUBKEY}
    forbidden.update(_deep_get_list(_branding_json(), ("forbidden_pubkeys", "forbiddenPubkeys")))
    assert pubkey not in forbidden, _msg(
        "plugins.updater.pubkey 仍是汉化版/上游的公钥",
        TAURI_CONF,
        "企业签名私钥（TAURI_SIGNING_PRIVATE_KEY）签出的更新包将无法通过校验，自动更新会全线失败。",
    )
    # 顺带确认它确实是一把 minisign 公钥，而不是占位符。
    # 注意不能写成「解不出来就跳过」：REPLACE-ME-WITH-CORP-PUBKEY 这类占位串正好
    # 解不出 base64，那样写等于给占位符开了后门（实测会通过）。解不出即判失败。
    try:
        # 先去掉所有空白：极少数配置会把公钥折成多行，那是合法的，不该判失败。
        compact = re.sub(r"\s+", "", pubkey)
        decoded = base64.b64decode(compact, validate=True).decode("utf-8", "ignore")
    except Exception as exc:
        raise AssertionError(
            _msg(
                f"plugins.updater.pubkey 不是合法 base64（{exc.__class__.__name__}），"
                "多半还是占位串",
                TAURI_CONF,
                "tauri signer generate 产出的公钥是 base64 文本，"
                "直接把 <key>.pub 的内容整段贴进来。",
            )
        ) from exc
    assert "minisign public key" in decoded.lower(), _msg(
        "plugins.updater.pubkey 解码后不含 minisign 公钥标识（可能是占位符或贴错内容）",
        TAURI_CONF,
    )


# ===========================================================================
# 4. 企业配置模板存活（enterprise/config/config.default.toml）
# ===========================================================================

@requires_enterprise
@requires_tomllib
def test_enterprise_config_default_is_valid_and_prefixed():
    """config.default.toml 可解析；model 必须带 provider 前缀，否则被静默路由到 openai。"""
    assert CONFIG_DEFAULT_TOML.is_file(), _msg(
        "企业默认配置 enterprise/config/config.default.toml 不存在", CONFIG_DEFAULT_TOML
    )
    try:
        with open(CONFIG_DEFAULT_TOML, "rb") as fh:
            data = tomllib.load(fh)
    except (tomllib.TOMLDecodeError, OSError) as exc:
        pytest.fail(
            _msg(
                f"config.default.toml 读不出来或不是合法 TOML（{exc.__class__.__name__}: {exc}）",
                CONFIG_DEFAULT_TOML,
            )
        )

    for key in REQUIRED_CONFIG_KEYS:
        assert key in data, _msg(
            f"config.default.toml 缺少必要键 {key}", CONFIG_DEFAULT_TOML
        )

    model = str(data["model"]).strip()
    assert ":" in model, _msg(
        f"config.default.toml 的 model={model!r} 没有 provider 前缀",
        CONFIG_DEFAULT_TOML,
        "裸模型名会被 ProviderRouter 静默路由到默认的 openai provider——不会报错，"
        "只是请求打到 api.openai.com，企业内网网关完全不生效。正确写法：custom:xxx / ollama:xxx。",
    )
    prefix = model.split(":", 1)[0]
    registry = pytest.importorskip(
        "coworker.providers.registry", reason="coworker 依赖未安装，跳过 model 前缀校验"
    )
    assert registry.get_descriptor(prefix) is not None, _msg(
        f"config.default.toml 的 model 前缀 {prefix!r} 不是已注册的 provider",
        f"{CONFIG_DEFAULT_TOML} 与 {registry.__file__} 的 DESCRIPTORS",
        "未知前缀同样会被当成裸模型名而回退到 openai。",
    )

    # 键名拼写守卫：load_config 只认 _FIELDS 里的键，写错的键**不会报错**，静默失效
    try:
        from coworker.config import _FIELDS as CONFIG_FIELDS  # noqa: PLC0415
    except Exception:
        CONFIG_FIELDS = {
            "model", "mode", "max_iterations", "allowed_commands", "auto_allow",
            "host", "port", "web_search_provider", "cloud_base_url",
            "cloud_auth_domain", "cloud_client_id", "cloud_audience",
            "cloud_relay_ws_url",
        }
    unknown = sorted(k for k in data if k not in CONFIG_FIELDS)
    assert not unknown, _msg(
        f"config.default.toml 含未被 coworker/config.py 识别的键：{unknown}",
        CONFIG_DEFAULT_TOML,
        "load_config 会静默忽略未知键（也可能是上游改了字段名），该项配置将完全不生效。",
    )

    modes = _valid_modes()
    assert str(data["mode"]).strip() in modes, _msg(
        f"config.default.toml 的 mode={data['mode']!r} 不是合法审批模式（合法值：{list(modes)}）",
        f"{CONFIG_DEFAULT_TOML} 与 coworker/permissions.py 的 Mode 枚举",
    )
    # TOML 里 port = true 会解析成 bool，而 Python 的 bool 是 int 的子类——
    # 光写 isinstance(..., int) 放行 true/false。端口范围也顺手卡住。
    port = data["port"]
    assert isinstance(port, int) and not isinstance(port, bool) and 1 <= port <= 65535, _msg(
        f"config.default.toml 的 port={port!r} 必须是 1–65535 的整数", CONFIG_DEFAULT_TOML
    )
    if "allowed_commands" in data:
        assert isinstance(data["allowed_commands"], list), _msg(
            "config.default.toml 的 allowed_commands 必须是数组", CONFIG_DEFAULT_TOML
        )
    if "max_iterations" in data:
        assert isinstance(data["max_iterations"], int) and data["max_iterations"] > 0, _msg(
            "config.default.toml 的 max_iterations 必须是正整数", CONFIG_DEFAULT_TOML
        )


# ===========================================================================
# 5. 企业 MCP 配置模板存活
# ===========================================================================

def _mcp_template_files() -> list[Path]:
    """收集企业 MCP 模板：enterprise/mcp/**/*.json + enterprise/config/mcp*.json。"""
    found: list[Path] = []
    if MCP_DIR.is_dir():
        found.extend(sorted(p for p in MCP_DIR.rglob("*.json") if p.is_file()))
    config_dir = ENTERPRISE_DIR / "config"
    if config_dir.is_dir():
        found.extend(sorted(p for p in config_dir.glob("mcp*.json") if p.is_file()))
    return found


@requires_enterprise
def test_enterprise_mcp_templates_are_valid():
    """MCP 模板是合法 JSON，且 mcpServers 结构符合 coworker/mcp/config.py 的解析约定。"""
    files = _mcp_template_files()
    assert files, _msg(
        "未找到任何企业 MCP 配置模板（enterprise/mcp/**/*.json 或 enterprise/config/mcp*.json）",
        MCP_DIR,
        "企业 CLI / 知识库的零代码接入依赖该模板。",
    )
    server_files = []
    for path in files:
        try:
            data = _load_json(path)
        except json.JSONDecodeError as exc:
            pytest.fail(_msg(f"MCP 模板不是合法 JSON（{exc}）", path))
        if not isinstance(data, dict) or "mcpServers" not in data:
            continue  # 同目录下的其它 json（如 package.json）不作要求
        server_files.append(path)
        servers = data["mcpServers"]
        assert isinstance(servers, dict), _msg(
            f"{path.name} 的 mcpServers 必须是对象（服务名 → 定义）", path
        )
        assert servers, _msg(f"{path.name} 的 mcpServers 为空", path)
        for name, raw in servers.items():
            assert isinstance(raw, dict), _msg(
                f"{path.name} 的 mcpServers.{name} 必须是对象", path
            )
            # 传输方式：stdio 需要 command，http/sse 需要 url（见 mcp/config.py::_parse，
            # 判据是 type ∈ _HTTP_TYPES 或存在 url）
            declared_http = str(raw.get("type", "")).lower() in HTTP_TYPES
            has_url = bool(raw.get("url"))
            has_stdio = bool(raw.get("command"))
            has_http = has_url or declared_http
            assert has_stdio or has_http, _msg(
                f"{path.name} 的 mcpServers.{name} 既没有 command（stdio）也没有 url/type（http）",
                path,
                "两者皆无时会被当作 stdio 且 command=None，启动即失败。",
            )
            # 只写 type: http 不给 url 同样跑不起来（transport=http 但 url=None），
            # 光判 has_http 会把这种半成品配置放过去。
            assert not (declared_http and not has_url), _msg(
                f"{path.name} 的 mcpServers.{name} 声明了 type={raw.get('type')!r} 却没有 url",
                path,
                "http 传输的目标地址只能来自 url 字段。",
            )
            assert not (has_stdio and raw.get("url")), _msg(
                f"{path.name} 的 mcpServers.{name} 同时给了 command 和 url",
                path,
                "有 url 就会被判定为 http 传输，command 被忽略——意图不明确。",
            )
            if "args" in raw:
                assert isinstance(raw["args"], list), _msg(
                    f"{path.name} 的 mcpServers.{name}.args 必须是数组", path
                )
            for key in ("env", "headers"):
                if key in raw:
                    assert isinstance(raw[key], dict), _msg(
                        f"{path.name} 的 mcpServers.{name}.{key} 必须是对象", path
                    )
            for key in ("include_tools", "exclude_tools"):
                if key in raw:
                    assert isinstance(raw[key], list), _msg(
                        f"{path.name} 的 mcpServers.{name}.{key} 必须是数组", path
                    )
            if "requires_approval" in raw:
                assert isinstance(raw["requires_approval"], bool), _msg(
                    f"{path.name} 的 mcpServers.{name}.requires_approval 必须是布尔值", path
                )
            # 密钥不能明文进仓库：企业模板一律用 ${VAR}（加载时由 SecretStore 解析）。
            # headers 也必须扫——Authorization: Bearer <token> 是最常见的泄露位置，
            # 而且要用 search 而不是 match：明文 token 通常前面还有 "Bearer "。
            for section in ("env", "headers"):
                for key, value in (raw.get(section) or {}).items():
                    text = str(value)
                    assert not SECRET_LOOKALIKE_RE.search(text), _msg(
                        f"{path.name} 的 mcpServers.{name}.{section}.{key} 像是明文密钥",
                        path,
                        "改用 ${VAR} 引用（coworker/secrets.py 的 _REF = "
                        r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}，只认字母/下划线开头的 ASCII 名，"
                        "可以嵌在字符串中间，例如 \"Bearer ${CORP_TOKEN}\"），"
                        "值放 <state-dir>/.env 或进程环境。",
                    )
    assert server_files, _msg(
        "企业 MCP 模板里没有任何包含 mcpServers 的文件", MCP_DIR
    )


# ===========================================================================
# 6. 企业主题包存活（enterprise/branding/theme.css）
# ===========================================================================

@requires_enterprise
def test_enterprise_theme_css_covers_light_and_dark():
    """theme.css 同时覆盖 :root 与 html[data-theme="dark"]，且核心变量齐全。"""
    assert THEME_CSS.is_file(), _msg(
        "企业主题 enterprise/branding/theme.css 不存在", THEME_CSS
    )
    # 先剥注释：被注释掉的变量声明对浏览器无效，不能算「定制还在」
    css = _strip_css_comments(_read_text(THEME_CSS))
    light = _css_block(css, r":root\s*(?=\{)")
    assert light is not None, _msg(
        "theme.css 缺少 :root 亮色变量块", THEME_CSS
    )
    # 暗色选择器与 surfaces/gui/src/styles.css 一致：html[data-theme="dark"]
    # （data-theme 由 index.html 内联脚本在首帧前写到 <html> 上）
    dark = _css_block(css, r'html\s*\[\s*data-theme\s*=\s*["\']dark["\']\s*\]\s*(?=\{)')
    assert dark is not None, _msg(
        'theme.css 缺少 html[data-theme="dark"] 暗色变量块',
        THEME_CSS,
        "只有亮色的话，用户切到暗色会退回社区版配色。",
    )
    required_vars = _env_list("OPENWORKER_ENTERPRISE_THEME_VARS") or list(DEFAULT_THEME_VARS)
    for block_name, block in (("(:root 亮色)", light), ('(html[data-theme="dark"] 暗色)', dark)):
        missing = [v for v in required_vars if not re.search(rf"{re.escape(v)}\s*:", block)]
        assert not missing, _msg(
            f"theme.css {block_name} 块缺少核心变量（被删掉或被注释掉都算）：{missing}",
            THEME_CSS,
            "这些变量是 styles.css 的单一事实源，缺一项该处就回落到社区配色。"
            "注意 /* --accent: …; */ 这种注释掉的写法不生效，本用例已剥掉注释后再检查。",
        )


_THEME_IMPORT_RE = re.compile(
    r"""^.*?["'][^"'\n]*(?:branding|enterprise)[^"'\n]*theme\.css["'].*$""",
    re.M,
)
# 上游 main.tsx 的第 7 行：import "./styles.css";
_BASE_STYLES_IMPORT_RE = re.compile(r"""^.*?["']\./styles\.css["'].*$""", re.M)


@requires_enterprise
def test_enterprise_theme_css_is_mounted():
    """企业主题的挂载点（GUI 入口的 import 一行）仍在，**且排在 ./styles.css 之后**。

    顺序是硬要求，不是风格问题：两张样式表都在 ``:root`` 上声明同名变量，
    CSS 层叠里后加载者胜出。企业 import 被放到 ``./styles.css`` 之前时，
    文件在、import 也在、构建也过，但界面完全是社区版配色——比彻底丢失更难排查，
    所以这里必须断言相对位置，而不是只断言「出现过」。
    """
    mounts = _env_list("OPENWORKER_ENTERPRISE_THEME_MOUNT")
    candidates = (
        [_ROOT / m for m in mounts] if mounts else list(GUI_ENTRY_CANDIDATES)
    )
    checked: list[Path] = []
    for path in candidates:
        if not path.is_file():
            continue
        checked.append(path)
        text = _read_text(path)
        hit = _THEME_IMPORT_RE.search(text)
        if not hit:
            continue
        base = _BASE_STYLES_IMPORT_RE.search(text)
        # 同一个文件里两条 import 都在时才比较顺序；挂载点在 index.html 之类
        # 没有 ./styles.css 的文件里时，无从比较，只认「引用存在」。
        assert base is None or hit.start() > base.start(), _msg(
            f"{path.name} 里企业主题的 import 排在 `./styles.css` 之前",
            path,
            "后加载的样式表才能覆盖先加载的 :root 变量。请把 "
            'import "../../../enterprise/branding/theme.css"; 移到 import "./styles.css"; 之后。',
        )
        return
    pytest.fail(
        _msg(
            "GUI 入口没有引用企业主题 enterprise/branding/theme.css",
            "、".join(str(p) for p in checked) or str(GUI_ENTRY_CANDIDATES[0]),
            "主题文件还在，但没有被 import 就等于没换肤。"
            "可用 OPENWORKER_ENTERPRISE_THEME_MOUNT 指定挂载文件（相对仓库根，逗号分隔）。",
        )
    )
