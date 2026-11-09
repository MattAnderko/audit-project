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
install -D -m 0644 -o root -g root "$REPO_ROOT/infra/v2/host/daemon.json" /etc/docker/daemon.json
install -D -m 0640 -o root -g root "$REPO_ROOT/infra/v2/host/docker.rules" /etc/audit/rules.d/docker.rules
# Újratelepítéskor a már betöltött Docker-szabályok ("Rule exists") törlése, csak a docker kulcsúak
auditctl -D -k docker >/dev/null 2>&1 || true
if ! augenrules --load; then
  echo "FIGYELEM: az auditd szabályok nem tölthetők be (pl. a kernel audit támogatása hiányzik, vagy egy szabály nem létező útvonalra mutat)." >&2
fi
systemctl reset-failed docker docker.socket 2>/dev/null || true
systemctl restart docker

# 3. Az alkalmazás telepítése a célkönyvtárba
mkdir -p "$TARGET"
# A titkok tartós helye: újratelepítéskor nem törlődik. Ha a titok újragenerálódna, a meglévő
# adatbázis-volume a régi jelszót őrizné (a PostgreSQL csak az első inicializáláskor állítja be).
SECRETS_STORE="$TARGET/secrets"
mkdir -p "$SECRETS_STORE"; chmod 0700 "$SECRETS_STORE"
# Korábbi elrendezés átvétele: a régebbi telepítések az infra/v2/secrets alatt tárolták a titkokat
if [[ -d "$TARGET/infra/v2/secrets" ]]; then
  for f in "$TARGET/infra/v2/secrets/"*.txt; do
    [[ -s "$f" && ! -e "$SECRETS_STORE/$(basename "$f")" ]] && install -m 0600 "$f" "$SECRETS_STORE/"
  done
fi
rm -rf "$TARGET/app" "$TARGET/infra"
mkdir -p "$TARGET/infra"
cp -r "$REPO_ROOT/app" "$TARGET/app"
cp -r "$REPO_ROOT/infra/v2" "$TARGET/infra/v2"
rm -rf "$TARGET/infra/v2/host"

# 4. Titkok generálása (M-03) – nem kerülnek a git repóba és az image-be
SECRETS="$TARGET/infra/v2/secrets"
mkdir -p "$SECRETS"; chmod 0700 "$SECRETS"
for s in db_password admin_password; do
  if [[ ! -s "$SECRETS_STORE/$s.txt" ]]; then
    (umask 077; openssl rand -hex 24 > "$SECRETS_STORE/$s.txt")
  fi
  # A fájl a userns-remap miatt a konténer (leképezett) felhasználója számára olvasható kell legyen;
  # a hoston a 0700-as szülőkönyvtár védi.
  install -m 0644 "$SECRETS_STORE/$s.txt" "$SECRETS/$s.txt"
done

# 5. Build és indítás
cd "$TARGET/infra/v2"
docker compose build --pull
docker compose up -d --wait
docker compose ps
