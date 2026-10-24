#!/usr/bin/env bash
# OpenWorker 中文版 · 一行安装
#
# 开箱叙事的结构借鉴 PC2005-cloud/dsh-pet（MIT）：一条命令、装完说明你会看见什么、
# 另给体检。文案和脚本是独立编写的，没有复制该仓库的代码或句子。
#
# 已克隆仓库时，在仓库根目录执行这一行：
#   bash scripts/install-zh.sh
#
# 还没克隆时不要去拉下面这个地址。它是占位符，脚本不会请求它：
#   curl -fsSL https://example.invalid/openworker-zh/install-zh.sh | bash
#
# 这一行不下载工具链，不写系统目录，不需要管理员权限，不把令牌打到屏幕上。
# 包管理器会使用它们自己的默认源；那些地址不写进本文件。

set -euo pipefail

PLACEHOLDER_URL="https://example.invalid/openworker-zh/install-zh.sh"
DEFAULT_PORT="8765"

usage() {
  cat <<EOF
OpenWorker 中文版
一行装好，打开就是中文界面。

用法
  bash scripts/install-zh.sh              安装
  bash scripts/install-zh.sh --check      只体检，不安装
  bash scripts/install-zh.sh --dry-run    预演，不写任何文件
  bash scripts/install-zh.sh --force      依赖已在时也重新安装
  bash scripts/install-zh.sh --help

你得到的是跑在自己电脑上的中文助手：后端负责对话，浏览器里是中文界面，令牌只留在本机。

这一行只做三件事：
① 检查 Python 与 Node.js 是否够用。不够就停下，不替你下载工具链。
② 准备后端虚拟环境，并装上界面依赖。
③ 写好两份本机启动脚本。屏幕上不出现令牌。

装完你应当看见中文界面，而不是英文菜单。
这一行不制作桌面安装包。

兼容
  macOS 与 Linux 的 bash。Windows 请用 WSL，本脚本不声称能在 cmd 里跑。
  需要 Python 3.10 或更高、Node.js 20 或更高，以及 npm。
  状态目录默认在仓库里的 .openworker-state。
  可用 OPENWORKER_ZH_STATE_DIR 改位置，用 OPENWORKER_ZH_PORT 改后端端口（默认 ${DEFAULT_PORT}）。

占位分发地址（不要请求）
  ${PLACEHOLDER_URL}

开箱叙事的结构借鉴 dsh-pet（MIT）。文案和脚本是独立编写的。
EOF
}

warn() {
  printf '%s\n' "$1" >&2
}

python_ok() {
  command -v python3 >/dev/null 2>&1 || return 1
  python3 -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)'
}

node_ok() {
  command -v node >/dev/null 2>&1 || return 1
  node -e 'const major = Number(String(process.versions.node).split(".")[0]); process.exit(major >= 20 ? 0 : 1)'
}

npm_ok() {
  command -v npm >/dev/null 2>&1
}

resolve_root() {
  local root
  if [[ -n "${OPENWORKER_ZH_ROOT:-}" ]]; then
    root="${OPENWORKER_ZH_ROOT}"
  else
    root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
  fi
  if [[ ! -f "${root}/pyproject.toml" || ! -f "${root}/surfaces/gui/package.json" ]]; then
    warn "这里不像 OpenWorker 中文版的仓库根目录。"
    warn "请在克隆下来的仓库根目录执行："
    warn "bash scripts/install-zh.sh"
    warn "分发地址仍是占位符，本脚本不会去请求它："
    warn "${PLACEHOLDER_URL}"
    return 1
  fi
  printf '%s\n' "${root}"
}

validate_port() {
  local port="$1"
  if [[ ! "${port}" =~ ^[0-9]+$ ]] || [[ "10#${port}" -lt 1 ]] || [[ "10#${port}" -gt 65535 ]]; then
    warn "端口必须是 1 到 65535 的数字。"
    return 1
  fi
}

check_tools() {
  local missing=0
  if python_ok; then
    printf '%s\n' "Python …… 通过"
  else
    warn "Python …… 缺少。需要 3.10 或更高。本脚本不下载工具链。"
    missing=1
  fi
  if node_ok; then
    printf '%s\n' "Node.js …… 通过"
  else
    warn "Node.js …… 缺少。需要 20 或更高。本脚本不下载工具链。"
    missing=1
  fi
  if npm_ok; then
    printf '%s\n' "npm …… 通过"
  else
    warn "npm …… 缺少。装好 Node.js 之后它应该在一起。本脚本不下载工具链。"
    missing=1
  fi
  [[ "${missing}" -eq 0 ]]
}

already_installed() {
  local root="$1"
  [[ -x "${root}/.venv/bin/openworker-server" && -d "${root}/surfaces/gui/node_modules" ]]
}

install_deps() {
  local root="$1"
  local py="${root}/.venv/bin/python"
  printf '%s\n' "正在准备后端虚拟环境。"
  if [[ ! -x "${py}" ]]; then
    if ! python3 -m venv "${root}/.venv"; then
      warn "创建虚拟环境失败。请先装好 Python 的 venv 模块，然后重新执行这一行。"
      return 1
    fi
  fi
  printf '%s\n' "正在安装后端依赖。"
  "${py}" -m pip install --upgrade pip
  "${py}" -m pip install -e "${root}"
  printf '%s\n' "正在安装界面依赖。"
  (
    cd "${root}/surfaces/gui"
    if [[ -f package-lock.json && ! -d node_modules ]]; then
      npm ci
    else
      npm install
    fi
  )
}

write_token() {
  local state="$1" port="$2" file old_umask
  file="${state}/sidecar-${port}.token"
  mkdir -p "${state}"
  if [[ -s "${file}" ]]; then
    chmod 600 "${file}" || true
    return 0
  fi
  old_umask="$(umask)"
  umask 077
  python3 -c 'import secrets; print(secrets.token_hex(32))' > "${file}"
  umask "${old_umask}"
  chmod 600 "${file}"
}

write_launchers() {
  local root="$1" state="$2" port="$3"
  local root_q state_q
  root_q="$(printf '%q' "${root}")"
  state_q="$(printf '%q' "${state}")"
  mkdir -p "${state}"
  cat > "${state}/start-server.sh" <<EOF
#!/usr/bin/env bash
set -euo pipefail
ROOT=${root_q}
STATE=${state_q}
PORT=${port}
export COWORKER_STATE_DIR="\${STATE}"
export COWORKER_API_TOKEN="\$(cat "\${STATE}/sidecar-\${PORT}.token")"
cd "\${ROOT}"
exec "\${ROOT}/.venv/bin/openworker-server" --cwd "\${ROOT}" --port "\${PORT}"
EOF
  cat > "${state}/start-gui.sh" <<EOF
#!/usr/bin/env bash
set -euo pipefail
ROOT=${root_q}
STATE=${state_q}
PORT=${port}
export COWORKER_STATE_DIR="\${STATE}"
export VITE_COWORKER_API_TOKEN="\$(cat "\${STATE}/sidecar-\${PORT}.token")"
cd "\${ROOT}/surfaces/gui"
exec npm run dev -- --host
EOF
  chmod 700 "${state}/start-server.sh" "${state}/start-gui.sh"
}

print_story() {
  cat <<EOF
OpenWorker 中文版
一行装好，打开就是中文界面。

你得到的是跑在自己电脑上的中文助手：后端负责对话，浏览器里是中文界面，令牌只留在本机。

这一行只做三件事：
① 检查 Python 与 Node.js 是否够用。不够就停下，不替你下载工具链。
② 准备后端虚拟环境，并装上界面依赖。
③ 写好两份本机启动脚本。屏幕上不出现令牌。

装完你应当看见中文界面，而不是英文菜单。
这一行不制作桌面安装包。
EOF
}

print_next() {
  local state="$1"
  printf '%s\n' ""
  printf '%s\n' "装好了。"
  printf '%s\n' ""
  printf '%s\n' "接下来开两个终端。"
  printf '%s\n' ""
  printf '%s\n' "终端 1，启动后端："
  printf 'bash %q\n' "${state}/start-server.sh"
  printf '%s\n' ""
  printf '%s\n' "终端 2，启动中文界面："
  printf 'bash %q\n' "${state}/start-gui.sh"
  printf '%s\n' ""
  printf '%s\n' "然后用浏览器打开："
  printf '%s\n' "http://localhost:1420/"
  printf '%s\n' ""
  printf '%s\n' "应当是中文界面。如果白屏，先看终端里的报错。"
  printf '%s\n' "以后想确认环境还在，执行：bash scripts/install-zh.sh --check"
}

dry_run_footer() {
  printf '%s\n' "预演结束：不会创建虚拟环境，不会安装依赖，不会写入令牌。"
}

load_layout() {
  if ! ROOT="$(resolve_root)"; then
    return 1
  fi
  PORT="${OPENWORKER_ZH_PORT:-${DEFAULT_PORT}}"
  if ! validate_port "${PORT}"; then
    return 1
  fi
  if [[ -n "${OPENWORKER_ZH_STATE_DIR:-}" ]]; then
    STATE="${OPENWORKER_ZH_STATE_DIR}"
  else
    STATE="${ROOT}/.openworker-state"
  fi
}

cmd_check() {
  if ! load_layout; then
    return 1
  fi
  printf '%s\n' "OpenWorker 中文版体检"
  if ! check_tools; then
    warn "体检未通过。缺的工具补上之后再执行安装。"
    return 1
  fi
  if already_installed "${ROOT}"; then
    printf '%s\n' "体检通过：依赖已在，可以直接启动。"
  else
    printf '%s\n' "体检通过：工具齐全，可以执行一行安装。"
  fi
}

cmd_dry_run() {
  print_story
  if ! load_layout; then
    dry_run_footer
    return 1
  fi
  if ! check_tools; then
    dry_run_footer
    return 1
  fi
  printf '%s\n' "将要安装的仓库："
  printf '%s\n' "${ROOT}"
  printf '%s\n' "将要使用的状态目录："
  printf '%s\n' "${STATE}"
  dry_run_footer
}

cmd_install() {
  local force="${1}"
  print_story
  if ! load_layout; then
    return 1
  fi
  if ! check_tools; then
    warn "安装停下了。补上缺少的工具后再执行这一行。"
    return 1
  fi
  if already_installed "${ROOT}" && [[ "${force}" -eq 0 ]]; then
    printf '%s\n' "依赖已在，跳过安装。要重装请加 --force。"
  else
    install_deps "${ROOT}"
  fi
  write_token "${STATE}" "${PORT}"
  write_launchers "${ROOT}" "${STATE}" "${PORT}"
  print_next "${STATE}"
}

self_test() {
  local tmp fake repo out rc
  tmp="$(mktemp -d)"
  # shellcheck disable=SC2064
  trap "rm -rf $(printf '%q' "${tmp}")" EXIT
  fake="${tmp}/bin"
  repo="${tmp}/repo"
  mkdir -p "${fake}" "${repo}/surfaces/gui" "${tmp}/missing"
  printf '%s\n' '[project]' > "${repo}/pyproject.toml"
  printf '%s\n' '{}' > "${repo}/surfaces/gui/package.json"
  printf '%s\n' '#!/bin/sh' 'exit 0' > "${fake}/python3"
  printf '%s\n' '#!/bin/sh' 'exit 0' > "${fake}/node"
  printf '%s\n' '#!/bin/sh' 'exit 0' > "${fake}/npm"
  chmod 700 "${fake}/python3" "${fake}/node" "${fake}/npm"

  out="$(PATH="${fake}:/usr/bin:/bin" OPENWORKER_ZH_ROOT="${repo}" /usr/bin/bash "${BASH_SOURCE[0]}" --dry-run)"
  case "${out}" in
    *"一行装好，打开就是中文界面。"*) ;;
    *) warn "self-test: 预演缺少开箱叙事"; return 1 ;;
  esac
  case "${out}" in
    *"不会创建虚拟环境，不会安装依赖，不会写入令牌。"*) ;;
    *) warn "self-test: 预演缺少不写入声明"; return 1 ;;
  esac
  if [[ -e "${repo}/.venv" || -e "${repo}/.openworker-state" ]]; then
    warn "self-test: 预演写出了文件"
    return 1
  fi

  out="$(PATH="${fake}:/usr/bin:/bin" OPENWORKER_ZH_ROOT="${repo}" /usr/bin/bash "${BASH_SOURCE[0]}" --help)"
  case "${out}" in
    *"example.invalid"*) ;;
    *) warn "self-test: 帮助里没有占位地址"; return 1 ;;
  esac
  case "${out}" in
    *"dsh-pet（MIT）"*) ;;
    *) warn "self-test: 帮助里没有许可证说明"; return 1 ;;
  esac

  set +e
  out="$(PATH="${fake}:/usr/bin:/bin" OPENWORKER_ZH_ROOT="${repo}" /usr/bin/bash "${BASH_SOURCE[0]}" --check 2>&1)"
  rc=$?
  set -e
  if [[ "${rc}" -ne 0 ]]; then
    warn "self-test: 工具齐全时体检应当通过"
    warn "${out}"
    return 1
  fi
  case "${out}" in
    *"可以执行一行安装"*) ;;
    *) warn "self-test: 体检缺少可以安装的结论"; return 1 ;;
  esac

  set +e
  out="$(PATH="${tmp}/missing" OPENWORKER_ZH_ROOT="${repo}" /usr/bin/bash "${BASH_SOURCE[0]}" --check 2>&1)"
  rc=$?
  set -e
  if [[ "${rc}" -eq 0 ]]; then
    warn "self-test: 缺少工具时体检应当失败"
    return 1
  fi
  case "${out}" in
    *"缺少。需要 20"*) ;;
    *) warn "self-test: 缺少 Node.js 时没有说明"; warn "${out}"; return 1 ;;
  esac
  case "${out}" in
    *"缺少。需要 3.10"*) ;;
    *) warn "self-test: 缺少 Python 时没有说明"; warn "${out}"; return 1 ;;
  esac
  if [[ -e "${repo}/.venv" || -e "${repo}/.openworker-state" ]]; then
    warn "self-test: 失败的体检写出了文件"
    return 1
  fi

  set +e
  out="$(OPENWORKER_ZH_ROOT="${tmp}/no-such-repo" /usr/bin/bash "${BASH_SOURCE[0]}" --dry-run 2>&1)"
  rc=$?
  set -e
  if [[ "${rc}" -eq 0 ]]; then
    warn "self-test: 仓库根目录不对时预演应当失败"
    return 1
  fi
  case "${out}" in
    *"${PLACEHOLDER_URL}"*) ;;
    *) warn "self-test: 找不到仓库时没有提示占位地址"; warn "${out}"; return 1 ;;
  esac
  case "${out}" in
    *"不会创建虚拟环境，不会安装依赖，不会写入令牌。"*) ;;
    *) warn "self-test: 失败的预演仍须声明不写入"; return 1 ;;
  esac

  local spaced token mode
  spaced="${tmp}/state dir"
  write_token "${spaced}" 8765
  write_launchers "${repo}" "${spaced}" 8765
  /usr/bin/bash -n "${spaced}/start-server.sh"
  /usr/bin/bash -n "${spaced}/start-gui.sh"
  token="$(cat "${spaced}/sidecar-8765.token")"
  if [[ "${#token}" -ne 64 ]]; then
    warn "self-test: 令牌长度不对"
    return 1
  fi
  if grep -F "${token}" "${spaced}/start-server.sh" "${spaced}/start-gui.sh" >/dev/null; then
    warn "self-test: 启动脚本写入了令牌"
    return 1
  fi
  if mode="$(stat -c %a "${spaced}/sidecar-8765.token" 2>/dev/null)"; then
    :
  else
    mode="$(stat -f %OLp "${spaced}/sidecar-8765.token")"
  fi
  if [[ "${mode}" != "600" ]]; then
    warn "self-test: 令牌文件权限不是 600"
    return 1
  fi
  # 第二次写入必须沿用原令牌，不能换一把。
  write_token "${spaced}" 8765
  if [[ "$(cat "${spaced}/sidecar-8765.token")" != "${token}" ]]; then
    warn "self-test: 重复安装更换了令牌"
    return 1
  fi

  printf '%s\n' "self-test: 通过"
}

main() {
  local mode="install" force=0
  while [[ $# -gt 0 ]]; do
    case "$1" in
      -h|--help) mode="help" ;;
      --check) mode="check" ;;
      --dry-run) mode="dry-run" ;;
      --self-test) mode="self-test" ;;
      --force) force=1 ;;
      *)
        warn "不认识的参数。"
        warn "可执行：bash scripts/install-zh.sh --help"
        return 2
        ;;
    esac
    shift
  done

  case "${mode}" in
    help) usage ;;
    self-test) self_test ;;
    check) cmd_check ;;
    dry-run) cmd_dry_run ;;
    install) cmd_install "${force}" ;;
    *)
      warn "内部错误：未知模式。"
      return 2
      ;;
  esac
}

main "$@"
