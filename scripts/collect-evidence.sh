#!/usr/bin/env bash
# Bizonyítékgyűjtés a CIS Docker Benchmark audithoz.
#
# Használat (a vizsgált Linux hoston, root jogosultsággal):
#   sudo ./scripts/collect-evidence.sh <címke> [compose-könyvtár]
#   pl.: sudo ./scripts/collect-evidence.sh v1 infra/v1
#
# Előfeltételek:
#   - docker, trivy, sha256sum telepítve
#   - docker-bench-security klónozva, útvonala a DOCKER_BENCH_DIR változóban
#     (alapértelmezés: /opt/docker-bench-security)
#
# Kimenet: evidence/<UTC dátum>_<címke>/ , benne SHA256SUMS és meta/run.log

set -uo pipefail

LABEL="${1:?Adj meg egy címkét, pl. v1 vagy v2}"
COMPOSE_DIR="${2:-}"
DOCKER_BENCH_DIR="${DOCKER_BENCH_DIR:-/opt/docker-bench-security}"

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
RUN_ID="$(date -u +%Y-%m-%dT%H%MZ)_${LABEL}"
OUT="${REPO_ROOT}/evidence/${RUN_ID}"

if [[ $EUID -ne 0 ]]; then
  echo "Root jogosultság szükséges (a CIS host-ellenőrzésekhez): sudo $0 $*" >&2
  exit 1
fi
if [[ -e "$OUT" ]]; then
  echo "Már létezik: $OUT – bizonyítékot nem írunk felül." >&2
  exit 1
fi

mkdir -p "$OUT"/{meta,config,docker,docker-bench,trivy}
LOG="$OUT/meta/run.log"

log()  { echo "[$(date -u +%FT%TZ)] $*" | tee -a "$LOG"; }
run()  { # run <kimeneti fájl> <parancs...>
  local out="$1"; shift
  log "RUN: $* > ${out#"$OUT"/}"
  "$@" >"$out" 2>&1 || log "  WARN: kilépési kód $? ($*)"
}

# Titkok maszkolása (env változók értéke, ha a nevük jelszóra/kulcsra utal).
mask_secrets() {
  sed -E -i 's/("[A-Za-z0-9_]*(PASSWORD|PASSWD|SECRET|TOKEN|API_KEY|PRIVATE_KEY|DATABASE_URL)[A-Za-z0-9_]*=)[^"]*"/\1***MASKED***"/g' "$1"
}

log "Mérés indul: RUN_ID=${RUN_ID}, auditor=${SUDO_USER:-root}"

# --- 1. Meta: környezet és eszközverziók -----------------------------------
run "$OUT/meta/host.txt"          bash -c 'hostname; uname -a; cat /etc/os-release'
run "$OUT/meta/docker-version.txt" docker version
run "$OUT/meta/docker-info.txt"    docker info
run "$OUT/meta/trivy-version.txt"  trivy --version
run "$OUT/meta/docker-bench-commit.txt" git -C "$DOCKER_BENCH_DIR" rev-parse HEAD

# --- 2. Konfigurációs fájlok (dokumentumvizsgálat) -------------------------
[[ -f /etc/docker/daemon.json ]] && cp -p /etc/docker/daemon.json "$OUT/config/" \
  || log "INFO: /etc/docker/daemon.json nem létezik"
run "$OUT/config/auditctl-rules.txt" auditctl -l
[[ -d /etc/audit/rules.d ]] && run "$OUT/config/audit-rules.d.txt" bash -c 'head -n 200 /etc/audit/rules.d/*.rules'
# CIS 1.1.1 manuális ellenőrzéséhez: külön partíción van-e a Docker gyökérkönyvtár
run "$OUT/config/mounts-docker.txt" bash -c \
  'docker info -f "{{.DockerRootDir}}"; findmnt -T /var/lib/docker -o TARGET,SOURCE,FSTYPE; findmnt -R /var/lib/docker -o TARGET,SOURCE,FSTYPE'
run "$OUT/config/docker-service.txt" systemctl cat docker.service docker.socket
run "$OUT/config/docker-files-perms.txt" bash -c \
  'ls -la /etc/docker /var/run/docker.sock /lib/systemd/system/docker.* /usr/lib/systemd/system/docker.* 2>&1'
if [[ -n "$COMPOSE_DIR" ]]; then
  mkdir -p "$OUT/config/compose"
  SRC="$COMPOSE_DIR"; [[ -d "$REPO_ROOT/$COMPOSE_DIR" ]] && SRC="$REPO_ROOT/$COMPOSE_DIR"
  if [[ -d "$SRC" ]]; then
    (cd "$SRC" && find . -maxdepth 3 \( -name 'compose*.y*ml' -o -name 'docker-compose*.y*ml' \
        -o -name 'Dockerfile*' -o -name '*.Dockerfile' -o -name 'nginx.conf' -o -name '.dockerignore' \) -exec cp --parents {} "$OUT/config/compose/" \;)
    log "Compose / Dockerfile másolatok: $SRC"
  else
    log "HIBA: a compose-könyvtár nem található: $COMPOSE_DIR"
  fi
fi

# --- 3. Megfigyelés: futó objektumok ---------------------------------------
run "$OUT/docker/ps.txt"        docker ps -a --no-trunc
run "$OUT/docker/images.txt"    docker images --digests --no-trunc
run "$OUT/docker/networks.txt"  docker network ls
run "$OUT/docker/volumes.txt"   docker volume ls
CONTAINERS="$(docker ps -q)"
if [[ -n "$CONTAINERS" ]]; then
  run "$OUT/docker/inspect-containers.json" docker inspect $CONTAINERS
  mask_secrets "$OUT/docker/inspect-containers.json"
  log "Titkok maszkolva: docker/inspect-containers.json"
fi
NETWORKS="$(docker network ls -q)"
[[ -n "$NETWORKS" ]] && run "$OUT/docker/inspect-networks.json" docker network inspect $NETWORKS

# --- 4. CIS Docker Benchmark: docker-bench-security ------------------------
if [[ -x "$DOCKER_BENCH_DIR/docker-bench-security.sh" || -f "$DOCKER_BENCH_DIR/docker-bench-security.sh" ]]; then
  log "RUN: docker-bench-security"
  # A szkriptet a saját könyvtárából kell futtatni (relatív include-ok).
  # bash-sel futtatjuk: a 2.2, 2.4, 2.5, 2.8, 2.9, 2.12 ellenőrzések bash-szintaxist ([[ ]]) használnak,
  # Ubuntun az `sh` (dash) alatt ezek hamisan WARN eredményt adnak (lásd a 2026-11-07T1549Z_v2 mérést).
  log "  shell: bash $(bash --version | head -1)"
  (cd "$DOCKER_BENCH_DIR" && bash docker-bench-security.sh -b -p -l "$OUT/docker-bench/docker-bench.log") \
    >"$OUT/docker-bench/stdout.txt" 2>&1 || log "  WARN: docker-bench kilépési kód $?"
else
  log "HIBA: docker-bench-security nem található itt: $DOCKER_BENCH_DIR"
fi

# --- 5. Trivy: image-sérülékenységek és konfigurációs hibák ----------------
IMAGES="$(docker ps --format '{{.Image}}' | sort -u)"
for img in $IMAGES; do
  safe="$(echo "$img" | tr '/:@' '___')"
  run "$OUT/trivy/image_${safe}.json" trivy image --quiet --scanners vuln --format json "$img"
  run "$OUT/trivy/image_${safe}.txt"  trivy image --scanners vuln --severity HIGH,CRITICAL "$img"
done
if [[ -n "$COMPOSE_DIR" ]]; then
  run "$OUT/trivy/config.json" trivy config --quiet --format json "$OUT/config/compose"
  run "$OUT/trivy/config.txt"  trivy config "$OUT/config/compose"
fi

# --- 6. Integritás ----------------------------------------------------------
log "Mérés vége, hash-ek készítése"
(cd "$OUT" && find . -type f ! -name SHA256SUMS -print0 | sort -z | xargs -0 sha256sum > SHA256SUMS)
[[ -n "${SUDO_USER:-}" ]] && chown -R "$SUDO_USER": "$OUT"

echo
echo "Kész: $OUT"
echo "Ellenőrzés később: (cd \"$OUT\" && sha256sum -c SHA256SUMS)"
