#!/usr/bin/env bash
# A v2 stack funkcionális és izolációs ellenőrzése, bizonyítékként mentve.
# Futtatás (a docker csoport tagjaként, a v2 telepítése után): ./scripts/functional-test.sh
# Kimenet: evidence/<UTC időbélyeg>_v2-functional/functional.txt + SHA256SUMS
set -uo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$REPO_ROOT/evidence/$(date -u +%Y-%m-%dT%H%MZ)_v2-functional"
[[ -e "$OUT" ]] && { echo "Már létezik: $OUT" >&2; exit 1; }
mkdir -p "$OUT"
export DOCKER_CONTEXT=default
B=http://127.0.0.1:8080
APP=booking-v2-app-1

code() { curl -s -o /dev/null -w '%{http_code}' "$@"; }

{
  echo "# v2 funkcionális teszt, $(date -u +%FT%TZ), host: $(hostname)"
  echo
  echo "## Alkalmazás a proxyn keresztül ($B)"
  echo "GET  /                         -> $(code "$B/")"
  SLOT=$(curl -s "$B/" | grep -oE '/book/[0-9]+' | head -1)
  echo "POST $SLOT (foglalás)          -> $(code -X POST -d 'name=Teszt Elek' -d 'email=teszt@example.com' "$B$SLOT")"
  echo "GET  /admin (hitelesítés nélkül) -> $(code "$B/admin")"
  echo "GET  /admin (v1 jelszó)          -> $(code -u admin:admin123 "$B/admin")"
  PW=$(docker exec "$APP" cat /run/secrets/admin_password)
  echo "GET  /admin (v2 secret)          -> $(code -u "admin:$PW" "$B/admin")"
  unset PW
  echo
  IP=$(ip -4 route get 1.1.1.1 2>/dev/null | grep -oP 'src \K[0-9.]+')
  echo "## Elérhetőség a host hálózati címén ($IP)"
  for p in 80 8000 5432 8080; do
    if timeout 2 bash -c "</dev/tcp/$IP/$p" 2>/dev/null; then echo "port $p: NYITOTT"; else echo "port $p: zárt"; fi
  done
  echo
  echo "## Az app konténer belülről"
  echo "id:                 $(docker exec "$APP" id)"
  echo "root fs írása:      $(docker exec "$APP" sh -c 'touch /x 2>&1 || true')"
  echo "jelszó-jellegű env: $(docker exec "$APP" env | grep -iE 'pass|secret' | sed -E 's/=.*/=<érték nem jelenik meg>/' | tr '\n' ' ')"
  echo "AppArmor profil:    $(docker inspect -f '{{.AppArmorProfile}}' "$APP")"
  echo
  echo "## userns-remap: az app folyamat felhasználója a hoston"
  echo "konténer uid 10001 -> host uid $(ps -o uid= -p "$(docker inspect -f '{{.State.Pid}}' "$APP")" | tr -d ' ')"
} | tee "$OUT/functional.txt"

(cd "$OUT" && sha256sum functional.txt > SHA256SUMS)
echo; echo "Kész: $OUT"
