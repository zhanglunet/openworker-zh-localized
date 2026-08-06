#!/usr/bin/env bash
#
# init-enterprise-repo.sh —— OpenWorker 企业定制版私有仓「一键初始化」脚本
#
# 三仓单向逐级同步链路：
#
#   andrewyng/openworker  (上游，公开)
#            │  sync-upstream.yml（已存在于汉化仓）
#            ▼
#   zhanglunet/openworker-zh-localized  (汉化版，公开)
#            │  sync-localized.yml（本脚本负责安装到企业仓）
#            ▼
#   <corp>/openworker-enterprise  (企业私有仓)
#
# 本脚本做的事：
#   1. 校验参数与运行环境；
#   2. 用 git clone --bare + git push --mirror 把汉化仓「带完整历史」镜像到企业私有仓；
#   3. 克隆企业私有仓，停用镜像时一并带过来的汉化仓工作流；
#   4. 创建 enterprise/ 定制目录骨架；
#   5. 生成 config / branding / mcp 四份可直接使用的模板；
#   6. 安装同步流水线 sync-localized.yml、企业发布流水线 release-corp.yml
#      与冒烟测试 test_enterprise_customization.py；
#   7. 打印必须人工完成的后续步骤清单。
#
# 设计原则：
#   - 严格模式（set -euo pipefail），任何一步失败立即退出；
#   - 幂等：已存在的目录/文件默认跳过，重复执行不会破坏已有定制（--force 才覆盖）；
#   - 所有破坏性动作（镜像推送、git push）执行前必须确认（--yes 可跳过）；
#   - -n/--dry-run 只打印将要执行的动作，不产生任何副作用、不访问网络；
#   - 打印与写入文件的仓库地址一律脱敏，避免把 https://user:token@host/... 里的
#     PAT 写进 CI 日志和版本库。
#
# 依赖：bash 4+、git 2.20+（推荐 2.23+，同步流水线用到 git switch）；python3 可选。
#
set -euo pipefail

# bash 版本硬门槛：脚本用到 ${var^^}（大小写转换，bash 4.0 起）。
# macOS 自带的是 bash 3.2，用 /bin/bash 直接跑会在派生环境变量名时静默出错，
# 所以这里提前拦掉，并给出可执行的修复建议。
if [ -z "${BASH_VERSINFO[0]:-}" ] || [ "${BASH_VERSINFO[0]}" -lt 4 ]; then
  printf '[错误] 需要 bash 4.0 及以上（当前 %s）。\n' "${BASH_VERSION:-未知}" >&2
  printf '       macOS 自带 bash 3.2，请先 brew install bash，然后用 /opt/homebrew/bin/bash 运行本脚本。\n' >&2
  exit 1
fi

# 不要让路径里的空格被词分割；换行保留为唯一分隔符。
IFS=$'\n\t'

# ---------------------------------------------------------------------------
# 常量
# ---------------------------------------------------------------------------

SCRIPT_NAME="$(basename "${BASH_SOURCE[0]}")"
# 本脚本所在目录 —— 同一目录下应当放着 sync-localized.yml 与
# test_enterprise_customization.py 两个模板文件（由企业模板包一并分发）。
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"

# 默认的上游汉化仓地址（第二级源）。
readonly DEFAULT_LOCALIZED_URL="https://github.com/zhanglunet/openworker-zh-localized.git"

# git 最低版本 / 推荐版本。
readonly GIT_MIN_VERSION="2.20"
readonly GIT_RECOMMENDED_VERSION="2.23"

# enterprise/ 下的八个定制子目录（与《企业定制版方案》一致，不要随意增删）。
readonly ENTERPRISE_DIRS=(
  skills
  branding
  config
  mcp
  connectors
  tools
  tests
  site
)

# 从汉化仓镜像过来、在企业私有仓里**必须停用**的工作流。
#
# 这批文件是 git push --mirror 的必然副产物：镜像带的是完整历史，
# .github/workflows/ 下汉化仓自己的流水线会原样落进企业仓，然后按各自的 cron / tag 触发。
# 其中 sync-upstream.yml 最危险 —— 它每天 01:35 UTC 直接 fetch andrewyng/openworker 并
# 往企业仓开 sync/upstream-main PR，等于**跳过汉化层**，把"逐级单向同步"变成两条并行链路，
# 还会和 sync-localized.yml 抢同一个 main。
#
# 停用方式是改名加 .disabled 后缀（GitHub 只识别 .github/workflows 下的 .yml/.yaml）：
#   - 文件仍在版本库里，同步时 git 的改名检测能把上游对原文件的修改合进来，
#     不会像 delete 那样每次都产生 modify/delete 冲突；
#   - 需要参考原内容时随手就能看到，不必翻历史。
readonly INHERITED_WORKFLOWS=(
  sync-upstream.yml
  update-site-reports.yml
  deploy-site.yml
  release.yml
  prerelease.yml
  build-windows.yml
)

# 每个被停用工作流的停用理由（打印给人看，也写进后续步骤清单）。
workflow_reason() {
  case "$1" in
    sync-upstream.yml)
      printf '每日直接从 andrewyng/openworker 同步，会绕过汉化层并与 sync-localized.yml 抢 main' ;;
    update-site-reports.yml)
      printf '每周定时以 contents:write 直接 push 回 main，改的是汉化站的生成产物' ;;
    deploy-site.yml)
      printf '把 website/ 部署到汉化版公开站 oaosf.cn（Cloudflare），企业内容不能走这条路' ;;
    release.yml)
      printf '监听 v* / app-v* tag，产出汉化版品牌的安装包与 latest-zh.json；企业发布用 release-corp.yml（corp-v* tag）' ;;
    prerelease.yml)
      printf '监听 beta-v* tag，产出汉化版未签名测试版' ;;
    build-windows.yml)
      printf '监听 win-* tag，产出汉化版 Windows 包' ;;
    *)
      printf '汉化仓专用流水线，企业仓不需要' ;;
  esac
}

# ---------------------------------------------------------------------------
# 全局变量（默认值 → 环境变量 → 命令行参数，后者优先）
# ---------------------------------------------------------------------------

CORP_ID="${CORP_ID:-}"                              # 企业标识，如 acme
CORP_NAME="${CORP_NAME:-}"                          # 企业中文名，如 「艾克米科技」
ENTERPRISE_URL="${ENTERPRISE_REPO_URL:-}"           # 企业私有仓 git 地址
LOCALIZED_URL="${LOCALIZED_REPO_URL:-$DEFAULT_LOCALIZED_URL}"
WORKDIR="${WORKDIR:-$PWD}"                          # 在哪里落地克隆出来的工作副本
TEMPLATE_DIR="${TEMPLATE_DIR:-$SCRIPT_DIR}"         # 模板文件（yml / py）来源目录

# 由 CORP_ID 派生、写进模板的环境变量前缀 / Python 包名前缀（validate_args 里计算）。
CORP_ENV=""
CORP_PKG=""
# 脱敏后的仓库地址（validate_args 里计算）：打印和写文件一律用这两个。
ENTERPRISE_URL_SAFE=""
LOCALIZED_URL_SAFE=""
# 从企业仓地址推导出来的本地目录名与完整路径（validate_args 里计算）。
REPO_BASENAME=""
TARGET_DIR=""

DRY_RUN=0        # -n/--dry-run
ASSUME_YES=0     # -y/--yes：跳过所有交互确认
FORCE=0          # --force：覆盖已存在的模板文件
SKIP_MIRROR=0    # --skip-mirror：企业私有仓已有内容时跳过镜像步骤
NO_PUSH=0        # --no-push：只在本地提交，不推送
KEEP_INHERITED=0 # --keep-inherited-workflows：保留镜像带过来的汉化仓工作流（不推荐）

# 本次运行「实际写出」的文件绝对路径。提交时只 git add 这些路径 ——
# 不要用 `git add enterprise`，否则重跑脚本会把用户正在改的定制文件
# 一起裹进「初始化骨架」这个提交里，提交信息与内容对不上。
CREATED_PATHS=()

# ---------------------------------------------------------------------------
# 输出helpers（尊重 NO_COLOR，非终端时自动去色）
# ---------------------------------------------------------------------------

if [[ -t 1 && -z "${NO_COLOR:-}" ]]; then
  C_RESET=$'\033[0m'; C_BOLD=$'\033[1m'; C_DIM=$'\033[2m'
  C_RED=$'\033[31m'; C_GREEN=$'\033[32m'; C_YELLOW=$'\033[33m'; C_BLUE=$'\033[34m'
else
  C_RESET=''; C_BOLD=''; C_DIM=''
  C_RED=''; C_GREEN=''; C_YELLOW=''; C_BLUE=''
fi

log()   { printf '%s\n' "$*"; }
info()  { printf '%s[信息]%s %s\n' "$C_BLUE"   "$C_RESET" "$*"; }
ok()    { printf '%s[完成]%s %s\n' "$C_GREEN"  "$C_RESET" "$*"; }
warn()  { printf '%s[警告]%s %s\n' "$C_YELLOW" "$C_RESET" "$*" >&2; }
die()   { printf '%s[错误]%s %s\n' "$C_RED"    "$C_RESET" "$*" >&2; exit 1; }
step()  { printf '\n%s==> %s%s\n' "$C_BOLD" "$*" "$C_RESET"; }
skip()  { printf '%s     跳过：%s%s\n' "$C_DIM" "$*" "$C_RESET"; }

# dry-run 下统一的动作前缀。
dry_note() { printf '%s     [dry-run] %s%s\n' "$C_DIM" "$*" "$C_RESET"; }

# ---------------------------------------------------------------------------
# 用法
# ---------------------------------------------------------------------------

usage() {
  cat <<USAGE
${SCRIPT_NAME} —— 初始化 OpenWorker 企业定制版私有仓

用法：
  ${SCRIPT_NAME} --corp <企业标识> --name <企业中文名> --repo <私有仓git地址> [选项]

必填参数（也可用同名环境变量提供）：
  -c, --corp <id>         企业标识，只允许小写字母/数字/连字符，如 acme
                          （环境变量 CORP_ID）
                          该值会成为技能名前缀、模型路由 id 前缀、配置文件名的一部分，
                          必须满足技能名规则 ^[A-Za-z0-9][A-Za-z0-9._-]*\$
  -N, --name <中文名>     企业中文名，用于品牌文案，如 艾克米科技
                          （环境变量 CORP_NAME）
  -r, --repo <url>        企业私有仓 git 地址（必须是「已创建但为空」的仓库）
                          （环境变量 ENTERPRISE_REPO_URL）

可选参数：
  -u, --upstream <url>    上游汉化仓地址
                          默认：${DEFAULT_LOCALIZED_URL}
                          （环境变量 LOCALIZED_REPO_URL）
  -d, --workdir <dir>     工作目录，企业仓会克隆到 <dir>/<repo名>
                          默认：当前目录（环境变量 WORKDIR）
  -t, --templates <dir>   模板文件目录，需包含 sync-localized.yml、release-corp.yml
                          与 test_enterprise_customization.py
                          默认：脚本所在目录（环境变量 TEMPLATE_DIR）

行为开关：
  -n, --dry-run           只打印将要执行的动作，不写文件、不访问网络
  -y, --yes               跳过所有交互确认（用于 CI；请确认参数无误）
      --force             覆盖已存在的模板文件（默认保留已有定制）
      --skip-mirror       跳过镜像步骤（企业私有仓已经有内容时使用）
      --no-push           只在本地创建提交，不执行 git push
      --keep-inherited-workflows
                          保留镜像带过来的汉化仓工作流（sync-upstream.yml 等）。
                          ${C_BOLD}不推荐${C_RESET}：sync-upstream.yml 会每天绕过汉化层
                          直接从上游同步，与 sync-localized.yml 抢同一个 main。
  -h, --help              显示本帮助

示例：
  # 首次初始化（会提示确认镜像推送）
  ./${SCRIPT_NAME} -c acme -N 艾克米科技 \\
      -r git@github.com:acme/openworker-enterprise.git

  # 先空跑一遍看看会做什么
  ./${SCRIPT_NAME} -c acme -N 艾克米科技 \\
      -r git@github.com:acme/openworker-enterprise.git --dry-run

  # 私有仓已镜像过，只补 enterprise/ 骨架与流水线
  ./${SCRIPT_NAME} -c acme -N 艾克米科技 \\
      -r git@github.com:acme/openworker-enterprise.git --skip-mirror
USAGE
}

# ---------------------------------------------------------------------------
# 参数解析
# ---------------------------------------------------------------------------

parse_args() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      -c|--corp)      [[ $# -ge 2 ]] || die "$1 需要一个参数"; CORP_ID="$2";        shift 2 ;;
      -N|--name)      [[ $# -ge 2 ]] || die "$1 需要一个参数"; CORP_NAME="$2";      shift 2 ;;
      -r|--repo)      [[ $# -ge 2 ]] || die "$1 需要一个参数"; ENTERPRISE_URL="$2"; shift 2 ;;
      -u|--upstream)  [[ $# -ge 2 ]] || die "$1 需要一个参数"; LOCALIZED_URL="$2";  shift 2 ;;
      -d|--workdir)   [[ $# -ge 2 ]] || die "$1 需要一个参数"; WORKDIR="$2";        shift 2 ;;
      -t|--templates) [[ $# -ge 2 ]] || die "$1 需要一个参数"; TEMPLATE_DIR="$2";   shift 2 ;;
      --corp=*)       CORP_ID="${1#*=}";        shift ;;
      --name=*)       CORP_NAME="${1#*=}";      shift ;;
      --repo=*)       ENTERPRISE_URL="${1#*=}"; shift ;;
      --upstream=*)   LOCALIZED_URL="${1#*=}";  shift ;;
      --workdir=*)    WORKDIR="${1#*=}";        shift ;;
      --templates=*)  TEMPLATE_DIR="${1#*=}";   shift ;;
      -n|--dry-run)   DRY_RUN=1;     shift ;;
      -y|--yes)       ASSUME_YES=1;  shift ;;
      --force)        FORCE=1;       shift ;;
      --skip-mirror)  SKIP_MIRROR=1; shift ;;
      --no-push)      NO_PUSH=1;     shift ;;
      --keep-inherited-workflows) KEEP_INHERITED=1; shift ;;
      -h|--help)      usage; exit 0 ;;
      --)             shift; break ;;
      -*)             usage >&2; die "未知选项：$1" ;;
      *)              usage >&2; die "多余的位置参数：$1" ;;
    esac
  done
}

# ---------------------------------------------------------------------------
# 参数校验
# ---------------------------------------------------------------------------

# redact_url <git地址> —— 抹掉 URL 里的用户名/口令。
#
# 企业仓地址经常写成 https://x-access-token:<PAT>@github.com/acme/openworker-enterprise.git
# （CI 里几乎一定是这种形态）。这个字符串会被打印到标准输出（= Actions 日志），
# 还会被 render 写进 enterprise/README.md 然后 commit + push ——
# 不脱敏就等于把 PAT 永久写进版本库。所有对外呈现一律走这个函数。
redact_url() {
  local url="$1" scheme rest authority
  case "$url" in
    *://*) scheme="${url%%://*}"; rest="${url#*://}" ;;
    *)     printf '%s' "$url"; return 0 ;;   # git@host:path 形态不含口令，原样返回
  esac
  authority="${rest%%/*}"                     # 第一个 / 之前的部分：[userinfo@]host[:port]
  case "$authority" in
    *@*) printf '%s://***@%s' "$scheme" "${rest#*@}" ;;
    *)   printf '%s' "$url" ;;
  esac
}

# normalize_url <git地址> —— 去掉尾部 / 与 .git，用于"两个地址是不是同一个仓"的比较。
normalize_url() {
  local url="${1%/}"
  printf '%s' "${url%.git}"
}

validate_args() {
  [[ -n "$CORP_ID" ]]        || { usage >&2; die "缺少企业标识（-c/--corp 或 CORP_ID）"; }
  [[ -n "$CORP_NAME" ]]      || { usage >&2; die "缺少企业中文名（-N/--name 或 CORP_NAME）"; }
  [[ -n "$ENTERPRISE_URL" ]] || { usage >&2; die "缺少私有仓地址（-r/--repo 或 ENTERPRISE_REPO_URL）"; }

  # 企业标识会直接拼进技能目录名（<state-dir>/skills/<name>/SKILL.md）与模型路由 id
  # （custom:<corp>-chat）。技能名在 coworker/skills/store.py 里由
  # _NAME_RE = ^[A-Za-z0-9][A-Za-z0-9._-]*$ 校验，长度上限 64，且不允许 .. / \。
  # 这里收得更紧（只要小写字母、数字、连字符），保证在文件名、URL、包名里都安全。
  if [[ ! "$CORP_ID" =~ ^[a-z0-9][a-z0-9-]*$ ]]; then
    die "企业标识 '${CORP_ID}' 非法：只允许小写字母、数字、连字符，且必须以字母或数字开头。"
  fi
  if (( ${#CORP_ID} > 32 )); then
    die "企业标识过长（${#CORP_ID} 字符）：技能名上限 64，留出前缀空间请控制在 32 以内。"
  fi

  # 由企业标识派生「环境变量前缀」。
  #
  # 模板（尤其 mcp.example.json）里要写 ${XXX_KB_TOKEN} 这种引用，由
  # coworker/secrets.py 的 SecretStore 在加载时解析，其正则是
  #     _REF = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")
  # —— 连字符不匹配，数字开头也不匹配。而 CORP_ID 本身是允许 acme-cn / 3m 这种写法的，
  # 直接拼就会得到 ${acme-cn_KB_TOKEN} / ${3m_KB_TOKEN}：SecretStore 认不出来，
  # 于是**原样**把 "Bearer ${acme-cn_ITSM_TOKEN}" 发给 MCP 服务器，且全程不报错，
  # 只表现为一个莫名其妙的 401。所以这里统一转成合法标识符：大写 + 连字符转下划线 +
  # 数字开头时加前缀。
  CORP_ENV="${CORP_ID//-/_}"
  CORP_ENV="${CORP_ENV^^}"
  if [[ "$CORP_ENV" =~ ^[0-9] ]]; then
    CORP_ENV="CORP_${CORP_ENV}"
  fi
  # 同一个标识符的小写形态，用于 Python 包名（模块名不能含连字符、不能数字开头）。
  CORP_PKG="${CORP_ENV,,}"

  # 仓库地址只做形态检查，真正的可达性交给 git（避免误判企业内网 GitLab / GHE）。
  case "$ENTERPRISE_URL" in
    http://*|https://*|ssh://*|git://*|*@*:*|/*|file://*) : ;;
    *) die "私有仓地址 '$(redact_url "$ENTERPRISE_URL")' 看起来不像 git 地址（https:// / ssh:// / git@host:path / 本地路径）。" ;;
  esac
  case "$LOCALIZED_URL" in
    http://*|https://*|ssh://*|git://*|*@*:*|/*|file://*) : ;;
    *) die "汉化仓地址 '$(redact_url "$LOCALIZED_URL")' 看起来不像 git 地址。" ;;
  esac

  # 比较前先归一化：https://host/a/b 和 https://host/a/b.git 是同一个仓，
  # 逐字比较会漏掉这种写法，让脚本在后面 git push --mirror / git push origin main
  # 时把企业骨架推进**公开**的汉化仓。
  if [[ "$(normalize_url "$ENTERPRISE_URL")" == "$(normalize_url "$LOCALIZED_URL")" ]]; then
    die "私有仓地址和汉化仓地址指向同一个仓库 —— 这会把上游公开仓当成推送目标，已阻止。"
  fi

  ENTERPRISE_URL_SAFE="$(redact_url "$ENTERPRISE_URL")"
  LOCALIZED_URL_SAFE="$(redact_url "$LOCALIZED_URL")"

  # 从地址推导本地目录名：去掉尾部 .git 与路径前缀。
  REPO_BASENAME="$(basename -- "$(normalize_url "$ENTERPRISE_URL")")"
  [[ -n "$REPO_BASENAME" ]] || die "无法从 '${ENTERPRISE_URL_SAFE}' 推导仓库名。"
  TARGET_DIR="${WORKDIR%/}/${REPO_BASENAME}"
}

# ---------------------------------------------------------------------------
# 前置检查
# ---------------------------------------------------------------------------

# 语义化版本比较：version_ge <a> <b> —— a >= b 时返回 0。
version_ge() {
  [[ "$(printf '%s\n%s\n' "$2" "$1" | sort -V | head -n1)" == "$2" ]]
}

preflight() {
  step "前置检查"

  # --- 必需命令 ---
  local missing=()
  local cmd
  for cmd in git basename dirname sort; do
    command -v "$cmd" >/dev/null 2>&1 || missing+=("$cmd")
  done
  if (( ${#missing[@]} > 0 )); then
    die "缺少必需命令：${missing[*]}"
  fi

  # --- git 版本 ---
  local git_version
  git_version="$(git --version | awk '{print $3}')"
  if ! version_ge "$git_version" "$GIT_MIN_VERSION"; then
    die "git 版本过低（当前 ${git_version}，最低要求 ${GIT_MIN_VERSION}）。"
  fi
  if ! version_ge "$git_version" "$GIT_RECOMMENDED_VERSION"; then
    warn "git ${git_version} 可用，但同步流水线 sync-localized.yml 使用了 git switch（需 ${GIT_RECOMMENDED_VERSION}+）。建议升级。"
  else
    ok "git ${git_version}"
  fi

  # --- python3（可选，仅用于本地跑 enterprise 冒烟测试）---
  if command -v python3 >/dev/null 2>&1; then
    ok "python3 $(python3 --version 2>&1 | awk '{print $2}')（可本地运行 enterprise/tests 冒烟测试）"
  else
    warn "未检测到 python3：enterprise/tests/test_enterprise_customization.py 只能在 CI 里跑。"
  fi

  # --- 目标目录 ---
  if [[ -e "$TARGET_DIR" ]]; then
    if [[ -d "$TARGET_DIR/.git" ]]; then
      info "目标目录已存在且是 git 仓库：${TARGET_DIR}（将复用，不重新克隆）"
    else
      die "目标目录已存在但不是 git 仓库：${TARGET_DIR}
请换一个 --workdir，或先手动清理该目录。"
    fi
  else
    if [[ ! -d "$WORKDIR" ]]; then
      info "工作目录 ${WORKDIR} 不存在，将创建。"
    fi
  fi

  # --- 模板目录 ---
  local f
  for f in sync-localized.yml release-corp.yml test_enterprise_customization.py; do
    if [[ -f "${TEMPLATE_DIR%/}/$f" ]]; then
      ok "找到模板 ${f}"
    else
      warn "模板目录缺少 ${f}（${TEMPLATE_DIR%/}/${f}）—— 该文件将跳过安装，稍后请手工放置。"
    fi
  done
}

# ---------------------------------------------------------------------------
# 交互确认 / 命令执行封装
# ---------------------------------------------------------------------------

# confirm <提示语> —— 用户回答 y/yes 才返回 0。--yes 直接通过；dry-run 直接通过（反正不执行）。
confirm() {
  local prompt="$1"
  if (( ASSUME_YES )) || (( DRY_RUN )); then
    return 0
  fi
  if [[ ! -t 0 ]]; then
    die "需要确认「${prompt}」但标准输入不是终端。请加 -y/--yes（确认参数无误后）或在终端里运行。"
  fi
  local reply=""
  printf '%s%s%s [y/N] ' "$C_BOLD" "$prompt" "$C_RESET"
  read -r reply || reply=""
  case "$reply" in
    y|Y|yes|YES|Yes) return 0 ;;
    *) return 1 ;;
  esac
}

# run <命令...> —— dry-run 下只打印。
run() {
  if (( DRY_RUN )); then
    dry_note "$*"
    return 0
  fi
  "$@"
}

# ---------------------------------------------------------------------------
# 文件生成 helpers
# ---------------------------------------------------------------------------

# render —— 从 stdin 读模板文本，把 @@XXX@@ 占位符替换成实际值后写到 stdout。
# 用占位符而不是 shell 变量插值，是为了让模板可以安全地使用 ${VAR}、反引号、$( ) 等字面量
# （mcp.example.json 里的 ${VAR} 必须原样保留，交给 coworker/secrets.py 在读取时解析）。
render() {
  local content
  content="$(cat)"
  content="${content//@@CORP_ID@@/$CORP_ID}"
  content="${content//@@CORP_ENV@@/$CORP_ENV}"
  content="${content//@@CORP_PKG@@/$CORP_PKG}"
  content="${content//@@CORP_NAME@@/$CORP_NAME}"
  # 写进文件的一律是脱敏地址：这些文件会被 commit + push，
  # 带 PAT 的原始地址一旦进版本库就等于泄密。
  content="${content//@@LOCALIZED_URL@@/$LOCALIZED_URL_SAFE}"
  content="${content//@@ENTERPRISE_URL@@/$ENTERPRISE_URL_SAFE}"
  printf '%s\n' "$content"
}

# write_file <路径> <内容> —— 已存在且未 --force 时跳过（幂等）。
#
# 内容必须走**参数**而不是 stdin：如果写成 `... | render | write_file path`，
# write_file 就成了管道的一环，会在**子 shell** 里执行，
# 函数里对 CREATED_PATHS 的追加会随子 shell 一起消失（提交时就漏文件了）。
# 调用方请写成 write_file "$path" "$(emit_xxx | render)"。
write_file() {
  local path="$1"
  local content="$2"
  local rel="${path#"$TARGET_DIR"/}"

  if [[ -e "$path" ]] && (( ! FORCE )); then
    skip "${rel}（已存在，用 --force 覆盖）"
    return 0
  fi

  if (( DRY_RUN )); then
    local bytes
    if [[ -n "$content" ]]; then
      bytes="$(printf '%s\n' "$content" | wc -c | tr -d ' ')"
    else
      bytes=0
    fi
    dry_note "写入 ${rel}（${bytes} 字节）"
    return 0
  fi

  mkdir -p -- "$(dirname -- "$path")"
  if [[ -n "$content" ]]; then
    printf '%s\n' "$content" > "$path"
  else
    : > "$path"        # .gitkeep 这类空占位文件
  fi
  CREATED_PATHS+=("$path")
  ok "写入 ${rel}"
}

# copy_template <模板文件名> <目标绝对路径>
copy_template() {
  local src="${TEMPLATE_DIR%/}/$1"
  local dest="$2"
  local rel="${dest#"$TARGET_DIR"/}"

  if [[ ! -f "$src" ]]; then
    warn "模板缺失：${src}
     → 请手工把 $1 复制到 ${rel}（内容见企业模板包）。"
    return 0
  fi
  if [[ -e "$dest" ]] && (( ! FORCE )); then
    skip "${rel}（已存在，用 --force 覆盖）"
    return 0
  fi
  if (( DRY_RUN )); then
    dry_note "复制 ${src} → ${rel}"
    return 0
  fi
  mkdir -p -- "$(dirname -- "$dest")"
  cp -- "$src" "$dest"
  CREATED_PATHS+=("$dest")
  ok "安装 ${rel}"
}

# copy_template_dir <模板目录名> <目标绝对目录>
# 与 copy_template 同语义，只是整目录复制（技能包这类多文件模板要用它）。
copy_template_dir() {
  local src="${TEMPLATE_DIR%/}/$1"
  local dest="$2"
  local rel="${dest#"$TARGET_DIR"/}"

  if [[ ! -d "$src" ]]; then
    warn "模板目录缺失：${src}
     → 请手工把 $1/ 复制到 ${rel}/（内容见企业模板包）。"
    return 0
  fi
  if [[ -e "$dest" ]] && (( ! FORCE )); then
    skip "${rel}/（已存在，用 --force 覆盖）"
    return 0
  fi
  if (( DRY_RUN )); then
    dry_note "复制目录 ${src}/ → ${rel}/"
    return 0
  fi
  mkdir -p -- "$(dirname -- "$dest")"
  # 尾部斜杠 + /. 保证复制的是目录内容而非嵌一层同名目录
  cp -R -- "$src/." "$dest"
  CREATED_PATHS+=("$dest")
  ok "安装 ${rel}/"
}

# ---------------------------------------------------------------------------
# 第 1 步：把汉化仓完整镜像到企业私有仓
# ---------------------------------------------------------------------------
#
# 为什么必须用 git clone --bare + git push --mirror，而不能用
# GitHub 网页的 "Import repository" 或下载 zip / Download ZIP 源码包？
#
#   * zip / Download ZIP / release tarball 里根本没有 .git 目录 —— 历史全丢。
#     之后企业仓和汉化仓就没有任何「共同祖先」（merge base）。
#     再执行 `git merge localized/main` 时，git 只能退化成把两棵毫无关系的树硬拼，
#     结果是「几乎每个文件都冲突」，同步流水线彻底失效。
#
#   * GitHub 网页版 Import 虽然能带历史，但：
#       - 只能对「新建的空仓库」做一次性导入，无法用于已存在的仓库；
#       - 企业自建的 GitLab / Gitea / GitHub Enterprise 未必提供同等功能；
#       - 导入过程不可脚本化、不可复现、无法在 CI 里重跑。
#
#   * `git clone --bare` 会把汉化仓所有分支（refs/heads/*）和标签（refs/tags/*）
#     完整取到本地裸仓库；`git push --mirror` 再把这些 ref 原样推到企业私有仓，
#     commit SHA 一字不改 —— 于是两仓天然共享全部历史，merge base 存在，
#     后续每次同步只需要处理真正的增量。
#
#   * 注意不用 `git clone --mirror`：它会连 refs/pull/*、refs/notes/* 一起带过来，
#     企业仓并不需要上游的 PR ref，徒增体积也容易触发 push 限制。
#
# 危险性提示：`git push --mirror` 会让远端 ref 与本地「完全一致」——
# 远端有而本地没有的分支/标签会被删除。所以下面先用 git ls-remote 确认目标仓为空。
#
# 裸克隆用的临时目录（供 EXIT trap 清理）。
MIRROR_TMP_ROOT=""
cleanup_mirror_tmp() {
  # 用「函数 + 全局变量」而不是把路径拼进 trap 字符串：
  # trap "rm -rf -- '<路径>'" 的路径里只要出现一个单引号，整条 trap 就会被拆成别的命令。
  if [[ -n "$MIRROR_TMP_ROOT" && -d "$MIRROR_TMP_ROOT" ]]; then
    rm -rf -- "$MIRROR_TMP_ROOT"
  fi
  MIRROR_TMP_ROOT=""
}

step_mirror() {
  step "第 1 步：镜像汉化仓 → 企业私有仓（保留完整历史与共同祖先）"

  if (( SKIP_MIRROR )); then
    skip "已指定 --skip-mirror"
    return 0
  fi

  # 检查目标仓是否为空。空仓 ls-remote 输出为空。
  local remote_refs=""
  if (( DRY_RUN )); then
    dry_note "git ls-remote --heads --tags ${ENTERPRISE_URL_SAFE}"
  else
    info "探测企业私有仓是否为空：${ENTERPRISE_URL_SAFE}"
    if ! remote_refs="$(git ls-remote --heads --tags "$ENTERPRISE_URL" 2>&1)"; then
      # git 的报错里会回显它试过的 URL（含口令），所以这里也要过一遍脱敏。
      die "无法访问企业私有仓：${ENTERPRISE_URL_SAFE}
请确认：仓库已创建、你有写权限、SSH key / PAT 已配置。
原始错误：
$(printf '%s' "$remote_refs" | sed -E 's#(://)[^/@[:space:]]+@#\1***@#g')"
    fi
    if [[ -n "$remote_refs" ]]; then
      warn "企业私有仓已经有内容（$(printf '%s\n' "$remote_refs" | wc -l | tr -d ' ') 个 ref）。"
      warn "git push --mirror 会删除远端上本地不存在的分支和标签 —— 这一步已自动跳过。"
      warn "如果确认要重新镜像，请先备份，再手动执行：
       git clone --bare ${LOCALIZED_URL_SAFE} /tmp/ow-mirror.git
       git -C /tmp/ow-mirror.git push --mirror ${ENTERPRISE_URL_SAFE}"
      SKIP_MIRROR=1
      return 0
    fi
    ok "企业私有仓为空，可以安全镜像。"
  fi

  if ! confirm "确认把 ${LOCALIZED_URL_SAFE} 完整镜像推送到 ${ENTERPRISE_URL_SAFE} ？"; then
    die "用户取消。可加 --skip-mirror 只做后续步骤。"
  fi

  # 裸克隆放到临时目录，退出时清理。
  local bare_dir
  if (( DRY_RUN )); then
    bare_dir="<临时目录>/openworker-zh-localized.git"
    dry_note "git clone --bare ${LOCALIZED_URL_SAFE} ${bare_dir}"
    dry_note "git -C ${bare_dir} push --mirror ${ENTERPRISE_URL_SAFE}"
    dry_note "rm -rf ${bare_dir}"
    return 0
  fi

  MIRROR_TMP_ROOT="$(mktemp -d)"
  bare_dir="$MIRROR_TMP_ROOT/openworker-zh-localized.git"
  trap cleanup_mirror_tmp EXIT

  info "裸克隆汉化仓（含全部分支与标签）…"
  git clone --bare "$LOCALIZED_URL" "$bare_dir"

  info "镜像推送到企业私有仓…"
  git -C "$bare_dir" push --mirror "$ENTERPRISE_URL"

  cleanup_mirror_tmp
  trap - EXIT
  ok "镜像完成：企业私有仓现在与汉化仓共享完整历史。"
}

# ---------------------------------------------------------------------------
# 第 2 步：克隆企业私有仓工作副本
# ---------------------------------------------------------------------------

step_clone() {
  step "第 2 步：克隆企业私有仓工作副本"

  if [[ -d "$TARGET_DIR/.git" ]]; then
    skip "${TARGET_DIR} 已是 git 仓库，复用现有工作副本"
    return 0
  fi

  if (( DRY_RUN )); then
    dry_note "mkdir -p ${WORKDIR}"
    dry_note "git clone ${ENTERPRISE_URL_SAFE} ${TARGET_DIR}"
    return 0
  fi

  mkdir -p -- "$WORKDIR"
  git clone "$ENTERPRISE_URL" "$TARGET_DIR"
  ok "已克隆到 ${TARGET_DIR}"
}

# 当前分支名（dry-run 下返回占位符）。
#
# 必须先试 symbolic-ref：企业仓还是空仓时（--skip-mirror 场景）HEAD 指向一个
# 尚未诞生的分支，`git rev-parse --abbrev-ref HEAD` 会往 **stdout** 打一个字面量
# "HEAD" 然后以 128 退出 —— 老写法 `... || printf 'main'` 会把两段拼成 "HEAD\nmain"，
# 后面的 `git push origin "$branch"` 必然失败，报错信息还完全看不懂。
# symbolic-ref 在未诞生分支上照样返回正确的分支名。
current_branch() {
  if (( DRY_RUN )) || [[ ! -d "$TARGET_DIR/.git" ]]; then
    printf 'main'
    return 0
  fi
  local b=""
  if b="$(git -C "$TARGET_DIR" symbolic-ref --quiet --short HEAD 2>/dev/null)" && [[ -n "$b" ]]; then
    printf '%s' "$b"
    return 0
  fi
  # detached HEAD：rev-parse 会返回字面量 "HEAD"，此时没有可推送的分支名，退回 main。
  if b="$(git -C "$TARGET_DIR" rev-parse --abbrev-ref HEAD 2>/dev/null)" \
     && [[ -n "$b" && "$b" != "HEAD" ]]; then
    printf '%s' "$b"
    return 0
  fi
  printf 'main'
}

# ---------------------------------------------------------------------------
# 第 3 步：停用镜像带过来的汉化仓工作流
# ---------------------------------------------------------------------------
#
# git push --mirror 是「完整历史 + 全部文件」，所以汉化仓 .github/workflows/ 下的
# 每一条流水线都会原样出现在企业私有仓，并按各自的 cron / tag 自动开始跑。
# 其中至少有四条在企业仓里是**有害**的（详见 INHERITED_WORKFLOWS 的注释）：
#   · sync-upstream.yml       每天绕过汉化层直接从 andrewyng/openworker 同步
#   · update-site-reports.yml 定时以 contents:write 直接 push 回 main
#   · deploy-site.yml         把内容部署到汉化版的公开站点
#   · release.yml / prerelease.yml / build-windows.yml
#                             用汉化版品牌和汉化版更新清单发包
#
# 停用 = 加 .disabled 后缀（GitHub 只把 .github/workflows 下的 .yml/.yaml 当工作流）。
# 用 git mv 而不是 rm：改名后 git 的 rename detection 能在后续同步里把上游对原文件的
# 修改合进重命名后的文件；删除则会每次都变成 modify/delete 冲突。
#
step_prune_workflows() {
  step "第 3 步：停用镜像带过来的汉化仓工作流"

  if (( KEEP_INHERITED )); then
    warn "已指定 --keep-inherited-workflows：sync-upstream.yml 会继续每天从上游直接同步，
     与 sync-localized.yml 争抢 main。请自行在 GitHub 的 Actions 页面禁用它们。"
    return 0
  fi

  local wf src dest rel
  for wf in "${INHERITED_WORKFLOWS[@]}"; do
    src="$TARGET_DIR/.github/workflows/${wf}"
    dest="${src}.disabled"
    rel=".github/workflows/${wf}"

    if [[ ! -f "$src" ]]; then
      if [[ -f "$dest" ]]; then
        skip "${rel}（已停用）"
      fi
      continue
    fi

    if (( DRY_RUN )); then
      dry_note "git mv ${rel} ${rel}.disabled  # $(workflow_reason "$wf")"
      continue
    fi

    if [[ -e "$dest" ]] && (( ! FORCE )); then
      skip "${rel}.disabled 已存在（用 --force 覆盖）"
      continue
    fi

    # git mv 会顺带把改名登记进索引；仓库异常时退回普通 mv，由后面的 git add 兜底。
    if ! git -C "$TARGET_DIR" mv -f -- "$rel" "${rel}.disabled" 2>/dev/null; then
      mv -f -- "$src" "$dest"
    fi
    CREATED_PATHS+=("$dest")
    ok "停用 ${rel} → ${wf}.disabled（$(workflow_reason "$wf")）"
  done
}

# ---------------------------------------------------------------------------
# 第 4 步：创建 enterprise/ 目录骨架
# ---------------------------------------------------------------------------

# 每个子目录的一句话用途（写进各自的 README.md）。
dir_purpose() {
  case "$1" in
    skills)     printf '企业专属技能包（SKILL.md）' ;;
    branding)   printf '品牌资产：主题变量、图标、文案' ;;
    config)     printf '默认配置模板（config.toml）' ;;
    mcp)        printf 'MCP 服务器配置模板（mcp.json）' ;;
    connectors) printf '企业内部系统连接器' ;;
    tools)      printf '企业专属工具（注册进 ToolRegistry）' ;;
    tests)      printf '企业定制的冒烟测试' ;;
    site)       printf '企业内网站点 / 文档发布物' ;;
    *)          printf '企业定制内容' ;;
  esac
}

# 每个子目录 README.md 的正文（含真实路径与键名）。
dir_readme_body() {
  case "$1" in
    skills)
      cat <<'MD'
## 放什么

企业专属技能，每个技能一个子目录，目录内必须有 `SKILL.md`：

```
enterprise/skills/@@CORP_ID@@-expense/SKILL.md
enterprise/skills/@@CORP_ID@@-onboarding/SKILL.md
```

## 技能名规则（硬约束）

技能名即目录名，由 `coworker/skills/store.py` 的
`_NAME_RE = ^[A-Za-z0-9][A-Za-z0-9._-]*$` 校验，长度上限 64，
且不允许出现 `..`、`/`、`\`。

**只能用 ASCII** —— 中文目录名会被直接拒绝。中文名请写在 `SKILL.md`
的 frontmatter `description` 里，目录名统一用 `@@CORP_ID@@-` 前缀。

## 安装到哪里

技能加载有两个作用域（见 `coworker/skills/store.py`）：

- 全局：`<state-dir>/skills/<name>/SKILL.md`
- 项目级：`<workspace>/.coworker/skills/<name>/SKILL.md`

`<state-dir>` 的解析顺序（`coworker/secrets.py` 的 `state_dir()`）：

1. `$COWORKER_STATE_DIR`（任意平台的显式覆盖，测试/sidecar 用）
2. Windows：`%APPDATA%\coworker`
3. macOS / Linux：`~/.config/coworker`

打包安装时把本目录下的技能复制到全局技能目录即可，例如：

```bash
cp -r enterprise/skills/@@CORP_ID@@-expense "${COWORKER_STATE_DIR:-$HOME/.config/coworker}/skills/"
```
MD
      ;;
    branding)
      cat <<'MD'
## 放什么

- `theme.css` —— 覆盖 GUI 的 CSS 变量（本目录已生成模板）
- 图标：`icons/32x32.png`、`icons/128x128.png`、`icons/128x128@2x.png`、
  `icons/icon.icns`、`icons/icon.ico`（尺寸与文件名必须与
  `surfaces/gui/src-tauri/tauri.conf.json` 的 `bundle.icon` 数组一致）
- 中文文案覆盖表

## 挂载点（会落在上游文件里的改动，同步时最容易冲突，请重点 review）

1. `surfaces/gui/src/main.tsx`
   在第 7 行 `import "./styles.css";` **之后**追加一行：

   ```ts
   import "../../../enterprise/branding/theme.css";
   ```

   顺序不能反 —— 后导入的样式表才能覆盖 `styles.css` 里的 `:root` 变量。

2. `surfaces/gui/src-tauri/tauri.conf.json`
   需要改的键：
   - `productName`
   - `identifier`
   - `bundle.publisher`
   - `plugins.updater.endpoints`（指向企业内网发布地址）
   - `plugins.updater.pubkey`（换成企业自己的 minisign 公钥）
MD
      ;;
    config)
      cat <<'MD'
## 放什么

- `config.default.toml` —— 企业默认配置模板（本目录已生成）
- `models.json` —— 私有模型能力声明（可选；用 verify-private-model.py 实测后生成）

## 怎么让它们真正到员工机器上（首启预置）

`coworker/provisioning.py` 会在服务启动时（`load_config()` 之前）把「已发布的默认值」
种进空的 `<state-dir>`。企业构建把下面这个目录打进安装包，并设 `COWORKER_DEFAULTS_DIR`
指向它：

```
defaults/
  config.toml        → <state-dir>/config.toml
  models.json        → <state-dir>/models.json
  mcp.json           → <state-dir>/mcp.json
  AGENTS.md          → <state-dir>/AGENTS.md      # 企业规范/术语表，自动进 system prompt
  skills/<name>/     → <state-dir>/skills/<name>/  # 逐个技能，不是整棵树
```

打包时把本目录的 `config.default.toml` 改名为 `defaults/config.toml` 即可。

三条铁律（已有测试钉住）：**不覆盖**已存在的文件（用户的就是用户的）、**不复活**被删掉的
技能（回执文件 `<state-dir>/.provisioned.json` 记着种过什么）、**不致命**（默认值有语法错
只告警，不能让人打不开应用）。逐技能而非整目录的粒度，是为了让后续版本能加新技能而不动
已有的。

想推「必须生效」的策略，这个机制不合适——它只填空位，不覆盖。

## 配置分层（`coworker/config.py`）

内置默认值 < 全局配置 < 工作区配置：

- 全局：`<state-dir>/config.toml`
- 工作区：`<workspace>/.coworker/config.toml`

只有 `_FIELDS` 白名单里的键会被读取，未知键静默忽略。

`allowed_commands` 与 `auto_allow` 属于 `_GLOBAL_ONLY_FIELDS`：
工作区配置里的 `auto_allow` 永远不生效；工作区的 `allowed_commands`
只是「申请」，必须用户显式信任该工作区（workspace trust）后才会被合并。
MD
      ;;
    mcp)
      cat <<'MD'
## 放什么

- `mcp.example.json` —— MCP 服务器配置模板（本目录已生成）

## 生效路径（`coworker/mcp/config.py`）

- 全局：`<state-dir>/mcp.json`
- 工作区：`<workspace>/.coworker/mcp.json`

工作区的 MCP 配置属于「可执行来源」（stdio 会拉起进程），
所以只有在用户信任该工作区之后才会被读取 —— 光是 clone 下来不会生效。

格式与 Claude Desktop / Cursor / Codex 完全兼容（标准 `mcpServers`）。
`command` / `args` / `env` / `url` / `headers` 里的 `${VAR}` 会在加载时
由 `coworker/secrets.py` 的 SecretStore 解析（进程环境变量 + 本地 `.env`）——
**密钥不要写进这个文件，也不要提交进仓库**。

## `${VAR}` 的命名硬约束

SecretStore 的引用正则是
`_REF = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")`
—— **只认字母/下划线开头的 ASCII 标识符**，连字符和数字开头都不匹配。
不匹配时不会报错，SecretStore 会把 `${...}` 原样留在字符串里，
MCP 服务器最终收到的就是字面量 `Bearer ${...}`，只表现为一个莫名其妙的 401。

所以本仓库统一用 `@@CORP_ENV@@_` 作为环境变量前缀（由企业标识
`@@CORP_ID@@` 大写、连字符转下划线得到），例如
`@@CORP_ENV@@_KB_TOKEN`、`@@CORP_ENV@@_ITSM_TOKEN`。

## 服务器条目可用的键

见 `coworker/mcp/config.py`：`MCPServerDef` 的字段是
`command` / `args` / `env` / `cwd` / `url` / `headers` / `enabled` /
`include_tools` / `exclude_tools` / `requires_approval` / `auth`。
另外还有一个只出现在 JSON 里、不进 `MCPServerDef` 的 `type` 键，
由 `_parse()` 用来决定传输方式：`type` 落在
`_HTTP_TYPES = {"http", "https", "sse", "streamable-http", "streamable_http"}`
里、或者填了 `url`，就按 http 处理，否则按 stdio 拉起进程。
MD
      ;;
    connectors)
      cat <<'MD'
## 放什么

企业内部系统的连接器实现（OA、工单、知识库、内部 API 等）。

## 挂载点

参考上游 `coworker/connectors/descriptors.py` 的描述符模式：
一个连接器 = 一份 `Field` 列表（GUI 动态渲染表单）+ 一个构造函数。
企业连接器实现放在本目录，再在上游的描述符列表里注册。

注册点属于「落在上游文件里的改动」，同步时会冲突，请在
`enterprise/tests/test_enterprise_customization.py` 里加断言守住。
MD
      ;;
    tools)
      cat <<'MD'
## 放什么

企业专属工具函数。工具名 = Python 函数的 `__name__`
（见 `coworker/tools/registry.py` 的 `ToolRegistry.register`）。

## 挂载点

在 `coworker/agent.py` 里通过 `registry.register_all([...])` 注册。

## 命名注意

工具名会出现在配置的 `auto_allow` 列表里，也会被
`coworker/risk.py` 的 `WRITE_TOOLS = {"write_file", "replace_in_file",
"apply_patch", "apply_unified_diff"}` 之类的集合匹配。
新增有写副作用的工具时，记得同步评估是否要纳入风险集合。
MD
      ;;
    tests)
      cat <<'MD'
## 放什么

守住企业定制不被上游同步覆盖的冒烟测试。

- `test_enterprise_customization.py` —— 主冒烟测试（由初始化脚本安装）

## 怎么跑

```bash
pytest enterprise/tests -q
```

## 为什么必须有

上游同步 PR 会把上游版本的文件重新带回来。挂载点改动（`main.tsx` 的
import、`tauri.conf.json` 的品牌键、provider 注册、connector 注册）
一旦被冲突解决时误丢，产品上看不出来，但企业定制就悄悄失效了。
这些测试就是「定制还在不在」的自动化断言，必须挂进 CI 的阻塞门禁。
MD
      ;;
    site)
      cat <<'MD'
## 放什么

企业内网站点 / 内部文档发布物（企业版帮助中心、发布说明、下载页）。

上游汉化仓的 `website/` 目录会随同步一起过来；企业自己的站点内容放这里，
避免直接改 `website/` 造成不必要的同步冲突。
MD
      ;;
    *)
      printf '企业定制内容。\n'
      ;;
  esac
}

step_skeleton() {
  step "第 4 步：创建 enterprise/ 目录骨架"

  local d
  for d in "${ENTERPRISE_DIRS[@]}"; do
    local dir="$TARGET_DIR/enterprise/$d"
    if (( DRY_RUN )); then
      dry_note "mkdir -p enterprise/${d}"
    else
      mkdir -p -- "$dir"
    fi

    # .gitkeep 保证空目录也能进版本库。
    write_file "$dir/.gitkeep" ""

    write_file "$dir/README.md" "$(emit_dir_readme "$d" | render)"
  done

  # enterprise/ 根 README —— 总览 + 挂载点清单
  write_file "$TARGET_DIR/enterprise/README.md" "$(emit_enterprise_readme | render)"
}

# 单个子目录的 README.md 全文。
emit_dir_readme() {
  local d="$1"
  printf '# enterprise/%s —— %s\n\n' "$d" "$(dir_purpose "$d")"
  printf '> @@CORP_NAME@@ 定制目录。由 init-enterprise-repo.sh 生成。\n\n'
  dir_readme_body "$d"
  printf '\n---\n\n'
  printf '同步说明：本目录属于「企业独立目录」，上游（汉化仓 / OpenWorker）不存在同名内容，\n'
  # 下面两行里的反引号是 Markdown 代码标记，必须原样输出，故用单引号。
  # shellcheck disable=SC2016
  printf '因此 `git merge localized/main` 时**永远不会冲突**。\n'
  # shellcheck disable=SC2016
  printf '真正会冲突的是落在上游文件里的挂载点改动 —— 见仓库根目录的 `enterprise/README.md`。\n'
}

emit_enterprise_readme() {
  cat <<'MD'
# enterprise/ —— @@CORP_NAME@@ 定制层

本目录是 @@CORP_NAME@@ OpenWorker 企业定制版的全部私有内容。
由 `init-enterprise-repo.sh` 初始化生成。

## 三仓同步链路

```
andrewyng/openworker  (上游，公开)
         │  .github/workflows/sync-upstream.yml
         ▼
zhanglunet/openworker-zh-localized  (汉化版，公开)
         │  .github/workflows/sync-localized.yml
         ▼
@@ENTERPRISE_URL@@  (本仓，私有)
```

单向逐级同步：企业仓只从汉化仓拉，**永远不向上游推**。

## 目录

| 目录 | 用途 |
| --- | --- |
| `skills/` | 企业专属技能包（SKILL.md） |
| `branding/` | 品牌资产：主题变量、图标、文案 |
| `config/` | 默认配置模板（config.default.toml）+ 品牌期望值（branding.json） |
| `mcp/` | MCP 服务器配置模板（mcp.json） |
| `connectors/` | 企业内部系统连接器 |
| `tools/` | 企业专属工具（注册进 ToolRegistry） |
| `tests/` | 企业定制的冒烟测试 |
| `site/` | 企业内网站点 / 文档发布物 |

## 挂载点清单（会冲突的地方，只有这些）

本目录里的文件上游都没有，合并时不会冲突。**真正需要人工 review 的是下面这几处
落在上游文件里的改动**，每次同步 PR 都要逐条确认它们还在：

| 上游文件 | 改动内容 |
| --- | --- |
| `surfaces/gui/src/main.tsx` | 在 `import "./styles.css";` 之后追加 `import "../../../enterprise/branding/theme.css";` |
| `surfaces/gui/src-tauri/tauri.conf.json` | `productName` / `identifier` / `bundle.publisher` / `plugins.updater.endpoints` / `plugins.updater.pubkey` |
| `coworker/providers/registry.py` | `DESCRIPTORS` 里企业自定义端点（复用 `name="custom"` 的 OpenAI 兼容描述符，字段 `base_url` / `api_key` / `model`） |
| `coworker/providers/matrix.py` | `MATRIX` 里新增企业模型条目，键是完整路由 id，如 `"custom:@@CORP_ID@@-chat"` |
| `coworker/connectors/descriptors.py` | 注册企业连接器 |
| `coworker/agent.py` | `registry.register_all([...])` 注册企业工具 |

`enterprise/tests/test_enterprise_customization.py` 会逐条断言以上挂载点，
CI 红了就说明同步把定制冲掉了。品牌字段的**期望值**写在
`enterprise/config/branding.json`，改 `tauri.conf.json` 时必须同步改它。

## 被停用的继承工作流

镜像会把汉化仓自己的流水线一并带进本仓。下面这些已由初始化脚本改名成
`*.yml.disabled`（GitHub 只识别 `.github/workflows` 下的 `.yml` / `.yaml`），
**不要改回来**：

| 文件 | 停用原因 |
| --- | --- |
| `sync-upstream.yml.disabled` | 每天直接从 `andrewyng/openworker` 同步，绕过汉化层，并与 `sync-localized.yml` 抢同一个 `main` |
| `update-site-reports.yml.disabled` | 定时以 `contents: write` 直接 push 回 `main` |
| `deploy-site.yml.disabled` | 把内容部署到汉化版公开站点 |
| `release.yml.disabled` / `prerelease.yml.disabled` / `build-windows.yml.disabled` | 用汉化版品牌与 `latest-zh.json` 发包；企业发布走 `release-corp.yml`（`corp-v*` tag） |

保留 `.disabled` 文件而不是删除，是为了让后续同步里 git 的改名检测能把上游对
这些文件的修改合进来；删除会每次都变成 modify/delete 冲突。

## 同步铁律

> **同步 PR 必须用 merge commit 合并，绝对不能 squash。**

squash 会把一串上游提交压成一个全新的、与汉化仓历史无关的提交，
祖先链就此断裂：下一次同步时 git 找不到正确的 merge base，
会把**上一轮已经解决过的冲突全部重放一遍**，而且越滚越大。

请在 GitHub 仓库设置里关掉 "Allow squash merging"，
或至少对 `sync/*` 分支强制 merge commit（见根目录初始化脚本打印的清单）。
MD
}

# ---------------------------------------------------------------------------
# 第 5 步：生成配置 / 品牌 / MCP 模板
# ---------------------------------------------------------------------------

emit_config_toml() {
  cat <<'TOML'
# ---------------------------------------------------------------------------
# @@CORP_NAME@@ OpenWorker 企业定制版 —— 默认配置模板
# 由 init-enterprise-repo.sh 生成；对应实现见 coworker/config.py
# ---------------------------------------------------------------------------
#
# 用法：复制到下面两个位置之一
#   全局：  <state-dir>/config.toml
#   工作区：<workspace>/.coworker/config.toml
#
# <state-dir> 的解析顺序（coworker/secrets.py 的 state_dir()）：
#   1. $COWORKER_STATE_DIR      —— 任意平台的显式覆盖
#   2. Windows: %APPDATA%\coworker
#   3. macOS / Linux: ~/.config/coworker
#
# 分层规则：内置默认值 < 全局 < 工作区。
# 只有 coworker/config.py 里 _FIELDS 白名单内的键会被读取，未知键静默忽略。
# 其中 allowed_commands / auto_allow 属于 _GLOBAL_ONLY_FIELDS：
#   - 工作区配置里的 auto_allow 永远不生效；
#   - 工作区配置里的 allowed_commands 只是「申请」，必须用户显式信任
#     该工作区（workspace trust）之后才会被合并进全局值。
# ---------------------------------------------------------------------------

# 模型路由 id。
# "custom:" 前缀对应 coworker/providers/registry.py 中 name="custom" 的
# 「自定义 API (OpenAI 兼容)」描述符，其字段为 base_url / api_key / model。
# base_url 和 api_key 通过 GUI 的 provider 配置界面填写，存进 SecretStore，
# 不要写在本文件里。
#
# 想让企业模型出现在 GUI 选择器并带上能力标注和上下文窗口，
# 需要在 coworker/providers/matrix.py 的 MATRIX 里新增一条，键是**完整路由 id**：
#
#     "custom:@@CORP_ID@@-chat": ModelEntry(
#         "@@CORP_NAME@@ 内部大模型", _AGENTIC_VISION, 128_000
#     ),
#
# 不加也能用（会回落到 capabilities.py 的保守启发式推断），只是没有标注。
model = "custom:@@CORP_ID@@-chat"

# 权限模式。coworker/permissions.py 的 Mode 枚举取值：
#   "discuss"     只读对话，不改文件，也不走规划流程
#   "plan"        只读 + 规划契约（explore → propose_plan → execute）
#   "interactive" 每个有副作用的动作都请求确认（默认，企业环境推荐）
#   "auto"        全自动，不询问
#   "custom"      interactive + 自动放行 auto_allow 里列出的工具
# 注意：CLI 的 --mode 只暴露 plan / interactive / auto 三个选项。
mode = "interactive"

# 单轮任务最大迭代步数。与 coworker/config.py 的默认值保持一致。
# 调高会增加长任务成功率，也会增加 token 消耗；企业内网模型较慢时不建议再调高。
max_iterations = 150

# 免确认直接执行的命令白名单。
#
# 匹配规则见 coworker/permissions.py 的 _command_allowed()，**不是**简单的字符串前缀匹配：
#   1. 命令里只要出现 shell 操作符（&& || ; | > < ` $( ) 之类）就整条拒绝 ——
#      否则一条 "git status" 白名单会把 `git status && rm -rf ~` 一起放行；
#   2. 通过后用 shlex.split 把命令和白名单条目都切成 argv，
#      条目的 token 序列必须是命令 token 序列的**完整前缀**。
#      于是 "git status" 能匹配 `git status -s`，但匹配不上 `git statusfoo`，
#      光写 "git" 也不会因为 `git status` 而命中（"git" 会匹配所有 git 子命令，慎用）。
#
# 上游的内置默认是**空列表**（DEFAULT_ALLOWED_COMMANDS = []），这是刻意的：
# 不存在「一定安全」的可执行程序 —— 名义上只读的命令也可能读到工作区之外的密钥、
# 展开环境变量、加载项目自带的配置/插件，或者顺带执行别的程序
# （例如 `find -exec`、pytest 的 collection 阶段）。
#
# 企业统一下发时，请只放确实评审过的命令前缀，并且写清楚理由。
# 下面给的是保守示例，默认全部注释掉，由企业安全团队逐条开启：
allowed_commands = [
  # "git status",
  # "git diff",
  # "git log",
  # "npm run lint",
]

# mode = "custom" 时自动放行的工具名列表（精确匹配工具名）。
# 工具名 = 注册进 ToolRegistry 的 Python 函数名，例如：
#   read_file / grep / git_log / run_shell / shell_task_output /
#   shell_task_kill / todo_write
# 有写副作用的工具见 coworker/risk.py 的 WRITE_TOOLS：
#   write_file / replace_in_file / apply_patch / apply_unified_diff
# 只在 mode = "custom" 时才有意义；mode = "interactive" 时本项被忽略。
auto_allow = [
  # "read_file",
  # "grep",
  # "git_log",
]

# 本地服务监听地址。默认只听回环，不要改成 0.0.0.0 —— 本服务没有内建鉴权，
# 暴露到局域网等于把整台机器的 shell 交出去。
host = "127.0.0.1"
port = 8765

# 联网搜索提供方："duckduckgo"（免密钥，默认）| "tavily" | "brave"（需要密钥）。
# 企业内网离线部署时建议保持 duckduckgo 或走内部代理。
web_search_provider = "duckduckgo"

# ---------------------------------------------------------------------------
# OpenWorker Cloud 相关（登录 + 托管连接器 + Slack/GitHub 入站中继）
# ---------------------------------------------------------------------------
# 企业私有化部署通常**不使用**官方云服务。把下面 5 个 cloud_* 键全部置为空字符串
# 即可关闭：
#   - cloud_base_url / cloud_auth_domain / cloud_client_id / cloud_audience
#     置空 → 云端登录与托管连接器不可用（本地 API key 直连不受影响）；
#   - cloud_relay_ws_url 置空 → 托管中继关闭（手动配置的 Slack Socket Mode 仍可用）。
#     特别注意：这个键的内置默认值指向**生产中继**，不是空值 ——
#     想关掉必须在配置里显式写空串，删掉这一行会回落到默认的生产地址。
#
# 如果企业自建了 BYO-VPC 部署，把这些指向自己的实例即可。
cloud_base_url = ""
cloud_auth_domain = ""
cloud_client_id = ""
cloud_audience = ""
cloud_relay_ws_url = ""
TOML
}

# enterprise/config/branding.json —— 品牌「期望值」的单一来源。
#
# 冒烟测试 enterprise/tests/test_enterprise_customization.py 读的就是这个文件：
# 它先做「不许等于汉化版旧值」的负向断言（不依赖任何配置，永远执行），
# 再拿本文件里的 productName / identifier / publisher / updaterHost 去和
# surfaces/gui/src-tauri/tauri.conf.json 逐字比对。
# 本文件缺失时那些正向断言会 **skip**（假绿灯），所以初始化时必须一并生成。
#
# 优先级：环境变量 OPENWORKER_ENTERPRISE_*  >  本文件。
# 有意**不写** providers / models：冒烟测试在两者都缺省时会回落到
# enterprise/config/config.default.toml 的 model 前缀（custom:）与 model 本身，
# 少一处需要手工保持同步的重复配置。
emit_branding_json() {
  cat <<'JSON'
{
  "_comment": "@@CORP_NAME@@ 企业品牌期望值。改 surfaces/gui/src-tauri/tauri.conf.json 时必须同步改这里，否则 enterprise/tests 会报「品牌被同步覆盖」。",
  "_comment_updaterHost": "更新服务域名（子串匹配 plugins.updater.endpoints）。冒烟测试禁止 endpoints 里出现 zhanglunet / andrewyng / github.com / githubusercontent.com / openworker.com——所以不能直接用私有仓的 GitHub Release 直链，必须换成企业自己的托管域名（release-corp.yml 的 vars.CORP_UPDATE_UPLOAD_URL 方式 B，或企业站反代）。下面是占位值，务必替换。",
  "productName": "@@CORP_NAME@@ 智能助手",
  "identifier": "com.@@CORP_ID@@.openworker",
  "publisher": "@@CORP_NAME@@",
  "updaterHost": "REPLACE-ME.@@CORP_ID@@.internal"
}
JSON
}

emit_theme_css() {
  cat <<'CSS'
/* ---------------------------------------------------------------------------
 * @@CORP_NAME@@ OpenWorker 企业定制版 —— 主题覆盖
 * 由 init-enterprise-repo.sh 生成。
 *
 * 生效方式（挂载点，会落在上游文件里）：
 * 在 surfaces/gui/src/main.tsx 的第 7 行 `import "./styles.css";` **之后**追加：
 *
 *     import "../../../enterprise/branding/theme.css";
 *
 * 顺序不能反 —— 只有后导入的样式表才能覆盖 styles.css 里的 :root 变量。
 *
 * 深色模式选择器必须写成 html[data-theme="dark"]，与上游一致：
 * data-theme 由 index.html 里的内联脚本在首屏绘制前打到 <html> 上，
 * 之后由 src/theme.ts 维护（Light / Dark / Auto 跟随系统，存在 localStorage）。
 * 用 @media (prefers-color-scheme: dark) 会覆盖不到手动切换的情况。
 *
 * 下面列出的是 surfaces/gui/src/styles.css 里真实存在的变量名，
 * 只覆盖需要换的，其余保持上游默认即可（注释掉的行是原始值，方便对照）。
 * ------------------------------------------------------------------------- */

/* ===== 浅色（默认） ===== */
:root {
  /* --- 品牌主色：企业换肤最关键的两个变量 --- */
  --accent: #2563eb;        /* 上游默认 #2563eb（钴蓝）。改成企业主色 */
  --accent-soft: #e9f0fd;   /* 上游默认 #e9f0fd。主色的浅色底，用于选中态/高亮块 */

  /* --- 用户气泡（"实心"填充块） --- */
  --solid: #e9ebf0;         /* 上游默认 #e9ebf0 */
  --on-solid: #1f2227;      /* 上游默认 #1f2227。必须与 --solid 保证 4.5:1 对比度 */

  /* --- 底色与文字 --- */
  /* --paper: #f5f6f7; */        /* 页面底色 */
  /* --panel: #ffffff; */        /* 面板/卡片底色 */
  /* --ink: #17191c; */          /* 正文 */
  /* --muted: #5b616b; */        /* 次要文字 */
  /* --faint: #9aa1aa; */        /* 更弱的文字 */
  /* --line: #e8eaed; */         /* 分隔线 */
  /* --line-strong: #d8dce1; */  /* 强调分隔线 */

  /* --- 状态色（改动前请确认对比度，这些承载语义） --- */
  /* --ok: #2f7d57; --ok-soft: #eef6f0; --ok-line: #cfe6d6; --ok-dot: #3f9c5a; */
  /* --warn-ink: #b45309; --warn-soft: #fef3c7; */
  /* --danger: #b91c1c; --danger-soft: #f9e7e5; */
  /* --teal-ink: #0f766e; --teal-line: #cfebea; --teal-soft: #edfafa; */

  /* --- 毛玻璃与遮罩 --- */
  /* --glass: rgba(255, 255, 255, 0.9); */
  /* --glass-strong: rgba(255, 255, 255, 0.96); */
  /* --glass-soft: rgba(255, 255, 255, 0.78); */
  /* --scrim: rgba(29, 27, 24, 0.32); */

  /* --- 字体 --- */
  /* 想换成企业内网自托管字体时，注意 styles.css 用的是本地 woff2
   * （surfaces/gui/src/fonts/manrope-700.woff2），没有任何外部字体请求。
   * 企业字体也请自托管，不要引 CDN。 */
  /* --sans: -apple-system, BlinkMacSystemFont, "Segoe UI", Inter, system-ui, sans-serif; */
  /* --mono: "SF Mono", "JetBrains Mono", Menlo, Consolas, monospace; */
  /* --serif: var(--sans); */
}

/* ===== 深色 ===== */
html[data-theme="dark"] {
  /* 深色下主色要"提亮"，否则在深色面板上对比度不足（上游就是这么做的）。
   * 不要直接复用浅色的主色值。 */
  --accent: #4c8dff;        /* 上游默认 #4c8dff */
  --accent-soft: #1c2a44;   /* 上游默认 #1c2a44 */

  --solid: #2e3138;         /* 上游默认 #2e3138 */
  --on-solid: #e6e8eb;      /* 上游默认 #e6e8eb */

  /* --paper: #131417; */
  /* --panel: #1c1e22; */
  /* --ink: #e6e8eb; */
  /* --muted: #9aa1ab; */
  /* --faint: #62686f; */
  /* --line: #2a2d33; */
  /* --line-strong: #3a3e46; */

  /* --ok: #58b07f; --ok-soft: #1a2b21; --ok-line: #2c4736; --ok-dot: #4dac72; */
  /* --warn-ink: #e8b04b; --warn-soft: #36280f; */
  /* --danger: #f07067; --danger-soft: #3d2422; */
  /* --teal-ink: #46c0b2; --teal-line: #1f4a45; --teal-soft: #11302d; */

  /* --glass: rgba(28, 30, 34, 0.9); */
  /* --glass-strong: rgba(28, 30, 34, 0.96); */
  /* --glass-soft: rgba(28, 30, 34, 0.78); */
  /* --scrim: rgba(0, 0, 0, 0.5); */
}

/* ===== 企业 Logo / 文字标 =====
 * styles.css 里 .brand-wordmark 用的是自托管的 Manrope 700。
 * 换成企业字体时，把 woff2 放进 enterprise/branding/fonts/ 并在这里重新声明。 */
/*
@font-face {
  font-family: "@@CORP_NAME@@Sans";
  font-style: normal;
  font-weight: 700;
  font-display: swap;
  src: url("./fonts/corp-700.woff2") format("woff2");
}
.brand-wordmark {
  font-family: "@@CORP_NAME@@Sans", "Manrope", -apple-system, system-ui, sans-serif;
}
*/
CSS
}

emit_mcp_json() {
  # 注意：这里必须用 quoted heredoc，${VAR} 要原样落进 JSON 文件，
  # 由 coworker/secrets.py 的 SecretStore 在加载时解析，不能被 shell 展开。
  cat <<'JSON'
{
  "_comment": "@@CORP_NAME@@ 企业定制版 MCP 服务器配置模板。复制到 <state-dir>/mcp.json（全局）或 <workspace>/.coworker/mcp.json（工作区，需先信任该工作区）。格式与 Claude Desktop / Cursor / Codex 完全兼容。",
  "_comment_secrets": "command / args / env / url / headers 里的 ${VAR} 会在加载时由 coworker/secrets.py 的 SecretStore 解析（进程环境变量 + 本地 .env）。密钥不要写进本文件，更不要提交进仓库。",
  "_comment_varname": "SecretStore 的正则是 _REF = ^\\$\\{[A-Za-z_][A-Za-z0-9_]*\\}$，只认字母/下划线开头的 ASCII 标识符；连字符或数字开头都匹配不上，且不会报错——${...} 会被原样发给服务器，只表现为 401。所以变量名统一用 @@CORP_ENV@@_ 前缀（企业标识 @@CORP_ID@@ 大写、连字符转下划线）。",
  "_comment_fields": "MCPServerDef（coworker/mcp/config.py）的字段：command / args / env / cwd / url / headers / enabled / include_tools / exclude_tools / requires_approval / auth。另有一个只存在于 JSON、不进 MCPServerDef 的 type 键，_parse() 用它决定传输方式：type 属于 _HTTP_TYPES = {http, https, sse, streamable-http, streamable_http} 或填了 url 即按 http 处理，否则按 stdio 拉起进程。",
  "mcpServers": {
    "@@CORP_ID@@-kb": {
      "_comment": "stdio 示例：本地进程型 MCP 服务器，企业知识库检索。没有 url、也没有 type 时按 stdio 处理。",
      "command": "python3",
      "args": ["-m", "@@CORP_PKG@@_mcp.knowledge_base"],
      "env": {
        "KB_ENDPOINT": "https://kb.@@CORP_ID@@.internal/api",
        "KB_TOKEN": "${@@CORP_ENV@@_KB_TOKEN}"
      },
      "cwd": "/opt/@@CORP_ID@@/mcp",
      "enabled": true,
      "include_tools": ["kb_search", "kb_fetch_doc"],
      "requires_approval": false
    },
    "@@CORP_ID@@-itsm": {
      "_comment": "http 示例：远程 MCP 服务器，企业工单系统。带 url 或 type 为 http/https/sse/streamable-http 时按 http 处理。",
      "type": "http",
      "url": "https://mcp.@@CORP_ID@@.internal/itsm/mcp",
      "headers": {
        "Authorization": "Bearer ${@@CORP_ENV@@_ITSM_TOKEN}",
        "X-Tenant": "@@CORP_ID@@"
      },
      "enabled": true,
      "include_tools": ["ticket_search", "ticket_create", "ticket_comment"],
      "exclude_tools": ["ticket_delete"],
      "requires_approval": true
    }
  }
}
JSON
}

step_templates() {
  step "第 5 步：生成 config / branding / mcp 模板"

  write_file "$TARGET_DIR/enterprise/config/config.default.toml" "$(emit_config_toml  | render)"
  write_file "$TARGET_DIR/enterprise/config/branding.json"        "$(emit_branding_json | render)"
  write_file "$TARGET_DIR/enterprise/branding/theme.css"          "$(emit_theme_css    | render)"
  write_file "$TARGET_DIR/enterprise/mcp/mcp.example.json"        "$(emit_mcp_json     | render)"

  # mcp.example.json 里的 _comment 键是给人看的注释。
  # coworker/mcp/config.py 只读取 mcpServers 下的条目，顶层多余键会被忽略；
  # mcpServers 内部的 _comment 也会落进 raw dict，但 MCPServerDef 只取已知字段，
  # 多余键同样不会报错。仍然建议部署到 <state-dir>/mcp.json 前删掉这些注释。
}

# ---------------------------------------------------------------------------
# 第 6 步：安装同步/发布流水线与冒烟测试
# ---------------------------------------------------------------------------

step_pipeline() {
  step "第 6 步：安装同步/发布流水线与冒烟测试"

  # 同步流水线：企业仓从汉化仓拉取。参考样板是汉化仓的
  # .github/workflows/sync-upstream.yml（每日 cron + workflow_dispatch，
  # 合并到 sync 分支，成功开 PR、冲突开 Issue）。
  copy_template "sync-localized.yml" \
    "$TARGET_DIR/.github/workflows/sync-localized.yml"

  # 企业发布流水线：监听 corp-v* tag，产出企业品牌安装包与 latest-<corp>.json。
  # 它替代第 3 步里被停用的 release.yml / prerelease.yml / build-windows.yml。
  copy_template "release-corp.yml" \
    "$TARGET_DIR/.github/workflows/release-corp.yml"

  # 冒烟测试：断言所有挂载点定制还在。
  copy_template "test_enterprise_customization.py" \
    "$TARGET_DIR/enterprise/tests/test_enterprise_customization.py"

  # 大表哥表格助手技能（excel-ai-analyst）：把含公式的业务 Excel 当遗留代码逆向工程。
  # 随技能分发配套脚本 scripts/excel_ai.py（四子命令），员工无需每次让 AI 现写。
  # 装到 enterprise/skills/ 后，还要再同步到运行时技能目录才会生效——见清单 E 步。
  copy_template_dir "skills/excel-ai-analyst" \
    "$TARGET_DIR/enterprise/skills/excel-ai-analyst"

  # 企业知识库检索技能：配合全局配置的 knowledge_roots（常驻只读挂载）使用。
  copy_template_dir "skills/corp-knowledge" \
    "$TARGET_DIR/enterprise/skills/corp-knowledge"

  # 企业 CLI → MCP 桥：用 tools.json 声明子命令，不必每个 CLI 手写一个 server。
  # 只放行白名单子命令、argv 直传不经 shell —— 比把整个 CLI 加进 allowed_commands 安全得多。
  copy_template_dir "mcp/cli-bridge" \
    "$TARGET_DIR/enterprise/mcp/cli-bridge"

  # 企业知识库检索 MCP server（知识库 v2）：知识库不是文件系统、或权限要按人校验时用它。
  # 与 knowledge_roots（v1 目录挂载）的区别：Agent 只拿得到检索结果，没有文件系统访问权。
  copy_template_dir "mcp/kb-server" \
    "$TARGET_DIR/enterprise/mcp/kb-server"

  # 内部系统 HTTP API → MCP 桥（ERP/工单/HR/审批流）。用 api.json 声明接口，不写 Python。
  # 随包两份示例是有意拆开的：读一份、写一份。MCP 的 requires_approval 是 server 级的，
  # 混在一起只能二选一——要么查订单也弹框，要么关单也不弹。接入指南见
  # docs/enterprise/CONNECTOR_GUIDE.md。
  copy_template_dir "mcp/corp-api" \
    "$TARGET_DIR/enterprise/mcp/corp-api"

  # 原生连接器描述符模板（CONNECTOR_GUIDE 路线 B）：要 GUI 卡片 + 逐工具审批时才用。
  # 放在 enterprise/connectors/ 下不会自动生效——需要把 5 行挂载点加进
  # coworker/connectors/descriptors.py，并把这个包放到 coworker/connectors/corp/。
  # 故意不自动改上游文件：那是一处会在同步时冲突的改动，必须由人来决定要不要。
  copy_template_dir "connectors/corp" \
    "$TARGET_DIR/enterprise/connectors/corp"

  # 提示把 enterprise/tests 挂进现有 CI。企业仓继承的 .github/workflows/ci.yml
  # 里 pytest 这一步跑的是 `pytest tests -q`，不会覆盖 enterprise/tests。
  local ci="$TARGET_DIR/.github/workflows/ci.yml"
  if [[ -f "$ci" ]] && grep -q 'pytest tests -q' "$ci" 2>/dev/null; then
    warn "继承来的 .github/workflows/ci.yml 只跑 'pytest tests -q'，不会跑企业冒烟测试。
     → 请把该步骤改为：pytest tests enterprise/tests -q
     （这是一处挂载点改动，同步时会冲突，属于预期。）"
  fi
}

# ---------------------------------------------------------------------------
# 第 7 步：提交
# ---------------------------------------------------------------------------

step_commit() {
  step "第 7 步：提交企业定制骨架"

  if (( DRY_RUN )); then
    dry_note "git -C ${TARGET_DIR} add -- <本次实际写出的文件>"
    dry_note "git -C ${TARGET_DIR} commit -m 'chore(enterprise): 初始化 ${CORP_ID} 企业定制骨架'"
    if (( NO_PUSH )); then
      dry_note "（已指定 --no-push，跳过推送）"
    else
      dry_note "git -C ${TARGET_DIR} push origin $(current_branch)"
    fi
    return 0
  fi

  # 只暂存本次真正写出的文件。这样重跑脚本时，用户在 enterprise/ 下
  # 未提交的定制改动不会被裹进这个提交。
  if (( ${#CREATED_PATHS[@]} == 0 )); then
    skip "本次没有新写出任何文件（骨架已是最新），不创建提交"
    return 0
  fi

  git -C "$TARGET_DIR" add -- "${CREATED_PATHS[@]}"

  if git -C "$TARGET_DIR" diff --cached --quiet; then
    skip "没有待提交的改动（骨架已是最新）"
    return 0
  fi

  info "待提交的文件："
  git -C "$TARGET_DIR" diff --cached --name-only | sed 's/^/       /'

  if ! confirm "确认创建这个提交？"; then
    warn "已放弃提交。改动仍在暂存区，可自行 git commit。"
    return 0
  fi

  git -C "$TARGET_DIR" commit -m "chore(enterprise): 初始化 ${CORP_ID} 企业定制骨架

- 创建 enterprise/{skills,branding,config,mcp,connectors,tools,tests,site}
- 生成 config.default.toml / branding.json / theme.css / mcp.example.json 模板
- 安装 sync-localized.yml 同步流水线、release-corp.yml 发布流水线与企业定制冒烟测试
- 停用镜像带过来的汉化仓工作流（sync-upstream / update-site-reports / deploy-site /
  release / prerelease / build-windows → *.yml.disabled）

由 init-enterprise-repo.sh 生成。"
  ok "已创建提交。"

  local branch
  branch="$(current_branch)"

  if (( NO_PUSH )); then
    skip "已指定 --no-push，未推送。手动推送：git -C ${TARGET_DIR} push origin ${branch}"
    return 0
  fi

  if confirm "推送到 origin/${branch} ？"; then
    git -C "$TARGET_DIR" push origin "$branch"
    ok "已推送到 origin/${branch}"
  else
    warn "未推送。手动推送：git -C ${TARGET_DIR} push origin ${branch}"
  fi
}

# ---------------------------------------------------------------------------
# 第 8 步：后续人工步骤清单
# ---------------------------------------------------------------------------

print_next_steps() {
  local branch
  branch="$(current_branch)"

  # 【G1】的措辞取决于是否真的停用过继承工作流 —— 用 --keep-inherited-workflows
  # 跑完还说"已停用"就是假消息，会让人跳过这一步。
  local g1_note
  if (( KEEP_INHERITED )); then
    g1_note="${C_YELLOW}本次用了 --keep-inherited-workflows，这些工作流还都是启用状态，必须人工处理：${C_RESET}
      到 Actions 页面逐个 Disable workflow，或把文件改名成 *.yml.disabled。
      ${C_YELLOW}只要 sync-upstream.yml 还在跑，它每天就会绕过汉化层
      直接把 andrewyng/openworker 合进本仓，并和 sync-localized.yml 抢同一个 main。${C_RESET}"
  else
    g1_note="它们已被初始化脚本改名成 *.yml.disabled，${C_BOLD}千万不要改回来${C_RESET} ——
      sync-upstream 会绕过汉化层，每天直接把上游合进本仓。"
  fi

  cat <<CHECKLIST

${C_BOLD}=====================================================================
 初始化完成 —— 以下步骤脚本做不了，必须人工在平台上完成
=====================================================================${C_RESET}

本地工作副本：${TARGET_DIR}
企业私有仓：  ${ENTERPRISE_URL_SAFE}
上游汉化仓：  ${LOCALIZED_URL_SAFE}
当前分支：    ${branch}

${C_BOLD}【A】仓库合并策略（最关键，做错会导致每次同步重放全部冲突）${C_RESET}

  A1. Settings → General → Pull Requests：
      ${C_YELLOW}关闭 "Allow squash merging"${C_RESET}
      ${C_YELLOW}关闭 "Allow rebase merging"${C_RESET}
      ${C_GREEN}只保留 "Allow merge commits"${C_RESET}

      原因：同步 PR 必须以 merge commit 落地。squash 会把上游一串提交压成
      一个与汉化仓历史无关的新提交，祖先链（merge base）就此断裂 ——
      下一次同步时 git 找不到共同祖先，会把上一轮已经解决过的冲突
      全部重放一遍，而且每同步一次就多累积一轮，最终无法维护。
      rebase 同理（改写 SHA）。

  A2. 如果因为其他流程必须保留 squash，至少在 Rulesets / 分支保护里
      对 ${C_BOLD}sync/*${C_RESET} 分支单独强制 merge commit，并在 PR 模板里写死提醒。

${C_BOLD}【B】GitHub Actions 权限${C_RESET}

  B1. Settings → Actions → General → Workflow permissions：
      勾选 ${C_YELLOW}"Read and write permissions"${C_RESET}
      勾选 ${C_YELLOW}"Allow GitHub Actions to create and approve pull requests"${C_RESET}

      不勾第二项，sync-localized.yml 里的 peter-evans/create-pull-request
      会报 "GitHub Actions is not permitted to create or approve pull requests"。

  B2. 私有仓默认可能禁用 Actions：Settings → Actions → General →
      Actions permissions 选 "Allow all actions"，或至少把两条流水线实际用到的
      action 加进允许列表：
        sync-localized.yml：actions/checkout@v4、actions/setup-python@v5、
                            actions/github-script@v7、peter-evans/create-pull-request@v7
        release-corp.yml：  actions/checkout@v4、actions/setup-node@v4、
                            actions/setup-python@v5、dtolnay/rust-toolchain@stable、
                            Swatinem/rust-cache@v2、actions/upload-artifact@v4、
                            actions/download-artifact@v4、softprops/action-gh-release@v2

${C_BOLD}【C】Secrets 与 Variables（名字必须逐字一致，写错不会报错、只会静默失效）${C_RESET}

  Settings → Secrets and variables → Actions

  C1. Secret ${C_BOLD}LOCALIZED_SYNC_TOKEN${C_RESET}（可选）
      汉化仓是公开仓时不需要 —— sync-localized.yml 检测到它为空就退回匿名
      https://github.com/\${LOCALIZED_REPO}.git 拉取。
      如果企业把汉化层也放进了私有仓，配一个对该仓有读权限的 PAT。
      ${C_YELLOW}注意名字是 LOCALIZED_SYNC_TOKEN，不是 LOCALIZED_REPO_TOKEN。${C_RESET}

  C2. Variables（不是 Secret）${C_BOLD}CORP_NAME${C_RESET} / ${C_BOLD}CORP_ID${C_RESET}
      release-corp.yml 用它们命名产物与更新清单：
        CORP_NAME → 安装包名前缀，${C_YELLOW}必须是纯 ASCII${C_RESET}（如 AcmeWorker）。
                    这里不能填中文企业名「${CORP_NAME}」，流水线 preflight 会直接拒绝。
        CORP_ID   → 更新清单文件名 latest-<CORP_ID>.json，建议就填 ${CORP_ID}。
      不配则用流水线内置默认值 AcmeWorker / acme。

  C3. Secret ${C_BOLD}TAURI_SIGNING_PRIVATE_KEY${C_RESET} / ${C_BOLD}TAURI_SIGNING_PRIVATE_KEY_PASSWORD${C_RESET}
      企业自己的 minisign 私钥，用于桌面端自动更新签名。
      对应的公钥填进 surfaces/gui/src-tauri/tauri.conf.json 的
      plugins.updater.pubkey。生成命令（二选一）：
        cd surfaces/gui && npm run tauri signer generate -- -w ~/.tauri/${CORP_ID}.key
        npx @tauri-apps/cli signer generate -w ~/.tauri/${CORP_ID}.key
      私钥无密码时 _PASSWORD 留空串即可（见 docs/release-signed-updates.md）。

  C4. 代码签名证书（可选；不配就只能出未签名内测版）
      这些名字取自 release-corp.yml 与 docs/enterprise/DEPLOYMENT.md，别自己发明：
        macOS：  APPLE_CERTIFICATE、APPLE_CERTIFICATE_PASSWORD、APPLE_SIGNING_IDENTITY、
                 APPLE_API_KEY_CONTENT、APPLE_API_KEY、APPLE_API_ISSUER
                 （公证走 App Store Connect API key，${C_YELLOW}没有 APPLE_ID /
                 APPLE_PASSWORD / APPLE_TEAM_ID 这三个 Secret${C_RESET}）
        Windows：WINDOWS_CERTIFICATE（base64 的 .pfx）、WINDOWS_CERTIFICATE_PASSWORD

  C5. 内网更新托管（release-corp.yml 的「方式 B」，可选）
      Variable ${C_BOLD}CORP_UPDATE_UPLOAD_URL${C_RESET} + Secret ${C_BOLD}CORP_UPDATE_UPLOAD_TOKEN${C_RESET}
      只有配了 URL 才会执行上传步骤。GitHub 托管 runner 访问不到企业内网 ——
      走这条路要么换 self-hosted runner，要么给上传接口一个带鉴权的公网入口。

${C_BOLD}【D】品牌挂载点（改上游文件，同步时会冲突，属于预期）${C_RESET}

  D1. surfaces/gui/src-tauri/tauri.conf.json
      - productName        → "${CORP_NAME} 智能助手"（自定，会成为可执行文件名）
      - identifier         → com.${CORP_ID}.openworker（必须全局唯一，且不能改来改去）
      - bundle.publisher   → "${CORP_NAME}"
      - plugins.updater.endpoints → 企业自己托管的 latest-${CORP_ID}.json
      - plugins.updater.pubkey    → 换成 C3 生成的企业公钥
      注意 1：现在继承来的 endpoints 还指向 zhanglunet/openworker-zh-localized，
              不换掉的话企业客户端会去公开仓拉更新包。
      注意 2：${C_YELLOW}不能用私有仓的 GitHub Release 直链${C_RESET} —— 客户端匿名访问不到，
              而且冒烟测试 test_updater_endpoints_point_at_enterprise_host 会把
              zhanglunet / andrewyng / github.com / githubusercontent.com /
              openworker.com 一律判为「非企业域」而报红。请用企业内网或企业站
              静态托管（对应 release-corp.yml 的 vars.CORP_UPDATE_UPLOAD_URL）。
      注意 3：改完这三个品牌字段，记得同步改
              enterprise/config/branding.json（冒烟测试的期望值来源）。

  D2. surfaces/gui/src/main.tsx
      在第 7 行 import "./styles.css"; ${C_BOLD}之后${C_RESET}追加：
        import "../../../enterprise/branding/theme.css";
      顺序不能反，否则覆盖不掉 :root 变量。

  D3. 替换 surfaces/gui/src-tauri/icons/ 下的图标
      （32x32.png / 128x128.png / 128x128@2x.png / icon.icns / icon.ico）

${C_BOLD}【E】模型与配置下发${C_RESET}

  E1. coworker/providers/matrix.py 的 MATRIX 里新增企业模型条目，
      键必须是完整路由 id，例如：
        "custom:${CORP_ID}-chat": ModelEntry("${CORP_NAME} 内部大模型", _AGENTIC_VISION, 128_000),

  E2. 把 enterprise/config/config.default.toml 复制到目标机器的
      <state-dir>/config.toml：
        Linux/macOS：~/.config/coworker/config.toml
        Windows：    %APPDATA%\\coworker\\config.toml
        或用 \$COWORKER_STATE_DIR 显式指定
      base_url / api_key 走 GUI 的 provider 配置界面（存进 SecretStore），
      不要写进 config.toml。

  E3. 把 enterprise/mcp/mcp.example.json 删掉 _comment 注释后复制成
      <state-dir>/mcp.json，并把 \${...} 引用的令牌配到环境变量或
      <state-dir>/.env 里。本仓库的变量名前缀是 ${C_BOLD}${CORP_ENV}_${C_RESET}
      （例：${CORP_ENV}_KB_TOKEN、${CORP_ENV}_ITSM_TOKEN）——
      SecretStore 只认 ^[A-Za-z_][A-Za-z0-9_]*\$ 形态的名字，
      带连字符的写法不会报错，只会把 \${...} 原样发出去，表现为莫名其妙的 401。

${C_BOLD}【F】CI 门禁${C_RESET}

  F1. 把 .github/workflows/ci.yml 里的 "pytest tests -q" 改成
      "pytest tests enterprise/tests -q"，让企业冒烟测试成为阻塞门禁。

  F2. Settings → Branches → 对 main 加分支保护，
      required status checks 勾上 ci.yml 的 job：pytest / gui-unit
      （gui-e2e 在汉化仓里是空跑的占位 job，不要设成必需）。

  F3. ${C_YELLOW}冒烟测试现在一定是红的${C_RESET}，这是预期：D1/D2/E1 还没做完，
      "品牌字段仍是汉化版的值 / 更新源仍指向公开仓 / 企业模型不在 MATRIX 里"
      这几条断言必然失败。做完 D、E 两节后它应该转绿；
      如果做完还是红，说明定制没落到位，照报错里的路径逐条查。

${C_BOLD}【G】验证同步链路${C_RESET}

  G1. 确认镜像带过来的汉化仓工作流不再出现在 Actions 页面：
      sync-upstream / Update site reports / Deploy oaosf.cn /
      Release / Prerelease / Build Windows 都不应该还在跑。
      ${g1_note}

  G2. Actions 页面手动触发一次 ${C_BOLD}"同步汉化版到企业版"${C_RESET}
      （sync-localized.yml 的 workflow_dispatch），
      确认能正常拉到汉化仓、开出 PR。

  G3. ${C_YELLOW}合并那个 PR 时务必用 "Create a merge commit"${C_RESET}，
      合并后本地执行下面两条，确认祖先链是通的（第二条应当输出一个 SHA）：
        git -C ${TARGET_DIR} remote add localized ${LOCALIZED_URL_SAFE}
        git -C ${TARGET_DIR} fetch localized main \\
          && git -C ${TARGET_DIR} merge-base HEAD localized/main

  G4. 发布验证：改好 tauri.conf.json 的 version 后
        git tag corp-v<版本> && git push origin corp-v<版本>
      触发 release-corp.yml。签名 Secrets 一个都不配也能跑，
      产出的是未签名 prerelease。

CHECKLIST

  if (( DRY_RUN )); then
    printf '%s（本次为 --dry-run，以上均未实际执行。）%s\n\n' "$C_YELLOW" "$C_RESET"
  fi
}

# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------

main() {
  parse_args "$@"
  validate_args

  step "OpenWorker 企业定制版私有仓初始化"
  log "  企业标识：  ${CORP_ID}"
  log "  企业名称：  ${CORP_NAME}"
  log "  变量前缀：  ${CORP_ENV}_（MCP/环境变量用）"
  log "  私有仓：    ${ENTERPRISE_URL_SAFE}"
  log "  汉化仓：    ${LOCALIZED_URL_SAFE}"
  log "  工作目录：  ${TARGET_DIR}"
  log "  模板目录：  ${TEMPLATE_DIR}"
  if (( DRY_RUN )); then
    printf '  %s模式：      dry-run（只打印，不改任何东西）%s\n' "$C_YELLOW" "$C_RESET"
  fi

  preflight

  if ! confirm "以上信息无误，开始初始化？"; then
    die "用户取消。"
  fi

  step_mirror
  step_clone
  step_prune_workflows
  step_skeleton
  step_templates
  step_pipeline
  step_commit
  print_next_steps
}

main "$@"
