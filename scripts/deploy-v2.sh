#!/usr/bin/env bash
# v2 telepítés: host hardening (daemon.json, auditd szabályok) + a javított alkalmazás-stack.
# Futtatás a vizsgált hoston: sudo ./scripts/deploy-v2.sh
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TARGET=/opt/booking            # natív Linux fájlrendszer (jogosultságok, secret fájlok miatt)

[[ $EUID -eq 0 ]] || { echo "sudo szükséges" >&2; exit 1; }

# 1. A v1 stack leállítása (a volume megmarad, a v1 bizonyíték már rögzítve van)
if [[ -f "$REPO_ROOT/infra/v1/compose.yaml" ]]; then
  docker compose -f "$REPO_ROOT/infra/v1/compose.yaml" down || true
fi

# 2. Host / daemon hardening (M-01, M-10)
install -m 0644 -o root -g root "$REPO_ROOT/infra/v2/host/daemon.json" /etc/docker/daemon.json
install -m 0640 -o root -g root "$REPO_ROOT/infra/v2/host/docker.rules" /etc/audit/rules.d/docker.rules
if ! augenrules --load; then
  echo "FIGYELEM: az auditd szabályok nem tölthetők be (pl. a WSL2 kernel nem támogatja az audit alrendszert)." >&2
fi
systemctl reset-failed docker docker.socket 2>/dev/null || true
systemctl restart docker

# 3. Az alkalmazás telepítése a célkönyvtárba
mkdir -p "$TARGET"
rm -rf "$TARGET/app" "$TARGET/infra"
mkdir -p "$TARGET/infra"
cp -r "$REPO_ROOT/app" "$TARGET/app"
cp -r "$REPO_ROOT/infra/v2" "$TARGET/infra/v2"
rm -rf "$TARGET/infra/v2/host"

# 4. Titkok generálása (M-03) – nem kerülnek a git repóba és az image-be
SECRETS="$TARGET/infra/v2/secrets"
mkdir -p "$SECRETS"; chmod 0700 "$SECRETS"
for s in db_password admin_password; do
  if [[ ! -s "$SECRETS/$s.txt" ]]; then
    openssl rand -hex 24 > "$SECRETS/$s.txt"
  fi
  # A fájl a userns-remap miatt a konténer (leképezett) felhasználója számára olvasható kell legyen;
  # a hoston a 0700-as szülőkönyvtár védi.
  chmod 0644 "$SECRETS/$s.txt"
done

# 5. Build és indítás
cd "$TARGET/infra/v2"
docker compose build --pull
docker compose up -d --wait
docker compose ps
