#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

ACTION="install"
if [[ $# -gt 0 && "${1}" != -* ]]; then
  ACTION="$1"
  shift
fi

INSTALL_DIR="${INSTALL_DIR:-$REPO_DIR}"
SERVICE_NAME="${SERVICE_NAME:-xpert}"
SERVICE_USER="${SERVICE_USER:-root}"
PYTHON_BIN="${PYTHON_BIN:-python3}"

SKIP_APT=0
SKIP_FRONTEND=0
SKIP_SYSTEMD=0
SKIP_MIGRATIONS=0
SKIP_XRAY_CHECK=0

APP_DIR="$REPO_DIR"
APT_UPDATED=0

log() {
  printf '[xpert-install] %s\n' "$*"
}

fail() {
  printf '[xpert-install] ERROR: %s\n' "$*" >&2
  exit 1
}

usage() {
  cat <<'EOF'
Usage:
  bash scripts/install.sh install [options]
  bash scripts/install.sh build
  bash scripts/install.sh audit

Commands:
  install   Full setup: backend deps + migrations + dashboard build + systemd service
  build     Only rebuild dashboard bundle (dist -> build)
  audit     Run duplicate-file audit report

Options (for install):
  --install-dir <path>      Target install directory (default: current repo)
  --service-name <name>     Systemd service name (default: xpert)
  --service-user <user>     Systemd service user (default: root)
  --python-bin <bin>        Python executable (default: python3)
  --skip-apt                Do not install apt packages
  --skip-frontend           Skip dashboard npm build
  --skip-systemd            Do not create/restart systemd service
  --skip-migrations         Skip alembic upgrade head
  --skip-xray-check         Skip warning if xray binary is missing
  -h, --help                Show this help

Environment overrides:
  INSTALL_DIR, SERVICE_NAME, SERVICE_USER, PYTHON_BIN
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --install-dir)
      [[ $# -ge 2 ]] || fail "Missing value for --install-dir"
      INSTALL_DIR="$2"
      shift 2
      ;;
    --service-name)
      [[ $# -ge 2 ]] || fail "Missing value for --service-name"
      SERVICE_NAME="$2"
      shift 2
      ;;
    --service-user)
      [[ $# -ge 2 ]] || fail "Missing value for --service-user"
      SERVICE_USER="$2"
      shift 2
      ;;
    --python-bin)
      [[ $# -ge 2 ]] || fail "Missing value for --python-bin"
      PYTHON_BIN="$2"
      shift 2
      ;;
    --skip-apt)
      SKIP_APT=1
      shift
      ;;
    --skip-frontend)
      SKIP_FRONTEND=1
      shift
      ;;
    --skip-systemd)
      SKIP_SYSTEMD=1
      shift
      ;;
    --skip-migrations)
      SKIP_MIGRATIONS=1
      shift
      ;;
    --skip-xray-check)
      SKIP_XRAY_CHECK=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      fail "Unknown option: $1"
      ;;
  esac
done

apt_install() {
  if [[ "$SKIP_APT" -eq 1 ]]; then
    fail "Missing dependencies and --skip-apt is set"
  fi
  if [[ "$EUID" -ne 0 ]]; then
    fail "Root privileges are required to install apt packages"
  fi
  if [[ "$APT_UPDATED" -eq 0 ]]; then
    log "Running apt-get update..."
    apt-get update -y
    APT_UPDATED=1
  fi
  log "Installing apt packages: $*"
  apt-get install -y "$@"
}

ensure_cmd() {
  local cmd="$1"
  shift
  if command -v "$cmd" >/dev/null 2>&1; then
    return 0
  fi
  apt_install "$@"
  command -v "$cmd" >/dev/null 2>&1 || fail "Command not found after install: $cmd"
}

copy_project_if_needed() {
  mkdir -p "$INSTALL_DIR"
  INSTALL_DIR="$(cd "$INSTALL_DIR" && pwd)"

  if [[ "$INSTALL_DIR" == "$REPO_DIR" ]]; then
    APP_DIR="$REPO_DIR"
    return 0
  fi

  log "Syncing project into ${INSTALL_DIR}"
  if command -v rsync >/dev/null 2>&1; then
    rsync -a \
      --exclude '.git/' \
      --exclude '.venv/' \
      --exclude '__pycache__/' \
      --exclude 'app/dashboard/node_modules/' \
      --exclude 'app/dashboard/dist/' \
      --exclude 'app/dashboard/build/' \
      --exclude '.env' \
      --exclude 'db.sqlite3' \
      --exclude 'data/' \
      "${REPO_DIR}/" "${INSTALL_DIR}/"
  else
    (
      cd "$REPO_DIR"
      tar \
        --exclude=.git \
        --exclude=.venv \
        --exclude=__pycache__ \
        --exclude=app/dashboard/node_modules \
        --exclude=app/dashboard/dist \
        --exclude=app/dashboard/build \
        --exclude=.env \
        --exclude=db.sqlite3 \
        --exclude=data \
        -cf - .
    ) | (
      cd "$INSTALL_DIR"
      tar -xf -
    )
  fi

  APP_DIR="$INSTALL_DIR"
}

prepare_env_file() {
  if [[ -f "$APP_DIR/.env" ]]; then
    return 0
  fi
  if [[ ! -f "$APP_DIR/.env.example" ]]; then
    fail "Missing .env.example in ${APP_DIR}"
  fi
  cp "$APP_DIR/.env.example" "$APP_DIR/.env"
  log "Created ${APP_DIR}/.env from .env.example"
}

setup_python() {
  ensure_cmd "$PYTHON_BIN" python3

  # Some images have python3 but miss ensurepip/venv runtime packages.
  local py_mm py_venv_pkg
  py_mm="$("$PYTHON_BIN" - <<'PY'
import sys
print(f"{sys.version_info.major}.{sys.version_info.minor}")
PY
)"
  py_venv_pkg="python${py_mm}-venv"

  local venv_probe_dir
  venv_probe_dir="$(mktemp -d)"
  if ! "$PYTHON_BIN" -m venv "${venv_probe_dir}/probe" >/dev/null 2>&1; then
    if [[ "$SKIP_APT" -eq 1 ]]; then
      rm -rf "$venv_probe_dir"
      fail "python venv is not usable. Install packages manually: ${py_venv_pkg} python3-venv python3-pip"
    fi

    local venv_pkgs=("python3-venv" "python3-pip")
    if command -v apt-cache >/dev/null 2>&1 && apt-cache show "$py_venv_pkg" >/dev/null 2>&1; then
      venv_pkgs=("$py_venv_pkg" "${venv_pkgs[@]}")
    fi
    log "Installing missing Python venv packages (${venv_pkgs[*]})..."
    apt_install "${venv_pkgs[@]}"
    rm -rf "$venv_probe_dir"
    venv_probe_dir="$(mktemp -d)"
    "$PYTHON_BIN" -m venv "${venv_probe_dir}/probe" >/dev/null 2>&1 || {
      rm -rf "$venv_probe_dir"
      fail "Unable to create virtualenv even after installing venv packages"
    }
  fi
  rm -rf "$venv_probe_dir"

  if [[ ! -x "$APP_DIR/.venv/bin/python" || ! -x "$APP_DIR/.venv/bin/pip" ]]; then
    if [[ -d "$APP_DIR/.venv" ]]; then
      log "Detected broken virtualenv at ${APP_DIR}/.venv, recreating..."
      rm -rf "$APP_DIR/.venv"
    fi
    log "Creating virtualenv at ${APP_DIR}/.venv"
    "$PYTHON_BIN" -m venv "$APP_DIR/.venv"
  fi

  if [[ ! -x "$APP_DIR/.venv/bin/pip" ]]; then
    log "Bootstrapping pip inside virtualenv..."
    "$APP_DIR/.venv/bin/python" -m ensurepip --upgrade || true
  fi

  [[ -x "$APP_DIR/.venv/bin/pip" ]] || fail "pip is missing in ${APP_DIR}/.venv. Install python3-venv/python3-pip and retry."

  log "Installing backend dependencies..."
  PIP_DISABLE_PIP_VERSION_CHECK=1 "$APP_DIR/.venv/bin/python" -m pip install --no-input -r "$APP_DIR/requirements.txt"
}

run_migrations() {
  if [[ "$SKIP_MIGRATIONS" -eq 1 ]]; then
    log "Skipping migrations (--skip-migrations)"
    return 0
  fi
  log "Running alembic migrations..."
  (
    cd "$APP_DIR"
    "$APP_DIR/.venv/bin/alembic" upgrade head
  )
}

node_major() {
  if ! command -v node >/dev/null 2>&1; then
    echo 0
    return 0
  fi
  node -p "Number(process.versions.node.split('.')[0])" 2>/dev/null || echo 0
}

ensure_modern_node() {
  local min_major=18
  local major
  local nodesource_list="/etc/apt/sources.list.d/nodesource.list"
  major="$(node_major)"
  if command -v npm >/dev/null 2>&1 && [[ "$major" =~ ^[0-9]+$ ]] && (( major >= min_major )); then
    log "Using Node.js $(node -v) and npm $(npm -v)"
    return 0
  fi

  if [[ "$SKIP_APT" -eq 1 ]]; then
    fail "Node.js >=${min_major} and npm are required for dashboard build. Re-run without --skip-apt or install Node.js manually."
  fi
  if [[ "$EUID" -ne 0 ]]; then
    fail "Root privileges are required to install Node.js"
  fi

  # Remove stale NodeSource entry from failed previous runs before first apt update.
  if [[ -f "$nodesource_list" ]]; then
    rm -f "$nodesource_list"
  fi

  log "Installing Node.js 20.x (required for Vite build)..."
  apt_install ca-certificates curl gnupg
  install -d -m 0755 /etc/apt/keyrings
  if [[ ! -f /etc/apt/keyrings/nodesource.gpg ]]; then
    curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key \
      | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg
  fi

  local codename
  codename="$(. /etc/os-release && echo "${VERSION_CODENAME:-}")"
  [[ -n "$codename" ]] || codename="nodistro"

  cat >"$nodesource_list" <<EOF
deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_20.x ${codename} main
EOF

  # NodeSource can return 404 for distro codenames on some mirrors.
  # Fallback to "nodistro" to keep installation stable.
  if ! apt-get update -y; then
    if [[ "$codename" != "nodistro" ]]; then
      log "NodeSource repo for '${codename}' is unavailable, retrying with 'nodistro'..."
      cat >"$nodesource_list" <<EOF
deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_20.x nodistro main
EOF
      apt-get update -y || fail "Failed to refresh apt indexes for NodeSource repository"
    else
      fail "Failed to refresh apt indexes for NodeSource repository"
    fi
  fi
  APT_UPDATED=1
  apt_install nodejs
  hash -r || true

  major="$(node_major)"
  if ! command -v npm >/dev/null 2>&1 || ! [[ "$major" =~ ^[0-9]+$ ]] || (( major < min_major )); then
    fail "Failed to provision Node.js >=${min_major}. Current: node=$(node -v 2>/dev/null || echo none), npm=$(npm -v 2>/dev/null || echo none)"
  fi

  log "Using Node.js $(node -v) and npm $(npm -v)"
}

build_frontend() {
  if [[ "$SKIP_FRONTEND" -eq 1 ]]; then
    log "Skipping dashboard build (--skip-frontend)"
    return 0
  fi

  ensure_modern_node

  local dashboard_dir="$APP_DIR/app/dashboard"
  [[ -d "$dashboard_dir" ]] || fail "Dashboard directory not found: $dashboard_dir"

  log "Installing dashboard dependencies and building..."
  (
    cd "$dashboard_dir"
    if [[ -f package-lock.json ]]; then
      npm ci
    else
      npm install
    fi
    npm run build
    mkdir -p build
    cp -a dist/. build/
  )
}

systemd_available() {
  command -v systemctl >/dev/null 2>&1 && [[ -d /run/systemd/system ]]
}

install_systemd_service() {
  if [[ "$SKIP_SYSTEMD" -eq 1 ]]; then
    log "Skipping systemd setup (--skip-systemd)"
    return 0
  fi
  if ! systemd_available; then
    log "Systemd is not available in this environment. Skipping service setup."
    return 0
  fi
  if [[ "$EUID" -ne 0 ]]; then
    fail "Root privileges are required to install systemd service"
  fi
  if ! id -u "$SERVICE_USER" >/dev/null 2>&1; then
    fail "Service user does not exist: $SERVICE_USER"
  fi

  local unit_file="/etc/systemd/system/${SERVICE_NAME}.service"
  log "Writing systemd unit: ${unit_file}"
  cat >"$unit_file" <<EOF
[Unit]
Description=Xpert
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=${SERVICE_USER}
WorkingDirectory=${APP_DIR}
Environment=PYTHONUNBUFFERED=1
Environment=PATH=${APP_DIR}/.venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
ExecStart=${APP_DIR}/.venv/bin/python ${APP_DIR}/main.py
Restart=always
RestartSec=3
LimitNOFILE=1048576

[Install]
WantedBy=multi-user.target
EOF

  systemctl daemon-reload
  systemctl enable "$SERVICE_NAME"
  systemctl restart "$SERVICE_NAME"

  if systemctl --quiet is-active "$SERVICE_NAME"; then
    log "Service started: ${SERVICE_NAME}"
  else
    systemctl --no-pager --full status "$SERVICE_NAME" || true
    fail "Service failed to start: ${SERVICE_NAME}"
  fi
}

read_env_value() {
  local key="$1"
  local file="$2"
  local value

  [[ -f "$file" ]] || return 0
  value="$(grep -E "^[[:space:]]*${key}[[:space:]]*=" "$file" | tail -n1 | sed -E 's/^[^=]*=[[:space:]]*//; s/[[:space:]]+$//; s/^"//; s/"$//' || true)"
  printf '%s' "$value"
}

check_xray() {
  if [[ "$SKIP_XRAY_CHECK" -eq 1 ]]; then
    return 0
  fi
  if command -v xray >/dev/null 2>&1; then
    return 0
  fi
  log "WARNING: xray binary not found in PATH."
  log "Install Xray before production use: https://github.com/XTLS/Xray-install"
}

print_summary() {
  local port
  local host_ip

  port="$(read_env_value "UVICORN_PORT" "$APP_DIR/.env")"
  port="${port:-8000}"
  host_ip="$(hostname -I 2>/dev/null | awk '{print $1}' || true)"
  host_ip="${host_ip:-127.0.0.1}"

  log "Done."
  log "Panel URL: http://${host_ip}:${port}/dashboard/"
  if [[ "$SKIP_SYSTEMD" -eq 0 ]] && systemd_available; then
    log "Service: systemctl status ${SERVICE_NAME}"
  fi
  log "Duplicate audit: bash ${APP_DIR}/scripts/audit_duplicates.sh"
}

install_all() {
  if [[ "$EUID" -ne 0 ]]; then
    fail "Run install as root (sudo)."
  fi

  copy_project_if_needed
  prepare_env_file
  setup_python
  run_migrations
  build_frontend
  check_xray
  install_systemd_service
  print_summary
}

case "$ACTION" in
  install)
    install_all
    ;;
  build)
    APP_DIR="$REPO_DIR"
    build_frontend
    ;;
  audit)
    bash "${SCRIPT_DIR}/audit_duplicates.sh" "$REPO_DIR"
    ;;
  *)
    usage
    exit 1
    ;;
esac
