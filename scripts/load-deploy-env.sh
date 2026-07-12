#!/bin/bash
# 从仓库根目录的 .env.deploy 加载部署配置（该文件不入库）。

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    echo "请通过 source 使用: source scripts/load-deploy-env.sh" >&2
    exit 1
fi

_load_deploy_env_script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${_load_deploy_env_script_dir}/.." && pwd)"
DEPLOY_ENV_FILE="${REPO_ROOT}/.env.deploy"

if [[ ! -f "${DEPLOY_ENV_FILE}" ]]; then
    echo "缺少 ${DEPLOY_ENV_FILE}" >&2
    echo "请执行: cp .env.deploy.example .env.deploy" >&2
    echo "然后填写你的部署服务器信息。" >&2
    return 1 2>/dev/null || exit 1
fi

set -a
# shellcheck disable=SC1090
source "${DEPLOY_ENV_FILE}"
set +a

_require_deploy_var() {
    local name="$1"
    if [[ -z "${!name:-}" ]]; then
        echo "缺少必填环境变量: ${name}（在 .env.deploy 中设置）" >&2
        return 1 2>/dev/null || exit 1
    fi
}

_require_deploy_var DEPLOY_REMOTE_USER
_require_deploy_var DEPLOY_REMOTE_HOST
_require_deploy_var DEPLOY_PUBLIC_URL

DEPLOY_BACKEND_REMOTE_PATH="${DEPLOY_BACKEND_REMOTE_PATH:-/home/josie/apps/family-bills-backend}"
DEPLOY_FRONTEND_REMOTE_PATH="${DEPLOY_FRONTEND_REMOTE_PATH:-/var/www/family-bills-frontend}"
DEPLOY_SERVICE_NAME="${DEPLOY_SERVICE_NAME:-family-bills-backend}"

# 从 https://example.com 提取 example.com
DEPLOY_PUBLIC_HOST="${DEPLOY_PUBLIC_URL#*://}"
DEPLOY_PUBLIC_HOST="${DEPLOY_PUBLIC_HOST%%/*}"
