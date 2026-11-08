#!/usr/bin/env bash
# A vizsgált host előkészítése: Docker Engine, Trivy, docker-bench-security, auditd (Manjaro/Arch esetén AppArmor is).
# Ez a v1 ("naiv") host-állapot: Docker a disztribúció / a Docker hivatalos csomagjaiból, alapértelmezett beállításokkal.
# Támogatott: Ubuntu 24.04 (apt) és Manjaro / Arch Linux (pacman).
# Futtatás: sudo ./scripts/setup-host.sh
set -euo pipefail

[[ $EUID -eq 0 ]] || { echo "sudo szükséges: sudo $0" >&2; exit 1; }

# A korábbi mérésekkel azonos docker-bench-security verzió (CIS Docker Benchmark v1.6.0)
DOCKER_BENCH_COMMIT=154869d

if command -v apt-get >/dev/null 2>&1; then
  export DEBIAN_FRONTEND=noninteractive
  apt-get update -q
  apt-get install -y -q ca-certificates curl gnupg git jq auditd

  install -m 0755 -d /etc/apt/keyrings

  # Docker Engine (hivatalos repó)
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
  chmod a+r /etc/apt/keyrings/docker.asc
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
    > /etc/apt/sources.list.d/docker.list

  # Trivy (Aqua Security repó)
  curl -fsSL https://aquasecurity.github.io/trivy-repo/deb/public.key | gpg --dearmor --yes -o /etc/apt/keyrings/trivy.gpg
  echo "deb [signed-by=/etc/apt/keyrings/trivy.gpg] https://aquasecurity.github.io/trivy-repo/deb generic main" \
    > /etc/apt/sources.list.d/trivy.list

  apt-get update -q
  apt-get install -y -q docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin trivy
  systemctl enable --now docker

elif command -v pacman >/dev/null 2>&1; then
  # Manjaro / Arch: Docker Engine, Trivy, auditd és AppArmor a disztribúció csomagjaiból.
  pacman -S --needed --noconfirm docker trivy audit apparmor git jq
  # Compose és buildx plugin csak akkor, ha még nincs (pl. a docker-desktop csomag már biztosítja)
  docker compose version >/dev/null 2>&1 || pacman -S --needed --noconfirm docker-compose
  docker buildx version  >/dev/null 2>&1 || pacman -S --needed --noconfirm docker-buildx
  systemctl enable --now docker.service auditd.service apparmor.service
  # Az AppArmort a kernelnek is be kell kapcsolnia (lsm= boot paraméter): scripts/enable-apparmor-grub.sh, utána újraindítás.
  if ! grep -qw apparmor /sys/kernel/security/lsm 2>/dev/null; then
    echo "FIGYELEM: az AppArmor a kernelben nem aktív. Futtasd: sudo ./scripts/enable-apparmor-grub.sh, majd indítsd újra a gépet." >&2
  fi

else
  echo "Nem támogatott disztribúció (sem apt, sem pacman)." >&2
  exit 1
fi

# docker-bench-security (CIS Docker Benchmark automatizált ellenőrzés), rögzített verzión
if [[ ! -d /opt/docker-bench-security ]]; then
  git clone https://github.com/docker/docker-bench-security.git /opt/docker-bench-security
fi
git -C /opt/docker-bench-security checkout -q "$DOCKER_BENCH_COMMIT"

# A felhasználó a docker csoportba (kényelmi lépés, a v1 része)
if [[ -n "${SUDO_USER:-}" ]]; then usermod -aG docker "$SUDO_USER"; fi

docker version --format 'Docker {{.Server.Version}}'
trivy --version | head -1
git -C /opt/docker-bench-security rev-parse --short HEAD
